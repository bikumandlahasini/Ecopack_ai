import psycopg2
import psycopg2.extras
import os
import time
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "eco_pack_ai"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def get_connection(retries=5, delay=2):
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            return conn
        except psycopg2.OperationalError as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise RuntimeError(f"DB connection failed: {e}")


def get_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            phone VARCHAR(20),
            password_hash VARCHAR(256) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS materials (
            material_id SERIAL PRIMARY KEY,
            material_name VARCHAR(120) UNIQUE NOT NULL,
            type VARCHAR(50),
            strength_score INTEGER,
            weight_capacity FLOAT,
            cost_per_unit FLOAT,
            biodegradability_score FLOAT,
            co2_emission_score FLOAT,
            recyclability_percentage FLOAT
        );

        CREATE TABLE IF NOT EXISTS history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            product_category VARCHAR(80),
            product_weight FLOAT,
            fragility VARCHAR(20),
            shipping_distance FLOAT,
            durability_score FLOAT,
            biodegradability_score FLOAT,
            recyclability_percent FLOAT,
            co2_emission_score FLOAT,
            rec_material_1 VARCHAR(120),
            rec_material_2 VARCHAR(120),
            rec_material_3 VARCHAR(120),
            predicted_cost FLOAT,
            sustainability_score FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
