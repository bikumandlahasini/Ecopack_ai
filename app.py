import os, sys, math, logging
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database.db import get_connection, get_cursor, init_db
from utils.model_loader import predict
from utils.recommender import rank_materials
from utils.validators import validate_signup, validate_login, validate_recommend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ecopackai_secret_2024")

INR = 83.0
ADMIN_USER = "admin"
ADMIN_PASS = "admin"

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


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin access required.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


def safe_float(value, name):
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid value for {name}")
    if math.isnan(v) or math.isinf(v):
        raise ValueError(f"Invalid value for {name}")
    return v


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
    except Exception as e:
        logger.exception("current_user error: %s", e)
        return None


# ── startup ───────────────────────────────────────────────────────────────────
def startup():
    try:
        init_db()
        print("✔ DB tables ready.")
    except Exception as e:
        print(f"✘ DB init error: {e}")
        return

    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE materials
            SET sustainability_score = ROUND(
                (biodegradability_score * 0.4
                + (recyclability_percentage / 100.0) * 0.4
                + GREATEST(0, 1 - co2_emission_score / 3.0) * 0.2)::numeric, 4)
            WHERE sustainability_score IS NULL
        """)
        fixed = cur.rowcount
        conn.commit(); cur.close(); conn.close()
        if fixed:
            print(f"✔ Fixed sustainability_score for {fixed} rows.")
    except Exception as e:
        print(f"✘ Sustainability fix error: {e}")

    mat_csv = os.path.join(BASE_DIR, "datasets", "materials.csv")
    try:
        import pandas as pd
        from datasets.generate_datasets import generate_materials, save_csv, insert_materials
        if not os.path.exists(mat_csv):
            df = generate_materials(5000)
            save_csv(df, "materials.csv")
        else:
            df = pd.read_csv(mat_csv)
        insert_materials(df)
        print("✔ Materials loaded.")
    except Exception as e:
        print(f"✘ Dataset error: {e}")

    cost_pkl = os.path.join(BASE_DIR, "models", "cost_model.pkl")
    co2_pkl  = os.path.join(BASE_DIR, "models", "co2_model.pkl")
    if not os.path.exists(cost_pkl) or not os.path.exists(co2_pkl):
        try:
            from models.train_models import train
            train()
            print("✔ Models trained.")
        except Exception as e:
            print(f"✘ Training error: {e}")
    else:
        try:
            predict("Bioplastic", 50, 10.0, 0.8, 70.0)
            print("✔ Models loaded.")
        except Exception as e:
            print(f"✘ Model load error: {e}")


# ── public pages ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
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
                flash("Email already registered.", "error")
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
            logger.exception("Signup error: %s", e)
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
            logger.exception("Login error: %s", e)
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
    user   = current_user()
    result = None
    form   = {}
    error  = None

    if request.method == "POST":
        form = request.form.to_dict()
        ok, msg = validate_recommend(form)
        if not ok:
            error = msg
        else:
            try:
                weight    = safe_float(form["product_weight"], "product_weight")
                fragility = form["fragility"]
                bio_inp   = safe_float(form["biodegradability_score"], "biodegradability_score")
                rec_inp   = safe_float(form["recyclability_percent"], "recyclability_percent")
                co2_inp   = safe_float(form["co2_emission_score"], "co2_emission_score")

                conn = get_connection()
                cur  = get_cursor(conn)
                cur.execute("SELECT * FROM materials LIMIT 500")
                materials = [dict(r) for r in cur.fetchall()]
                cur.close(); conn.close()

                if not materials:
                    error = "No materials in database."
                else:
                    ranked = rank_materials(materials, weight, fragility)
                    top3   = ranked[:3]
                    top    = top3[0]

                    pred_cost_usd, pred_co2 = predict(
                        top["type"], top["strength_score"], top["weight_capacity"],
                        top["biodegradability_score"], top["recyclability_percentage"]
                    )
                    pred_cost_inr = round(pred_cost_usd * INR, 2)
                    co2_reduction = round(max(0, (1 - pred_co2 / max(co2_inp, 0.01)) * 100), 1)

                    result = {
                        "top3": top3,
                        "predicted_cost_inr": pred_cost_inr,
                        "predicted_co2": pred_co2,
                        "sustainability_score": top["sustainability_score"],
                        "co2_reduction": co2_reduction,
                    }

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
                            safe_float(form["shipping_distance"], "shipping_distance"),
                            safe_float(form["durability_score"], "durability_score"),
                            bio_inp, rec_inp, co2_inp,
                            top3[0]["material_name"],
                            top3[1]["material_name"] if len(top3) > 1 else None,
                            top3[2]["material_name"] if len(top3) > 2 else None,
                            pred_cost_inr, top["sustainability_score"]
                        ))
                        conn.commit(); cur.close(); conn.close()
                    except Exception as e:
                        logger.exception("History save error: %s", e)

            except ValueError as e:
                error = str(e)
            except Exception as e:
                logger.exception("Recommendation error: %s", e)
                error = f"Recommendation failed: {e}"

    return render_template("recommend.html",
                           user=user, categories=CATEGORIES,
                           form=form, result=result, error=error)


# ── history ───────────────────────────────────────────────────────────────────
@app.route("/history")
@login_required
def history():
    user = current_user()
    rows = []
    try:
        conn = get_connection()
        cur  = get_cursor(conn)
        cur.execute("""
            SELECT * FROM history WHERE user_id=%s
            ORDER BY created_at DESC LIMIT 50
        """, (session["user_id"],))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()
    except Exception as e:
        logger.exception("History load error: %s", e)
        flash(f"Could not load history: {e}", "error")
    return render_template("history.html", user=user, rows=rows)


@app.route("/history/delete/<int:rec_id>", methods=["POST"])
@login_required
def delete_history(rec_id):
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("DELETE FROM history WHERE id=%s AND user_id=%s",
                    (rec_id, session["user_id"]))
        conn.commit(); cur.close(); conn.close()
        flash("Record deleted.", "success")
    except Exception as e:
        logger.exception("Delete history error: %s", e)
        flash("Could not delete record.", "error")
    return redirect(url_for("history"))


# ── profile ───────────────────────────────────────────────────────────────────
@app.route("/profile")
@login_required
def profile():
    user  = current_user()
    count = 0
    try:
        conn  = get_connection()
        cur   = get_cursor(conn)
        cur.execute("SELECT COUNT(*) AS cnt FROM history WHERE user_id=%s",
                    (session["user_id"],))
        count = cur.fetchone()["cnt"]
        cur.close(); conn.close()
    except Exception as e:
        logger.exception("Profile load error: %s", e)
    return render_template("profile.html", user=user, rec_count=count)


# ── admin login ───────────────────────────────────────────────────────────────
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        if u == ADMIN_USER and p == ADMIN_PASS:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


# ── admin dashboard ───────────────────────────────────────────────────────────
def _get_admin_stats():
    """Fetch all admin stats in one place — reused by dashboard and exports."""
    stats = {}
    conn = get_connection()
    cur  = get_cursor(conn)

    cur.execute("SELECT COUNT(*) AS cnt FROM users")
    stats["total_users"] = cur.fetchone()["cnt"]

    cur.execute("SELECT COUNT(*) AS cnt FROM history")
    stats["total_recs"] = cur.fetchone()["cnt"]

    cur.execute("SELECT AVG(co2_emission_score) AS avg FROM history")
    stats["avg_co2"] = round((cur.fetchone()["avg"] or 0), 2)

    cur.execute("SELECT AVG(sustainability_score) AS avg FROM history")
    stats["avg_sus"] = round((cur.fetchone()["avg"] or 0), 2)

    cur.execute("SELECT AVG(predicted_cost) AS avg FROM history")
    avg_eco_cost = cur.fetchone()["avg"] or 0
    BASELINE_COST_INR = 350.0
    stats["avg_cost_saving"] = round(max(0, BASELINE_COST_INR - avg_eco_cost), 2)
    stats["cost_saving_pct"] = round(max(0, (BASELINE_COST_INR - avg_eco_cost) / BASELINE_COST_INR * 100), 1)

    cur.execute("""
        SELECT AVG(co2_emission_score) AS avg_co2 FROM history
    """)
    avg_co2_val = cur.fetchone()["avg_co2"] or 0
    BASELINE_CO2 = 2.5
    stats["co2_reduction_pct"] = round(max(0, (BASELINE_CO2 - avg_co2_val) / BASELINE_CO2 * 100), 1)

    cur.execute("""
        SELECT rec_material_1 AS mat, COUNT(*) AS cnt
        FROM history WHERE rec_material_1 IS NOT NULL
        GROUP BY rec_material_1 ORDER BY cnt DESC LIMIT 5
    """)
    stats["top_materials"] = [dict(r) for r in cur.fetchall()]
    stats["top_material"] = stats["top_materials"][0]["mat"] if stats["top_materials"] else "—"

    cur.execute("""
        SELECT DATE(created_at) AS day, COUNT(*) AS cnt
        FROM history
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY day ORDER BY day
    """)
    stats["last7"] = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT DATE(created_at) AS day, AVG(predicted_cost) AS avg_cost
        FROM history
        WHERE created_at >= NOW() - INTERVAL '30 days'
        GROUP BY day ORDER BY day
    """)
    stats["cost_trend"] = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT DATE(created_at) AS day, AVG(co2_emission_score) AS avg_co2
        FROM history
        WHERE created_at >= NOW() - INTERVAL '30 days'
        GROUP BY day ORDER BY day
    """)
    stats["co2_trend"] = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT DATE(created_at) AS day, AVG(sustainability_score) AS avg_sus
        FROM history
        WHERE created_at >= NOW() - INTERVAL '30 days'
        GROUP BY day ORDER BY day
    """)
    stats["sus_trend"] = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT id, name, email, phone, created_at FROM users
        ORDER BY created_at DESC LIMIT 50
    """)
    stats["users"] = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT id, user_id, product_category, product_weight, fragility,
               rec_material_1, predicted_cost, sustainability_score, co2_emission_score, created_at
        FROM history ORDER BY created_at DESC LIMIT 200
    """)
    stats["history_rows"] = [dict(r) for r in cur.fetchall()]

    cur.close(); conn.close()
    return stats


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    stats = {}
    try:
        stats = _get_admin_stats()
    except Exception as e:
        logger.exception("Admin dashboard error: %s", e)
        flash(f"Dashboard error: {e}", "error")
    return render_template("admin_dashboard.html", stats=stats)


