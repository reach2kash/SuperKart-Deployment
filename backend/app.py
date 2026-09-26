import joblib
import pandas as pd
from flask import Flask, request, jsonify

superkart_api = Flask("SuperKart")

# Load once at startup - the pipeline includes preprocessing, so raw inputs are fine
import os
MODEL_PATH = os.environ.get("MODEL_PATH", "superkart_model.joblib")
model = joblib.load(MODEL_PATH)

REQUIRED_FEATURES = [
    "Product_Weight", "Product_Sugar_Content", "Product_Allocated_Area",
    "Product_MRP", "Store_Size", "Store_Location_City_Type", "Store_Type",
    "Product_Id_char", "Store_Age_Years", "Product_Type_Category",
]


@superkart_api.get("/")
def home():
    return "Welcome to the SuperKart System"


@superkart_api.get("/health")
def health():
    return jsonify({"status": "ok"})


@superkart_api.post("/v1/predict")
def predict_sales():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Request body must be valid JSON"}), 400
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400
    missing = [f for f in REQUIRED_FEATURES if f not in data]
    if missing:
        return jsonify({"error": f"Missing required features: {missing}"}), 400
    try:
        input_data = pd.DataFrame([{f: data[f] for f in REQUIRED_FEATURES}])
        prediction = float(model.predict(input_data)[0])
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {e}"}), 500
    return jsonify({"Sales": round(prediction, 2)})


@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "Attach a CSV file as multipart field 'file'"}), 400
    try:
        input_data = pd.read_csv(file)
        predictions = model.predict(input_data).tolist()
    except Exception as e:
        return jsonify({"error": f"Batch prediction failed: {e}"}), 500
    return jsonify({str(i): round(float(p), 2) for i, p in enumerate(predictions)})


if __name__ == "__main__":
    superkart_api.run(host="0.0.0.0", port=7860)
