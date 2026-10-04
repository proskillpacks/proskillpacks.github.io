#!/usr/bin/env python3
"""Step 2: classify and measure the top 100 skills.sh skills. No model judging: keyword rules below, regexes, file lists, arithmetic.
Inputs: top100.json, fetch_log.csv, trees.json, raw/. Outputs: data.csv (one row per listed skill), summary.json.
JOB CATEGORY RULES (first match wins; the skill's NAME is tried against all rules first, then its DESCRIPTION if fetched):"""
import csv, json, os, re
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__))
RULES = [  # (category, audience, keywords)
 ("Workspace apps (mail, calendar, docs, tasks)", "business", ["lark", "feishu", "calendar", "mail", "spreadsheet", "sheets", "slides", "wiki", "meeting", "approval", "okr", "attendance", "drive", "notion", "obsidian", "gmail", "workspace", "standup"]),
 ("Image, video and audio generation", "creative", ["video", "image", "audio", "music", "avatar", "photo", "thumbnail", "lipsync", "inpaint", "outpaint", "remotion", "nano-banana", "flux", "kling", "seedance", "hyperframes", "face-swap", "relight", "controlnet", "wan-", "higgsfield", "motion", "gif"]),
 ("Marketing, SEO and sales", "business", ["seo", "marketing", "copywriting", "copy-editing", "content-strategy", "ad-creative", "ads", "cold-email", "churn", "sales", "revops", "lead", "pricing", "launch", "social", "cro", "funnel", "email", "directory-submissions", "competitor", "customer-research", "product-marketing", "conversion", "upsell", "twitter", "reddit"]),
 ("UI and frontend design", "developer", ["ui", "ux", "frontend", "css", "tailwind", "typography", "animate", "polish", "layout", "shadcn", "taste", "colorize", "bolder", "quieter", "delight", "distill", "adapt", "critique", "mobile-apps", "react", "composition", "web-"]),
 ("Cloud, database and vendor platforms", "developer", ["azure", "aws", "gcp", "firebase", "supabase", "cloudflare", "prisma", "convex", "neon", "postgres", "vercel", "stripe", "sentry", "wrangler", "deploy", "database", "entra", "kusto", "foundry", "adk", "agents-cli"]),
 ("Agent, browser and skill tooling", "developer", ["skill", "agent", "mcp", "orchestrat", "browser", "scrape", "firecrawl", "caveman", "find-", "hyperframes-cli", "cli", "automation"]),
 ("Dev workflow: review, testing, planning", "developer", ["tdd", "test", "debug", "merge", "review", "refactor", "architecture", "handoff", "triage", "grill", "prototype", "plan", "spec", "implement", "domain", "codebase", "commit", "brainstorm", "verification", "setup", "research", "teach", "ticket", "diagnos", "wayfinder", "ask-", "writing", "paper", "repo", "explore", "run", "safe"]),
]
def tokens(text): return re.findall(r"[a-z0-9]+", text.lower())
def hit(toks, kws):
    # a keyword matches a whole word; keywords of 5 or more letters also match as a word start (orchestrat -> orchestration)
    return any(t == k or (len(k) >= 5 and t.startswith(k)) for t in toks for k in kws)
UI_WORD = {"frontend", "web", "mobile", "ui", "ux", "taste", "visual"}
def classify(name, desc):
    for text in (name, desc):
        if not text: continue
        toks = tokens(text)
        for cat, aud, kws in RULES:
            k2 = kws + (["design"] if (cat == "UI and frontend design" and UI_WORD & set(toks)) else [])
            if hit(toks, [k.strip("-") for k in k2]): return cat, aud
    return "Other or unclear", "other"