# ── export PDF ────────────────────────────────────────────────────────────────
@app.route("/admin/export/pdf")
@admin_required
def export_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.units import cm
    from io import BytesIO
    from datetime import datetime
    from flask import make_response

    try:
        stats = _get_admin_stats()
    except Exception as e:
        flash(f"PDF export error: {e}", "error")
        return redirect(url_for("admin_dashboard"))

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    GREEN  = colors.HexColor("#198754")
    BLACK  = colors.HexColor("#111111")

    title_style = ParagraphStyle("title", parent=styles["Title"],
                                 textColor=GREEN, fontSize=22, spaceAfter=4)
    h2_style    = ParagraphStyle("h2", parent=styles["Heading2"],
                                 textColor=BLACK, fontSize=13, spaceBefore=14, spaceAfter=6)
    body_style  = styles["Normal"]

    elements = []
    elements.append(Paragraph("🌿 EcoPackAI — Sustainability Report", title_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", body_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=GREEN, spaceAfter=12))

    # KPI Summary
    elements.append(Paragraph("Key Performance Indicators", h2_style))
    kpi_data = [
        ["Metric", "Value"],
        ["Total Users",            str(stats.get("total_users", 0))],
        ["Total Recommendations",  str(stats.get("total_recs", 0))],
        ["Avg Sustainability Score",str(stats.get("avg_sus", 0))],
        ["Avg CO₂ Score",          str(stats.get("avg_co2", 0))],
        ["CO₂ Reduction %",        f"{stats.get('co2_reduction_pct', 0)}%"],
        ["Avg Cost Saving (₹)",    f"₹{stats.get('avg_cost_saving', 0)}"],
        ["Cost Saving %",          f"{stats.get('cost_saving_pct', 0)}%"],
        ["Top Material",           stats.get("top_material", "—")],
    ]
    kpi_table = Table(kpi_data, colWidths=[9*cm, 7*cm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), GREEN),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f0fdf4")]),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.HexColor("#dee2e6")),
        ("PADDING",      (0,0), (-1,-1), 8),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 0.5*cm))

    # Top Materials
    elements.append(Paragraph("Top 5 Recommended Materials", h2_style))
    mat_data = [["#", "Material Name", "Times Recommended"]]
    for i, m in enumerate(stats.get("top_materials", []), 1):
        mat_data.append([str(i), m["mat"], str(m["cnt"])])
    if len(mat_data) > 1:
        mat_table = Table(mat_data, colWidths=[1.5*cm, 11*cm, 4*cm])
        mat_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0), GREEN),
            ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,-1), 10),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f0fdf4")]),
            ("GRID",         (0,0), (-1,-1), 0.5, colors.HexColor("#dee2e6")),
            ("PADDING",      (0,0), (-1,-1), 8),
        ]))
        elements.append(mat_table)

    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dee2e6")))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph("EcoPackAI — AI-Powered Eco Packaging Recommendation System", body_style))

    doc.build(elements)
    buf.seek(0)
    resp = make_response(buf.read())
    resp.headers["Content-Type"]        = "application/pdf"
    resp.headers["Content-Disposition"] = "attachment; filename=ecopackai_report.pdf"
    return resp


