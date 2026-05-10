import requests
import pandas as pd
from rapidfuzz import process

NSE_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
def clean_text(text):
    return (
        text.upper()
        .replace("&", "AND")
        .replace("CORPN", "CORPORATION")
        .replace("LTD", "LIMITED")
        .strip()
    )
def load_nse_database():
    df = pd.read_csv(NSE_URL)

    # Debug: show actual column names
    print("Columns found:", list(df.columns))

    # NSE sometimes changes column labels
    possible_name_cols = [
        "NAME OF COMPANY",
        "Company Name",
        "NAME",
        "Security Name"
    ]

    name_col = None
    for col in possible_name_cols:
        if col in df.columns:
            name_col = col
            break

    if name_col is None:
        raise RuntimeError("Company name column not found in NSE CSV")

    df[name_col] = df[name_col].astype(str).str.upper()

    return df, name_col


def company_to_nse_ticker(query):
    df, name_col = load_nse_database()

    match, score, idx = process.extractOne(
        query.upper(),
        df[name_col],
        score_cutoff=60
    )

    if match is None:
        return None

    symbol = df.iloc[idx]["SYMBOL"]
    return symbol + ".NS"


def JO(companyname):
    # Example
    company=clean_text(companyname)
    ticker = company_to_nse_ticker(company)
    print("Ticker:", ticker)
    return ticker