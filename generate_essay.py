import docx
from docx.shared import Pt, Cm, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def create_essay():
    doc = docx.Document()

    # 1. Set completely symmetric margins (20mm all around) per user preference
    sections = doc.sections
    for section in sections:
        section.top_margin = Mm(20)
        section.bottom_margin = Mm(20)
        section.left_margin = Mm(20)
        section.right_margin = Mm(20)

    # Base styling: Times New Roman, 14pt
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(14)

    # Paragraph formatting: 1.5 line spacing, 1.25cm indent
    paragraph_format = style.paragraph_format
    paragraph_format.line_spacing = 1.5
    paragraph_format.first_line_indent = Cm(1.25)

    def add_title_p(text="", bold=False, size=14):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = 1.0 # Single spacing for title page to save space
        p.paragraph_format.first_line_indent = Cm(0)
        if text:
            r = p.add_run(text)
            if bold:
                r.bold = True
            r.font.size = Pt(size)
        return p

    # --- TITLE PAGE ---
    add_title_p("МИНИСТЕРСТВО ОБРАЗОВАНИЯ И НАУКИ")
    add_title_p("Учалинский горный колледж (УКГП)")

    for _ in range(8):
        add_title_p()

    add_title_p("РЕФЕРАТ", bold=True, size=16)
    add_title_p("По дисциплине: Физическая культура")
    add_title_p()
    add_title_p("На тему: «Спорт и нормы»", bold=True, size=16)

    for _ in range(8):
        add_title_p()

    add_title_p("Выполнил:")
    add_title_p("студент 1 курса, группы РиУП-26")
    add_title_p("Юсупов Камиль Ильдарович")

    add_title_p()

    add_title_p("Руководитель:")
    add_title_p("преподаватель Заботина С.Р.")

    for _ in range(8):
        add_title_p()

    add_title_p("Учалы – 2026")

    doc.add_page_break()

    # --- CONTENT ---
    with open('essay_content.txt', 'r', encoding='utf-8') as f:
        content_text = f.read()

    paragraphs = content_text.split('\n')

    for p_text in paragraphs:
        p_text = p_text.strip()
        if not p_text:
            continue

        p = doc.add_paragraph(p_text)

        # Check if it's a heading
        if p_text in ["Введение", "Заключение", "Список литературы"] or p_text.startswith("Глава"):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.runs[0].bold = True
            p.paragraph_format.first_line_indent = 0
            p.paragraph_format.space_after = Pt(14)
            p.paragraph_format.line_spacing = 1.5
        elif p_text[0].isdigit() and p_text[1] == '.' and p_text[2].isdigit():
            # Subheading
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.runs[0].bold = True
            p.paragraph_format.first_line_indent = 0
            p.paragraph_format.space_after = Pt(14)
            p.paragraph_format.line_spacing = 1.5
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Cm(1.25)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.5

    doc.save('Реферат_Спорт_и_нормы.docx')

if __name__ == '__main__':
    create_essay()
