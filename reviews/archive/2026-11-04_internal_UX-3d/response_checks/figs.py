"""Before/after figures of the processing (JPEG, each under 300 KB) from the outputs of lanes_ab.sh / look_ab.mjs.

    python3 figs.py <outputs folder> <figs folder>

Each figure is a row of panels with a caption strip above each (orig = before the processing, new = after)."""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont

FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"]


def font():
    for f in FONTS:
        if os.path.exists(f):
            return ImageFont.truetype(f, 12)
    return None  # the default bitmap font: Latin captions only

FIGS = [  # name, [(panel file relative to the outputs folder, caption)]
    ("r01_volume_depth", [("final/probe_volsphere_orig/b_cloud_with_spheres.jpg", "A1 before: back sphere drawn over the lobe"),
                          ("final/probe_volsphere_new/b_cloud_with_spheres.jpg", "A1 after: the lobe in front covers it")]),
    ("r02_plane_and_volume", [("final/probe_planevol_orig/a_plane_on.jpg", "A2 before: slice hides the cloud in front"),
                              ("final/probe_planevol_new/a_plane_on.jpg", "A2 after: cloud in front drawn over the slice")]),
    ("r03_two_planes", [("final/probe_twoplanes_orig/b_current.jpg", "A2 before: plane 2 over all of plane 1"),
                        ("final/probe_twoplanes_new/b_current.jpg", "A2 after: right at every pixel")]),
    ("r04_views_2d", [("final/p02_dslit_orig/0_default.jpg", "A3 before: p02 opened from below"),
                      ("final/p02_dslit_new/0_default.jpg", "A3 after: from above"),
                      ("final/p04_cyl_orig/v_top.jpg", "A3 before: p04 «Сверху» edge-on"),
                      ("final/p04_cyl_new/v_top.jpg", "A3 after: «Сверху» face-on, x right")]),
    ("r05_first_view", [("final/v12_gauss_orig/0_default.jpg", "A4 before: v12 opened cropped"),
                        ("final/v12_gauss_new/0_default.jpg", "A4 after: 8 of 8 corners"),
                        ("final/v11_narrow_orig/0_default.jpg", "A4 before: v11"),
                        ("final/v11_narrow_new/0_default.jpg", "A4 after: v11")]),
    ("r06_lit", [("final/probe_flat_orig/c_basic_zoom.jpg", "A5 before: atoms as flat discs"),
                 ("final/probe_flat_new/c_basic_zoom.jpg", "A5 after: lit sphere impostors"),
                 ("lookF/v13_3dm2_orig/b_no_planes.jpg", "A5 before: current arrows flat"),
                 ("lookF/v13_3dm2_new/b_no_planes.jpg", "A5 after: lit arrows inside the cloud")]),
    ("r07_box_growth", [("final/probe_boxjump_orig/b_after_box_grew.jpg", "A7/U1 before: view reset when the box grew"),
                        ("final/probe_boxjump_new/b_after_box_grew.jpg", "A7/U1 after: the user's view kept")]),
    ("r08_zoom_out", [("final/v08_double_orig/6_zoomout.jpg", "A8 before: zoomed out, blank"),
                      ("final/v08_double_new/6_zoomout.jpg", "A8 after: still drawn")]),
    ("r09_labels", [("final/v08_double_orig/v_beam.jpg", "A9 before: far labels over the screen"),
                    ("final/v08_double_new/v_beam.jpg", "A9 after: labels on outer edges, px size"),
                    ("final/p01_sun_earth_orig/0_default.jpg", "A9 before: z label on a vertical edge"),
                    ("final/p01_sun_earth_new/0_default.jpg", "A9 after: placed by up")]),
    ("r10_volume_units", [("lookF/v13_1s_orig/b_no_planes.jpg", "A10 before: v13 1s nearly invisible"),
                          ("lookF/v13_1s_new/b_no_planes.jpg", "A10 after: tau = 4"),
                          ("lookF/v14_cc1S_orig/b_no_planes.jpg", "A10 before: v14 1S"),
                          ("lookF/v14_cc1S_new/b_no_planes.jpg", "A10 after")]),
    ("r12_v10_floor", [("final/v10_terrell_orig/0_default.jpg", "A12 before: floor as zig-zag bands"),
                       ("final/v10_terrell_new/0_default.jpg", "A12 after: one colour per cell")]),
    ("r14_top_view", [("final/v08_double_orig/v_top.jpg", "A14 before: «Сверху» z down"),
                      ("final/v08_double_new/v_top.jpg", "A14 after: z right, x up (as the window)")]),
    ("r19_zfight", [("final/probe_zfight_orig/a_through_light.jpg", "A19 before: dot grid over the screen"),
                    ("final/probe_zfight_new/a_through_light.jpg", "A19 after")]),
    ("r20_translucent", [("lookF/v17_near_orig/a_opened.jpg", "A2/A5 before: v17 near"),
                         ("lookF/v17_near_new/a_opened.jpg", "A2/A5 after"),
                         ("lookF/p02_ball3d_orig/b_no_planes.jpg", "A1 before: p02 ball cuts the packet"),
                         ("lookF/p02_ball3d_new/b_no_planes.jpg", "A1 after")]),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src"); ap.add_argument("dst")
    a = ap.parse_args()
    os.makedirs(a.dst, exist_ok=True)
    for name, panels in FIGS:
        ims = []
        for rel, cap in panels:
            p = os.path.join(a.src, rel)
            if not os.path.exists(p):
                print("missing", p); continue
            im = Image.open(p).convert("RGB")
            s = 420 / im.height
            im = im.resize((int(im.width * s), 420))
            fnt = font()
            text = cap if fnt else cap.encode("ascii", "replace").decode()
            d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
            lines, cur = [], ""
            for w in text.split():  # wrapped to the panel's width
                t = (cur + " " + w).strip()
                if cur and d0.textlength(t, font=fnt) > im.width - 8:
                    lines.append(cur); cur = w
                else:
                    cur = t
            lines.append(cur)
            strip = Image.new("RGB", (im.width, 44), (240, 240, 240))
            for k, ln in enumerate(lines[:3]):
                ImageDraw.Draw(strip).text((4, 1 + 14 * k), ln, fill=(0, 0, 0), font=fnt)
            col = Image.new("RGB", (im.width, 464)); col.paste(strip, (0, 0)); col.paste(im, (0, 44))
            ims.append(col)
        if not ims:
            continue
        m = Image.new("RGB", (sum(i.width for i in ims) + 6 * (len(ims) - 1), 464), (255, 255, 255))
        x = 0
        for i in ims:
            m.paste(i, (x, 0)); x += i.width + 6
        out = os.path.join(a.dst, name + ".jpg")
        for q in (80, 65, 50, 40):
            m.save(out, quality=q)
            if os.path.getsize(out) < 290 * 1024:
                break
        print(name, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
