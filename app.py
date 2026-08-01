from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
from flask import send_from_directory
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split

app = Flask(__name__, static_folder=".")
CORS(app)

# ===================== GLOBAL VARIABLES =====================
df = None
model = None
scaler = None
label_encoders = {}
feature_columns = []
trained = False


# ===================== LOAD DATA =====================
def load_data():
    global df
    try:
        path = "retail_store_inventory.csv"
        print("📂 Files:", os.listdir())

        df = pd.read_csv(path)
        print("✅ Dataset loaded:", df.shape)

    except Exception as e:
        print("❌ DATA LOAD ERROR:", str(e))
        df = None


# ===================== PREPROCESS =====================
def preprocess():
    global df, model, scaler, label_encoders, feature_columns, trained

    if df is None:
        print("❌ No dataset")
        trained = False
        return

    try:
        data = df.copy()

        # Drop columns safely
        for col in ["Store ID", "Product ID"]:
            if col in data.columns:
                data.drop(col, axis=1, inplace=True)

        # Date features
        if "Date" in data.columns:
            data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
            data["Year"] = data["Date"].dt.year
            data["Month"] = data["Date"].dt.month
            data["Day"] = data["Date"].dt.day
            data["DayOfWeek"] = data["Date"].dt.dayofweek
            data["Quarter"] = data["Date"].dt.quarter
            data.drop("Date", axis=1, inplace=True)

        # Remove leakage
        if "Units Sold" in data.columns:
            data.drop("Units Sold", axis=1, inplace=True)

        # Encode categorical
        for col in data.select_dtypes(include="object").columns:
            le = LabelEncoder()
            data[col] = le.fit_transform(data[col].astype(str))
            label_encoders[col] = le

        if "Demand Forecast" not in data.columns:
            print("❌ Missing target")
            trained = False
            return

        y = data["Demand Forecast"]
        X = data.drop("Demand Forecast", axis=1)

        feature_columns = X.columns.tolist()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        model = RandomForestRegressor(n_estimators=100, max_depth=20)
        model.fit(X_train, y_train)

        trained = True
        print("✅ Model trained")

    except Exception as e:
        print("❌ PREPROCESS ERROR:", str(e))
        trained = False


# ===================== INPUT PREP =====================
def prepare_input(data):
    if scaler is None or not feature_columns:
        raise Exception("Model not ready")

    input_df = pd.DataFrame([data])

    for col in label_encoders:
        if col in input_df:
            try:
                # If unseen label appears, map to a fallback code 0
                input_df[col] = label_encoders[col].transform(input_df[col])
            except Exception:
                # Create numeric column with fallback 0 for unknown categories
                input_df[col] = 0
        else:
            input_df[col] = 0

    for col in feature_columns:
        if col not in input_df:
            input_df[col] = 0

    input_df = input_df[feature_columns]
    return scaler.transform(input_df)


# ===================== ROUTES =====================
@app.route('/')
def root_page():
    # Prefer index.html, fallback to dashboard.html
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    if os.path.exists('dashboard.html'):
        return send_from_directory('.', 'dashboard.html')
    return "No front-end available", 404

@app.route('/signup')
def signup_page():
    if os.path.exists('signup.html'):
        return send_from_directory('.', 'signup.html')
    return root_page()

@app.route('/dashboard')
def dashboard_page():
    if os.path.exists('dashboard.html'):
        return send_from_directory('.', 'dashboard.html')
    return root_page()

@app.route('/login.html')
def login_html():
    return root_page()

@app.route('/signup.html')
def signup_html():
    return root_page()

@app.route('/dashboard.html')
def dashboard_html():
    return dashboard_page()
@app.route('/api/options')
def options():
    if df is None:
        return jsonify({
            'categories': [],
            'regions': [],
            'weather': [],
            'seasonality': []
        })

    return jsonify({
        'categories': sorted(df['Category'].dropna().unique().tolist()) if 'Category' in df.columns else [],
        'regions': sorted(df['Region'].dropna().unique().tolist()) if 'Region' in df.columns else [],
        'weather': sorted(df['Weather Condition'].dropna().unique().tolist()) if 'Weather Condition' in df.columns else [],
        'seasonality': sorted(df['Seasonality'].dropna().unique().tolist()) if 'Seasonality' in df.columns else []
    })


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "trained": trained})


