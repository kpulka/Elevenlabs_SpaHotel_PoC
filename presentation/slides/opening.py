"""Slajdy 1–3: tytuł, problem biznesowy, persona."""

from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

from .common import (
    CHARCOAL, CREAM, GOLD, NAVY, SAGE, WHITE, add_header, add_notes,
    add_picture_if, new_slide,
)


def slide_01_title(prs, t, assets):
    s1 = new_slide(prs, NAVY)

    line = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.8), Inches(1.5), Inches(0.06))
    line.fill.solid()
    line.fill.fore_color.rgb = GOLD
    line.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(0.8), Inches(2.1), Inches(7.5), Inches(3.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = t["s1_title"]
    p1.font.size = Pt(38)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.font.name = "Georgia"

    p2 = tf.add_paragraph()
    p2.text = t["s1_sub"]
    p2.font.size = Pt(22)
    p2.font.color.rgb = GOLD
    p2.font.name = "Georgia"

    p3 = tf.add_paragraph()
    p3.text = t["s1_tagline"]
    p3.font.size = Pt(14)
    p3.font.color.rgb = CREAM

    bb = s1.shapes.add_textbox(Inches(0.8), Inches(6.2), Inches(10), Inches(0.6))
    p_b = bb.text_frame.paragraphs[0]
    p_b.text = t["s1_badge"]
    p_b.font.size = Pt(12)
    p_b.font.color.rgb = SAGE

    add_picture_if(s1, assets, "anna_widget_desktop.jpg", Inches(8.0), Inches(1.4), Inches(4.7))
    add_notes(s1, t["s1_notes"])
    return s1


def slide_02_problem(prs, t, assets):
    s2 = new_slide(prs, CREAM)
    add_header(s2, t["s2_title"], t["s2_cat"], dark_theme=False)

    for i, (head, desc, icon) in enumerate(t["s2_cards"]):
        row = i // 2
        col = i % 2
        left = Inches(0.8 + col * 5.9)
        top = Inches(1.9 + row * 2.5)

        box = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(5.6), Inches(2.2))
        box.fill.solid()
        box.fill.fore_color.rgb = WHITE
        box.line.color.rgb = GOLD
        box.line.width = Pt(1)

        tb = s2.shapes.add_textbox(left + Inches(0.3), top + Inches(0.2), Inches(5.0), Inches(1.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"{icon}  {head}"
        p.font.size = Pt(17)
        p.font.bold = True
        p.font.color.rgb = NAVY
        p.font.name = "Georgia"

        p_desc = tf.add_paragraph()
        p_desc.text = f"\n{desc}"
        p_desc.font.size = Pt(13)
        p_desc.font.color.rgb = CHARCOAL

    add_notes(s2, t["s2_notes"])
    return s2


def slide_03_persona(prs, t, assets):
    s3 = new_slide(prs, NAVY)
    add_header(s3, t["s3_title"], t["s3_cat"], dark_theme=True)

    add_picture_if(s3, assets, "persona_zofia.png", Inches(0.8), Inches(1.9), Inches(4.2))

    tb3 = s3.shapes.add_textbox(Inches(5.3), Inches(1.8), Inches(7.2), Inches(5.0))
    tf3 = tb3.text_frame
    tf3.word_wrap = True

    for i, (title_p, body_p) in enumerate(t["s3_points"]):
        p = tf3.paragraphs[0] if i == 0 else tf3.add_paragraph()
        p.text = f"• {title_p} "
        p.font.bold = True
        p.font.size = Pt(14)
        p.font.color.rgb = GOLD

        run = p.add_run()
        run.text = body_p
        run.font.bold = False
        run.font.color.rgb = WHITE
        run.font.size = Pt(14)

    add_notes(s3, t["s3_notes"])
    return s3
