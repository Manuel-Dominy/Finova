import yfinance as yf
import pandas as pd

def get_yoy_growth_from_scratch(ticker, year):
    stock = yf.Ticker(ticker)

    # Annual income statement
    income = stock.financials.T   # transpose for easy access
    income.index = income.index.year

    if year not in income.index or year - 1 not in income.index:
        return None

    revenue_curr = income.loc[year, "Total Revenue"]
    revenue_prev = income.loc[year - 1, "Total Revenue"]
    print(revenue_curr,revenue_prev)
    profit_curr = income.loc[year, "Net Income"]
    profit_prev = income.loc[year - 1, "Net Income"]
    print(profit_curr,profit_prev)
    revenue_yoy = ((revenue_curr - revenue_prev) / revenue_prev) * 100
    profit_yoy = ((profit_curr - profit_prev) / profit_prev) * 100

    return {
        "Company": ticker,
        "Year": year,
        "Revenue_YoY_Growth_%": round(revenue_yoy, 2),
        "Profit_YoY_Growth_%": round(profit_yoy, 2)
    }
