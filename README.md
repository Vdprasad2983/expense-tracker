# Expense Tracker — Streamlit App

A modern, dashboard-driven **Income & Expense Tracker** built using **Streamlit + Google Sheets** with PDF reporting, category management, and data exports. This app requires zero backend hosting — Google Sheets acts as the database.

## Features

- Dashboard: totals, charts, and category insights
- Add Entry: income/expense with dynamic categories
- Category management: add/remove categories
- Monthly PDF reports (ReportLab)
- Export to CSV / Excel

## Project Structure

```
expense_tracker/
├── app.py
├── utils.py
├── gsheets_handler.py
├── report.py
├── requirements.txt
└── README.md
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Update `SHEET_URL` in `app.py` with your Google Sheet URL.
3. Run:
```bash
streamlit run app.py
```

## Notes

- Make sure your Google Sheet has the columns: Date, Time, Type, Income, Expense, Remaining Balance, Category, Income/Expense
- Share the sheet appropriately so the `streamlit_gsheets` connection can access it.
