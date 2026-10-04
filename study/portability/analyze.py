#!/usr/bin/env python3
"""Step 2: measure each fetched SKILL.md with regexes. No model judging. Output: data.csv (one row per fetched skill) and summary.json.
Run: python3 analyze.py   (needs fetch.py to have run: raw/, fetch_log.csv, trees.json)"""
import csv, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
log = [r for r in csv.DictReader(open(f"{HERE}/fetch_log.csv")) if r["status"] == "ok"]
trees = json.load(open(f"{HERE}/trees.json"))

VENDOR_TOOLS = {  # tool names that only exist in one agent product
 "WebFetch": r"\bWebFetch\b", "WebSearch": r"\bWebSearch\b", "TodoWrite": r"\bTodoWrite\b", "AskUserQuestion": r"\bAskUserQuestion\b",
 "NotebookEdit": r"\bNotebookEdit\b", "ExitPlanMode": r"\bExitPlanMode\b", "Bash(...)": r"\bBash\(", "Task tool": r"\bTask tool\b|\bTask\(",
 "Skill tool": r"\bSkill tool\b", "mcp__": r"\bmcp__\w+", "named tool (Read/Write/Edit/Glob/Grep tool)": r"\b(?:Read|Write|Edit|Glob|Grep) tool\b",
}
PRODUCTS = {  # agent product names written into the instructions
 "Claude Code": r"\bClaude Code\b", "claude.ai": r"\bclaude\.ai\b", "Cursor": r"\bCursor\b", "Codex": r"\bCodex\b",
 "Gemini CLI": r"\bGemini CLI\b", "Copilot": r"\bCopilot\b", "CLAUDE.md/GEMINI.md file": r"\b(?:CLAUDE|GEMINI)\.md\b",
}
PATHS = {  # vendor-specific folders and env vars
 "~/.claude or .claude/": r"(?:~/|\./|\b)\.claude/", "~/.cursor or .cursor/": r"\.cursor/", "~/.codex or .codex/": r"\.codex/",
 "~/.gemini or .gemini/": r"\.gemini/", "$CLAUDE_* env var": r"\$\{?CLAUDE_\w+",
}
GENERIC_PATH = r"\.agents/"
FALLBACK = re.compile(r"(?:if|when)\s+(?:you\s+)?(?:can ?not|can't|cannot|don't have|do not have|have no|are unable|aren't able|unable to|is not available|isn't available|are not available|is unavailable|no access)|fall ?back|otherwise,?\s+(?:ask|use|paste)|ask the user to (?:paste|provide|supply)|if .{0,40}(?:isn't|is not|not) installed", re.I)
# keys named in the public Agent Skills spec (agentskills.io) besides name and description
SPEC_KEYS = {"license", "compatibility", "metadata", "allowed-tools"}
SCRIPT_EXT = {".py": "Python", ".sh": "shell", ".bash": "shell", ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".ts": "TypeScript", ".rb": "Ruby", ".go": "Go", ".ps1": "PowerShell"}

