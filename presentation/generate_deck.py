"""Generator of the case-study deck (PL and EN) — python-pptx.

Użycie:
    python presentation/generate_deck.py                  # tylko PL -> presentation/
    python presentation/generate_deck.py --lang en        # tylko EN
    python presentation/generate_deck.py --lang all       # oba decki
    python presentation/generate_deck.py --lang all --out-dir DIR   # poza repo (np. do porównania)

Wyjście (nazwy z pola "file" w JSON-ie):
    Bukowy_Dwor_Case_Study.pptx     (PL)
    Bukowy_Dwor_Case_Study_EN.pptx  (EN)

Źródło treści: presentation/content_pl.json i content_en.json (kanon, 1:1 z dawnego TEXTS).
Układ (kolory, funkcje slajdów): presentation/slides/. Grafiki: presentation/assets/.
deck_spec*.json NIE są czytane przez generator (historyczne, patrz presentation/README.md).
Ręczne HTML-e (prezentacja.html, presentation_en.html) też nie są generowane.
"""

import argparse
import json
import os

from pptx import Presentation
from pptx.util import Inches

from slides import SLIDES

HERE = os.path.dirname(os.path.abspath(__file__))
LANGS = ("pl", "en")


def load_content(lang):
    with open(os.path.join(HERE, f"content_{lang}.json"), encoding="utf-8") as fh:
        return json.load(fh)


def create_presentation(lang="pl", out_dir=HERE):
    t = load_content(lang)
    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9 widescreen
    prs.slide_height = Inches(7.5)

    assets = os.path.join(HERE, "assets")
    for build in SLIDES:
        build(prs, t, assets)

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, t["file"])
    prs.save(out_path)
    print(f"[{lang}] deck generated: {out_path}")
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate the Bukowy Dwor case-study deck (PL/EN).")
    parser.add_argument("--lang", choices=["pl", "en", "all"], default="pl",
                        help="which deck to build (default: pl)")
    parser.add_argument("--out-dir", default=HERE,
                        help="where to write the .pptx files (default: presentation/)")
    args = parser.parse_args(argv)

    langs = LANGS if args.lang == "all" else (args.lang,)
    return [create_presentation(lang, args.out_dir) for lang in langs]


if __name__ == "__main__":
    main()
