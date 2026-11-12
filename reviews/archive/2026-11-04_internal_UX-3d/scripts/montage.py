#!/usr/bin/env python3
"""Montage of screenshots for viewing (and for the review: each output JPEG under 300 KB).
usage: montage.py out.jpg [--h H] [--q Q] img1[:caption] img2[:caption] ..."""
import sys
from PIL import Image, ImageDraw, ImageFont

args = sys.argv[1:]
out = args.pop(0)
H, Q, cols = 520, 70, 0
while args and args[0].startswith("--"):
    k = args.pop(0)
    if k == "--h": H = int(args.pop(0))
    elif k == "--q": Q = int(args.pop(0))
    elif k == "--cols": cols = int(args.pop(0))
ims = []
for a in args:
    p, _, cap = a.partition(":")
    im = Image.open(p).convert("RGB")
    w = int(im.width * H / im.height)
    im = im.resize((w, H), Image.LANCZOS)
    if cap:
        d = ImageDraw.Draw(im)
        try:
            f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except Exception:
            f = ImageFont.load_default()
        tw = d.textlength(cap, font=f)
        d.rectangle([0, H - 24, tw + 10, H], fill=(255, 230, 0))
        d.text((5, H - 22), cap, fill=(0, 0, 0), font=f)
    ims.append(im)
cols = cols or len(ims)
rows = [ims[i:i + cols] for i in range(0, len(ims), cols)]
W = max(sum(i.width for i in r) + 4 * (len(r) - 1) for r in rows)
out_im = Image.new("RGB", (W, len(rows) * H + 4 * (len(rows) - 1)), (255, 255, 255))
y = 0
for r in rows:
    x = 0
    for im in r:
        out_im.paste(im, (x, y)); x += im.width + 4
    y += H + 4
q = Q
while True:
    out_im.save(out, quality=q, optimize=True)
    import os
    if os.path.getsize(out) < 290 * 1024 or q <= 30:
        break
    q -= 8
print(out, out_im.size, os.path.getsize(out) // 1024, "KB q", q)
