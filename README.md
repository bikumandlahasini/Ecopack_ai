# EcoPackAI – Packaging Recommendation System

## Pages
- `/` — Landing page (Login / Sign Up)
- `/signup` — Create account
- `/login` — Sign in
- `/recommend` — Get packaging recommendation (main feature)
- `/history` — Past recommendations
- `/profile` — User profile

## Project Structure
```
eco_pack_ai/
├── app.py
├── .env                          ← Set your DB password here
├── requirements.txt
├── database/db.py                ← DB connection + table creation
├── datasets/generate_datasets.py ← Generate 2000 materials
├── models/
│   ├── train_models.py           ← Train RF + XGBoost
│   ├── cost_model.pkl            ← (auto-generated)
│   ├── co2_model.pkl             ← (auto-generated)
│   └── label_encoder.pkl         ← (auto-generated)
├── utils/
│   ├── model_loader.py
│   ├── recommender.py
│   └── validators.py
├── static/css/style.css
├── static/js/main.js
└── templates/
    ├── base.html
    ├── index.html
    ├── signup.html
    ├── login.html
    ├── recommend.html
    ├── history.html
    └── profile.html
```

## Setup Instructions

### 1. Install dependencies
```bash
cd eco_pack_ai
pip install -r requirements.txt
```

### 2. Configure PostgreSQL
Edit `.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=eco_pack_ai
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD
```

Create the database:
```sql
CREATE DATABASE eco_pack_ai;
```

### 3. Generate dataset + populate DB
```bash
python datasets/generate_datasets.py
```

### 4. Train ML models
```bash
python models/train_models.py
```

### 5. Run the app
```bash
python app.py
```
Open: http://localhost:5000

## Notes
- Costs shown in ₹ Indian Rupees (1 USD = 83 INR)
- Models auto-train on first run if .pkl files are missing
- DB tables auto-created on startup
- Second run is always safe (ON CONFLICT DO NOTHING)
