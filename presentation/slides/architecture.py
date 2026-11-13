"""Slajdy 4–8: architektura, decyzje, RAG, narzędzia, kanały."""

from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

from .common import (
    CARD_NAVY, CHARCOAL, CREAM, GOLD, NAVY, SAGE, WHITE, add_header, add_notes,
    add_picture_if, add_table, new_slide,
)


def slide_04_architecture(prs, t, assets):
    s4 = new_slide(prs, NAVY)
    add_header(s4, t["s4_title"], t["s4_cat"], dark_theme=True)

    add_picture_if(s4, assets, "diagram_architecture.png", Inches(0.8), Inches(1.8), Inches(7.5))

    tb4 = s4.shapes.add_textbox(Inches(8.5), Inches(1.8), Inches(4.3), Inches(5.0))
    tf4 = tb4.text_frame
    tf4.word_wrap = True

    p4_1 = tf4.paragraphs[0]
    p4_1.text = t["s4_panel_title"]
    p4_1.font.size = Pt(18)
    p4_1.font.bold = True
    p4_1.font.color.rgb = GOLD

    p4_desc = tf4.add_paragraph()
    p4_desc.text = t["s4_panel_body"]
    p4_desc.font.size = Pt(13)
    p4_desc.font.color.rgb = WHITE

    add_notes(s4, t["s4_notes"])
    return s4


def slide_05_decisions(prs, t, assets):
    s5 = new_slide(prs, CREAM)
    add_header(s5, t["s5_title"], t["s5_cat"], dark_theme=False)

    for i, (d_title, d_desc) in enumerate(t["s5_decisions"]):
        top = Inches(1.9 + i * 1.7)
        box = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top, Inches(11.7), Inches(1.5))
        box.fill.solid()
        box.fill.fore_color.rgb = WHITE
        box.line.color.rgb = GOLD

        tb = s5.shapes.add_textbox(Inches(1.1), top + Inches(0.15), Inches(11.1), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = d_title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_b = tf.add_paragraph()
        p_b.text = d_desc
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = CHARCOAL

    add_notes(s5, t["s5_notes"])
    return s5


def slide_06_rag(prs, t, assets):
    s6 = new_slide(prs, NAVY)
    add_header(s6, t["s6_title"], t["s6_cat"], dark_theme=True)

    box_l = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.9), Inches(5.6), Inches(5.0))
    box_l.fill.solid()
    box_l.fill.fore_color.rgb = CARD_NAVY
    box_l.line.color.rgb = GOLD

    tb_l = s6.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.0), Inches(4.5))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    p = tf_l.paragraphs[0]
    p.text = t["s6_left_title"]
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GOLD

    p2 = tf_l.add_paragraph()
    p2.text = t["s6_left_body"]
    p2.font.size = Pt(13)
    p2.font.color.rgb = WHITE

    box_r = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.9), Inches(5.6), Inches(5.0))
    box_r.fill.solid()
    box_r.fill.fore_color.rgb = CARD_NAVY
    box_r.line.color.rgb = SAGE

    tb_r = s6.shapes.add_textbox(Inches(7.2), Inches(2.1), Inches(5.0), Inches(4.5))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = t["s6_right_title"]
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = SAGE

    p2 = tf_r.add_paragraph()
    p2.text = t["s6_right_body"]
    p2.font.size = Pt(13)
    p2.font.color.rgb = WHITE

    add_notes(s6, t["s6_notes"])
    return s6


def slide_07_tools(prs, t, assets):
    s7 = new_slide(prs, CREAM)
    add_header(s7, t["s7_title"], t["s7_cat"], dark_theme=False)
    add_table(
        s7, t["s7_headers"], t["s7_rows"],
        Inches(0.8), Inches(1.9), Inches(11.7), Inches(4.8),
        col_widths=[3.2, 5.5, 3.0],
    )
    add_notes(s7, t["s7_notes"])
    return s7


def slide_08_omnichannel(prs, t, assets):
    s8 = new_slide(prs, NAVY)
    add_header(s8, t["s8_title"], t["s8_cat"], dark_theme=True)

    add_picture_if(s8, assets, "anna_widget_chips.jpg", Inches(0.8), Inches(1.8), Inches(3.2))

    tb8 = s8.shapes.add_textbox(Inches(4.3), Inches(1.8), Inches(8.2), Inches(5.0))
    tf8 = tb8.text_frame
    tf8.word_wrap = True

    p = tf8.paragraphs[0]
    p.text = t["s8_ch1_title"]
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GOLD

    p_t = tf8.add_paragraph()
    p_t.text = t["s8_ch1_body"]
    p_t.font.size = Pt(13)
    p_t.font.color.rgb = WHITE

    p2 = tf8.add_paragraph()
    p2.text = t["s8_ch2_title"]
    p2.font.size = Pt(18)
    p2.font.bold = True
    p2.font.color.rgb = SAGE

    p_w = tf8.add_paragraph()
    p_w.text = t["s8_ch2_body"]
    p_w.font.size = Pt(13)
    p_w.font.color.rgb = WHITE

    add_notes(s8, t["s8_notes"])
    return s8
