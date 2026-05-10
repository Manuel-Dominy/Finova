from flask import Flask, request, jsonify
import os
from intrins import main
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # enable CORS
VALID_API_KEY = "Finova123456789"
@app.route('/predict', methods=['POST'])
def predict():
    api_key = request.headers.get("X-API-KEY")
    if api_key != VALID_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    file_path = "COMPANY_sentiment.csv"
    if os.path.exists(file_path):
        os.remove(file_path)
        print("CSV file deleted.")
    else:
        print("File does not exist.")
    data = request.get_json()
    company = data.get("company")

    if not company:
        return jsonify({"error": "No company provided"}), 400

    main(company)

    return jsonify({"status": "success"})

if __name__ == '__main__':
    # Start the server on port 5000
    
    app.run(host='0.0.0.0', port=1025,debug=True)
