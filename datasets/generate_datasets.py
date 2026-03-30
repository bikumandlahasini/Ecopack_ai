import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import random
import numpy as np
import pandas as pd
from database.db import get_connection, init_db

random.seed(42)
np.random.seed(42)

ECO_MATERIALS = [
    ("Corrugated Board",     "Paper",      0.85, 0.30, 0.5),
    ("Recycled Kraft Paper", "Paper",      0.80, 0.28, 0.4),
    ("Molded Pulp",          "Paper",      0.82, 0.25, 0.45),
    ("Bagasse",              "Paper",      0.88, 0.22, 0.55),
    ("Newsprint Wrap",       "Paper",      0.75, 0.20, 0.35),
    ("PLA Bioplastic",       "Bioplastic", 0.90, 0.40, 1.8),
    ("Corn Starch Foam",     "Bioplastic", 0.85, 0.35, 1.6),
    ("Cassava Bioplastic",   "Bioplastic", 0.87, 0.38, 1.7),
    ("PHA Bioplastic",       "Bioplastic", 0.92, 0.42, 2.0),
    ("Wheat Starch Film",    "Bioplastic", 0.83, 0.33, 1.5),
    ("Bamboo Fiber",         "Composite",  0.30, 1.20, 4.0),
    ("Mushroom Packaging",   "Composite",  0.88, 0.50, 3.5),
    ("Hemp Composite",       "Composite",  0.35, 1.10, 3.8),
    ("Seaweed Wrap",         "Composite",  0.90, 0.45, 3.2),
    ("Coconut Husk Board",   "Composite",  0.32, 1.00, 3.6),
    ("Recycled Glass",       "Glass",      0.20, 0.80, 2.0),
    ("Borosilicate Glass",   "Glass",      0.18, 0.85, 2.2),
    ("Soda Lime Glass",      "Glass",      0.22, 0.75, 1.9),
    ("Recycled Aluminum",    "Metal",      0.10, 1.50, 3.5),
    ("Tin Plate Steel",      "Metal",      0.08, 1.60, 3.8),
    ("Stainless Steel",      "Metal",      0.12, 1.55, 4.0),
]

VARIANTS = ["Standard", "Premium", "Lite", "Pro", "Eco", "Ultra",
            "Heavy Duty", "Slim", "Compact", "Industrial"]


def compute_sustainability(bio, recycle, co2):
    return round(bio * 0.4 + (recycle / 100.0) * 0.4 + max(0, 1 - co2 / 3.0) * 0.2, 4)


def generate_materials(n=5000):
    rows = []
    seen = set()
    while len(rows) < n:
        base_name, mat_type, bio_base, co2_base, cost_base = random.choice(ECO_MATERIALS)
        variant = random.choice(VARIANTS)
        name = f"{base_name} {variant}"
        if name in seen:
            continue
        seen.add(name)
        strength  = random.randint(20, 100)
        wt_cap    = round(random.uniform(0.5, 50.0), 2)
        cost      = round(cost_base * random.uniform(0.7, 1.8) + strength * 0.02, 4)
        bio       = round(min(1.0, bio_base + random.uniform(-0.08, 0.08)), 4)
        co2       = round(co2_base * random.uniform(0.6, 1.6) + wt_cap * 0.01, 4)
        recycle   = round(random.uniform(10, 95), 2)
        sus       = compute_sustainability(bio, recycle, co2)
        rows.append(dict(
            material_name=name, type=mat_type,
            strength_score=strength, weight_capacity=wt_cap,
            cost_per_unit=cost, biodegradability_score=bio,
            co2_emission_score=co2, recyclability_percentage=recycle,
            sustainability_score=sus
        ))
    return pd.DataFrame(rows)


def generate_products(n=3000):
    categories   = ["Electronics","Food & Beverage","Pharmaceuticals","Cosmetics",
                    "Industrial","Automotive","Apparel","Furniture","Toys",
                    "Sports","Medical","Agriculture","Chemical","Retail","Luxury"]
    fragilities  = ["Low", "Medium", "High"]
    mat_names    = [m[0] for m in ECO_MATERIALS]
    rows = []
    for _ in range(n):
        cat      = random.choice(categories)
        weight   = round(random.uniform(0.1, 50.0), 2)
        frag     = random.choice(fragilities)
        dist     = round(random.uniform(10, 5000), 1)
        dur      = round(random.uniform(20, 100), 1)
        mat      = random.choice(mat_names)
        cost     = round(random.uniform(0.5, 20.0), 2)
        sus      = round(random.uniform(0.3, 1.0), 4)
        rows.append(dict(category=cat, weight=weight, fragility=frag,
                         shipping_distance=dist, durability_required=dur,
                         recommended_material=mat, estimated_cost=cost,
                         sustainability_score=sus))
    return pd.DataFrame(rows)


def save_csv(df, filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    df.to_csv(path, index=False)
    print(f"  Saved {len(df)} rows → {path}")


def insert_materials(df):
    if "sustainability_score" not in df.columns:
        df["sustainability_score"] = df.apply(
            lambda r: compute_sustainability(
                r.biodegradability_score, r.recyclability_percentage, r.co2_emission_score), axis=1)

    conn = get_connection()
    cur  = conn.cursor()
    upserted = 0
    for _, row in df.iterrows():
        try:
            cur.execute("""
                INSERT INTO materials
                    (material_name, type, strength_score, weight_capacity,
                     cost_per_unit, biodegradability_score, co2_emission_score,
                     recyclability_percentage, sustainability_score)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (material_name) DO UPDATE
                    SET sustainability_score = EXCLUDED.sustainability_score
            """, (row.material_name, row.type, int(row.strength_score),
                  row.weight_capacity, row.cost_per_unit,
                  row.biodegradability_score, row.co2_emission_score,
                  row.recyclability_percentage, row.sustainability_score))
            upserted += cur.rowcount
        except Exception as e:
            conn.rollback()
            print(f"  Skip '{row.material_name}': {e}")
    conn.commit()
    cur.close()
    conn.close()
    print(f"  Upserted {upserted} materials into DB")


if __name__ == "__main__":
    init_db()
    df_mat = generate_materials(5000)
    save_csv(df_mat, "materials.csv")
    insert_materials(df_mat)
    df_prod = generate_products(3000)
    save_csv(df_prod, "products.csv")
    print("Done.")
