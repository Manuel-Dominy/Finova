import yfinance as yf
import pandas as pd
import difflib
import os
import requests
from Comments import sentiment
from Rag_based import Main
from mana import Main
from RP import get_yoy_growth_from_scratch
from NSETICKER import JO
from intrinsic import fun
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_screener_symbol(company_name):
    url = f"https://www.screener.in/api/company/search/?q={company_name}"
    r = requests.get(url, headers=HEADERS)
    data = r.json()
    if not data:
        return None
    return data[0]["url"].split("/")[2]


def build_dcf_csv(company_name):
    symbol = get_screener_symbol(company_name)
    print("✅ Screener Symbol:", symbol)
    return symbol
# =========================================================
# 1. EXTENDED NSE DATABASE
# =========================================================
NSE_DATABASE = {
    "TATA CONSULTANCY SERVICES (TCS)": "TCS.NS",
    "TATA MOTORS": "TATAMOTORS.NS",
    "TATA STEEL": "TATASTEEL.NS",
    "TATA POWER": "TATAPOWER.NS",
    "TATA CONSUMER": "TATACONSUM.NS",
    "TITAN COMPANY": "TITAN.NS",
    "VOLTAS": "VOLTAS.NS",
    "TATA ELXSI": "TATAELXSI.NS",
    "TRENT": "TRENT.NS",
    "RELIANCE INDUSTRIES": "RELIANCE.NS",
    "JIO FINANCIAL SERVICES": "JIOFIN.NS",
    "ADANI ENTERPRISES": "ADANIENT.NS",
    "ADANI PORTS": "ADANIPORTS.NS",
    "ADANI POWER": "ADANIPOWER.NS",
    "ADANI GREEN": "ADANIGREEN.NS",
    "ADANI TOTAL GAS": "ATGL.NS",
    "HDFC BANK": "HDFCBANK.NS",
    "ICICI BANK": "ICICIBANK.NS",
    "AXIS BANK": "AXISBANK.NS",
    "KOTAK MAHINDRA BANK": "KOTAKBANK.NS",
    "INDUSIND BANK": "INDUSINDBK.NS",
    "IDFC FIRST BANK": "IDFCFIRSTB.NS",
    "STATE BANK OF INDIA (SBI)": "SBIN.NS",
    "BANK OF BARODA": "BANKBARODA.NS",
    "PUNJAB NATIONAL BANK (PNB)": "PNB.NS",
    "CANARA BANK": "CANBK.NS",
    "UNION BANK": "UNIONBANK.NS",
    "BAJAJ FINANCE": "BAJFINANCE.NS",
    "BAJAJ FINSERV": "BAJAJFINSV.NS",
    "LIC INDIA": "LICI.NS",
    "CHOLAMANDALAM FINANCE": "CHOLAFIN.NS",
    "SHRIRAM FINANCE": "SHRIRAMFIN.NS",
    "INFOSYS": "INFY.NS",
    "HCL TECH": "HCLTECH.NS",
    "WIPRO": "WIPRO.NS",
    "TECH MAHINDRA": "TECHM.NS",
    "LTIMINDTREE": "LTIM.NS",
    "PERSISTENT SYSTEMS": "PERSISTENT.NS",
    "ITC LTD": "ITC.NS",
    "HINDUSTAN UNILEVER (HUL)": "HINDUNILVR.NS",
    "NESTLE INDIA": "NESTLEIND.NS",
    "BRITANNIA": "BRITANNIA.NS",
    "DABUR INDIA": "DABUR.NS",
    "GODREJ CONSUMER": "GODREJCP.NS",
    "MARUTI SUZUKI": "MARUTI.NS",
    "MAHINDRA & MAHINDRA": "M&M.NS",
    "BAJAJ AUTO": "BAJAJ-AUTO.NS",
    "EICHER MOTORS": "EICHERMOT.NS",
    "HEROMOTOCO": "HEROMOTOCO.NS",
    "SUN PHARMA": "SUNPHARMA.NS",
    "DR REDDY'S": "DRREDDY.NS",
    "CIPLA": "CIPLA.NS",
    "DIVIS LAB": "DIVISLAB.NS",
    "LUPIN": "LUPIN.NS",
    "ONGC": "ONGC.NS",
    "COAL INDIA": "COALINDIA.NS",
    "NTPC": "NTPC.NS",
    "POWER GRID": "POWERGRID.NS",
    "GAIL": "GAIL.NS",
    "IOC": "IOC.NS",
    "BPCL": "BPCL.NS",
    "LARSEN & TOUBRO (L&T)": "LT.NS",
    "HAL": "HAL.NS",
    "BEL": "BEL.NS",
    "SIEMENS INDIA": "SIEMENS.NS",
    "ABB INDIA": "ABB.NS",
    "ULTRATECH CEMENT": "ULTRACEMCO.NS",
    "AMBUJA CEMENTS": "AMBUJACEM.NS",
    "ACC CEMENT": "ACC.NS",
    "SHREE CEMENT": "SHREECEM.NS",
    "HINDALCO": "HINDALCO.NS",
    "JSW STEEL": "JSWSTEEL.NS",
    "SAIL": "SAIL.NS",
    "NMDC": "NMDC.NS",
    "BHARTI AIRTEL": "BHARTIARTL.NS",
    "VODAFONE IDEA": "IDEA.NS",
    "DMART (AVENUE SUPERMARTS)": "DMART.NS",
    "ZOMATO": "ZOMATO.NS",
    "NYKAA": "NYKAA.NS",
}