def frontmatter(text):
    m = re.match(r"---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m: return None, text
    keys = []
    for line in m.group(1).splitlines():
        k = re.match(r"^([A-Za-z0-9_-]+)\s*:", line)
        if k: keys.append(k.group(1))
    return keys, text[m.end():]

rows = []
for r in log:
    text = open(f"{HERE}/raw/{int(r['rank']):03d}-{r['skill']}.md").read()
    keys, body = frontmatter(text)
    dm = re.search(r"^description:\s*(.*?)(?=^\w[\w-]*:|\Z)", text.split("---",2)[1] if text.startswith("---") else "", re.S | re.M)
    desc = re.sub(r"\s+", " ", dm.group(1)).strip().strip(">|-").strip() if dm else ""
    extra = [k for k in (keys or []) if k not in ("name", "description")]
    row = dict(rank=r["rank"], source=r["source"], skill=r["skill"], installs=r["installs"], lines=len(text.splitlines()),
               has_frontmatter=int(keys is not None), description_chars=len(desc), extra_keys=";".join(extra), n_extra_keys=len(extra),
               has_allowed_tools=int(any(k in ("allowed-tools", "allowed_tools", "tools") for k in extra)))
    for n, p in VENDOR_TOOLS.items(): row["tool:" + n] = len(re.findall(p, text))  # whole file, frontmatter included
    nonspec = [k for k in extra if k not in SPEC_KEYS]
    row["nonspec_keys"] = ";".join(nonspec); row["n_nonspec_keys"] = len(nonspec)
    row["vendor_tool_hits"] = sum(row["tool:" + n] for n in VENDOR_TOOLS)
    for n, p in PRODUCTS.items(): row["product:" + n] = len(re.findall(p, body))
    row["product_hits"] = sum(row["product:" + n] for n in PRODUCTS)
    for n, p in PATHS.items(): row["path:" + n] = len(re.findall(p, body))
    row["vendor_path_hits"] = sum(row["path:" + n] for n in PATHS)
    row["generic_agents_path"] = len(re.findall(GENERIC_PATH, body))
    d = r["path"][: -len("SKILL.md")]
    files = [p for p in trees[r["source"]] if p.startswith(d)] if d else list(trees[r["source"]])
    langs = sorted({SCRIPT_EXT[os.path.splitext(p)[1]] for p in files if os.path.splitext(p)[1] in SCRIPT_EXT})
    row["files_in_skill_dir"] = len(files)
    row["bundled_script_langs"] = ";".join(langs); row["has_script"] = int(bool(langs))
    row["has_references_dir"] = int(any("/references/" in "/" + p[len(d):] or p[len(d):].startswith("references/") for p in files))
    row["fallback_phrase"] = int(bool(FALLBACK.search(body)))
    row["any_vendor_coupling"] = int(row["vendor_tool_hits"] + row["product_hits"] + row["vendor_path_hits"] + row["has_allowed_tools"] + row["n_nonspec_keys"] > 0)
    rows.append(row)
cols = list(rows[0].keys())
with open(f"{HERE}/data.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

from collections import Counter
n = len(rows)
def cnt(pred): return sum(1 for r in rows if pred(r))
S = dict(sample=n, repos=len({r["source"] for r in rows}),
 with_extra_keys=cnt(lambda r: r["n_extra_keys"] > 0), with_allowed_tools=cnt(lambda r: r["has_allowed_tools"]),
 vendor_tool_names=cnt(lambda r: r["vendor_tool_hits"] > 0), product_names=cnt(lambda r: r["product_hits"] > 0),
 vendor_paths=cnt(lambda r: r["vendor_path_hits"] > 0), generic_agents_path=cnt(lambda r: r["generic_agents_path"] > 0),
 any_coupling=cnt(lambda r: r["any_vendor_coupling"]), no_coupling=cnt(lambda r: not r["any_vendor_coupling"]),
 has_script=cnt(lambda r: r["has_script"]), fallback_phrase=cnt(lambda r: r["fallback_phrase"]),
 coupled_with_fallback=cnt(lambda r: r["any_vendor_coupling"] and r["fallback_phrase"]),
 coupled_without_fallback=cnt(lambda r: r["any_vendor_coupling"] and not r["fallback_phrase"]),
 lines_median=sorted(r["lines"] for r in rows)[n // 2], lines_max=max(r["lines"] for r in rows), over_500=cnt(lambda r: r["lines"] > 500), over_200=cnt(lambda r: r["lines"] > 200))
S["description_over_1024"] = cnt(lambda r: r["description_chars"] > 1024)
S["description_median_chars"] = sorted(r["description_chars"] for r in rows)[n // 2]
S["installs_total"] = sum(int(r["installs"]) for r in rows)
S["installs_in_coupled"] = sum(int(r["installs"]) for r in rows if r["any_vendor_coupling"])
S["body_only_coupling"] = cnt(lambda r: r["vendor_tool_hits"] - r["tool:Bash(...)"] + r["product_hits"] + r["vendor_path_hits"] > 0)
S["top3_publishers_skills"] = sum(v for _, v in Counter(r["source"] for r in rows).most_common(3))
S["no_extra_keys"] = cnt(lambda r: r["n_extra_keys"] == 0)
S["scripts_and_fallback"] = cnt(lambda r: r["has_script"] and r["fallback_phrase"])
S["with_nonspec_keys"] = cnt(lambda r: r["n_nonspec_keys"] > 0)
S["nonspec_key_names"] = Counter(k for r in rows for k in r["nonspec_keys"].split(";") if k).most_common()
S["tool_breakdown"] = {k: cnt(lambda r, k=k: r["tool:" + k] > 0) for k in VENDOR_TOOLS}
S["product_breakdown"] = {k: cnt(lambda r, k=k: r["product:" + k] > 0) for k in PRODUCTS}
S["path_breakdown"] = {k: cnt(lambda r, k=k: r["path:" + k] > 0) for k in PATHS}
from collections import Counter
S["extra_key_names"] = Counter(k for r in rows for k in r["extra_keys"].split(";") if k).most_common()
S["script_langs"] = Counter(l for r in rows for l in r["bundled_script_langs"].split(";") if l).most_common()
S["no_frontmatter"] = cnt(lambda r: not r["has_frontmatter"])
S["with_references_dir"] = cnt(lambda r: r["has_references_dir"])
# repo-level view so one big vendor set cannot dominate
repos = {}
for r in rows: repos.setdefault(r["source"], []).append(r)
S["repos_with_any_coupling"] = sum(1 for v in repos.values() if any(x["any_vendor_coupling"] for x in v))
S["repos_all_clean"] = sum(1 for v in repos.values() if all(not x["any_vendor_coupling"] for x in v))
S["skipped_total"] = len(list(csv.DictReader(open(f"{HERE}/fetch_log.csv")))) - n
json.dump(S, open(f"{HERE}/summary.json", "w"), indent=1)
print(json.dumps(S, indent=1))
