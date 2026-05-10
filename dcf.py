# =========================================================
# DCF VALUATION ENGINE
# =========================================================
from predict import predict_growth
def adjusted_growth_rate(raw_growth):
    """
    raw_growth should be in decimal form.
    Example: 0.25 for 25%
    """

    if raw_growth >= 0.25:
        return 0.13   # midpoint of 12–15%

    elif 0.10 <= raw_growth < 0.25:
        return 0.08   # moderate adjustment

    elif 0 < raw_growth < 0.10:
        return 0.06   # slight conservative cut

    else:  # negative growth
        return 0.02   # recovery assumption (2%)
def dcf_model(
    fcf,
    growth_rate,
    discount_rate,
    terminal_growth_rate,
    projection_years,
    total_debt,
    shares_outstanding
):
    rate=adjusted_growth_rate(growth_rate)
    """
    Enterprise to Equity DCF Model
    """

    if discount_rate <= terminal_growth_rate:
        raise ValueError("Discount rate must be greater than terminal growth rate.")

    projected_fcfs = []
    discounted_fcfs = []

    # 1️⃣ Project FCF
    for year in range(1, projection_years + 1):
        projected_fcf = fcf * ((1 + rate) ** year)
        projected_fcfs.append(projected_fcf)

    # 2️⃣ Discount FCF
    for year, cashflow in enumerate(projected_fcfs, start=1):
        pv = cashflow / ((1 + discount_rate) ** year)
        discounted_fcfs.append(pv)

    # 3️⃣ Terminal Value (Gordon Growth)
    terminal_fcf = projected_fcfs[-1] * (1 + terminal_growth_rate)
    terminal_value = terminal_fcf / (discount_rate - terminal_growth_rate)

    # 4️⃣ Discount Terminal Value
    terminal_value_pv = terminal_value / ((1 + discount_rate) ** projection_years)

    # 5️⃣ Enterprise Value
    enterprise_value = sum(discounted_fcfs) + terminal_value_pv

    # 6️⃣ Equity Value (Adjust for Debt)
    equity_value = enterprise_value - total_debt

    # 7️⃣ Intrinsic Value Per Share
    intrinsic_value = equity_value / shares_outstanding

    return {
        "Enterprise Value": enterprise_value,
        "Equity Value": equity_value,
        "Intrinsic Value Per Share": intrinsic_value
    }
def run_dcf_analysis(stock_data, growth_rate):
    """
    stock_data = dictionary returned from your get_data()
    growth_rate = decimal (e.g., 0.10 for 10%)
    """

    fcf = stock_data["FCF"]
    total_debt = stock_data["Total Debt"]
    shares = stock_data["Shares"]
    current_price = stock_data["Current Price"]

    # ---- Assumptions ----
    projection_years = 5
    discount_rate = 0.12  # You can refine later using CAPM
    terminal_growth_rate = 0.03

    result = dcf_model(
        fcf=fcf,
        growth_rate=growth_rate,
        discount_rate=discount_rate,
        terminal_growth_rate=terminal_growth_rate,
        projection_years=projection_years,
        total_debt=total_debt,
        shares_outstanding=shares
    )

    intrinsic = result["Intrinsic Value Per Share"]
    margin_of_safety = (intrinsic - current_price) / current_price
    if margin_of_safety > 0:
        o="undervalued"
        print("🟢 Stock appears UNDERVALUED")
    else:
        o="overvalued"
        print("🔴 Stock appears OVERVALUED")
    a= {
        "Intrinsic":round(intrinsic, 2),
        "Margin of safety":round(intrinsic, 2),
        "OVER/UNDER":o,
    }

    print("\n" + "="*50)
    print("📊 DCF VALUATION RESULT")
    print("="*50)
    print(f"Intrinsic Value Per Share : ₹{intrinsic:,.2f}")
    print(f"Current Market Price      : ₹{current_price:,.2f}")
    print(f"Margin of Safety          : {margin_of_safety:.2%}")

    return a

new_data = {
    "Current Price":994,
    "Total Revenue": 26537008,
    "Net Income": 2500777,
    "EBIT": 3512747,
    "OCF": 553780,
    "FCF": -4578932,
    "ROE": 0.149406024,
    "ROCE": 0.099344865,
    "Tax Rate": 0.094700687,
    "Capex": 5132712,
    "D&A": 976720,
    "Total Debt": 16213284,
    "Shares": 133198037,
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
run_dcf_analysis(new_data,res["CAGR_revenue"])