# =========================================================
# 2. HELPER FUNCTIONS
# =========================================================

def safe_get(df, keys, col):
    if df is None or df.empty: return 0.0
    if isinstance(keys, str): keys = [keys]
    for key in keys:
        if key in df.index and col in df.columns:
            val = df.loc[key, col]
            return float(val) if not pd.isna(val) else 0.0
    return 0.0

def get_year_column(df, target_year):
    df_cols = pd.to_datetime(df.columns, errors='coerce')
    for col, dt in zip(df.columns, df_cols):
        if pd.notna(dt) and dt.year == int(target_year):
            return col
    print(f"⚠ Year {target_year} not found. Using latest available column.")
    return df.columns[-1]  # fallback to most recent

def search_ticker(query):
    query = query.upper().strip()
    results = [(name, ticker) for name, ticker in NSE_DATABASE.items() if query in name]
    if not results:
        results = JO(query)
    return results

def save_to_csv(data, filename="stock_analysis_results.csv"):
    df_new = pd.DataFrame([data])
    if not os.path.isfile(filename):
        df_new.to_csv(filename, index=False)
    else:
        df_new.to_csv(filename, mode='a', header=False, index=False)
    print(f"📁 Data saved to {filename}")

# =========================================================
# 3. EXTRACTION LOGIC
# =========================================================

