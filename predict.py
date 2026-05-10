import pandas as pd
import joblib

# Load saved objects
model = joblib.load("linear_growth_model.pkl") 
scaler = joblib.load("scaler.pkl") 
features = joblib.load("model_features.pkl")


def predict_growth(new_data_dict):
    """
    new_data_dict: dictionary containing feature values
    Returns predicted Revenue & Profit YoY growth
    """
    
    # Convert to DataFrame
    df_input = pd.DataFrame([new_data_dict])
    
    # Ensure correct feature order
    df_input = df_input[features]
    
    # Scale
    df_scaled = scaler.transform(df_input)
    
    # Predict
    prediction = model.predict(df_scaled)
    
    return {
        "CAGR_revenue": round(float(prediction[0][0]), 2),
        "CAGR_netincome": round(float(prediction[0][1]), 2)
    }
new_data = {
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

result = predict_growth(new_data)

print(result)