#!/usr/bin/env python3
"""Step 1: fetch SKILL.md for each skill in top100.json (skills.sh all-time installs, 2026-10-04).
Locates the file via one GitHub tree listing per repo (git/trees), then one raw fetch per file, 0.5 s apart.
Sources that are not github.com owner/repo (e.g. a vendor domain) are skipped and recorded. Output: raw/<n>-<skillId>.md, fetch_log.csv"""
import json, os, subprocess, time, csv, re, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(f"{HERE}/raw", exist_ok=True)
top = json.load(open(f"{HERE}/top100.json"))
def curl(u):
    r = subprocess.run(["curl", "-sL", "-m", "30", "-A", "psp-portability-study", "-w", "\n%{http_code}", u], capture_output=True, text=True)
    body, _, code = r.stdout.rpartition("\n")
    return code, body
trees = {}
alltrees = {}
log = []
for rank, (src, sid, inst) in enumerate(top, 1):
    row = dict(rank=rank, source=src, skill=sid, installs=inst, status="", path="")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", src) or src.split("/")[0].count(".") and "." in src.split("/")[0]:
        row["status"] = "skipped: not a github owner/repo source"; log.append(row); continue
    if src not in trees:
        time.sleep(0.5)
        code, body = curl(f"https://api.github.com/repos/{src}/git/trees/HEAD?recursive=1")
        try:
            allp = [t["path"] for t in json.loads(body)["tree"] if t["type"] == "blob"]
            alltrees[src] = allp
            trees[src] = [p for p in allp if p.endswith("SKILL.md")]
        except Exception: trees[src] = None
    paths = trees[src]
    if not paths:
        row["status"] = "skipped: repo tree unavailable or no SKILL.md"; log.append(row); continue
    cand = [p for p in paths if p.rsplit("/", 2)[-2:-1] == [sid]] or [p for p in paths if p == "SKILL.md" and False]
    if not cand:
        cand = [p for p in paths if f"/{sid}/" in "/" + p]
    if not cand:
        row["status"] = "skipped: skill folder not found in repo"; log.append(row); continue
    p = sorted(cand, key=len)[0]; row["path"] = p
    time.sleep(0.5)
    code, body = curl(f"https://raw.githubusercontent.com/{src}/HEAD/{urllib.parse.quote(p)}")
    if code != "200":
        row["status"] = f"skipped: raw fetch {code}"; log.append(row); continue
    open(f"{HERE}/raw/{rank:03d}-{sid}.md", "w").write(body)
    row["status"] = "ok"; log.append(row)
with open(f"{HERE}/fetch_log.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(log[0].keys())); w.writeheader(); w.writerows(log)
json.dump(alltrees, open(f"{HERE}/trees.json", "w"))
from collections import Counter
print(Counter(r["status"] for r in log))