def iter_get(ticker,userticker,target_year):
    if target_year=="2025":
        print("GI")
    elif target_year=="2024":
        print(target_year)
        try:
            stock = yf.Ticker(ticker)
            fin, bs, cf = stock.financials, stock.balance_sheet, stock.cashflow
            if "quarterly" in str(fin.index):
                fin = stock.financials
            if fin is None or fin.empty: return None
            info = stock.info
        except: return None
        sent=sentiment(userticker,target_year)
        if sent is None:
            return None
        year=int(target_year)
        output=get_yoy_growth_from_scratch(ticker,year)

        if output is None:
            print("YoY growth not available for this year or ticker")
            return None
        else:
            print(output["Revenue_YoY_Growth_%"])
            
        print("collect:",sent)
        s=str(target_year)
        user_input = build_dcf_csv(userticker)
        if user_input is None:
            return None
        mod=Main(user_input,s)
        if mod is None:
            return None
        print(mod["Leadership"])

        col = get_year_column(fin, target_year)
        if col is None: return None
        print(f"✅ Processing Period Ending: {col.date()}")

        # --- Metrics Extraction ---
        total_revenue = safe_get(fin, ["Total Revenue"], col)
        net_income = safe_get(fin, ["Net Income"], col)
        ebit = safe_get(fin, ["EBIT", "Operating Income"], col)
        tax_provision = safe_get(fin, ["Tax Provision", "Income Tax Expense"], col)
        pretax_income = safe_get(fin, ["Pretax Income"], col)
        tax_rate = (tax_provision / pretax_income) if pretax_income > 0 else 0.25

        # Cash Flows
        ocf = safe_get(cf, ["Operating Cash Flow", "Total Cash From Operating Activities"], col)
        capex = abs(safe_get(cf, ["Capital Expenditure"], col))
        da = safe_get(cf, ["Depreciation And Amortization"], col)
        fcf = safe_get(cf, ["Free Cash Flow"], col)
        if fcf == 0: fcf = ocf - capex

        # Balance Sheet Items
        equity = safe_get(bs, ["Stockholders Equity"], col)
        total_assets = safe_get(bs, ["Current Assets"], col)
        current_liabilities = safe_get(bs, ["Current Liabilities"], col)
        total_debt = safe_get(bs, ["Total Debt"], col)
        sares=info.get("sharesOutstanding", 1)
        print(sares,equity)

        # Ratios
        roe = net_income / equity if equity > 0 else 0
        capital_employed = total_assets - current_liabilities
        roce = ebit / capital_employed if capital_employed > 0 else 0
        
        # Prices and Sector
        current_price = info.get('currentPrice', 0.0)
        sector = info.get('sector', 'N/A')

        data = {
            "Company_Name":userticker,
            "Ticker": ticker,
            "Sector": sector,
            "Year Analyzed": target_year,
            "Date Ending": col.date(),
            "Current Price": current_price,
            "Total Revenue": total_revenue,
            "Net Income": net_income,
            "EBIT": ebit,
            "OCF": ocf,
            "FCF": fcf,
            "ROE": round(roe,4),
            "ROCE": round(roce,4),
            "Tax Rate": tax_rate,
            "Capex": capex,
            "D&A": da,
            "Total Debt": total_debt,
            "Shares": info.get('sharesOutstanding', 1),
            "Current Assets":total_assets,
            "Current Liabilities":current_liabilities,
            "Sentiment": float(sent),
            "Leadership": int(mod["Leadership"]),
            "CapitalAllocation": int(mod["CapitalAllocation"]),
            "Governance": int(mod["Governance"]),
            "Communication": int(mod["Communication"]),
            "Stability": int(mod["Stability"]),
            "MarketTrust": int(mod["MarketTrust"]),
            "FinalManagementScore": float(mod["FinalManagementScore"]),
            "Revenue_YoY_Growth_%": float(output["Revenue_YoY_Growth_%"]),
            "Profit_YoY_Growth_%": float(output["Profit_YoY_Growth_%"])
        }

        print("\n" + "="*45 + f"\n 📊 DATA SUMMARY FOR {ticker}\n" + "="*45)
        for k, v in data.items():
            if isinstance(v, float):
                if any(x in k for x in ["Rate", "ROE", "ROCE"]): print(f"{k:<20} | {v:.2%}")
                elif k == "Shares": print(f"{k:<20} | {v:,.0f}")
                else: print(f"{k:<20} | ₹{v:,.2f}")
            else: print(f"{k:<20} | {v}")

        save_to_csv(data)
    else:
        try:
            stock = yf.Ticker(ticker)
            fin, bs, cf = stock.financials, stock.balance_sheet, stock.cashflow
            if "quarterly" in str(fin.index):
                fin = stock.financials
            if fin is None or fin.empty: return None
            info = stock.info
        except: return None

        col = get_year_column(fin, target_year)
        if col is None: return None
        print(f"✅ Processing Period Ending: {col.date()}")

        # --- Metrics Extraction ---
        total_revenue = safe_get(fin, ["Total Revenue"], col)
        net_income = safe_get(fin, ["Net Income"], col)
        ebit = safe_get(fin, ["EBIT", "Operating Income"], col)
        tax_provision = safe_get(fin, ["Tax Provision", "Income Tax Expense"], col)
        pretax_income = safe_get(fin, ["Pretax Income"], col)
        tax_rate = (tax_provision / pretax_income) if pretax_income > 0 else 0.25

        # Cash Flows
        ocf = safe_get(cf, ["Operating Cash Flow", "Total Cash From Operating Activities"], col)
        capex = abs(safe_get(cf, ["Capital Expenditure"], col))
        da = safe_get(cf, ["Depreciation And Amortization"], col)
        fcf = safe_get(cf, ["Free Cash Flow"], col)
        if fcf == 0: fcf = ocf - capex

        # Balance Sheet Items
        equity = safe_get(bs, ["Stockholders Equity"], col)
        total_assets = safe_get(bs, ["Current Assets"], col)
        current_liabilities = safe_get(bs, ["Current Liabilities"], col)
        total_debt = safe_get(bs, ["Total Debt"], col)
        sares=info.get("sharesOutstanding", 1)
        print(sares,equity)

        # Ratios
        roe = net_income / equity if equity > 0 else 0
        capital_employed = total_assets - current_liabilities
        roce = ebit / capital_employed if capital_employed > 0 else 0
        
        # Prices and Sector
        current_price = info.get('currentPrice', 0.0)
        sector = info.get('sector', 'N/A')

        data = {
            "Company_Name":userticker,
            "Ticker": ticker,
            "Sector": sector,
            "Year Analyzed": target_year,
            "Date Ending": col.date(),
            "Current Price": current_price,
            "Total Revenue": total_revenue,
            "Net Income": net_income,
            "EBIT": ebit,
            "OCF": ocf,
            "FCF": fcf,
            "ROE": round(roe,4),
            "ROCE": round(roce,4),
            "Tax Rate": tax_rate,
            "Capex": capex,
            "D&A": da,
            "Total Debt": total_debt,
            "Shares": info.get('sharesOutstanding', 1),
            "Current Assets":total_assets,
            "Current Liabilities":current_liabilities
        }

        print("\n" + "="*45 + f"\n 📊 DATA SUMMARY FOR {ticker}\n" + "="*45)
        for k, v in data.items():
            if isinstance(v, float):
                if any(x in k for x in ["Rate", "ROE", "ROCE"]): print(f"{k:<20} | {v:.2%}")
                elif k == "Shares": print(f"{k:<20} | {v:,.0f}")
                else: print(f"{k:<20} | ₹{v:,.2f}")
            else: print(f"{k:<20} | {v}")

        save_to_csv(data)
