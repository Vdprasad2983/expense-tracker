# Redesigned Expense Tracker — single-file Streamlit app (Tabs UI)
# Save this as app.py (replace your existing app.py) and keep your gsheets_handler.py as-is.
# This version uses tabs (Option A), modern layout, IST defaults, improved save logic,
# immediate cache clearing, and nicer visuals (CSS injected).

import streamlit as st
import pandas as pd
from datetime import datetime, date
import pytz
import uuid
import io
from typing import Tuple

# Import your existing gsheets helper (must remain in repo)
from gsheets_handler import load_sheet, save_sheet
from utils import parse_date, DEFAULT_INCOME_CATS, DEFAULT_EXPENSE_CATS, ensure_numeric, calc_totals, append_row
from report import generate_monthly_pdf

# Page config and theme-like settings
st.set_page_config(page_title='Expense Tracker — Modern', layout='wide')

# Inject lightweight CSS for a modern look
enterprise_css = """
<style>

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
    background-color: #f5f7fb;
    color: #1b1f23;
}

/* Top title */
.header-title {
    font-size: 36px;
    font-weight: 700;
    color: #1b1f23;
    margin-bottom: 5px;
}
.header-subtitle {
    font-size: 16px;
    color: #6a737d;
    margin-bottom: 25px;
}

/* Navigation Tabs */
.stTabs [data-baseweb="tab"] {
    font-weight: 600;
    color: #6a737d;
    padding: 10px 18px;
    font-size: 16px;
}
.stTabs [aria-selected="true"] {
    color: #000 !important;
    border-bottom: 3px solid #4f46e5 !important; /* Premium Violet */
}

/* Cards */
.card {
    padding: 20px;
    border-radius: 16px;
    background: white;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
    transition: 0.2s;
}
.card:hover {
    transform: translateY(-3px);
    box-shadow: 0 7px 20px rgba(0,0,0,0.08);
}

/* Metrics */
.metric-value {
    font-size: 26px;
    font-weight: 700;
}
.metric-label {
    font-size: 14px;
    color: #6a737d;
}

/* Buttons */
.stButton>button {
    background: #4f46e5;
    color: white !important;
    border-radius: 10px;
    padding: 10px 20px;
    font-size: 16px;
    border:none;
    font-weight: 600;
    transition: 0.2s;
}
.stButton>button:hover {
    background: #4338ca;
}

/* Inputs clean design */
input, select, textarea {
    background: #ffffff !important;
    border-radius: 8px !important;
    border: 1px solid #d1d5db !important;
    color: #111827 !important;
}

/* Dataframe table */
div[data-testid="dataframe"] {
    border-radius: 10px;
    border: 1px solid #e5e7eb;
    overflow: hidden;
}

</style>
"""
st.markdown(enterprise_css, unsafe_allow_html=True)
# ---------------------
# Config: Sheet and worksheet
# ---------------------
# Use full sheet URL (recommended) or edit link
SHEET_URL = st.secrets.get('sheet_url', "https://docs.google.com/spreadsheets/d/19Bpfg04cACOQUEOAkfqEGuxL3TLoL8524l904KQayBA")
WORKSHEET = st.secrets.get('worksheet_name', 'sheet1')

# ---------------------
# Helper: IST default time
# ---------------------
import pytz

def get_current_ist_time():
    utc_now = datetime.utcnow()
    ist = pytz.timezone('Asia/Kolkata')
    return utc_now.replace(tzinfo=pytz.utc).astimezone(ist).time()

# ---------------------
# Load data (safe)
# ---------------------
@st.cache_data(ttl=30)
def cached_load(sheet_url: str, worksheet: str) -> Tuple[pd.DataFrame, object]:
    df_raw, conn = load_sheet(sheet_url, worksheet)
    return df_raw, conn

with st.spinner('Loading data...'):
    try:
        df_raw, conn = cached_load(SHEET_URL, WORKSHEET)
        # Ensure DataFrame columns are standardized
        if not isinstance(df_raw, pd.DataFrame):
            df_raw = pd.DataFrame(df_raw)
        # Show debug if missing expected cols
        # Normalize column names (strip)
        df_raw.columns = [c.strip() for c in df_raw.columns]
        # If Date exists, parse
        if 'Date' in df_raw.columns:
            df_raw['Date'] = df_raw['Date'].apply(parse_date)
        else:
            # ensure at least an empty df with expected columns
            expected = ['Date','Time','Type','Income','Expense','Remaining Balance','Category','Income/Expense']
            df_raw = df_raw.reindex(columns=expected)
        df = ensure_numeric(df_raw, ['Income','Expense','Remaining Balance'])
    except Exception as e:
        st.error('Failed to load Google Sheet. Make sure sheet URL and connection are configured.')
        st.exception(e)
        st.stop()

# Initialize categories in session state
if 'income_cats' not in st.session_state:
    st.session_state.income_cats = list(DEFAULT_INCOME_CATS)
if 'expense_cats' not in st.session_state:
    st.session_state.expense_cats = list(DEFAULT_EXPENSE_CATS)

# Top header
col1, col2 = st.columns([4,1])
with col1:
    st.markdown('<div class="header"><div class="app-title">💼 Expense Tracker</div><div class="subtitle">A clean modern redesign</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="small">Connected to Google Sheets</div>', unsafe_allow_html=True)

# Tabs navigation (Option A)
tabs = st.tabs(["Dashboard","Add Entry","Categories","Reports","View Data"]) 

