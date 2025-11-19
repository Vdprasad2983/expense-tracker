# utils.py
from datetime import datetime, date
from typing import List, Dict
import pandas as pd
import re

# Default categories (modifiable by user in-app)
DEFAULT_INCOME_CATS = ["Salary", "Bonus", "Refund", "Part-time", "Other Income"]
DEFAULT_EXPENSE_CATS = [
    "Food","Shopping","Transportation","Bills","Entertainment",
    "Health","Housing","Travel","Education","Bank Charges",
    "Repair","Gift","Other Expense"
]


# -----------------------------
# SAFE DATE PARSING
# -----------------------------
def parse_date(v):
    """Safely parse date strings or return date objects unchanged."""
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        # Remove accidental spaces
        v = v.strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(v, fmt).date()
            except:
                pass
    return v


# -----------------------------
# CLEAN NUMERIC FORMAT
# -----------------------------
def clean_numeric(x):
    """Convert values like '1,200', '₹ 500', ' 800 ' safely to float."""
    if pd.isna(x):
        return 0
    if isinstance(x, (int, float)):
        return float(x)
    x = str(x)
    x = x.replace("₹", "").replace(",", "").strip()
    x = re.sub(r"[^\d\.\-]", "", x)   # remove any non-numeric symbol
    try:
        return float(x)
    except:
        return 0


def ensure_numeric(df: pd.DataFrame, cols: List[str]):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].apply(clean_numeric)
    return df


# -----------------------------
# CORRECT TOTALS + BALANCE
# -----------------------------
def calc_totals(df: pd.DataFrame) -> Dict[str, float]:
    if df.empty:
        return {"income": 0, "expense": 0, "balance": 0}

    income = df["Income"].sum() if "Income" in df.columns else 0
    expense = df["Expense"].sum() if "Expense" in df.columns else 0

    # NEW: Always compute fresh balance
    balance = income - expense

    return {"income": income, "expense": expense, "balance": balance}


# -----------------------------
# APPEND NEW ROW
# -----------------------------
def append_row(df: pd.DataFrame, row: dict) -> pd.DataFrame:
    return pd.concat([df, pd.DataFrame([row])], ignore_index=True)
