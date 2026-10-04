#!/usr/bin/env python3
"""Step 3: two PNG charts from summary.json and data.csv only (matplotlib is not installed here, so PIL)."""
import csv, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../assets"))
from PIL import Image, ImageDraw
from make_images import F, BG, INK, MUTED, LIME
S = json.load(open(f"{HERE}/summary.json")); n = S["listed"]
# chart 1: job categories
cats = list(S["category_counts"].items())
W, H = 1200, 170 + 66 * len(cats) + 70
im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
d.text((48, 34), "What the top 100 skills do", font=F("B", 36), fill=INK)
d.text((48, 84), "Skills.sh all-time installs, 2026-10-04. Job category by published keyword rules.", font=F("R", 21), fill=MUTED)
y = 140; x0 = 520; wmax = 560; mx = max(c for _, c in cats)
for name, c in cats:
    d.text((48, y + 8), name[:44], font=F("M", 22), fill=INK)
    d.rounded_rectangle([x0, y + 4, x0 + wmax, y + 46], radius=8, fill="#17503f")
    d.rounded_rectangle([x0, y + 4, x0 + max(6, int(wmax * c / mx)), y + 46], radius=8, fill=LIME)
    d.text((x0 + wmax + 18, y + 8), f"{c} of {n}", font=F("B", 22), fill=INK); y += 66
d.text((48, H - 46), "Source: gtm/study/top-skills/data.csv. Keyword rules are in analyze.py. Some categories mix skills from one publisher.", font=F("R", 17), fill=MUTED)
im.save(f"{HERE}/chart-jobs.png", optimize=True)
# chart 2: concentration
items = [("Top 3 publishers", S["conc3"]), ("Top 5 publishers", S["conc5"]), ("Top 10 publishers", S["conc10"])]
W, H = 1200, 600
im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
d.text((48, 34), "A few publishers hold most of the top 100", font=F("B", 36), fill=INK)
d.text((48, 84), f"Share of the {n} listed skills, and of their install counts. {S['publishers']} publishers in total.", font=F("R", 21), fill=MUTED)
y = 150
for name, c in items:
    sk = c["skills"] * 100 / n
    d.text((48, y + 22), name, font=F("M", 24), fill=INK)
    for k, (val, label, col) in enumerate([(sk, f"{c['skills']}% of skills", LIME), (c["installs_pct"], f"{c['installs_pct']}% of installs", "#7fb069")]):
        yy = y + k * 56
        d.rounded_rectangle([340, yy + 4, 340 + 640, yy + 46], radius=8, fill="#17503f")
        d.rounded_rectangle([340, yy + 4, 340 + max(6, int(640 * val / 100)), yy + 46], radius=8, fill=col)
        d.text((340 + 660, yy + 8), label, font=F("B", 22), fill=INK)
    y += 140
d.text((48, H - 46), "Source: gtm/study/top-skills/summary.json. Publisher = owner part of the skills.sh source id.", font=F("R", 17), fill=MUTED)
im.save(f"{HERE}/chart-publishers.png", optimize=True)
print("ok")
