"""
report_builder.py
Core utility library for generating beautifully formatted, human-crafted academic project reports
in Microsoft Word (.docx) and exporting to PDF via native Word COM / docx2pdf.

Features:
- Times New Roman typography throughout (body, headings, tables, headers, footers).
- Strictly Black and White styling for all text, headings, banners, and tables (except images).
- Clean, simple, minimalist cover page: no tables, no degree/program tags, centered student names with roll numbers.
- Fully framed, continuous bordered tables with solid black cell-level borders on every single cell.
- Row split protection (cantSplit) and repeating headers (tblHeader).
- Embedded high-res architecture and evaluation figures with centered captions (retaining original colors).
- Dynamic page numbering (Page X of Y) with distinct cover page suppression.
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx2pdf import convert

# Strictly Black and White palette (except embedded figures)
COLOR_BLACK = RGBColor(0, 0, 0)
BORDER_COLOR = "000000"         # Solid Black
BORDER_SZ = "6"                 # 0.75 pt

def set_cell_background(cell, fill_hex):
    """Set cell shading color (pure monochrome)."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd')
        tcPr.append(shd)
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)

def set_cell_margins(cell, top=110, bottom=110, left=150, right=150):
    """Set cell internal padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = tcPr.find(qn('w:tcMar'))
    if tcMar is None:
        tcMar = OxmlElement('w:tcMar')
        tcPr.append(tcMar)
    else:
        tcMar.clear()
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)

def set_cell_borders(cell, color=BORDER_COLOR, sz=BORDER_SZ, val="single"):
    """
    Explicitly assign solid black borders to top, bottom, left, and right of an individual cell.
    This guarantees that borders are never clipped, hidden, or discontinued.
    """
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.find(qn('w:tcBorders'))
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    else:
        tcBorders.clear()

    for side in ['top', 'left', 'bottom', 'right']:
        node = OxmlElement(f'w:{side}')
        node.set(qn('w:val'), val)
        node.set(qn('w:sz'), sz)
        node.set(qn('w:space'), '0')
        node.set(qn('w:color'), color)
        tcBorders.append(node)

def set_table_borders(table, color=BORDER_COLOR, sz=BORDER_SZ, val="single"):
    """Set full outer borders and interior grid lines at the table level."""
    tblPr = table._tbl.tblPr
    tblBorders = tblPr.find(qn('w:tblBorders'))
    if tblBorders is None:
        tblBorders = OxmlElement('w:tblBorders')
        tblPr.append(tblBorders)
    else:
        tblBorders.clear()

    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), val)
        border.set(qn('w:sz'), sz)
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), color)
        tblBorders.append(border)

def create_base_doc(running_header_text):
    """Initialize a Document with standard VIT layout and Times New Roman styles in pure Black & White."""
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    section.different_first_page_header_footer = True

    # Configure Normal Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = COLOR_BLACK
    normal_style.paragraph_format.line_spacing = 1.18
    normal_style.paragraph_format.space_after = Pt(5)

    # Running header for body pages
    header = section.header
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hrun = hp.add_run(running_header_text)
    hrun.font.name = 'Times New Roman'
    hrun.font.size = Pt(8.5)
    hrun.font.color.rgb = COLOR_BLACK

    # Running footer for body pages
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    frun = fp.add_run('Page ')
    frun.font.name = 'Times New Roman'
    frun.font.size = Pt(9)
    frun.font.color.rgb = COLOR_BLACK
    fld1 = OxmlElement('w:fldSimple')
    fld1.set(qn('w:instr'), 'PAGE')
    fp._p.append(fld1)
    frun2 = fp.add_run(' of ')
    frun2.font.name = 'Times New Roman'
    frun2.font.size = Pt(9)
    frun2.font.color.rgb = COLOR_BLACK
    fld2 = OxmlElement('w:fldSimple')
    fld2.set(qn('w:instr'), 'NUMPAGES')
    fp._p.append(fld2)

    return doc

def add_cover_page(doc, review_num, review_stage_title, review_sub):
    """
    Build a simple, clean, minimalist VIT cover page in pure Black & White:
    - No tables for names.
    - No degree or programme tags.
    - Clean centered text layout for student names and register numbers.
    """
    # Top Institution Header
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(16)
    p_inst.paragraph_format.space_after = Pt(2)
    r1 = p_inst.add_run("VELLORE INSTITUTE OF TECHNOLOGY\n")
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(16)
    r1.font.bold = True
    r1.font.color.rgb = COLOR_BLACK

    r2 = p_inst.add_run("School of Computer Science and Engineering\n")
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)
    r2.font.color.rgb = COLOR_BLACK

    r3 = p_inst.add_run("Vellore – 632014, Tamil Nadu, India")
    r3.font.name = "Times New Roman"
    r3.font.size = Pt(10)
    r3.font.color.rgb = COLOR_BLACK

    # Spacing
    p_sp1 = doc.add_paragraph()
    p_sp1.paragraph_format.space_after = Pt(28)

    # Review Stage Banner
    p_banner = doc.add_paragraph()
    p_banner.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_banner.paragraph_format.space_after = Pt(4)
    rb = p_banner.add_run(f"PROJECT EVALUATION – {review_stage_title.upper()}")
    rb.font.name = "Times New Roman"
    rb.font.size = Pt(13)
    rb.font.bold = True
    rb.font.color.rgb = COLOR_BLACK

    # Main Project Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(6)
    rt = p_title.add_run("GreenOps Cloud Orchestration")
    rt.font.name = "Times New Roman"
    rt.font.size = Pt(22)
    rt.font.bold = True
    rt.font.color.rgb = COLOR_BLACK

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(6)
    rs = p_sub.add_run("Spatial and Temporal Demand Shifting for Carbon-Aware Cloud Workload Scheduling")
    rs.font.name = "Times New Roman"
    rs.font.size = Pt(12.5)
    rs.font.italic = True
    rs.font.color.rgb = COLOR_BLACK

    p_desc = doc.add_paragraph()
    p_desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_desc.paragraph_format.space_after = Pt(40)
    rd = p_desc.add_run(review_sub)
    rd.font.name = "Times New Roman"
    rd.font.size = Pt(11)
    rd.font.color.rgb = COLOR_BLACK

    # Submission Block (Simple clean text - NO table, NO degree/program)
    p_subm = doc.add_paragraph()
    p_subm.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_subm.paragraph_format.space_after = Pt(10)
    rsm = p_subm.add_run("A Project Report Submitted by")
    rsm.font.name = "Times New Roman"
    rsm.font.size = Pt(11.5)
    rsm.font.italic = True
    rsm.font.color.rgb = COLOR_BLACK

    # Student Names Block
    p_names = doc.add_paragraph()
    p_names.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_names.paragraph_format.space_after = Pt(50)
    p_names.paragraph_format.line_spacing = 1.3

    rn1 = p_names.add_run("SANJEEVKUMAR K S (24MID0172)\n")
    rn1.font.name = "Times New Roman"
    rn1.font.size = Pt(12)
    rn1.font.bold = True
    rn1.font.color.rgb = COLOR_BLACK

    rn2 = p_names.add_run("NITHISH KUMAR (24MIC0032)\n")
    rn2.font.name = "Times New Roman"
    rn2.font.size = Pt(12)
    rn2.font.bold = True
    rn2.font.color.rgb = COLOR_BLACK

    rn3 = p_names.add_run("MUHAMMED FAHEEM K (24MID0158)")
    rn3.font.name = "Times New Roman"
    rn3.font.size = Pt(12)
    rn3.font.bold = True
    rn3.font.color.rgb = COLOR_BLACK

    # Institution Footer Block
    p_foot = doc.add_paragraph()
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_foot.paragraph_format.space_after = Pt(2)
    rf1 = p_foot.add_run("Department of Computer Science and Engineering\n")
    rf1.font.name = "Times New Roman"
    rf1.font.size = Pt(11)
    rf1.font.bold = True
    rf1.font.color.rgb = COLOR_BLACK

    rf2 = p_foot.add_run("Vellore Institute of Technology, Vellore\n")
    rf2.font.name = "Times New Roman"
    rf2.font.size = Pt(10)
    rf2.font.color.rgb = COLOR_BLACK

    rf3 = p_foot.add_run("Academic Session 2024–2025")
    rf3.font.name = "Times New Roman"
    rf3.font.size = Pt(9.5)
    rf3.font.color.rgb = COLOR_BLACK

    # Page Break for clean body start
    doc.add_page_break()

def add_h1(doc, text):
    """Level 1 heading - Pure black text, no underline."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = COLOR_BLACK
    return p

