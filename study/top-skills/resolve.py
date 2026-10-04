#!/usr/bin/env python3
"""Step 1b: second try for skills fetch.py could not place. Rules, no judgement:
 (a) if the repo has at most 15 SKILL.md files not already matched to another top-100 skill, fetch those (one fetch each, 0.5 s apart)
     and accept the one whose frontmatter `name` equals the skills.sh id (folder name differs from the skill name);
 (b) else if the repo tree has a path containing 'remove-<id>', record 'removed from the repo (a removal changeset exists)';
 (c) else record 'no SKILL.md folder or name matches this id in the repo tree'.
Updates fetch_log.csv and raw/. Run after fetch.py."""
import csv, json, os, re, subprocess, time, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(f"{HERE}/fetch_log.csv")))
trees = json.load(open(f"{HERE}/trees.json"))
claimed = {}
for r in rows:
    if r["status"] == "ok": claimed.setdefault(r["source"], set()).add(r["path"])
def raw(src, p):
    r = subprocess.run(["curl", "-sL", "-m", "30", "-A", "psp-top-skills-study", "-w", "\n%{http_code}", f"https://raw.githubusercontent.com/{src}/HEAD/{urllib.parse.quote(p)}"], capture_output=True, text=True)
    b, _, c = r.stdout.rpartition("\n"); return c, b
for r in rows:
    if not r["status"].startswith("skipped: skill folder not found"): continue
    src, sid = r["source"], r["skill"]
    cands = [p for p in trees[src] if p.endswith("/SKILL.md") and p not in claimed.get(src, set())]
    hit = None
    if len(cands) <= 15:
        for p in cands:
            time.sleep(0.5); c, b = raw(src, p)
            m = re.search(r"^name:\s*(\S+)", b, re.M)
            if c == "200" and m and m.group(1).strip("\"'") == sid: hit = (p, b); break
    if hit:
        open(f"{HERE}/raw/{int(r['rank']):03d}-{sid}.md", "w").write(hit[1])
        r["status"], r["path"] = "ok", hit[0]
    elif any(("remove-" + sid) in p for p in trees[src]):
        r["status"] = "skipped: removed from the repo (a removal changeset exists)"
    else:
        r["status"] = "skipped: no SKILL.md folder or name matches this id in the repo tree"
with open(f"{HERE}/fetch_log.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
from collections import Counter
print(Counter(r["status"] for r in rows))
