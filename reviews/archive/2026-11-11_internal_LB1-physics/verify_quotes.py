# Reviewer's check that every quotation in REVIEW.md occurs in the text extracted (pdftotext 22.x) from the downloaded
# source. The sources are kept outside the repository (see REVIEW.md, "Sources"); pass their folder as the argument.
# Whitespace (line breaks, layout spaces) is collapsed before matching; nothing else is normalised.
import argparse
import pathlib
import re

QUOTES = [
    ("lagrava_thesis.txt", "with the exception that the rescaling is applied before the collision"),
    ("lagrava_thesis.txt", "We consider that the convective scaling is used."),
    ("lagrava_thesis.txt", "The authors find that a constant relates the post–collision non–equilibrium part"),
    ("lagrava_thesis.txt", "a four-point symmetric cubic interpolation is mandatory, as it ensures that the method remains "
                           "second order accurate"),
    ("lagrava_thesis.txt", "the non-equilibrium part fineq = fi − fieq is proportional to the gradient of the velocity, it "
                           "is therefore necessary to rescale it when communi- cating it between grids"),
    ("cond-mat_9903423.txt", "however, the second term is deliberately omitted in order to achieve independent "
                             "fluctuations of L and ~si"),
    ("cond-mat_9903423.txt", "The Andersen method [8] uses the box volume V = Ld and the scaled coordinates"),
    ("cond-mat_0403756.txt", "These equations introduce the volume V as a dynam-"),
    ("bpt1972.txt", "relative to the LNRF has components"),
    ("bpt1972.txt", "the locally nonrotating frames (LNRF) for which the observers"),
    ("an14.txt", "These surfaces are referred to as the outer (r+ ) and inner (r− ) horizons"),
]


def norm(s):
    return re.sub(r"\s+", " ", s)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="verify the review's quotations against the extracted source texts")
    ap.add_argument("src", help="folder with the extracted .txt files")
    a = ap.parse_args()
    ok = True
    for f, q in QUOTES:
        t = norm(pathlib.Path(a.src, f).read_text(encoding="utf-8", errors="replace"))
        hit = norm(q) in t
        ok &= hit
        print(f"{'FOUND ' if hit else 'MISSING'} {f}: {q[:90]}")
    print("all found" if ok else "SOME MISSING")
