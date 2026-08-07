# EDGE-TAXONOMY — the inputs that break code, as a checklist

Run this taxonomy against **every input** of the unit under test —
parameters, payload fields, query params, file contents, environment.
It is a checklist, not inspiration: tick each class or state why it
cannot apply.

## The taxonomy

1. **Empty / null / missing.** `None`/`null`/`undefined`, empty string,
   empty list, empty object, field absent vs field present-but-null —
   these are different inputs and often hit different branches.
2. **Boundaries.** 0, 1, max, max+1; first/last element; the exact
   page-size; expiry at the second it expires. Off-by-one lives here —
   test both sides of every fence, not just "a big number".
3. **Duplicates and ordering.** Repeated elements, same key twice,
   already-sorted vs reverse-sorted vs shuffled input; anything that
   claims ordering gets a test that would fail if order flipped.
4. **Hostile strings.** Unicode (emoji, RTL, combining marks),
   leading/trailing/inner whitespace, injection-shaped content
   (`'; DROP`, `<script>`, `{{template}}`, path traversal `../`),
   very long strings. Hostile means "legal but adversarial" — these
   must be handled, not rejected by accident.
5. **Huge inputs.** The 10k-element list, the megabyte payload, the
   deeply nested object — where quadratic code and recursion limits
   announce themselves.
6. **Repeated and concurrent calls.** Same request twice (idempotency),
   interleaved calls on shared state, retry-after-partial-failure. If
   the code touches shared state, one test runs it in contention.
7. **Wrong types / malformed shapes.** String where int expected, list
   where object, truncated JSON — asserting the *designed* rejection
   (422 with machine code, TypeError with message), not a stack trace.

## The embarrassment question

After the checklist, ask: **"what input would embarrass us in
production?"** — the CEO's name with an apostrophe, the order placed at
23:59:59 on Dec 31, the user with zero items on the plan page. That
input is the missing test. Add it. The taxonomy catches classes; this
question catches the instance your domain makes inevitable.

## Using the taxonomy without bloating the suite

- One representative test per class per input is the floor; add more
  only where the class intersects a real branch.
- Parametrize (`pytest.mark.parametrize`, `test.each`) so ten inputs
  share one test body — ten copy-pasted tests hide the eleventh case.
- Each edge test still asserts the exact outcome (value, error code,
  message contract) — an edge input asserted with `is not None` is the
  taxonomy defeated by the assertion (see MUTATION.md).

## Grounding

- Classic boundary-value analysis and equivalence partitioning — the
  test-design lineage this checklist compresses.
- Google Testing Blog, "Code Coverage Best Practices" — untested
  branches hide exactly where unconsidered inputs live.
