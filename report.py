# report.py
import io
from datetime import date
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import pandas as pd


def generate_monthly_pdf(df: pd.DataFrame, year: int, month: int) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    elements = []

    title = f"Monthly Report: {month:02d}-{year}"
    elements.append(Paragraph(title, styles['Heading1']))
    elements.append(Spacer(1,12))

    # Filter df for month
    dfm = df.copy()
    dfm['Date'] = pd.to_datetime(dfm['Date'])
    dfm = dfm[(dfm['Date'].dt.year == year) & (dfm['Date'].dt.month == month)]
    dfm = dfm.sort_values('Date')

    total_income = dfm['Income'].sum() if 'Income' in dfm.columns else 0
    total_expense = dfm['Expense'].sum() if 'Expense' in dfm.columns else 0
    end_balance = dfm['Remaining Balance'].iloc[-1] if ('Remaining Balance' in dfm.columns and not dfm.empty) else (total_income - total_expense)

    elements.append(Paragraph(f"Total Income: ₹ {total_income:,.2f}", styles['Normal']))
    elements.append(Paragraph(f"Total Expense: ₹ {total_expense:,.2f}", styles['Normal']))
    elements.append(Paragraph(f"End Balance: ₹ {end_balance:,.2f}", styles['Normal']))
    elements.append(Spacer(1,12))

    # Category breakdown
    if 'Category' in dfm.columns and not dfm.empty:
        cat = dfm.groupby('Category')['Expense'].sum().sort_values(ascending=False)
        data = [['Category', 'Amount (₹)']] + [[k, f"{v:,.2f}"] for k,v in cat.items()]
        t = Table(data, colWidths=[300,120])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0b6e4f')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('ALIGN',(1,1),(-1,-1),'RIGHT'),
            ('GRID',(0,0),(-1,-1),0.25,colors.grey)
        ]))
        elements.append(t)
        elements.append(Spacer(1,12))

    # Transactions table (limited columns)
    cols = ['Date','Time','Type','Income','Expense','Remaining Balance','Category','Income/Expense']
    table_rows = [cols]
    for _, r in dfm.iterrows():
        row = [
            r.get('Date').strftime('%Y-%m-%d') if pd.notnull(r.get('Date')) else '',
            r.get('Time',''),
            r.get('Type',''),
            f"{r.get('Income',0):,.2f}",
            f"{r.get('Expense',0):,.2f}",
            f"{r.get('Remaining Balance',0):,.2f}",
            r.get('Category',''),
            r.get('Income/Expense','')
        ]
        table_rows.append(row)

    if len(table_rows) > 1:
        tbl = Table(table_rows, repeatRows=1, colWidths=[80,50,120,80,80,90,120,80])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0b6e4f')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('GRID',(0,0),(-1,-1),0.25,colors.grey),
            ('FONTSIZE',(0,0),(-1,-1),8)
        ]))
        elements.append(tbl)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
