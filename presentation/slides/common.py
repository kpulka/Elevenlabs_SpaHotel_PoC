"""Wspólny układ slajdów: paleta, tło, nagłówek, tabela, notatki prelegenta.

Moduł nie zawiera treści — ta idzie z `content_pl.json` / `content_en.json`.
"""

import os

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

NAVY = RGBColor(27, 42, 74)       # #1B2A4A
GOLD = RGBColor(201, 168, 76)     # #C9A84C
CREAM = RGBColor(245, 240, 232)   # #F5F0E8
WHITE = RGBColor(255, 255, 255)
CHARCOAL = RGBColor(44, 44, 44)   # #2C2C2C
SAGE = RGBColor(122, 158, 126)    # #7A9E7E
MUTED = RGBColor(138, 138, 138)
CARD_NAVY = RGBColor(35, 52, 88)
TABLE_ALT = RGBColor(250, 246, 240)

# Nazwy akcentów z JSON-a -> kolor. Dane nie niosą obiektów RGB, tylko nazwy.
ACCENTS = {"navy": NAVY, "gold": GOLD, "sage": SAGE}

BRAND_LINE = "ELEVENLABS DEPLOYMENT STRATEGIST CASE STUDY"


def new_slide(prs, bg=NAVY):
    """Pusty slajd (layout 6 = blank) z prostokątnym tłem na całą kartę."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, prs, bg)
    return slide


def add_bg(slide, prs, color=NAVY):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()
    return bg


def add_header(slide, title_text, category_text=BRAND_LINE, dark_theme=True):
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.4))
    tf_cat = cat_box.text_frame
    tf_cat.word_wrap = True
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = GOLD
    p_cat.font.name = "Arial"

    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.9))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.size = Pt(28)
    p_title.font.bold = True
    p_title.font.color.rgb = WHITE if dark_theme else NAVY
    p_title.font.name = "Georgia"


def add_notes(slide, notes_text):
    slide.notes_slide.notes_text_frame.text = notes_text


def add_picture_if(slide, assets, name, left, top, width):
    """Wstawia grafikę z assets/, jeśli plik istnieje (jak w poprzedniej wersji)."""
    path = os.path.join(assets, name)
    if os.path.exists(path):
        slide.shapes.add_picture(path, left, top, width)


def add_table(slide, headers, rows, left, top, width, height, col_widths):
    shape = slide.shapes.add_table(len(rows) + 1, len(headers), left, top, width, height)
    table = shape.table
    for idx, w in enumerate(col_widths):
        table.columns[idx].width = Inches(w)
    for col, h in enumerate(headers):
        cell = table.cell(0, col)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.bold = True
        p.font.color.rgb = GOLD
        p.font.size = Pt(13)
    for row_idx, row in enumerate(rows, start=1):
        for col_idx, val in enumerate(row):
            cell = table.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if row_idx % 2 == 1 else TABLE_ALT
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(12)
            p.font.color.rgb = CHARCOAL
    return table
