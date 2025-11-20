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
    # Writes entire dataframe to the sheet (simple and reliable for small sheets)
    conn.update(spreadsheet=sheet_url, worksheet=worksheet, data=df)