# ---------------------
# DASHBOARD TAB
# ---------------------
with tabs[0]:
    st.subheader('Dashboard')
    totals = calc_totals(df)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="small">Total Income</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric green">₹ {totals["income"]:,.2f}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="small">Total Expense</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric red">₹ {totals["expense"]:,.2f}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="small">Balance</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric blue">₹ {totals["balance"]:,.2f}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('---')
    st.subheader('Income vs Expense (by Date)')
    temp = df.copy()
    if temp['Date'].notna().any():
        temp['Date'] = pd.to_datetime(temp['Date'])
        agg = temp.groupby('Date')[['Income','Expense']].sum()
        st.line_chart(agg)
    else:
        st.info('No date-stamped data available yet.')

    st.subheader('Expenses by Category')
    if 'Category' in df.columns and df['Expense'].sum() > 0:
        cat = df[df['Expense']>0].groupby('Category')['Expense'].sum().sort_values(ascending=False)
        st.bar_chart(cat)
    else:
        st.info('No expense data yet.')

# ---------------------
# ADD ENTRY TAB
# ---------------------
with tabs[1]:
    st.subheader('Add Entry')
    entry_type = st.radio('Type', ['Income','Expense'], horizontal=True)

    # form without clear_on_submit, we'll clear on success
    with st.form('entry_form'):
        cols = st.columns(3)
        amount = cols[0].number_input('Amount (₹)', min_value=0.0, format='%.2f')
        category = cols[1].selectbox('Category', options=(st.session_state.income_cats if entry_type=='Income' else st.session_state.expense_cats))
        date_val = cols[0].date_input('Date', value=date.today(), max_value=date.today())
        time_val = cols[1].time_input('Time', value=get_current_ist_time())
        desc = cols[2].text_input('Description (optional)')

        submitted = st.form_submit_button('Add Entry')
        if submitted:
            # build row with unique id
            current_balance = calc_totals(df)['balance']
            new_balance = current_balance + amount if entry_type=='Income' else current_balance - amount
            row = {
                'ID': str(uuid.uuid4())[:8],
                'Date': date_val,
                'Time': time_val.strftime('%H:%M'),
                'Type': desc,
                'Income': float(amount) if entry_type=='Income' else 0.0,
                'Expense': float(amount) if entry_type=='Expense' else 0.0,
                'Remaining Balance': new_balance,
                'Category': category,
                'Income/Expense': entry_type
            }

            # Save robustly: read fresh, append, write full
            try:
                # clear cache and reload fresh
                st.cache_data.clear()
                fresh, _ = load_sheet(SHEET_URL, WORKSHEET)
                if not isinstance(fresh, pd.DataFrame):
                    fresh = pd.DataFrame(fresh)
                fresh.columns = [c.strip() for c in fresh.columns]
                combined = pd.concat([fresh, pd.DataFrame([row])], ignore_index=True)
                save_sheet(conn, SHEET_URL, combined, WORKSHEET)
                st.success('Saved ✅')
                # clear cache again and rerun to show updated values
                st.cache_data.clear()
                st.experimental_rerun()
            except Exception as e:
                st.error('Failed to save — check connection and permissions')
                st.exception(e)

# ---------------------
# CATEGORIES TAB
# ---------------------
with tabs[2]:
    st.subheader('Manage Categories')
    st.write('Income Categories')
    with st.form('inc_cat'):
        new_inc = st.text_input('Add Income Category')
        if st.form_submit_button('Add Income Category') and new_inc:
            st.session_state.income_cats.append(new_inc.strip())
            st.success('Added')
    for i, c in enumerate(st.session_state.income_cats):
        c1,c2 = st.columns([6,1])
        c1.write(c)
        if c2.button('Delete', key=f'del_inc_{i}'):
            st.session_state.income_cats.pop(i)
            st.experimental_rerun()

    st.markdown('---')
    st.write('Expense Categories')
    with st.form('exp_cat'):
        new_exp = st.text_input('Add Expense Category')
        if st.form_submit_button('Add Expense Category') and new_exp:
            st.session_state.expense_cats.append(new_exp.strip())
            st.success('Added')
    for i, c in enumerate(st.session_state.expense_cats):
        c1,c2 = st.columns([6,1])
        c1.write(c)
        if c2.button('Delete', key=f'del_exp_{i}'):
            st.session_state.expense_cats.pop(i)
            st.experimental_rerun()

# ---------------------
# REPORTS TAB
# ---------------------
with tabs[3]:
    st.subheader('Reports & Export')
    years = sorted(list({d.year for d in df['Date'] if hasattr(d, 'year')})) if not df['Date'].empty else [date.today().year]
    year = st.selectbox('Year', years, index=len(years)-1)
    month = st.selectbox('Month', list(range(1,13)), index=date.today().month-1)

    if st.button('Generate Monthly PDF'):
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
    towrite = io.BytesIO()
    df.to_excel(towrite, index=False, engine='openpyxl')
    towrite.seek(0)
    st.download_button('Download Excel', data=towrite, file_name='transactions.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ---------------------
# VIEW DATA TAB
# ---------------------
with tabs[4]:
    st.subheader('Transactions')
    st.dataframe(df.sort_values('Date', ascending=False))

    st.markdown('---')
    st.subheader('Filter Transactions')
    from_d = st.date_input('From', value=(min(df['Date']) if not df['Date'].empty else date.today().replace(day=1)))
    to_d = st.date_input('To', value=(max(df['Date']) if not df['Date'].empty else date.today()))
    sel_cat = st.selectbox('Category', ['All'] + sorted([c for c in df['Category'].unique() if c]))
    mask = (df['Date'] >= from_d) & (df['Date'] <= to_d)
    if sel_cat != 'All':
        mask &= (df['Category'] == sel_cat)
    st.dataframe(df[mask].sort_values('Date', ascending=False))

# End of redesigned app