# ===================== PREDICT =====================
@app.route("/api/predict", methods=["POST"])
def predict():
    global trained, model

    try:
        print("📥 Predict request")

        if df is None:
            load_data()

        if not trained or model is None:
            print("⚡ Training model...")
            preprocess()

        if not trained or model is None:
            return jsonify({"error": "Model not trained"}), 500

        data = request.get_json()
        if not data:
            return jsonify({"error": "No input"}), 400

        features = prepare_input(data)
        prediction = model.predict(features)[0]

        return jsonify({
            "success": True,
            "predicted_demand": float(prediction),
            "confidence_level": 90,
            "recommended_stock": float(prediction * 1.2),
            "estimated_cost": float(prediction * 10),

            "monthly_forecast": [
                {
                    "month": i,
                    "forecasted_demand": float(prediction * (1 + i*0.02)),
                    "lower_bound": float(prediction * 0.8),
                    "upper_bound": float(prediction * 1.2),
                    "recommended_action": "Maintain Stock"
                } for i in range(1, 7)
            ],

            "recommendations": [
                {"icon": "📊", "message": "Normal demand level"}
            ]
        })

    except Exception as e:
        print("❌ PREDICT ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


# ===================== DATASET =====================
@app.route("/api/dataset-info")
def dataset_info():
    if df is None:
        return jsonify({"error": "Dataset not loaded"}), 500
    resp = {
        "total_records": len(df),
        "stores": df["Store ID"].unique().tolist() if "Store ID" in df.columns else [],
        "products": df["Product ID"].unique().tolist() if "Product ID" in df.columns else [],
        "categories": df["Category"].unique().tolist() if "Category" in df.columns else [],
        "regions": df["Region"].unique().tolist() if "Region" in df.columns else [],
        "date_range": {
            "start": str(df["Date"].min()) if "Date" in df.columns else None,
            "end": str(df["Date"].max()) if "Date" in df.columns else None
        }
    }

    return jsonify(resp)


# ===================== ANALYTICS =====================
@app.route("/api/analytics")
def analytics():
    if df is None:
        return jsonify({"error": "Dataset not loaded"}), 500

    return jsonify({
        "total_records": len(df)
    })


# ===================== MODEL INFO =====================
@app.route("/api/model-info")
def model_info():
    return jsonify({
        "total_features": len(feature_columns),
        "model": "Random Forest"
    })


# ===================== SAMPLE DATA =====================
@app.route("/api/sample-data")
def sample_data():
    try:
        n = int(request.args.get("n", 5))

        if df is None:
            return jsonify({"error": "Dataset not loaded"}), 500

        return jsonify({
            "data": df.head(n).to_dict(orient="records")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===================== RECOMMEND =====================
@app.route("/api/recommend", methods=["POST"])
def recommend():
    try:
        return jsonify({
            "success": True,
            "top_products": [
                {"Category": "Groceries", "Units Sold": 120},
                {"Category": "Electronics", "Units Sold": 80}
            ],
            "bundles": [
                {"antecedents": ["Milk"], "consequents": ["Bread"]}
            ],
            "cluster": "Medium Demand Store",
            "model_comparison": {
                "random_forest": 4.9,
                "neural_network": 4.7
            },
            "reasons": [
                "High regional demand",
                "Seasonal trend"
            ],
            "actions": [
                "Increase stock",
                "Run promotions"
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/history")
def history():

    return jsonify([
        {
            "id":1,
            "category":"Groceries",
            "region":"North",
            "predicted_demand":120,
            "alert":"Restock Required"
        }
    ])

# ===================== LOAD ON START =====================
print('Initializing: loading dataset and preprocessing')
try:
    load_data()
    preprocess()
except Exception as e:
    print('Startup load/preprocess error:', repr(e))


# ===================== RUN =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)