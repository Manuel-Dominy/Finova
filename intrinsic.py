import pandas as pd
from predict import predict_growth
import os

# =========================
# Calculate Financial Ratios
# =========================
def calculate_ratios_from_csv(df, years=5):

    df = df.sort_values("Year Analyzed").tail(years)

    # Operating Margin
    df["Operating_Margin"] = df["EBIT"] / df["Total Revenue"]
    print(df[["Year Analyzed", "Capex", "Total Revenue"]])

    # Depreciation %
    df["Dep_pct"] = df["D&A"] / df["Total Revenue"]

    # Capex %
    df["Capex_pct"] = df["Capex"].abs() / df["Total Revenue"]

    # Working Capital %
    df["NWC"] = df["Current Assets"] - df["Current Liabilities"]
    df["Change_NWC"] = df["NWC"].diff()
    df["Change_Revenue"] = df["Total Revenue"].diff()

    # Avoid division by zero
    df["WC_ratio"] = df["Change_NWC"] / df["Change_Revenue"].replace(0, pd.NA)
    rat_series = df["WC_ratio"].dropna()

    if len(rat_series) < 2:
        wc_pct = 0.05
    else:
        wc_pct = min(max(rat_series.mean(), 0.05), 0.12)

    # Safety caps
    tax_rate = min(max(df["Tax Rate"].mean(), 0.20), 0.30)
    operating_margin = min(df["Operating_Margin"].mean(), 0.40)
    capex_pct = min(df["Capex_pct"].mean(), 0.15)

    return {
        "operating_margin": round(operating_margin, 4),
        "dep_pct": df["Dep_pct"].mean(),
        "capex_pct": round(capex_pct, 4),
        "wc_pct": wc_pct,
        "tax_rate": round(tax_rate, 4),
    }

# =========================
# DCF MODEL
# =========================
def dcf_intrinsic_value(
    current_revenue,
    revenue_cagr,
    operating_margin,
    tax_rate,
    depreciation_pct,
    capex_pct,
    working_capital_pct,
    discount_rate,
    terminal_growth_rate,
    projection_years,
    total_debt,
    shares_outstanding
):

    if discount_rate <= terminal_growth_rate:
        raise ValueError("Discount rate must be greater than terminal growth rate.")

    revenue = current_revenue
    projected_fcfs = []

    for year in range(1, projection_years + 1):

        # Fade reinvestment as firm matures
        fade = 1 - (year / (projection_years + 2))

        adj_capex_pct = capex_pct * fade
        adj_wc_pct = working_capital_pct * fade

        revenue_next = revenue * (1 + revenue_cagr)

        ebit = revenue_next * operating_margin
        nopat = ebit * (1 - tax_rate)

        depreciation = revenue_next * depreciation_pct
        capex = revenue_next * adj_capex_pct

        delta_revenue = max(revenue_next - revenue, 0)
        wc = delta_revenue * adj_wc_pct

        fcf = nopat + depreciation - capex - wc
        projected_fcfs.append(fcf)

        revenue = revenue_next

    pv_fcfs = [
        fcf / ((1 + discount_rate) ** (i + 1))
        for i, fcf in enumerate(projected_fcfs)
    ]

    # Terminal stage
    terminal_revenue = revenue * (1 + terminal_growth_rate)
    terminal_ebit = terminal_revenue * operating_margin
    terminal_nopat = terminal_ebit * (1 - tax_rate)

    terminal_depreciation = terminal_revenue * depreciation_pct
    terminal_capex = terminal_depreciation

    # Incremental WC only
    terminal_wc = terminal_revenue * terminal_growth_rate * working_capital_pct * 0.5

    terminal_fcf = (
        terminal_nopat
        + terminal_depreciation
        - terminal_capex
        - terminal_wc
    )

    terminal_value = terminal_fcf / (discount_rate - terminal_growth_rate)
    terminal_value_pv = terminal_value / ((1 + discount_rate) ** projection_years)

    enterprise_value = sum(pv_fcfs) + terminal_value_pv
    equity_value = enterprise_value - total_debt
    intrinsic_value = equity_value / shares_outstanding

    return intrinsic_value

# =========================
# MASTER FUNCTION
# =========================
def run_dcf_from_csv(csv_path, ticker, discount_rate, terminal_growth_rate, projection_years):

    df = pd.read_csv(csv_path)
    company_df = df[df["Ticker"] == ticker].sort_values("Year Analyzed")
    latest = company_df.iloc[-1]
    print(latest)
    stock_data = latest.to_dict()
    j = predict_growth(stock_data)
    growth_rate = j["CAGR_revenue"]
    netincome = j["CAGR_netincome"]
    print(j)
    # Normalize growth BEFORE DCF
    if growth_rate >= 0.25:
        growth_rate = 0.13
    elif 0.10 <= growth_rate < 0.25:
        growth_rate = 0.08
    elif 0 < growth_rate < 0.10:
        growth_rate = 0.06
    else:
        growth_rate = 0.02

    ratios = calculate_ratios_from_csv(company_df)

    intrinsic_value = dcf_intrinsic_value(
        current_revenue=latest["Total Revenue"],
        revenue_cagr=growth_rate,
        operating_margin=ratios["operating_margin"],
        tax_rate=ratios["tax_rate"],
        depreciation_pct=ratios["dep_pct"],
        capex_pct=ratios["capex_pct"],
        working_capital_pct=ratios["wc_pct"],
        discount_rate=discount_rate,
        terminal_growth_rate=terminal_growth_rate,
        projection_years=projection_years,
        total_debt=latest["Total Debt"],
        shares_outstanding=latest["Shares"]
    )

    return {
        "CAGR_revenue": growth_rate,
        "CAGR_netincome": netincome,
        "Operating Margin": ratios["operating_margin"],
        "Tax Rate": ratios["tax_rate"],
        "Depreciation %": ratios["dep_pct"],
        "Capex %": ratios["capex_pct"],
        "Working Capital %": ratios["wc_pct"],
        "Intrinsic Value Per Share": round(intrinsic_value,2)
    }

# =========================
# SAVE RESULT
# =========================
def save_result_to_csv(csv_path, ticker, result_dict):

    df = pd.read_csv(csv_path)
    latest_row = df[df["Ticker"] == ticker].sort_values("Year Analyzed").iloc[-1:].copy()

    for key, value in result_dict.items():
        latest_row[key] = value

    output_file = "result.csv"

    if os.path.exists(output_file):
        result_df = pd.read_csv(output_file)
        result_df = result_df[result_df["Ticker"] != ticker]
        result_df = pd.concat([result_df, latest_row], ignore_index=True)
    else:
        result_df = latest_row

    result_df.to_csv(output_file, index=False)
    print(f"Saved results for {ticker} to result.csv")
    return result_df

def fun(tick):
    result = run_dcf_from_csv(
        csv_path="stock_analysis_results.csv",
        ticker=tick,
        discount_rate=0.10,
        terminal_growth_rate=0.04,
        projection_years=5
    )
    print("CAGR_revenue:",result["CAGR_revenue"],"Operating Margin:",result["Operating Margin"],"Tax Rate:",result["Tax Rate"],"Depreciation %:",result["Depreciation %"],"Capex %:",result["Capex %"],"Working Capital %:",result["Working Capital %"],"Intrinsic Value Per Share:",result["Intrinsic Value Per Share"])
    result_df = save_result_to_csv("stock_analysis_results.csv", tick, result)
    print(result_df)
