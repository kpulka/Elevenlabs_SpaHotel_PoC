#!/usr/bin/env python3
"""Guard the numbers the deck and documents are allowed to publish.

Why this exists
---------------
The 2026-11-10 review found the online English deck claiming ``3,738 minutes (~$0.027/min)``
while the deck generator said ``$22 / 275 min`` and ``$299 / 3,738 min`` -- which is $0.08/min,
three times higher. The Polish deck claimed two 500 PLN bookings cover a $299 plan (they cover
$250). Type-checking, i18n parity and forbidden-string checks all passed: **nothing compared
numbers between artifacts**, and the HTML decks are hand-maintained, so they drifted from the
generator silently.

What it checks
--------------
1. Arithmetic: $22 / 275 min and $299 / 3,738 min must describe the same per-minute rate, and
   that rate must be what the documents print.
2. Every "presentation surface" (both PPTX decks, both HTML decks, both spec files, the
   business case) carries the canonical figures and none of the retracted ones.
3. Both PPTX files still have 14 slides.

Standard library only (a .pptx is a zip), so CI needs no python-pptx. Slides are read by
concatenating the ``<a:t>`` runs of each paragraph, which survives text split across runs.

Historical documents that quote the old figures *as history* (``presentation/02_v1_interview_
thought_process_en.md``, ``docs/lessons-learned.md``, ``presentation/README.md``) are not in the
surface table on purpose.

Run:
    python presentation/verify_deck.py
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SLIDE_COUNT = 14
CREATOR_COST, CREATOR_MINUTES = 22.0, 275.0
SCALE_COST, SCALE_MINUTES = 299.0, 3738.0
FX_PLN_PER_USD = 4.0
NIGHT_BOOKING_PLN = 500.0
BOOKINGS_TO_COVER_SCALE = 3

PLANS = {
    "PPTX pl": ROOT / "presentation" / "Bukowy_Dwor_Case_Study.pptx",
    "PPTX en": ROOT / "presentation" / "Bukowy_Dwor_Case_Study_EN.pptx",
    "HTML pl": ROOT / "presentation" / "prezentacja.html",
    "HTML en": ROOT / "presentation" / "presentation_en.html",
    "spec pl": ROOT / "presentation" / "deck_spec.json",
    "spec en": ROOT / "presentation" / "deck_spec_en.json",
    "business case": ROOT / "docs" / "business-case.md",
}

# Tokens retracted on 2026-11-10. A presentation surface may not still show them.
RETRACTED = [
    "$0.027", "0.027/min", "0,027",
    "2 x 500", "2 × 500 PLN", "(2 x 500",
    "$2,000", "$4,000", "2 000",
    "Replaces 1 FTE", "Saves 3", "1 FTE night",
    "$400–$800", "400 PLN–800",
    "1 godzinie pracy", "1h pracy recepcjonisty", "1 hr of human",
]

# Each surface must mention at least these figures.
REQUIRED = {
    "PPTX pl": ["275", "3 738", "$299", "500 PLN", "3,5", "0,08 USD/min"],
    "PPTX en": ["275", "3,738", "$299", "500 PLN", "3.5", "$0.08/min"],
    "HTML pl": ["275", "3 738", "$299", "500 PLN", "0,08 USD/min"],
    "HTML en": ["275", "3,738", "$299", "500 PLN", "0.08/min"],
    "spec pl": ["275", "3 738", "0,08 USD/min"],
    "spec en": ["275", "3,738", "0.08/min"],
    "business case": ["275", "3,738", "0.08"],
}


def pptx_text(path: Path) -> tuple[str, int]:
    """Return (text, slide count) from a .pptx, joining runs paragraph by paragraph."""
    chunks: list[str] = []
    slides = 0
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
        slides = len(names)
        for name in sorted(names, key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[1]).group(1))):
            xml = archive.read(name).decode("utf-8", "replace")
            for paragraph in xml.split("</a:p>"):
                runs = re.findall(r"<a:t>(.*?)</a:t>", paragraph, flags=re.S)
                if runs:
                    chunks.append("".join(runs))
        notes = [n for n in archive.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", n)]
        for name in notes:
            xml = archive.read(name).decode("utf-8", "replace")
            for paragraph in xml.split("</a:p>"):
                runs = re.findall(r"<a:t>(.*?)</a:t>", paragraph, flags=re.S)
                if runs:
                    chunks.append("".join(runs))
    return "\n".join(chunks), slides


def surface_text(key: str, path: Path) -> tuple[str, int | None]:
    if path.suffix == ".pptx":
        return pptx_text(path)
    if not path.exists():
        raise SystemExit(f"brak pliku: {path}")
    return path.read_text(encoding="utf-8"), None


def main() -> int:
    failures: list[str] = []

    # 1. The arithmetic itself.
    rate_creator = CREATOR_COST / CREATOR_MINUTES
    rate_scale = SCALE_COST / SCALE_MINUTES
    if abs(rate_creator - rate_scale) > 0.005:
        failures.append(
            f"plany nie opisują tego samego kursu: {CREATOR_COST}/{CREATOR_MINUTES}="
            f"{rate_creator:.3f} vs {SCALE_COST}/{SCALE_MINUTES}={rate_scale:.3f}"
        )
    published_rate = round(rate_scale, 2)
    if published_rate != 0.08:
        failures.append(f"kurs do publikacji wyszedł {published_rate}, a dokumenty mówią 0.08")
    coverage_usd = BOOKINGS_TO_COVER_SCALE * NIGHT_BOOKING_PLN / FX_PLN_PER_USD
    if coverage_usd < SCALE_COST:
        failures.append(
            f"{BOOKINGS_TO_COVER_SCALE} × {NIGHT_BOOKING_PLN:.0f} PLN = ${coverage_usd:.0f} nie pokrywa "
            f"planu Scale (${SCALE_COST:.0f})"
        )

    # 2. Cross-artifact consistency.
    for key, path in PLANS.items():
        text, slides = surface_text(key, path)
        if slides is not None and slides != SLIDE_COUNT:
            failures.append(f"{key}: {slides} slajdów, oczekiwano {SLIDE_COUNT}")
        for needle in REQUIRED[key]:
            if needle not in text:
                failures.append(f"{key}: brak wymaganej liczby/zwrotu {needle!r}")
        for needle in RETRACTED:
            if needle in text:
                failures.append(f"{key}: wciąż zawiera wycofaną liczbę {needle!r}")
        print(f"  {key:14} {len(text):6} znaków" + (f", {slides} slajdów" if slides else ""))

    print(f"\nkurs: {CREATOR_COST:.0f}/{CREATOR_MINUTES:.0f} = {rate_creator:.3f} "
          f"| {SCALE_COST:.0f}/{SCALE_MINUTES:.0f} = {rate_scale:.3f} -> ${published_rate:.2f}/min")
    print(f"pokrycie Scale: {BOOKINGS_TO_COVER_SCALE} × {NIGHT_BOOKING_PLN:.0f} PLN "
          f"= {BOOKINGS_TO_COVER_SCALE * NIGHT_BOOKING_PLN:.0f} PLN = ${coverage_usd:.0f}")

    if failures:
        print(f"\nNIEPOWODZENIE ({len(failures)}):")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("\nOK: liczby spójne we wszystkich artefaktach")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