# ── export Excel ──────────────────────────────────────────────────────────────
@app.route("/admin/export/excel")
@admin_required
def export_excel():
    import pandas as pd
    from io import BytesIO
    from flask import make_response
    from datetime import datetime

    try:
        stats = _get_admin_stats()
    except Exception as e:
        flash(f"Excel export error: {e}", "error")
        return redirect(url_for("admin_dashboard"))

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:

        # Sheet 1 — KPI Summary
        kpi_df = pd.DataFrame([
            {"Metric": "Total Users",             "Value": stats.get("total_users", 0)},
            {"Metric": "Total Recommendations",   "Value": stats.get("total_recs", 0)},
            {"Metric": "Avg Sustainability Score", "Value": stats.get("avg_sus", 0)},
            {"Metric": "Avg CO2 Score",            "Value": stats.get("avg_co2", 0)},
            {"Metric": "CO2 Reduction %",          "Value": f"{stats.get('co2_reduction_pct',0)}%"},
            {"Metric": "Avg Cost Saving INR",      "Value": stats.get("avg_cost_saving", 0)},
            {"Metric": "Cost Saving %",            "Value": f"{stats.get('cost_saving_pct',0)}%"},
            {"Metric": "Top Material",             "Value": stats.get("top_material", "—")},
            {"Metric": "Report Generated",         "Value": datetime.now().strftime("%d %b %Y %H:%M")},
        ])
        kpi_df.to_excel(writer, sheet_name="KPI Summary", index=False)

        # Sheet 2 — Recommendation History
        if stats.get("history_rows"):
            hist_df = pd.DataFrame(stats["history_rows"])
            hist_df.to_excel(writer, sheet_name="Recommendation History", index=False)

        # Sheet 3 — Top Materials
        if stats.get("top_materials"):
            mat_df = pd.DataFrame(stats["top_materials"])
            mat_df.columns = ["Material Name", "Times Recommended"]
            mat_df.to_excel(writer, sheet_name="Top Materials", index=False)

        # Sheet 4 — Users
        if stats.get("users"):
            users_df = pd.DataFrame(stats["users"])[["id","name","email","phone","created_at"]]
            users_df.to_excel(writer, sheet_name="Users", index=False)

        # Sheet 5 — CO2 Trend
        if stats.get("co2_trend"):
            co2_df = pd.DataFrame(stats["co2_trend"])
            co2_df.to_excel(writer, sheet_name="CO2 Trend", index=False)

        # Sheet 6 — Cost Trend
        if stats.get("cost_trend"):
            cost_df = pd.DataFrame(stats["cost_trend"])
            cost_df.to_excel(writer, sheet_name="Cost Trend", index=False)

    buf.seek(0)
    resp = make_response(buf.read())
    resp.headers["Content-Type"]        = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    resp.headers["Content-Disposition"] = "attachment; filename=ecopackai_analytics.xlsx"
    return resp


# ── run ───────────────────────────────────────────────────────────────────────
startup()

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    host  = "127.0.0.1" if debug else "0.0.0.0"
    app.run(host=host, port=port, debug=debug)
