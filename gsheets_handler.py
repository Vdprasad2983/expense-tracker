# gsheets_handler.py

import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from typing import Tuple


def load_sheet(sheet_url: str, worksheet: str = 'sheet1') -> Tuple[pd.DataFrame, GSheetsConnection]:
    conn = st.connection('gsheets', type=GSheetsConnection)
    data = conn.read(spreadsheet=sheet_url, worksheet=worksheet)
    df = pd.DataFrame(data)
    return df, conn


def save_sheet(conn: GSheetsConnection, sheet_url: str, df: pd.DataFrame, worksheet: str = 'sheet1'):
    # Clear cache
    st.cache_data.clear()

    # Always reload the latest sheet before writing
    fresh = conn.read(spreadsheet=sheet_url, worksheet=worksheet)
    fresh_df = pd.DataFrame(fresh)

    # Append new rows to the fresh data
    combined = pd.concat([fresh_df, df.iloc[-1:]], ignore_index=True)

    # Save combined data
    conn.update(spreadsheet=sheet_url, worksheet=worksheet, data=combined)

    # Clear cache again to reflect immediately
    st.cache_data.clear()
