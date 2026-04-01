# 🌿 EcoPackAI — AI-Powered Eco Packaging Recommendation System

> Internship-level Flask + PostgreSQL + Machine Learning project with Business Intelligence dashboard, PDF/Excel export, and Render deployment.

---

## 🚀 Tech Stack

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Backend      | Python Flask                        |
| Database     | PostgreSQL + psycopg2               |
| ML Models    | Scikit-learn RandomForest           |
| Data         | Pandas, NumPy                       |
| Frontend     | Bootstrap 5, Chart.js               |
| Export       | ReportLab (PDF), openpyxl (Excel)   |
| Deployment   | Render (gunicorn)                   |
| Auth         | Werkzeug password hashing, sessions |

---

## 📋 Milestone Features

### Milestone 1 — Core System
- ✅ Flask app with PostgreSQL integration
- ✅ User signup, login, logout with hashed passwords
- ✅ Session management
- ✅ Packaging recommendation form (8 input fields)
- ✅ Top 3 material recommendations with scores

### Milestone 2 — Machine Learning
- ✅ RandomForest cost prediction model
- ✅ RandomForest CO₂ prediction model
- ✅ R² accuracy 0.85+, MAE, RMSE, cross-validation
- ✅ 5000-row materials dataset (20+ real eco materials)
- ✅ 3000-row products dataset
- ✅ Auto-train on first run

### Milestone 3 — User Features
- ✅ Recommendation history with delete
- ✅ User profile page
- ✅ CO₂ reduction % calculation
- ✅ Cost prediction in Indian Rupees (₹)
- ✅ Sustainability score display

### Milestone 4 — Admin & Analytics
- ✅ Admin login (admin/admin)
- ✅ Business Intelligence dashboard
- ✅ 6 KPI cards (users, recs, CO₂ reduction, cost savings, sustainability, top material)
- ✅ 5 analytics charts (bar, line, CO₂ trend, cost trend, sustainability trend)
- ✅ Users table
- ✅ Recent recommendations table

### Milestone 5 — Export & Reports
- ✅ PDF report export (ReportLab) — KPIs, top materials, branding
- ✅ Excel export (openpyxl) — 6 sheets: KPI, history, materials, users, CO₂ trend, cost trend

---

## 📁 Project Structure

```
eco_pack_ai/
├── app.py                    # Main Flask app, all routes
├── requirements.txt
├── .env
├── database/
│   └── db.py                 # DB connection, init_db()
├── datasets/
│   ├── generate_datasets.py  # 5000 materials, 3000 products
│   ├── materials.csv
│   └── products.csv
├── models/
│   ├── train_models.py       # RandomForest training
│   ├── cost_model.pkl
│   ├── co2_model.pkl
│   ├── label_encoder.pkl
│   └── metrics.json
├── utils/
│   ├── model_loader.py
│   ├── recommender.py
│   └── validators.py
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── signup.html
    ├── recommend.html
    ├── history.html
    ├── profile.html
    ├── admin_login.html
    └── admin_dashboard.html
```

---

## ⚙️ Local Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure .env
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/eco_pack_ai
SECRET_KEY=ecopackai_secret_2024
```

### 3. Create PostgreSQL database
```sql
CREATE DATABASE eco_pack_ai;
```

### 4. Generate dataset and train models
```bash
python datasets/generate_datasets.py
python models/train_models.py
```

### 5. Run the app
```bash
python app.py
```

Open: http://127.0.0.1:5000

> Tables are auto-created, materials are auto-loaded, models are auto-trained on first run.

---

## 🌐 Pages

| URL                  | Description                        |
|----------------------|------------------------------------|
| `/`                  | Home page with hero + features     |
| `/signup`            | Create account                     |
| `/login`             | Login                              |
| `/recommend`         | Get packaging recommendation       |
| `/history`           | Past recommendations + delete      |
| `/profile`           | User profile                       |
| `/admin`             | Admin login (admin/admin)          |
| `/admin/dashboard`   | Full BI dashboard + charts         |
| `/admin/export/pdf`  | Download PDF sustainability report |
| `/admin/export/excel`| Download Excel analytics report    |

---

## 🚀 Deploy on Render

```bash
# 1. Push to GitHub
git init
git add .
git commit -m "EcoPackAI v1.0"
git remote add origin https://github.com/YOUR_USERNAME/eco_pack_ai.git
git push -u origin main

# 2. On Render dashboard:
# - New Web Service → connect GitHub repo
# - Build command: pip install -r requirements.txt
# - Start command: gunicorn app:app
# - Add environment variables:
#     DATABASE_URL = (from Render PostgreSQL)
#     SECRET_KEY   = ecopackai_secret_2024
```

---

## 🔐 Admin Credentials
- Username: `admin`
- Password: `admin`

---

## 📸 Screenshots
> _(Add screenshots here after deployment)_
- [ ] Home page hero
- [ ] Recommendation form + results
- [ ] Admin dashboard with charts
- [ ] PDF export sample
- [ ] Excel export sample

---

## 🔮 Future Enhancements
- [ ] Email notifications for recommendations
- [ ] User password reset
- [ ] Material comparison tool
- [ ] API endpoints for mobile app
- [ ] Multi-language support
- [ ] Carbon credit calculator
- [ ] Supplier integration
- [ ] Real-time material pricing

---

## 📄 License
MIT — Free to use for educational and internship purposes.
