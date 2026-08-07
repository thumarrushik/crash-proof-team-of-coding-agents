import sys, json, re
try:
    d = json.load(sys.stdin)
    rules = json.load(open(".claude/rules.json"))
except Exception:
    sys.exit(0)
tool = d.get("tool_name", "")
cmd = (d.get("tool_input") or {}).get("command", "")
cmd = re.sub(r"^\s*cd\s+\S+\s*&&\s*", "", cmd)   # ignore a leading `cd X &&`
for r in rules:
    hit = None
    if r.get("kind") == "bash_regex" and tool == "Bash" and re.match(r["pattern"], cmd):
        hit = {"rule": r["name"], "cmd": cmd[:120]}
    elif r.get("kind") == "tool_use" and tool in r.get("tools", "").split(","):
        path = str((d.get("tool_input") or {}).get("file_path", ""))
        if path.split("/")[-1] not in r.get("exclude_paths", []):
            hit = {"rule": r["name"], "tool": tool}
    if hit:
        with open(".claude/rule-flags.jsonl", "a") as f:
            f.write(json.dumps(hit) + "\n")
