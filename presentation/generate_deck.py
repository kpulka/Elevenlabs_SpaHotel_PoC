"""Render the Bukowy Dwor case study deck from deck_spec.json.

Usage:
    python3 generate_deck.py [output.pptx]

The slide content, layout and speaker notes come from deck_spec.json, which is
the single source of truth. Image paths in the spec are relative to this
directory. Without an argument the deck is written to
Bukowy_Dwor_Case_Study.pptx next to this script.

Supported slide layouts:
    title          Title slide with optional subtitle, footer and images.
    title_content  Heading plus bullets, optional tables and images.
    two_content    Heading plus two bullet columns, optional images.

Optional per-slide keys:
    background     Hex colour for the slide background (default: navy for
                   title slides, cream for content slides).
    body_box       {left, top, width, height} in inches for the bullet area.
    bullets_below  Bullets placed under the last table.
    left_box / right_box
                   Box overrides for the two columns of a two_content slide.
    category       Small caption above the heading (default: case study label).
    images         List of {path, left, top, width} entries.
    tables         List of {left, top, width, height, rows} entries; the first
                   row is the header.
    notes          Speaker notes.
"""

import json
import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_PATH = os.path.join(HERE, "deck_spec.json")
DEFAULT_OUT = os.path.join(HERE, "Bukowy_Dwor_Case_Study.pptx")

NAVY = RGBColor(0x1B, 0x2A, 0x4A)
PANEL = RGBColor(0x23, 0x34, 0x58)
GOLD = RGBColor(0xC9, 0xA8, 0x4C)
CREAM = RGBColor(0xF5, 0xF0, 0xE8)
ROW_ALT = RGBColor(0xFA, 0xF6, 0xF0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CHARCOAL = RGBColor(0x2C, 0x2C, 0x2C)
SAGE = RGBColor(0x7A, 0x9E, 0x7E)

CATEGORY_DEFAULT = "CASE STUDY · BUKOWY DWÓR"
HEADING_FONT = "Georgia"
BODY_FONT = "Arial"


def hex_to_rgb(hex_str):
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def is_dark(color):
    r, g, b = color[0], color[1], color[2]
    return (0.299 * r + 0.587 * g + 0.114 * b) < 128


def add_background(prs, slide, color):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def add_text(slide, left, top, width, height, text, size, color, bold=False,
             font=BODY_FONT, word_wrap=True):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = word_wrap
    paragraph = frame.paragraphs[0]
    paragraph.text = text
    paragraph.font.size = Pt(size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = color
    paragraph.font.name = font
    return box


def add_bullets(slide, box_spec, items, size, color, accent=None):
    """Write bullet items into a text box. Items may be strings or
    {"text": ..., "level": n} objects. Empty strings are skipped."""
    left, top, width, height = box_spec
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    first = True
    for item in items:
        if isinstance(item, dict):
            text, level = item.get("text", ""), int(item.get("level", 0))
        else:
            text, level = item, 0
        if not text.strip():
            continue
        paragraph = frame.paragraphs[0] if first else frame.add_paragraph()
        first = False
        marker = "•" if level == 0 else "–"
        indent = "" if level == 0 else "     "
        paragraph.text = f"{indent}{marker} {text}"
        paragraph.space_after = Pt(8)
        paragraph.font.size = Pt(size - 2 * level)
        paragraph.font.color.rgb = color
        paragraph.font.name = BODY_FONT
    return box


def add_table(slide, spec_table, header_fill, body_fill_a, body_fill_b, text_color):
    rows = spec_table["rows"]
    n_rows, n_cols = len(rows), len(rows[0])
    shape = slide.shapes.add_table(
        n_rows, n_cols,
        Inches(spec_table["left"]), Inches(spec_table["top"]),
        Inches(spec_table["width"]), Inches(spec_table["height"]),
    )
    table = shape.table
    col_width = spec_table["width"] / n_cols
    for col in range(n_cols):
        table.columns[col].width = Inches(col_width)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = header_fill
            else:
                cell.fill.fore_color.rgb = body_fill_a if r % 2 == 1 else body_fill_b
            paragraph = cell.text_frame.paragraphs[0]
            paragraph.text = value
            paragraph.font.name = BODY_FONT
            paragraph.font.size = Pt(13 if r == 0 else 12)
            paragraph.font.bold = r == 0
            paragraph.font.color.rgb = GOLD if r == 0 else text_color


def add_images(prs, slide, images, base_dir):
    for image in images:
        path = os.path.join(base_dir, image["path"])
        if not os.path.exists(path):
            print(f"warning: image not found, skipped: {path}", file=sys.stderr)
            continue
        slide.shapes.add_picture(path, Inches(image["left"]), Inches(image["top"]),
                                 Inches(image["width"]))


def add_heading(slide, category, title, text_color):
    add_text(slide, 0.8, 0.5, 11.7, 0.4, category.upper(), 11, GOLD, bold=True)
    add_text(slide, 0.8, 0.85, 11.7, 0.9, title, 28, WHITE if text_color == WHITE else NAVY,
             bold=True, font=HEADING_FONT)


def render_title(prs, slide, spec, background, text_color, base_dir):
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.8),
                                  Inches(1.5), Inches(0.06))
    line.fill.solid()
    line.fill.fore_color.rgb = GOLD
    line.line.fill.background()

    box = slide.shapes.add_textbox(Inches(0.8), Inches(2.1), Inches(7.5), Inches(3.2))
    frame = box.text_frame
    frame.word_wrap = True
    title_p = frame.paragraphs[0]
    title_p.text = spec["title"]
    title_p.font.size = Pt(38)
    title_p.font.bold = True
    title_p.font.color.rgb = WHITE
    title_p.font.name = HEADING_FONT
    if spec.get("subtitle"):
        sub_p = frame.add_paragraph()
        sub_p.text = spec["subtitle"]
        sub_p.font.size = Pt(18)
        sub_p.font.color.rgb = GOLD
        sub_p.font.name = HEADING_FONT
        sub_p.space_before = Pt(12)
    if spec.get("footer"):
        add_text(slide, 0.8, 6.2, 10, 0.6, spec["footer"], 12, SAGE)


