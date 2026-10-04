#!/usr/bin/env python3
"""Step 3: two PNG charts from data.csv only (matplotlib is not installed here, so PIL). Run: python3 charts.py"""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../assets"))
from PIL import Image, ImageDraw
from make_images import F, BG, INK, MUTED, LIME
rows = list(csv.DictReader(open(f"{HERE}/data.csv")))
n = len(rows)
def c(pred): return sum(1 for r in rows if pred(r))
def bars(fname, title, sub, items, note):
    W, H = 1200, 160 + 78 * len(items) + 80
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.text((48, 36), title, font=F("B", 36), fill=INK)
    d.text((48, 86), sub, font=F("R", 22), fill=MUTED)
    x0, wmax, y = 470, 600, 150
    for label, v, tot in items:
        d.text((48, y + 8), label, font=F("M", 24), fill=INK)
        d.rounded_rectangle([x0, y + 4, x0 + wmax, y + 48], radius=8, fill="#17503f")
        w = max(6, int(wmax * v / tot)); d.rounded_rectangle([x0, y + 4, x0 + w, y + 48], radius=8, fill=LIME)
        d.text((x0 + wmax + 20, y + 8), f"{v} of {tot}", font=F("B", 24), fill=INK)
        y += 78
    d.text((48, H - 52), note, font=F("R", 18), fill=MUTED)
    im.save(f"{HERE}/{fname}", optimize=True)
bars("chart-coupling.png", "What ties a skill to one agent", f"Share of {n} most-installed skills (SKILL.md files we could fetch)",
 [("Any of the below", c(lambda r: r["any_vendor_coupling"] == "1"), n),
  ("Extra key (non-spec or allowed-tools)", c(lambda r: int(r["n_nonspec_keys"]) > 0 or r["has_allowed_tools"] == "1"), n),
  ("Vendor tool name in text", c(lambda r: int(r["vendor_tool_hits"]) > 0), n),
  ("Agent product name in text", c(lambda r: int(r["product_hits"]) > 0), n),
  ("Vendor folder path (~/.claude etc.)", c(lambda r: int(r["vendor_path_hits"]) > 0), n)],
 "Source: gtm/study/portability/data.csv, skills.sh all-time installs, 2026-10-04. Regex counts, no model judging.")
langs = {}
for r in rows:
    for l in filter(None, r["bundled_script_langs"].split(";")): langs[l] = langs.get(l, 0) + 1
items = [("No bundled script", c(lambda r: r["has_script"] == "0"), n)] + [(f"{k}", v, n) for k, v in sorted(langs.items(), key=lambda x: -x[1])]
bars("chart-scripts.png", "Most skills are plain text", f"Bundled scripts in the skill folder, by language (a skill can have several)",
 items, "Source: gtm/study/portability/data.csv, file lists from the GitHub tree API, 2026-10-04.")
print("ok")