def add_h2(doc, text):
    """Level 2 heading - Pure black text, no underline."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = COLOR_BLACK
    return p

def add_h3(doc, text):
    """Level 3 heading - Pure black text."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.italic = True
    r.font.color.rgb = COLOR_BLACK
    return p

def add_p(doc, text, bold_prefix=None, italic=False, space_after=5):
    """Add justified body paragraph in pure black."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.18

    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.font.name = "Times New Roman"
        rb.font.size = Pt(11)
        rb.font.bold = True
        rb.font.color.rgb = COLOR_BLACK

    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    r.font.italic = italic
    r.font.color.rgb = COLOR_BLACK
    return p

def add_bullet(doc, text, bold_prefix=None):
    """Add formatted bullet item in pure black."""
    p = doc.add_paragraph(style='List Bullet')
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15

    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.font.name = "Times New Roman"
        rb.font.size = Pt(11)
        rb.font.bold = True
        rb.font.color.rgb = COLOR_BLACK

    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    r.font.color.rgb = COLOR_BLACK
    return p

def add_table(doc, headers, rows, col_widths=None, highlight_idx=-1, caption=None):
    """
    Create a complete, fully-margined table in pure Black & White:
    - Solid black borders explicitly drawn on all 4 sides of every cell.
    - Clean monochrome header row (light grayscale #F2F2F2 with bold black text).
    - Pure white data rows (#FFFFFF) with black text.
    - Row-split protection (cantSplit) on every row.
    - Repeating header row (tblHeader).
    """
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table = doc.add_table(rows=num_rows, cols=num_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Table-level solid black borders
    set_table_borders(table, color=BORDER_COLOR, sz=BORDER_SZ, val="single")

    # Header Row
    header_row = table.rows[0]
    header_trPr = header_row._tr.get_or_add_trPr()
    header_trPr.append(OxmlElement('w:tblHeader'))
    header_trPr.append(OxmlElement('w:cantSplit'))

    for col_idx, h in enumerate(headers):
        cell = header_row.cells[col_idx]
        set_cell_background(cell, "F2F2F2")
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
        set_cell_borders(cell, color=BORDER_COLOR, sz=BORDER_SZ, val="single")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx == 0 else WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = COLOR_BLACK

    # Data Rows
    for row_idx, r_data in enumerate(rows, start=1):
        row = table.rows[row_idx]
        row_trPr = row._tr.get_or_add_trPr()
        row_trPr.append(OxmlElement('w:cantSplit'))

        is_hl = (row_idx - 1) == highlight_idx
        # Monochrome highlight (clean light gray) or pure white
        bg = "E5E5E5" if is_hl else "FFFFFF"

        for col_idx, val in enumerate(r_data):
            cell = row.cells[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
            set_cell_borders(cell, color=BORDER_COLOR, sz=BORDER_SZ, val="single")
            p = cell.paragraphs[0]
            val_str = str(val)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx == 0 else WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(val_str)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.5)
            if is_hl:
                r.font.bold = True
            r.font.color.rgb = COLOR_BLACK

    # Apply column widths if provided
    if col_widths and len(col_widths) == num_cols:
        for r in table.rows:
            for idx, w in enumerate(col_widths):
                r.cells[idx].width = Inches(w)

    # Caption (Italic black text)
    if caption:
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(4)
        p_cap.paragraph_format.space_after = Pt(12)
        rc = p_cap.add_run(caption)
        rc.font.name = "Times New Roman"
        rc.font.size = Pt(9.5)
        rc.font.italic = True
        rc.font.color.rgb = COLOR_BLACK

def add_image(doc, img_path, caption, width_in=5.8):
    """Add a centered image (retains original colors) with centered italic black caption."""
    if not os.path.exists(img_path):
        print(f"[Warning] Image not found: {img_path}")
        return

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(2)
    p_img.paragraph_format.keep_with_next = True

    run = p_img.add_run()
    run.add_picture(img_path, width=Inches(width_in))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(12)
    rc = p_cap.add_run(caption)
    rc.font.name = "Times New Roman"
    rc.font.size = Pt(9.5)
    rc.font.italic = True
    rc.font.color.rgb = COLOR_BLACK

def save_and_convert(doc, docx_path, pdf_path):
    """Save the Word document and invoke docx2pdf for native Word rendering."""
    print(f"[*] Saving Word document to: {docx_path}")
    doc.save(docx_path)
    print(f"[*] Converting to PDF via Word COM: {pdf_path}")
    convert(docx_path, pdf_path)
    if os.path.exists(pdf_path):
        size = os.path.getsize(pdf_path)
        print(f"[✓] Successfully generated {pdf_path} ({size:,} bytes)")
    else:
        print(f"[✗] Failed to generate {pdf_path}")
