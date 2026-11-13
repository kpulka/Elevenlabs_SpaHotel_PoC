"""Slajdy 9–14: demo, bezpieczeństwo, multi-hotel, koszty, roadmapa, Q&A."""

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from .common import (
    ACCENTS, CHARCOAL, CREAM, GOLD, NAVY, WHITE, add_header, add_notes,
    add_picture_if, add_table, new_slide,
)


def slide_09_demo(prs, t, assets):
    s9 = new_slide(prs, CREAM)
    add_header(s9, t["s9_title"], t["s9_cat"], dark_theme=False)

    add_picture_if(s9, assets, "anna_widget_success.jpg", Inches(0.8), Inches(1.8), Inches(3.2))

    tb9 = s9.shapes.add_textbox(Inches(4.4), Inches(1.8), Inches(8.1), Inches(5.0))
    tf9 = tb9.text_frame
    tf9.word_wrap = True

    for i, (sc_title, sc_desc) in enumerate(t["s9_scenarios"]):
        p = tf9.paragraphs[0] if i == 0 else tf9.add_paragraph()
        p.text = f"{sc_title}"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_b = tf9.add_paragraph()
        p_b.text = f"{sc_desc}\n"
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = CHARCOAL

    add_notes(s9, t["s9_notes"])
    return s9


def slide_10_security(prs, t, assets):
    s10 = new_slide(prs, NAVY)
    add_header(s10, t["s10_title"], t["s10_cat"], dark_theme=True)

    add_picture_if(s10, assets, "enterprise_security.png", Inches(0.8), Inches(1.8), Inches(6.8))

    tb10 = s10.shapes.add_textbox(Inches(7.9), Inches(1.8), Inches(4.7), Inches(5.0))
    tf10 = tb10.text_frame
    tf10.word_wrap = True

    for i, (it_title, it_desc) in enumerate(t["s10_items"]):
        p = tf10.paragraphs[0] if i == 0 else tf10.add_paragraph()
        p.text = f"🔒 {it_title}"
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = GOLD

        p_b = tf10.add_paragraph()
        p_b.text = f"{it_desc}\n"
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = WHITE

    add_notes(s10, t["s10_notes"])
    return s10


def slide_11_multihotel(prs, t, assets):
    s11 = new_slide(prs, NAVY)
    add_header(s11, t["s11_title"], t["s11_cat"], dark_theme=True)

    add_picture_if(s11, assets, "diagram_multihotel.png", Inches(0.8), Inches(1.8), Inches(6.8))

    tb11 = s11.shapes.add_textbox(Inches(7.9), Inches(1.8), Inches(4.7), Inches(5.0))
    tf11 = tb11.text_frame
    tf11.word_wrap = True

    p = tf11.paragraphs[0]
    p.text = t["s11_panel_title"]
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GOLD

    p_body = tf11.add_paragraph()
    p_body.text = t["s11_panel_body"]
    p_body.font.size = Pt(12)
    p_body.font.color.rgb = WHITE

    add_notes(s11, t["s11_notes"])
    return s11


def slide_12_costs(prs, t, assets):
    s12 = new_slide(prs, CREAM)
    add_header(s12, t["s12_title"], t["s12_cat"], dark_theme=False)

    add_table(
        s12, t["s12_headers"], t["s12_rows"],
        Inches(0.8), Inches(1.9), Inches(11.7), Inches(2.3),
        col_widths=[3.9, 3.9, 3.9],
    )

    tb12 = s12.shapes.add_textbox(Inches(0.8), Inches(4.5), Inches(11.7), Inches(2.4))
    tf12 = tb12.text_frame
    tf12.word_wrap = True

    p = tf12.paragraphs[0]
    p.text = t["s12_roi_title"]
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY

    p_roi = tf12.add_paragraph()
    p_roi.text = t["s12_roi_body"]
    p_roi.font.size = Pt(13)
    p_roi.font.color.rgb = CHARCOAL

    add_notes(s12, t["s12_notes"])
    return s12


def slide_13_roadmap(prs, t, assets):
    s13 = new_slide(prs, CREAM)
    add_header(s13, t["s13_title"], t["s13_cat"], dark_theme=False)

    for i, (ph_title, ph_desc, accent) in enumerate(t["s13_phases"]):
        left = Inches(0.8 + i * 4.0)
        box = s13.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(1.9), Inches(3.7), Inches(5.0))
        box.fill.solid()
        box.fill.fore_color.rgb = WHITE
        box.line.color.rgb = ACCENTS[accent]
        box.line.width = Pt(2)

        tb = s13.shapes.add_textbox(left + Inches(0.2), Inches(2.1), Inches(3.3), Inches(4.5))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = ph_title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_b = tf.add_paragraph()
        p_b.text = f"\n{ph_desc}"
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = CHARCOAL

    add_notes(s13, t["s13_notes"])
    return s13


def slide_14_qa(prs, t, assets):
    s14 = new_slide(prs, NAVY)

    tb14 = s14.shapes.add_textbox(Inches(1.5), Inches(2.5), Inches(10.3), Inches(3.0))
    tf14 = tb14.text_frame
    tf14.word_wrap = True
    p = tf14.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = t["s14_title"]
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = GOLD
    p.font.name = "Georgia"

    p2 = tf14.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.text = t["s14_sub"]
    p2.font.size = Pt(22)
    p2.font.color.rgb = WHITE

    add_notes(s14, t["s14_notes"])
    return s14
