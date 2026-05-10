from flask import Flask, request, jsonify
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle
import numpy as np

app = Flask(__name__)

# --- CONFIGURATION ---
# The API Key you requested
VALID_API_KEY = "FinovaProjectApiKey7036"
# The mapping used in your training code
MAPPING = {0: "negative", 1: "neutral", 2: "positive"}

# 1. Load the saved model and tokenizer
model = tf.keras.models.load_model("sentiment_model.h5")
with open('tokenizer.pickle', 'rb') as handle:
    tokenizer = pickle.load(handle)

@app.route('/predict', methods=['POST'])
def predict():
    # 2. API Key Security Check
    # We look for the key in the request headers
    api_key = request.headers.get("X-API-KEY")
    if api_key != VALID_API_KEY:
        return jsonify({"error": "Unauthorized: Invalid API Key"}), 401

    # 3. Get the data from the request body
    data = request.get_json()
    sentences = data.get("sentences")  # list of sentences
    if not sentences:
        return jsonify({"error": "No sentences provided"}), 400

    results = []
    scores = []

    for text in sentences:
        if not text.strip():  # skip empty strings
            continue

        seq = tokenizer.texts_to_sequences([text])
        padded = pad_sequences(seq, maxlen=200)
        pred = model.predict(padded)
        class_idx = int(np.argmax(pred[0]))
        confidence = float(np.max(pred[0]))

        MAPPING = {0: "negative", 1: "neutral", 2: "positive"}
        sentiment = MAPPING[class_idx]

        score_map = {"negative": -1, "neutral": 0, "positive": 1}
        scores.append(score_map[sentiment])

        results.append({
            "text": text,
            "sentiment": sentiment,
            "confidence": confidence,
            "score": score_map[sentiment]
        })

    normalized_score = float(np.mean(scores)) if scores else 0.0

    return jsonify({
        "status": "success",
        "results": results,
        "normalized_score": normalized_score
    })


if __name__ == '__main__':
    # Start the server on port 5000
    
    app.run(host='0.0.0.0', port=5001,debug=True)