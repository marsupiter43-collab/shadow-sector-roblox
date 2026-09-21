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

    # --- TITLE PAGE ---
    # Center all text on title page
    doc.add_paragraph()

    ministry = doc.add_paragraph("МИНИСТЕРСТВО ОБРАЗОВАНИЯ И НАУКИ")
    ministry.alignment = WD_ALIGN_PARAGRAPH.CENTER

    college = doc.add_paragraph("Учалинский горный колледж (УКГП)")
    college.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for _ in range(3):
        doc.add_paragraph()

    title_type = doc.add_paragraph("РЕФЕРАТ")
    title_type.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_type.runs[0].bold = True
    title_type.runs[0].font.size = Pt(16)

    subject = doc.add_paragraph("По дисциплине: Физическая культура")
    subject.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    topic = doc.add_paragraph("На тему: «Спорт и нормы»")
    topic.alignment = WD_ALIGN_PARAGRAPH.CENTER
    topic.runs[0].bold = True
    topic.runs[0].font.size = Pt(16)

    for _ in range(5):
        doc.add_paragraph()

    student = doc.add_paragraph("Выполнил:")
    student.alignment = WD_ALIGN_PARAGRAPH.CENTER
    student_name = doc.add_paragraph("студент 1 курса, группы РиУП-26")
    student_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    student_name2 = doc.add_paragraph("Юсупов Камиль Ильдарович")
    student_name2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    teacher = doc.add_paragraph("Проверил(а):")
    teacher.alignment = WD_ALIGN_PARAGRAPH.CENTER
    teacher_name = doc.add_paragraph("преподаватель Заботина С.Р.")
    teacher_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    teacher_grade = doc.add_paragraph("Оценка: _____________")
    teacher_grade.alignment = WD_ALIGN_PARAGRAPH.CENTER
    teacher_sig = doc.add_paragraph("Подпись: _____________")
    teacher_sig.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for _ in range(3):
        doc.add_paragraph()

    city_year = doc.add_paragraph("Учалы – 2026")
    city_year.alignment = WD_ALIGN_PARAGRAPH.CENTER

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
        elif p_text[0].isdigit() and p_text[1] == '.' and p_text[2].isdigit():
            # Subheading
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.runs[0].bold = True
            p.paragraph_format.first_line_indent = 0
            p.paragraph_format.space_after = Pt(14)
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Cm(1.25)
            p.paragraph_format.space_after = Pt(0)

    doc.save('Реферат_Спорт_и_нормы.docx')

if __name__ == '__main__':
    create_essay()
