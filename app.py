# === app.py (Complete Enterprise Redesign - Tabs UI) ===
# Replace your existing app.py with this file.
# Keep gsheets_handler.py and utils.py in the repo (an updated gsheets_handler is included below).

import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date
import pytz
import uuid
import io
from typing import Tuple

# Import helpers (ensure gsheets_handler.py in repo is the updated version included below)
from gsheets_handler import load_sheet, save_sheet
from utils import parse_date, DEFAULT_INCOME_CATS, DEFAULT_EXPENSE_CATS, ensure_numeric, calc_totals, append_row
from report import generate_monthly_pdf

# Page setup
st.set_page_config(page_title='Expense Tracker — Enterprise', layout='wide', initial_sidebar_state='collapsed')

# --- PREMIUM ENTERPRISE THEME (Style 3) ---
enterprise_css = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
    background-color: #f5f7fb;
    color: #0f1724;
}
.header-title { font-size: 30px; font-weight: 700; color: #0f1724; }
.header-subtitle { font-size:14px; color:#6b7280; margin-top:4px }
.stTabs [data-baseweb="tab"] { font-weight:600; color:#6b7280; padding:10px 18px; font-size:16px }
.stTabs [aria-selected="true"] { color:#0f1724 !important; border-bottom:3px solid #4f46e5 !important; }
.card { padding:18px; border-radius:14px; background:white; border:1px solid #e6eef8; box-shadow: 0 6px 18px rgba(15,23,36,0.04); }
.metric-value { font-size:22px; font-weight:700 }
.metric-label { font-size:13px; color:#6b7280 }
.stButton>button { background:#4f46e5; color:white !important; border-radius:10px; padding:10px 18px; font-weight:600 }
.stButton>button:hover { background:#4338ca }
input, select, textarea { background:#fff !important; color:#0f1724 !important; border-radius:8px !important; border:1px solid #e6eef8 !important }
div[data-testid="dataframe"] { border-radius:10px; border:1px solid #e6eef8; overflow:hidden }
.stDownloadButton>button { background:#06b6d4 !important; color:white !important }
hr { border: 1px solid rgba(15,23,36,0.04) }
</style>
"""
st.markdown(enterprise_css, unsafe_allow_html=True)

# ------------------
# Configuration — sheet URL pulled from secrets or fallback
# ------------------
SHEET_URL = st.secrets.get('sheet_url', "https://docs.google.com/spreadsheets/d/19Bpfg04cACOQUEOAkfqEGuxL3TLoL8524l904KQayBA")
WORKSHEET = st.secrets.get('worksheet_name', 'sheet1')  # use actual sheet tab name

# ------------------
# Timezone helper (IST default)
# ------------------
def current_ist_time():
    utc_now = datetime.utcnow()
    ist = pytz.timezone('Asia/Kolkata')
    return utc_now.replace(tzinfo=pytz.utc).astimezone(ist).time()

# ------------------
# Cached loader (short TTL)
# ------------------
@st.cache_data(ttl=20)
def cached_load(sheet_url: str, worksheet: str):
    df_raw, conn = load_sheet(sheet_url, worksheet)
    return df_raw, conn

# Load data
with st.spinner('Loading data...'):
    try:
        df_raw, conn = cached_load(SHEET_URL, WORKSHEET)
        if not isinstance(df_raw, pd.DataFrame):
            df_raw = pd.DataFrame(df_raw)
        # normalize header names
        df_raw.columns = [c.strip() for c in df_raw.columns]
        if 'Date' in df_raw.columns:
            df_raw['Date'] = df_raw['Date'].apply(parse_date)
        else:
            expected = ['Date','Time','Type','Income','Expense','Remaining Balance','Category','Income/Expense']
            df_raw = df_raw.reindex(columns=expected)
        df = ensure_numeric(df_raw, ['Income','Expense','Remaining Balance'])
    except Exception as e:
        st.error('Failed to load Google Sheet — check sheet URL, sharing, and secrets.')
        st.exception(e)
        st.stop()

# Initialize categories
if 'income_cats' not in st.session_state: st.session_state.income_cats = list(DEFAULT_INCOME_CATS)
if 'expense_cats' not in st.session_state: st.session_state.expense_cats = list(DEFAULT_EXPENSE_CATS)

# Header
col_h1, col_h2 = st.columns([6,1])
with col_h1:
    st.markdown('<div class="header-title">Expense Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-subtitle">Professional finance dashboard • Connected to Google Sheets</div>', unsafe_allow_html=True)
with col_h2:
    st.write('')

# Tabs
tabs = st.tabs(["Dashboard","Add Entry","Categories","Reports","View Data"])

# ------------------
# Dashboard
# ------------------
with tabs[0]:
    st.subheader('Overview')
    totals = calc_totals(df)
    a,b,c = st.columns([1,1,1])
    with a:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Total Income</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">₹ {totals["income"]:,.2f}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Total Expense</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">₹ {totals["expense"]:,.2f}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Balance</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">₹ {totals["balance"]:,.2f}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('---')
    st.subheader('Income vs Expense')
    temp = df.copy()
    if temp['Date'].notna().any():
        temp['Date'] = pd.to_datetime(temp['Date'])
        agg = temp.groupby('Date')[['Income','Expense']].sum().reset_index()
        chart = alt.Chart(agg).transform_fold(['Income','Expense'], as_=['Type','Amount']).mark_line(point=True).encode(
            x='Date:T', y='Amount:Q', color='Type:N', tooltip=['Date:T','Type:N','Amount:Q']
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info('No date-stamped data yet.')

    st.subheader('Expenses by Category')
    if 'Category' in df.columns and df['Expense'].sum() > 0:
        cat = df[df['Expense']>0].groupby('Category', dropna=False)['Expense'].sum().reset_index().sort_values('Expense', ascending=False)
        bar = alt.Chart(cat).mark_bar().encode(x='Expense:Q', y=alt.Y('Category:N', sort='-x'), tooltip=['Category','Expense:Q']).properties(height=320)
        st.altair_chart(bar, use_container_width=True)
    else:
        st.info('No expense data yet.')

# ------------------
# Add Entry
# ------------------
with tabs[1]:
    st.subheader('Add Transaction')
    entry_type = st.radio('Type',['Income','Expense'], horizontal=True)
    with st.form('entry'):
        c1,c2,c3 = st.columns([2,2,2])
        amount = c1.number_input('Amount (₹)', min_value=0.0, format='%.2f')
        category = c2.selectbox('Category', options=(st.session_state.income_cats if entry_type=='Income' else st.session_state.expense_cats))
        date_val = c1.date_input('Date', value=date.today(), max_value=date.today())
        time_val = c2.time_input('Time', value=current_ist_time())
        desc = c3.text_input('Description')
        submit = st.form_submit_button('Save Transaction')
        if submit:
            row = {
                'ID': str(uuid.uuid4())[:8],
                'Date': date_val,
                'Time': time_val.strftime('%H:%M'),
                'Type': desc,
                'Income': float(amount) if entry_type=='Income' else 0.0,
                'Expense': float(amount) if entry_type=='Expense' else 0.0,
                'Remaining Balance': calc_totals(df)['balance'] + (amount if entry_type=='Income' else -amount),
                'Category': category,
                'Income/Expense': entry_type
            }
            try:
                # robust save: reload fresh, append, write, clear cache
                st.cache_data.clear()
                fresh_raw, _ = load_sheet(SHEET_URL, WORKSHEET)
                if not isinstance(fresh_raw, pd.DataFrame): fresh_raw = pd.DataFrame(fresh_raw)
                fresh_raw.columns = [c.strip() for c in fresh_raw.columns]
                combined = pd.concat([fresh_raw, pd.DataFrame([row])], ignore_index=True)
                save_sheet(conn, SHEET_URL, combined, WORKSHEET)
                st.success('Transaction saved ✅')
                st.cache_data.clear()
                st.experimental_rerun()
            except Exception as e:
                st.error('Save failed — check permissions and connection')
                st.exception(e)

# ------------------
# Categories
# ------------------
with tabs[2]:
    st.subheader('Manage Categories')
    st.markdown('**Income Categories**')
    with st.form('inc_form'):
        new_inc = st.text_input('New Income Category')
        if st.form_submit_button('Add Income') and new_inc:
            st.session_state.income_cats.append(new_inc.strip())
            st.success('Added')
    for i,cname in enumerate(st.session_state.income_cats):
        r1,r2 = st.columns([8,1])
        r1.write(cname)
        if r2.button('Delete', key=f'del_inc_{i}'):
            st.session_state.income_cats.pop(i)
            st.experimental_rerun()

    st.markdown('---')
    st.markdown('**Expense Categories**')
    with st.form('exp_form'):
        new_exp = st.text_input('New Expense Category')
        if st.form_submit_button('Add Expense') and new_exp:
            st.session_state.expense_cats.append(new_exp.strip())
            st.success('Added')
    for i,cname in enumerate(st.session_state.expense_cats):
        r1,r2 = st.columns([8,1])
        r1.write(cname)
        if r2.button('Delete', key=f'del_exp_{i}'):
            st.session_state.expense_cats.pop(i)
            st.experimental_rerun()

# ------------------
# Reports
# ------------------
with tabs[3]:
    st.subheader('Reports & Exports')
    years = sorted(list({d.year for d in df['Date'] if hasattr(d, 'year')})) if not df['Date'].empty else [date.today().year]
    year = st.selectbox('Year', years, index=len(years)-1)
    month = st.selectbox('Month', list(range(1,13)), index=date.today().month-1)
    if st.button('Generate Monthly PDF'):
        try:
            pdf = generate_monthly_pdf(df, int(year), int(month))
            st.download_button('Download PDF', data=pdf, file_name=f'report_{year}_{month:02d}.pdf', mime='application/pdf')
            st.success('Report ready')
        except Exception as e:
            st.error('Failed to generate PDF')
            st.exception(e)

    st.markdown('---')
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button('Download CSV', data=csv, file_name='transactions.csv', mime='text/csv')
    towrite = io.BytesIO()
    try:
        df.to_excel(towrite, index=False, engine='openpyxl')
        towrite.seek(0)
        st.download_button('Download Excel', data=towrite, file_name='transactions.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        st.error('Excel export unavailable — missing dependency')

# ------------------
# View Data
# ------------------
with tabs[4]:
    st.subheader('Transactions')
    st.dataframe(df.sort_values('Date', ascending=False))
    st.markdown('---')
    from_d = st.date_input('From', value=(min(df['Date']) if not df['Date'].empty else date.today().replace(day=1)))
    to_d = st.date_input('To', value=(max(df['Date']) if not df['Date'].empty else date.today()))
    sel_cat = st.selectbox('Category', ['All'] + sorted([c for c in (df['Category'].dropna() if 'Category' in df.columns else pd.Series([])).unique()]))
    mask = (df['Date'] >= from_d) & (df['Date'] <= to_d)
    if sel_cat != 'All': mask &= (df['Category'] == sel_cat)
    st.dataframe(df[mask].sort_values('Date', ascending=False))

# === End of app.py ===


# === gsheets_handler.py (Updated — replace existing file) ===
# This updated handler ensures robust save and cache-clear behavior.

"""
gsheets_handler.py
Must be saved in repo as gsheets_handler.py
Uses st-gsheets-connection (st_gsheets_connection package)
"""

import streamlit as st
import pandas as pd
from st_gsheets_connection import GSheetsConnection
from typing import Tuple


def load_sheet(sheet_url: str, worksheet: str = 'sheet1') -> Tuple[pd.DataFrame, GSheetsConnection]:
    """Returns (dataframe, connection). The spreadsheet arg must be full URL."""
    conn = st.connection('gsheets', type=GSheetsConnection)
    data = conn.read(spreadsheet=sheet_url, worksheet=worksheet)
    df = pd.DataFrame(data)
    return df, conn


def save_sheet(conn: GSheetsConnection, sheet_url: str, df: pd.DataFrame, worksheet: str = 'sheet1'):
    """Writes the entire dataframe to the sheet and clears cache.
    This is safer for concurrent writes on Streamlit Cloud.
    """
    # write
    conn.update(spreadsheet=sheet_url, worksheet=worksheet, data=df)
    # clear streamlit cache so subsequent reads fetch the updated sheet
    try:
        st.cache_data.clear()
    except Exception:
        pass

# === End of gsheets_handler.py
