import os, sys
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database.db import get_connection, get_cursor, init_db
from utils.model_loader import predict
from utils.recommender import rank_materials
from utils.validators import validate_signup, validate_login, validate_recommend

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ecopackai_secret_2024")

# ── INR conversion factor (1 USD ≈ 83 INR) ───────────────────────────────────
INR = 83.0

CATEGORIES = [
    "Electronics", "Food & Beverage", "Pharmaceuticals", "Cosmetics",
    "Industrial", "Automotive", "Apparel", "Furniture", "Toys",
    "Sports", "Medical", "Agriculture", "Chemical", "Retail", "Luxury",
]


# ── helpers ───────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    try:
        conn = get_connection()
        cur  = get_cursor(conn)
        cur.execute("SELECT id, name, email, phone FROM users WHERE id=%s", (uid,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return dict(row) if row else None
    except Exception:
        return None


# ── startup ───────────────────────────────────────────────────────────────────
def startup():
    try:
        init_db()
        print("✔ DB tables ready.")
    except Exception as e:
        print(f"✘ DB init error: {e}")

    mat_csv = os.path.join(BASE_DIR, "datasets", "materials.csv")
    if not os.path.exists(mat_csv):
        print("Dataset missing — generating...")
        try:
            from datasets.generate_datasets import generate_materials, save_csv, insert_materials
            df = generate_materials(2000)
            save_csv(df, "materials.csv")
            insert_materials(df)
            print("✔ Dataset generated.")
        except Exception as e:
            print(f"✘ Dataset error: {e}")

    cost_pkl = os.path.join(BASE_DIR, "models", "cost_model.pkl")
    co2_pkl  = os.path.join(BASE_DIR, "models", "co2_model.pkl")
    if not os.path.exists(cost_pkl) or not os.path.exists(co2_pkl):
        print("Models missing — training...")
        try:
            from models.train_models import train
            train()
            print("✔ Models trained.")
        except Exception as e:
            print(f"✘ Training error: {e}")
    else:
        try:
            predict("Paper", 50, 10.0, 0.8, 70.0)
            print("✔ Models loaded.")
        except Exception as e:
            print(f"✘ Model load error: {e}")


# ── landing ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("recommend"))
    return render_template("index.html")


# ── signup ────────────────────────────────────────────────────────────────────
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("user_id"):
        return redirect(url_for("recommend"))
    if request.method == "POST":
        data = request.form.to_dict()
        ok, msg = validate_signup(data)
        if not ok:
            flash(msg, "error")
            return render_template("signup.html", form=data)
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("SELECT id FROM users WHERE email=%s", (data["email"].strip(),))
            if cur.fetchone():
                flash("Email already registered. Please log in.", "error")
                cur.close(); conn.close()
                return render_template("signup.html", form=data)
            pwd_hash = generate_password_hash(data["password"])
            cur.execute(
                "INSERT INTO users (name,email,phone,password_hash) VALUES (%s,%s,%s,%s) RETURNING id",
                (data["name"].strip(), data["email"].strip(),
                 data["phone"].strip(), pwd_hash)
            )
            uid = cur.fetchone()[0]
            conn.commit(); cur.close(); conn.close()
            session["user_id"]   = uid
            session["user_name"] = data["name"].strip()
            flash("Account created! Welcome to EcoPackAI 🌿", "success")
            return redirect(url_for("recommend"))
        except Exception as e:
            flash(f"Registration failed: {e}", "error")
            return render_template("signup.html", form=data)
    return render_template("signup.html", form={})


# ── login ─────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("recommend"))
    if request.method == "POST":
        data = request.form.to_dict()
        ok, msg = validate_login(data)
        if not ok:
            flash(msg, "error")
            return render_template("login.html", form=data)
        try:
            conn = get_connection()
            cur  = get_cursor(conn)
            cur.execute("SELECT * FROM users WHERE email=%s", (data["email"].strip(),))
            user = cur.fetchone()
            cur.close(); conn.close()
            if not user or not check_password_hash(user["password_hash"], data["password"]):
                flash("Invalid email or password.", "error")
                return render_template("login.html", form=data)
            session["user_id"]   = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("recommend"))
        except Exception as e:
            flash(f"Login failed: {e}", "error")
            return render_template("login.html", form=data)
    return render_template("login.html", form={})


# ── logout ────────────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


# ── recommend ─────────────────────────────────────────────────────────────────
@app.route("/recommend", methods=["GET", "POST"])
@login_required
def recommend():
    user    = current_user()
    result  = None
    form    = {}
    error   = None

    if request.method == "POST":
        form = request.form.to_dict()
        ok, msg = validate_recommend(form)
        if not ok:
            error = msg
        else:
            try:
                weight   = float(form["product_weight"])
                fragility = form["fragility"]
                bio_inp  = float(form["biodegradability_score"])
                rec_inp  = float(form["recyclability_percent"])
                co2_inp  = float(form["co2_emission_score"])

                # Fetch materials from DB
                conn = get_connection()
                cur  = get_cursor(conn)
                cur.execute("SELECT * FROM materials LIMIT 500")
                materials = [dict(r) for r in cur.fetchall()]
                cur.close(); conn.close()

                if not materials:
                    error = "No materials in database. Run generate_datasets.py first."
                else:
                    ranked = rank_materials(materials, weight, fragility)
                    top3   = ranked[:3]

                    # ML predictions for top material
                    top = top3[0]
                    pred_cost_usd, pred_co2 = predict(
                        top["type"], top["strength_score"], top["weight_capacity"],
                        top["biodegradability_score"], top["recyclability_percentage"]
                    )
                    pred_cost_inr = round(pred_cost_usd * INR, 2)

                    result = {
                        "top3": top3,
                        "predicted_cost_inr": pred_cost_inr,
                        "predicted_co2": pred_co2,
                        "sustainability_score": top["sustainability_score"],
                    }

                    # Save to history
                    try:
                        conn = get_connection()
                        cur  = conn.cursor()
                        cur.execute("""
                            INSERT INTO history
                                (user_id,product_category,product_weight,fragility,
                                 shipping_distance,durability_score,biodegradability_score,
                                 recyclability_percent,co2_emission_score,
                                 rec_material_1,rec_material_2,rec_material_3,
                                 predicted_cost,sustainability_score)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """, (
                            session["user_id"],
                            form["product_category"], weight, fragility,
                            float(form["shipping_distance"]),
                            float(form["durability_score"]),
                            bio_inp, rec_inp, co2_inp,
                            top3[0]["material_name"],
                            top3[1]["material_name"] if len(top3) > 1 else None,
                            top3[2]["material_name"] if len(top3) > 2 else None,
                            pred_cost_inr, top["sustainability_score"]
                        ))
                        conn.commit(); cur.close(); conn.close()
                    except Exception as e:
                        print(f"History save error: {e}")

            except Exception as e:
                error = f"Recommendation failed: {e}"

    return render_template("recommend.html",
                           user=user, categories=CATEGORIES,
                           form=form, result=result, error=error)


# ── history ───────────────────────────────────────────────────────────────────
@app.route("/history")
@login_required
def history():
    user  = current_user()
    rows  = []
    try:
        conn = get_connection()
        cur  = get_cursor(conn)
        cur.execute("""
            SELECT * FROM history
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT 50
        """, (session["user_id"],))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()
    except Exception as e:
        flash(f"Could not load history: {e}", "error")
    return render_template("history.html", user=user, rows=rows)


# ── profile ───────────────────────────────────────────────────────────────────
@app.route("/profile")
@login_required
def profile():
    user = current_user()
    count = 0
    try:
        conn = get_connection()
        cur  = get_cursor(conn)
        cur.execute("SELECT COUNT(*) AS cnt FROM history WHERE user_id=%s",
                    (session["user_id"],))
        count = cur.fetchone()["cnt"]
        cur.close(); conn.close()
    except Exception:
        pass
    return render_template("profile.html", user=user, rec_count=count)


# ── run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    startup()
    app.run(debug=True, port=5000)
