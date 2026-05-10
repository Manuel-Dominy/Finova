# =========================================================
# DCF VALUATION ENGINE (Improved Version)
# =========================================================
from predict import predict_growth
def adjusted_growth_rate(raw_growth):
    """
    Adjust raw growth conservatively.
    raw_growth must be decimal (0.25 = 25%)
    """

    if raw_growth >= 0.25:
        return 0.13
    elif 0.10 <= raw_growth < 0.25:
        return 0.08
    elif 0 < raw_growth < 0.10:
        return 0.06
    else:
        return 0.02  # recovery assumption


def normalize_fcf(stock_data):
    """
    If FCF is negative, try to estimate normalized FCF
    using OCF and reduced capex assumption.
    """
    fcf = stock_data["FCF"]

    if fcf > 0:
        return fcf

    # Assume only 50% of capex is maintenance
    ocf = stock_data["OCF"]
    capex = stock_data["Capex"]

    maintenance_capex = capex * 0.5
    normalized_fcf = ocf - maintenance_capex

    return normalized_fcf


def dcf_model(
    fcf,
    growth_rate,
    discount_rate,
    terminal_growth_rate,
    projection_years,
    total_debt,
    shares_outstanding,
    cash=0
):
    """
    Enterprise to Equity DCF Model
    """

    if discount_rate <= terminal_growth_rate:
        raise ValueError("Discount rate must be greater than terminal growth rate.")

    if shares_outstanding <= 0:
        raise ValueError("Invalid shares outstanding.")

    rate = adjusted_growth_rate(growth_rate)

    # 1️⃣ Project FCF
    projected_fcfs = [
        fcf * ((1 + rate) ** year)
        for year in range(1, projection_years + 1)
    ]

    # 2️⃣ Discount FCF
    discounted_fcfs = [
        cf / ((1 + discount_rate) ** year)
        for year, cf in enumerate(projected_fcfs, start=1)
    ]

    # 3️⃣ Terminal Value
    terminal_fcf = projected_fcfs[-1] * (1 + terminal_growth_rate)
    terminal_value = terminal_fcf / (discount_rate - terminal_growth_rate)

    # 4️⃣ Discount Terminal Value
    terminal_value_pv = terminal_value / ((1 + discount_rate) ** projection_years)

    # 5️⃣ Enterprise Value
    enterprise_value = sum(discounted_fcfs) + terminal_value_pv

    # 6️⃣ Equity Value
    equity_value = enterprise_value + cash - total_debt

    # 7️⃣ Intrinsic Value Per Share
    intrinsic_value = equity_value / shares_outstanding

    return intrinsic_value, enterprise_value, equity_value


def run_dcf_analysis(stock_data, growth_rate):

    current_price = stock_data["Current Price"]
    total_debt = stock_data["Total Debt"]
    shares = stock_data["Shares"]
    cash = stock_data.get("Cash", 0)

    # Normalize FCF if needed
    base_fcf = normalize_fcf(stock_data)
    print(base_fcf)
    if base_fcf <= 0:
        print("⚠ Warning: FCF still negative after normalization.")
        print("DCF may not be reliable.\n")

    # Assumptions
    projection_years = 5
    discount_rate = 0.12
    terminal_growth_rate = 0.04

    intrinsic, ev, equity = dcf_model(
        fcf=base_fcf,
        growth_rate=growth_rate,
        discount_rate=discount_rate,
        terminal_growth_rate=terminal_growth_rate,
        projection_years=projection_years,
        total_debt=total_debt,
        shares_outstanding=shares,
        cash=cash
    )

    margin_of_safety = (intrinsic - current_price) / current_price

    status = "UNDERVALUED" if margin_of_safety > 0 else "OVERVALUED"

    print("\n" + "=" * 60)
    print("📊 DCF VALUATION RESULT")
    print("=" * 60)
    print(f"Enterprise Value        : ₹{ev:,.2f}")
    print(f"Equity Value            : ₹{equity:,.2f}")
    print(f"Intrinsic Value/Share   : ₹{intrinsic:,.2f}")
    print(f"Current Market Price    : ₹{current_price:,.2f}")
    print(f"Margin of Safety        : {margin_of_safety:.2%}")
    print(f"Valuation Status        : {status}")
    print("=" * 60)

    return {
        "Intrinsic Value": round(intrinsic, 2),
        "Margin of Safety %": round(margin_of_safety * 100, 2),
        "Status": status
    }
new_data = {
    "Current Price":994,
    "Total Revenue": 26537008000,
    "Net Income": 2500777,
    "EBIT": 3512747,
    "OCF": 553780,
    "FCF": 260900000,
    "ROE": 0.149406024,
    "ROCE": 0.099344865,
    "Tax Rate": 0.094700687,
    "Capex": 5132712,
    "D&A": 976720,
    "Total Debt": 635100000,
    "Shares": 207396267,
    "Sentiment": 0.266666667,
    "Leadership": 8,
    "CapitalAllocation": 7,
    "Governance": 9,
    "Communication": 8,
    "Stability": 8,
    "MarketTrust": 8,
    "Revenue_YoY_Growth_%":28.12,
    "Profit_YoY_Growth_%":-11.93
}
res=predict_growth(new_data)
print(res)
run_dcf_analysis(new_data,res["CAGR_revenue"])