def get_data(ticker,userticker):
    print(f"\n⏳ Fetching data for {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        fin, bs, cf = stock.financials, stock.balance_sheet, stock.cashflow
        if fin is None or fin.empty: return None
        info = stock.info
    except: return None

    available_years = [str(pd.to_datetime(c).year) for c in fin.columns if not pd.isna(pd.to_datetime(c))]
    for x in available_years:
        iter_get(ticker,userticker,x)
    
    return True

# =========================================================
# 4. MAIN LOOP
# =========================================================
import os
def main(query):
    file="stock_analysis_results.csv"
    file_path = "management_analysis_2024.csv"
    file_path_1 = "COMPANY_sentiment_2024.csv"
    if os.path.exists(file):
        os.remove(file)
        print("✅ File deleted successfully")
    else:
        print("❌ File does not exist")
        print("🚀 Stock Data Scraper (CSV Export & Sector column)")
    if os.path.exists(file_path):
        os.remove(file_path)
        print("✅ File deleted successfully")
    else:
        print("❌ File does not exist")
        print("🚀 Stock Data Scraper (CSV Export & Sector column)")
    if os.path.exists(file_path_1):
        os.remove(file_path_1)
        print("✅ File deleted successfully")
    else:
        print("❌ File does not exist")
        print("🚀 Stock Data Scraper (CSV Export & Sector column)")
    ticker = JO(query)
    print(ticker)
        #if matches:
            #for i, (name, t) in enumerate(matches): print(f" [{i+1}] {name} ({t})")
            #sel = input("Select number (or Enter for first): ")
            #idx = int(sel)-1 if sel.isdigit() and 0 < int(sel) <= len(matches) else 0
            #ticker = matches[idx][1]
        #else:
            #ticker = query.upper() + ".NS"

    extracted = get_data(ticker,query)
    fun(ticker)
        
