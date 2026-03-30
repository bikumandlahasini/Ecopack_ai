# EcoPackAI — AI-Powered Eco Packaging Recommendation System

## Tech Stack
- Python Flask, PostgreSQL, psycopg2, dotenv
- Scikit-learn (RandomForest), Pandas, NumPy
- Bootstrap 5, Chart.js
- Render deployment ready

## Setup (Local)

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

### 4. Run the app
```bash
python app.py
```
Tables are auto-created, materials are auto-loaded, models are auto-trained on first run.

Open: http://127.0.0.1:5000

## Pages
| URL | Description |
|-----|-------------|
| `/` | Home page |
| `/signup` | Create account |
| `/login` | Login |
| `/recommend` | Get packaging recommendation |
| `/history` | Past recommendations |
| `/profile` | User profile |
| `/admin` | Admin login (admin/admin) |
| `/admin/dashboard` | Admin analytics dashboard |

## Deploy on Render
1. Push to GitHub
2. Create new Web Service on Render
3. Set environment variable: `DATABASE_URL` (from Render PostgreSQL)
4. Set `SECRET_KEY`
5. Start command: `gunicorn app:app`

## Admin Credentials
- Username: `admin`
- Password: `admin`