def render_content(prs, slide, spec, background, text_color, base_dir, layout):
    category = spec.get("category", CATEGORY_DEFAULT)
    add_heading(slide, category, spec["title"], text_color)

    if layout == "two_content":
        left_box = spec.get("left_box", [0.8, 1.9, 5.6, 5.0])
        right_box = spec.get("right_box", [6.9, 1.9, 5.6, 5.0])
        add_bullets(slide, left_box, spec.get("bullets_left", []), 16, text_color)
        add_bullets(slide, right_box, spec.get("bullets_right", []), 16, text_color)
    else:
        body = spec.get("body_box")
        box = [body["left"], body["top"], body["width"], body["height"]] if body \
            else [0.8, 1.9, 11.7, 5.0]
        if spec.get("bullets"):
            add_bullets(slide, box, spec["bullets"], 16, text_color)

    for table in spec.get("tables", []):
        add_table(slide, table, NAVY, WHITE, ROW_ALT, CHARCOAL)
        table_bottom = table["top"] + table["height"]
        if spec.get("bullets_below"):
            add_bullets(slide, [0.8, table_bottom + 0.4, 11.7, 2.6],
                        spec["bullets_below"], 16, text_color)

    add_images(prs, slide, spec.get("images", []), base_dir)


def render_deck(spec, out_path, base_dir):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    for index, slide_spec in enumerate(spec["slides"], start=1):
        layout = slide_spec.get("layout", "title_content")
        if layout not in ("title", "title_content", "two_content"):
            raise ValueError(f"slide {index}: unknown layout '{layout}'")

        default_bg = NAVY if layout == "title" else CREAM
        background = hex_to_rgb(slide_spec["background"]) if slide_spec.get("background") \
            else default_bg
        text_color = WHITE if is_dark(background) else CHARCOAL

        slide = prs.slides.add_slide(blank_layout)
        add_background(prs, slide, background)

        if layout == "title":
            render_title(prs, slide, slide_spec, background, text_color, base_dir)
            add_images(prs, slide, slide_spec.get("images", []), base_dir)
        else:
            render_content(prs, slide, slide_spec, background, text_color, base_dir, layout)

        if slide_spec.get("notes"):
            slide.notes_slide.notes_text_frame.text = slide_spec["notes"]

    prs.save(out_path)
    return len(spec["slides"])


def main(argv):
    out_path = argv[1] if len(argv) > 1 else DEFAULT_OUT
    # utf-8-sig tolerates a leading byte-order mark if one is present.
    with open(SPEC_PATH, encoding="utf-8-sig") as handle:
        spec = json.load(handle)
    count = render_deck(spec, out_path, HERE)
    print(f"Rendered {count} slides to {out_path}")


if __name__ == "__main__":
    main(sys.argv)
