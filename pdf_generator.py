import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically calculate total page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Top border for footer
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(36, 36, A4[0] - 36, 36)
        
        self.drawString(36, 24, "Paisa Pulse • Personal Financial Statement")
        self.drawRightString(A4[0] - 36, 24, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def generate_pdf_report(username, transactions, filter_info=None):
    """
    Generate a professional PDF statement from a list of transactions.
    Returns bytes buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e1b4b')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b')
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#334155')
    )
    cell_bold_style = ParagraphStyle(
        'CellBoldText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )
    cell_header_style = ParagraphStyle(
        'CellHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    # 1. Header Section with Brand
    header_data = [
        [
            Paragraph("<b>Paisa</b><font color='#4f46e5'><b>Pulse</b></font>", title_style),
            Paragraph(f"<b>Statement Date:</b> {datetime.now().strftime('%d %b %Y, %I:%M %p')}<br/><b>Account:</b> {username}", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[280, 242])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 14))

    # 2. Filter Summary Banner
    filter_desc = filter_info if filter_info else "All recorded transactions included"
    banner_data = [[
        Paragraph(f"<b>Report Scope:</b> {filter_desc}", cell_style)
    ]]
    banner_table = Table(banner_data, colWidths=[522])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 14))

    # 3. KPI Metrics Summary Cards
    total_income = sum(float(t['amount'] or 0) for t in transactions if t['type'] == 'income')
    total_expense = sum(float(t['amount'] or 0) for t in transactions if t['type'] == 'expense')
    net_balance = total_income - total_expense
    total_count = len(transactions)

    kpi_data = [
        [
            Paragraph("TOTAL TRANSACTIONS", ParagraphStyle('KpiH', fontName='Helvetica-Bold', fontSize=7, textColor=colors.HexColor('#64748b'))),
            Paragraph("TOTAL INCOME", ParagraphStyle('KpiH', fontName='Helvetica-Bold', fontSize=7, textColor=colors.HexColor('#059669'))),
            Paragraph("TOTAL EXPENSES", ParagraphStyle('KpiH', fontName='Helvetica-Bold', fontSize=7, textColor=colors.HexColor('#e11d48'))),
            Paragraph("NET CASH FLOW", ParagraphStyle('KpiH', fontName='Helvetica-Bold', fontSize=7, textColor=colors.HexColor('#4f46e5'))),
        ],
        [
            Paragraph(f"<b>{total_count}</b>", ParagraphStyle('KpiV', fontName='Helvetica-Bold', fontSize=13, textColor=colors.HexColor('#1e293b'))),
            Paragraph(f"<b>Rs. {total_income:,.2f}</b>", ParagraphStyle('KpiV', fontName='Helvetica-Bold', fontSize=13, textColor=colors.HexColor('#059669'))),
            Paragraph(f"<b>Rs. {total_expense:,.2f}</b>", ParagraphStyle('KpiV', fontName='Helvetica-Bold', fontSize=13, textColor=colors.HexColor('#e11d48'))),
            Paragraph(f"<b>Rs. {net_balance:,.2f}</b>", ParagraphStyle('KpiV', fontName='Helvetica-Bold', fontSize=13, textColor=colors.HexColor('#4f46e5'))),
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[120, 134, 134, 134])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#ecfdf5')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#fff1f2')),
        ('BACKGROUND', (3, 0), (3, -1), colors.HexColor('#eef2ff')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 16))

    # 4. Detailed Transactions Table
    table_headers = [
        Paragraph("#", cell_header_style),
        Paragraph("Date", cell_header_style),
        Paragraph("Type", cell_header_style),
        Paragraph("Category", cell_header_style),
        Paragraph("Description / Note", cell_header_style),
        Paragraph("Amount (INR)", cell_header_style)
    ]
    
    rows = [table_headers]
    for i, t in enumerate(transactions, 1):
        is_inc = (t['type'] == 'income')
        amt_prefix = "+" if is_inc else "-"
        amt_color = '#059669' if is_inc else '#1e293b'
        amt_str = f"<b>{amt_prefix}Rs. {float(t['amount']):,.2f}</b>"
        
        type_str = f"<font color='{'#059669' if is_inc else '#e11d48'}'><b>{t['type'].upper()}</b></font>"
        
        d_str = str(t['date'])[:10]
        try:
            d_fmt = datetime.strptime(d_str, "%Y-%m-%d").strftime("%d %b %Y")
        except Exception:
            d_fmt = d_str

        rows.append([
            Paragraph(str(i), cell_style),
            Paragraph(d_fmt, cell_style),
            Paragraph(type_str, cell_style),
            Paragraph(t['category'].capitalize(), cell_bold_style),
            Paragraph(t['note'] or "—", cell_style),
            Paragraph(f"<font color='{amt_color}'>{amt_str}</font>", cell_style),
        ])

    tx_table = Table(rows, colWidths=[24, 68, 54, 86, 170, 120])
    tx_table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e1b4b')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]

    # Alternating row colors
    for idx in range(1, len(rows)):
        bg = colors.HexColor('#f8fafc') if idx % 2 == 0 else colors.white
        tx_table_style.append(('BACKGROUND', (0, idx), (-1, idx), bg))

    tx_table.setStyle(TableStyle(tx_table_style))
    story.append(tx_table)

    # Build document with custom canvas
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
