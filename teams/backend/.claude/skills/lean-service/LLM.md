# LLM (and any optional / heavy dependency)

Applies to LLM clients, ML libs, or any heavy/optional integration. Three rules: **fail loud**, **stay
injectable**, **validate generated artifacts before persisting**.

## LLM endpoint-group file layout

ALL LLM-related code for an endpoint group lives in its own **`llm/`** package — a **sibling of `utils/`**
inside the group's services subfolder (same depth), so LLM concerns are isolated from the group's ordinary
shared logic:

```
src/v0/services/<group>/
  builder.py           # light wrapper for the /build endpoint — validates, calls llm.agent, persists
  utils/               # the group's NON-LLM shared logic (queries, validators, scorers)
    __init__.py
    <concern>.py
  llm/                 # ALL LLM code — a PACKAGE at the SAME DEPTH as utils/ (not inside it)
    __init__.py
    agent.py           # CORE LOGIC — the generate→validate→refine orchestration / graph; model injectable
    prompt.py          # SYSTEM PROMPT(s) + builders (prompt text lives here, never inline in agent.py)
    model.py           # STRUCTURED-OUTPUT Pydantic models (the typed shapes the model must return)
```

- **`agent.py`** holds the orchestration (the state machine / graph: generate → validate → refine →
  persist) and takes the model/generate-fn **injected** so it's mock-testable (see below).
- **`prompt.py`** holds every system/instruction prompt + builders — never inline prompt strings in the
  agent, so prompts are reviewable and tunable in one place.
- **`model.py`** holds the Pydantic models bound to the LLM's **structured output** (function/JSON-schema),
  so generation is typed, not free-text parsing.
- Keep non-LLM shared logic in `utils/`; keep everything LLM in `llm/`. The endpoint wrapper imports from
  `llm/` (and `utils/` as needed) and stays thin.
- **Name the wrapper `builder.py`, not `build.py`.** The group `__init__.py` re-exports the wrapper's
  `build()` function; if the module were also named `build`, the function would shadow the submodule and
  `from <group> import build` would return the function, not the module (see HARD-RULES.md).

## Optional deps fail loud

- Declare the libs as an **optional extra** in packaging (e.g. `[llm]`); bake them into the image only.
- **Lazy-import at the point of use** (inside the function, not module top) so the app boots without them.
- Missing lib OR missing credential (e.g. no API key) → raise a `DependencyError` → **503
  `ERR_DEPENDENCY_UNAVAILABLE`**. Never return a canned/fallback result. The message names what's missing.

## Stay injectable (so it's testable with no network/key)

- The component that calls the model takes the **generate/client function as a parameter**; the production
  path constructs the real one (lazy-import + key check), tests inject a deterministic fake.
- Result: the orchestration (generate → validate → refine → persist) is unit-tested with no network and no
  key, in CI, every run. Separately, exercise the **real transport** against a local OpenAI-compatible
  server (a stub or a local model) to prove request serialization + response parsing — without a paid call.
- Support a local/self-hosted backend via a base-URL override (e.g. `OPENAI_BASE_URL` + `OPENAI_MODEL`) so
  the real path runs for **free** against a local model (Ollama / LM Studio / vLLM). Paid hosted is just
  the default when no base URL is set.

## Validate generated artifacts before persisting (nothing faked)

LLM (or any generator) output is probabilistic and often "looks right" but isn't. Gate it:

1. **Compile/parse** it (regex → `re.compile`; code → AST allowlist; config → schema).
2. **Require it to satisfy the provided examples/spec** (a generated regex must match ≥1 example,
   case-insensitively if that's how it'll run; a proposed scoring rule must be scored against labeled
   examples and report accuracy).
3. **Refine ≤2×** by feeding the failure back; then **drop + report** what still fails. Never silently keep
   an invalid candidate. Return both what was created and what was rejected (with reasons).

Orchestrate this as a small state machine / graph (generate → validate → refine → persist) with the
generate node injectable per above.

## Safe-AST, never `eval`

If you accept user expressions (rule logic, filters, DSLs): parse to an AST, **allowlist only the node
types you need** (e.g. boolean ops, names, literals), interpret by hand, and reject everything else
(calls, attribute access, imports) with a clear validation error. Never `eval`/`exec` user input. Validate
referenced names exist (e.g. as known identifiers) up front.