WHEN = re.compile(r"use (this skill |it )?(when|for|to)\b|when (the user|you|users|someone|asked|asking)|should be used when|triggers? (on|when)|invoke when|use whenever", re.I)
SCRIPT_EXT = {".py": "Python", ".sh": "shell", ".bash": "shell", ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".ts": "TypeScript", ".rb": "Ruby", ".go": "Go", ".ps1": "PowerShell"}
top = json.load(open(f"{HERE}/top100.json")); log = {int(r["rank"]): r for r in csv.DictReader(open(f"{HERE}/fetch_log.csv"))}
trees = json.load(open(f"{HERE}/trees.json"))
fetched_ids = {r["skill"] for r in log.values() if r["status"] == "ok"}
def fm(text):
    m = re.match(r"---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m: return "", text
    d = re.search(r"^description:\s*(.*?)(?=^\w[\w-]*:|\Z)", m.group(1), re.S | re.M)
    desc = re.sub(r"\s+", " ", d.group(1)).strip().strip(">|-").strip().strip("\"'") if d else ""
    return desc, text[m.end():]
rows = []
for i, (src, sid, inst) in enumerate(top, 1):
    l = log[i]; ok = l["status"] == "ok"
    pub = src.split("/")[0]
    row = dict(rank=i, source=src, publisher=pub, skill=sid, installs=inst, fetched=int(ok), not_fetched_reason="")
    desc = ""; lines = 0; langs = []
    if ok:
        text = open(f"{HERE}/raw/{i:03d}-{sid}.md").read(); desc, body = fm(text); lines = len(text.splitlines())
        d = l["path"][:-len("SKILL.md")]
        files = [p for p in trees[src] if p.startswith(d)] if d else list(trees[src])
        langs = sorted({SCRIPT_EXT[os.path.splitext(p)[1]] for p in files if os.path.splitext(p)[1] in SCRIPT_EXT})
    else:
        r = l["status"].replace("skipped: ", "")
        if r.startswith("not a github"):
            r = "source is a vendor domain, not a GitHub repo" + ("; same skill id fetched from a GitHub source" if sid in fetched_ids else "; same skill id not fetched elsewhere")
        row["not_fetched_reason"] = r
    cat, aud = classify(sid, desc)
    row.update(category=cat, audience=aud, lines=lines if ok else "", description_chars=len(desc) if ok else "",
               says_when_to_use=int(bool(WHEN.search(desc))) if ok else "", has_script=int(bool(langs)) if ok else "", script_langs=";".join(langs),
               class_basis="name" if classify(sid, "")[0] != "Other or unclear" else ("description" if ok and cat != "Other or unclear" else "none"))
    rows.append(row)
with open(f"{HERE}/data.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

n = len(rows); F = [r for r in rows if r["fetched"]]
inst = sorted((r["installs"] for r in rows), reverse=True); tot = sum(inst)
share = lambda k: round(100 * sum(inst[:k]) / tot, 1)
pubs_skills = Counter(r["publisher"] for r in rows)
pubs_inst = Counter()
for r in rows: pubs_inst[r["publisher"]] += r["installs"]
def conc(k): return dict(skills=sum(c for _, c in pubs_skills.most_common(k)), installs_pct=round(100 * sum(c for _, c in pubs_inst.most_common(k)) / tot, 1))
def bucket(vals, edges):
    out = []; lo = 0
    for e in edges: out.append((f"{lo}-{e}" if lo else f"up to {e}", sum(1 for v in vals if lo < v <= e) if lo else sum(1 for v in vals if v <= e))); lo = e
    out.append((f"over {edges[-1]}", sum(1 for v in vals if v > edges[-1]))); return out
lines_v = sorted(r["lines"] for r in F); dc = sorted(r["description_chars"] for r in F)
med = lambda v: v[len(v) // 2]
merged = Counter(); minst = Counter()
for r in rows:
    k = "lark (open.feishu.cn + larksuite)" if r["publisher"] in ("open.feishu.cn", "larksuite") else r["publisher"]
    merged[k] += 1; minst[k] += r["installs"]
conc3_merged = dict(skills=sum(c for _, c in merged.most_common(3)), installs_pct=round(100 * sum(minst[k] for k, _ in merged.most_common(3)) / tot, 1), publishers=[k for k, _ in merged.most_common(3)])
S = dict(conc3_lark_merged=conc3_merged, listed=n, fetched=len(F), not_fetched=n - len(F),
 not_fetched_reasons=dict(Counter(r["not_fetched_reason"] for r in rows if not r["fetched"])),
 category_counts=dict(Counter(r["category"] for r in rows).most_common()), audience_counts=dict(Counter(r["audience"] for r in rows)),
 classified_by_name=sum(1 for r in rows if r["class_basis"] == "name"), classified_by_description=sum(1 for r in rows if r["class_basis"] == "description"), other=sum(1 for r in rows if r["category"] == "Other or unclear"),
 publishers=len(pubs_skills), top_publishers=[(p, c, round(100 * pubs_inst[p] / tot, 1)) for p, c in pubs_skills.most_common(10)],
 conc3=conc(3), conc5=conc(5), conc10=conc(10),
 installs_total=tot, installs_rank1=inst[0], installs_rank10=inst[9], installs_rank50=inst[49], installs_rank100=inst[-1], installs_median=inst[n // 2],
 head_ratio_rank1_to_rank100=round(inst[0] / inst[-1], 1), share_top1=share(1), share_top10=share(10), share_top20=share(20), share_top50=share(50),
 over_1m=sum(1 for v in inst if v > 1_000_000), between_500k_1m=sum(1 for v in inst if 500_000 < v <= 1_000_000), under_500k=sum(1 for v in inst if v <= 500_000),
 lines_median=med(lines_v), lines_buckets=bucket(lines_v, [50, 100, 200, 500]), lines_max=lines_v[-1],
 desc_median=med(dc), desc_buckets=bucket(dc, [150, 300, 500, 1024]),
 says_when_to_use=sum(r["says_when_to_use"] for r in F), has_script=sum(r["has_script"] for r in F),
 script_langs=dict(Counter(l for r in F for l in r["script_langs"].split(";") if l)),
 vendor_authored_share_note="publisher = owner part of the skills.sh source id")
json.dump(S, open(f"{HERE}/summary.json", "w"), indent=1)
print(json.dumps({k: S[k] for k in ("listed", "fetched", "category_counts", "audience_counts", "other", "conc3", "conc5", "conc10", "top_publishers", "share_top10", "head_ratio_rank1_to_rank100", "lines_buckets", "desc_buckets", "says_when_to_use", "has_script", "script_langs", "not_fetched_reasons", "over_1m", "under_500k")}, indent=1))
