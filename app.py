# app.py
import streamlit as st
import pandas as pd
from datetime import date
from utils import parse_date, DEFAULT_INCOME_CATS, DEFAULT_EXPENSE_CATS, ensure_numeric, calc_totals, append_row
from gsheets_handler import load_sheet, save_sheet
from report import generate_monthly_pdf
import io

st.set_page_config(page_title='Expense Tracker', layout='wide')

# ---------------------
# Configuration
# ---------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/19Bpfg04cACOQUEOAkfqEGuxL3TLoL8524l904KQayBA"
WORKSHEET = 'sheet1'

# ---------------------
# Load data
# ---------------------
with st.spinner('Loading data...'):
    try:
        df_raw, conn = load_sheet(SHEET_URL, WORKSHEET)
        df_raw['Date'] = df_raw['Date'].apply(parse_date)
        df = ensure_numeric(df_raw, ['Income','Expense','Remaining Balance'])
    except Exception as e:
        st.error('Failed to load Google Sheet. Make sure sheet URL and connection are configured.')
        st.exception(e)
        st.stop()

# Initialize session state
if 'income_cats' not in st.session_state:
    st.session_state.income_cats = DEFAULT_INCOME_CATS.copy()
if 'expense_cats' not in st.session_state:
    st.session_state.expense_cats = DEFAULT_EXPENSE_CATS.copy()

# ---------------------
# Layout: Sidebar Menu
# ---------------------
st.sidebar.title('Expense Tracker')
page = st.sidebar.selectbox('Go to', ['Dashboard','Add Entry','Categories','Reports','View Data'])

# ---------------------
# DASHBOARD
# ---------------------
if page == 'Dashboard':
    st.title('📊 Dashboard')
    totals = calc_totals(df)
    col1, col2, col3 = st.columns(3)
    col1.metric('Total Income', f"₹ {totals['income']:,.2f}")
    col2.metric('Total Expense', f"₹ {totals['expense']:,.2f}")
    col3.metric('Balance', f"₹ {totals['balance']:,.2f}")

    st.markdown('---')
    st.subheader('Income vs Expense')
    temp = df.copy()
    temp['Date'] = pd.to_datetime(temp['Date'])
    agg = temp.groupby('Date')[['Income','Expense']].sum()
    st.line_chart(agg)

    st.subheader('Category Breakdown (Expenses)')
    cat = df[df['Expense']>0].groupby('Category')['Expense'].sum().sort_values(ascending=False)
    if not cat.empty:
        st.bar_chart(cat)
    else:
        st.info('No expense data yet.')

# ---------------------
# ADD ENTRY
# ---------------------
elif page == 'Add Entry':
    st.title('➕ Add Entry')
    entry_type = st.radio('Type', ['Income','Expense'], horizontal=True)

    with st.form('entry_form', clear_on_submit=True):
        col1, col2 = st.columns(2)
        amount = col1.number_input('Amount (₹)', min_value=1.0, format='%.2f')
        category = col2.selectbox('Category', options=(st.session_state.income_cats if entry_type=='Income' else st.session_state.expense_cats))
        date_val = col1.date_input('Date', value=date.today(), max_value=date.today())
        time_val = col2.time_input('Time')
        desc = st.text_input('Description (optional)')

        submitted = st.form_submit_button('Add')
        if submitted:
            # compute new remaining balance
            current_balance = calc_totals(df)['balance']
            new_balance = current_balance + amount if entry_type=='Income' else current_balance - amount
            row = {
                'Date': date_val,
                'Time': time_val.strftime('%H:%M'),
                'Type': desc,
                'Income': amount if entry_type=='Income' else 0,
                'Expense': amount if entry_type=='Expense' else 0,
                'Remaining Balance': new_balance,
                'Category': category,
                'Income/Expense': entry_type
            }
            df2 = append_row(df, row)
            df2['Date'] = df2['Date'].apply(parse_date)
            try:
                save_sheet(conn, SHEET_URL, df2, WORKSHEET)
                st.success('Entry saved to Google Sheets ✅')
                st.rerun()
            except Exception as e:
                st.error('Failed to save — check connection')
                st.exception(e)

# ---------------------
# CATEGORIES
# ---------------------
elif page == 'Categories':
    st.title('🗂️ Manage Categories')
    st.subheader('Income Categories')
    with st.form('inc_cat_form'):
        new_inc = st.text_input('Add Income Category')
        if st.form_submit_button('Add Income Category') and new_inc:
            st.session_state.income_cats.append(new_inc.strip())
            st.success('Added')

    for i, c in enumerate(st.session_state.income_cats):
        col1, col2 = st.columns([4,1])
        col1.write(c)
        if col2.button('Delete', key=f'del_inc_{i}'):
            st.session_state.income_cats.pop(i)
            st.rerun()

    st.markdown('---')
    st.subheader('Expense Categories')
    with st.form('exp_cat_form'):
        new_exp = st.text_input('Add Expense Category')
        if st.form_submit_button('Add Expense Category') and new_exp:
            st.session_state.expense_cats.append(new_exp.strip())
            st.success('Added')

    for i, c in enumerate(st.session_state.expense_cats):
        col1, col2 = st.columns([4,1])
        col1.write(c)
        if col2.button('Delete', key=f'del_exp_{i}'):
            st.session_state.expense_cats.pop(i)
            st.rerun()

# ---------------------
# REPORTS
# ---------------------
elif page == 'Reports':
    st.title('📅 Reports & Exports')
    st.subheader('Monthly PDF Report')

    years = sorted(list({d.year for d in df['Date'] if hasattr(d, 'year')})) if not df['Date'].empty else [date.today().year]
    year = st.selectbox('Year', years, index=len(years)-1)
    month = st.selectbox('Month', list(range(1,13)), index=date.today().month-1)

    if st.button('Generate PDF'):
        try:
            pdf_bytes = generate_monthly_pdf(df, int(year), int(month))
            st.download_button('Download PDF', data=pdf_bytes, file_name=f'monthly_{year}_{month:02d}.pdf', mime='application/pdf')
            st.success('Report ready')
        except Exception as e:
            st.error('Failed to generate PDF — ensure reportlab is installed')
            st.exception(e)

    st.markdown('---')
    st.subheader('Export Data')
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button('Download CSV', data=csv, file_name='transactions.csv', mime='text/csv')
    # Excel export
    towrite = io.BytesIO()
    df.to_excel(towrite, index=False, engine='openpyxl')
    towrite.seek(0)
    st.download_button('Download Excel', data=towrite, file_name='transactions.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ---------------------
# VIEW DATA
# ---------------------
elif page == 'View Data':
    st.title('📋 Transactions')
    st.dataframe(df.sort_values('Date', ascending=False))
    st.markdown('---')
    st.subheader('Filter Transactions')
    c1, c2, c3 = st.columns(3)
    from_d = c1.date_input('From', value=(min(df['Date']) if not df['Date'].empty else date.today().replace(day=1)))
    to_d = c2.date_input('To', value=(max(df['Date']) if not df['Date'].empty else date.today()))
    cat_opts = ['All'] + sorted([c for c in df['Category'].unique() if c])
    sel_cat = c3.selectbox('Category', cat_opts)
    mask = (df['Date'] >= from_d) & (df['Date'] <= to_d)
    if sel_cat != 'All':
        mask &= (df['Category'] == sel_cat)
    st.dataframe(df[mask].sort_values('Date', ascending=False))
