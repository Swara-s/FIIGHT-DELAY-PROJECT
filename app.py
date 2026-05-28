"""Main Flask application for flight delay prediction system."""

from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash

from backend.config import Config
from backend.database import get_connection, init_db, now_iso
from backend.ml import load_or_train_models, train_models, predict_delay


app = Flask(__name__)
app.config.from_object(Config)

init_db()
model_bundle = load_or_train_models()


def login_required(view_func):
    """Protect routes that require authentication."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


@app.context_processor
def inject_user_context():
    """Inject auth state into all templates."""
    return {
        "is_authenticated": "user_id" in session,
        "current_user_name": session.get("user_name"),
        "current_user_role": session.get("role"),
    }


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not full_name or not email or len(password) < 6:
            flash("Enter valid details. Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                flash("Email already registered. Please login.", "warning")
                return redirect(url_for("login"))

            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()["count"]
            role = "admin" if user_count == 0 else "user"
            cursor.execute(
                """
                INSERT INTO users (full_name, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (full_name, email, generate_password_hash(password), role, now_iso()),
            )
            conn.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["user_name"] = user["full_name"]
        session["role"] = user["role"]
        flash("Welcome back!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("home"))


@app.route("/predict", methods=["GET"])
@login_required
def predict_page():
    return render_template("predict.html")


@app.route("/predict", methods=["POST"])
@login_required
def predict_submit():
    global model_bundle
    try:
        payload = {
            "Airline": request.form.get("airline", "").strip(),
            "Airport": request.form.get("airport", "").strip(),
            "Weather_Condition": request.form.get("weather_condition", "").strip(),
            "Departure_Hour": int(request.form.get("departure_hour", 0)),
            "Arrival_Hour": int(request.form.get("arrival_hour", 0)),
            "Flight_Distance_KM": float(request.form.get("flight_distance_km", 0)),
            "Day_Of_Week": int(request.form.get("day_of_week", 1)),
        }
        flight_number = request.form.get("flight_number", "").strip().upper()

        required_values = [payload["Airline"], payload["Airport"], payload["Weather_Condition"], flight_number]
        if any(not item for item in required_values):
            raise ValueError("Please fill all required fields.")
        if not (0 <= payload["Departure_Hour"] <= 23 and 0 <= payload["Arrival_Hour"] <= 23):
            raise ValueError("Hour must be between 0 and 23.")
        if payload["Flight_Distance_KM"] <= 0:
            raise ValueError("Flight distance must be greater than 0.")
        if not (1 <= payload["Day_Of_Week"] <= 7):
            raise ValueError("Day of week must be between 1 and 7.")

        result = predict_delay(model_bundle, payload)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO prediction_history (
                    user_id, flight_number, airline, airport, weather_condition,
                    departure_time, arrival_time, delay_probability,
                    predicted_delay_minutes, delay_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    flight_number,
                    payload["Airline"],
                    payload["Airport"],
                    payload["Weather_Condition"],
                    f"{payload['Departure_Hour']:02d}:00",
                    f"{payload['Arrival_Hour']:02d}:00",
                    result["delay_probability"],
                    result["predicted_delay_minutes"],
                    result["delay_status"],
                    now_iso(),
                ),
            )
            conn.commit()

        session["last_prediction"] = {
            "flight_number": flight_number,
            "airline": payload["Airline"],
            "airport": payload["Airport"],
            **result,
        }
        return redirect(url_for("result"))

    except ValueError as validation_error:
        flash(str(validation_error), "danger")
        return redirect(url_for("predict_page"))
    except Exception:
        flash("Prediction failed due to an unexpected error. Try again.", "danger")
        return redirect(url_for("predict_page"))


@app.route("/result")
@login_required
def result():
    prediction = session.get("last_prediction")
    if not prediction:
        flash("Please submit a prediction first.", "warning")
        return redirect(url_for("predict_page"))
    return render_template("result.html", prediction=prediction)


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    global model_bundle
    try:
        payload = request.get_json(force=True)
        required = [
            "Airline",
            "Airport",
            "Weather_Condition",
            "Departure_Hour",
            "Arrival_Hour",
            "Flight_Distance_KM",
            "Day_Of_Week",
        ]
        missing = [field for field in required if field not in payload]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
        result = predict_delay(model_bundle, payload)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": f"Prediction error: {str(exc)}"}), 500


@app.route("/api/dashboard-data")
@login_required
def dashboard_data():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prediction_history WHERE user_id = ? ORDER BY id DESC", (session["user_id"],))
        rows = cursor.fetchall()

    total_predictions = len(rows)
    delayed_count = sum(1 for row in rows if row["delay_status"] == "Likely Delayed")
    on_time_count = total_predictions - delayed_count
    delay_percent = round((delayed_count / total_predictions) * 100, 2) if total_predictions else 0

    airline_map = {}
    weather_map = {}
    trend_map = {}
    for row in rows:
        airline_map[row["airline"]] = airline_map.get(row["airline"], 0) + 1
        weather_map[row["weather_condition"]] = weather_map.get(row["weather_condition"], 0) + 1
        day = row["created_at"][:10]
        trend_map[day] = trend_map.get(day, 0) + 1

    payload = {
        "stats": {
            "total_predictions": total_predictions,
            "delayed_count": delayed_count,
            "on_time_count": on_time_count,
            "delay_percent": delay_percent,
            "model": model_bundle.classifier_name,
            "regression_mae": model_bundle.metrics.get("regression_mae"),
        },
        "airline_analysis": airline_map,
        "weather_analysis": weather_map,
        "trend_analysis": dict(sorted(trend_map.items())),
    }
    return jsonify(payload)


@app.route("/api/retrain-model", methods=["POST"])
@login_required
def retrain_model():
    global model_bundle
    if session.get("role") != "admin":
        return jsonify({"error": "Only admin can retrain the model."}), 403
    model_bundle = train_models()
    return jsonify({"message": "Model retrained successfully.", "best_model": model_bundle.classifier_name})


if __name__ == "__main__":
    app.run(debug=True)
