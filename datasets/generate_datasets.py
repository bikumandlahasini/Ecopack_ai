"""
Dataset generation + model training in one script.
Run: python datasets/generate_datasets.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import random
import numpy as np
import pandas as pd
from database.db import get_connection, init_db

random.seed(42)
np.random.seed(42)

MAT_TYPES   = ["Paper", "Glass", "Metal", "Bioplastic", "Composite"]
ADJECTIVES  = ["Ultra","Eco","Bio","Nano","Flex","Rigid","Lite","Heavy","Smart","Green",
                "Pure","Prime","Core","Dual","Tri","Micro","Macro","Hyper","Super","Mega",
                "Poly","Mono","Multi","Uni","Pro","Max","Mini","Soft","Hard","Thin",
                "Thick","Clear","Dark","Bright","Matte","Gloss","Rough","Smooth","Dense",
                "Porous","Sealed","Open","Rapid","Steady","Stable","Active","Passive"]
MAT_NOUNS   = ["Shield","Wrap","Board","Foam","Film","Liner","Coat","Layer","Pad","Sheet",
                "Mesh","Net","Tube","Box","Tray","Bag","Pouch","Sleeve","Cover","Guard",
                "Barrier","Panel","Block","Slab","Strip","Fiber","Weave","Cord","Band",
                "Ring","Disc","Plate","Frame","Shell","Core","Base","Cap","Lid","Seal"]
SUFFIXES    = ["X","Pro","Plus","Max","Lite","HD","V2","V3","S","M","L","XL",
               "Alpha","Beta","Gamma","Delta","Sigma","Prime","Elite","Ultra","Nano","Eco"]

TYPE_COST = {"Paper":0.5,"Glass":2.0,"Metal":3.5,"Bioplastic":1.8,"Composite":4.0}
TYPE_CO2  = {"Paper":0.3,"Glass":0.8,"Metal":1.5,"Bioplastic":0.4,"Composite":1.2}
TYPE_BIO  = {"Paper":0.85,"Glass":0.2,"Metal":0.1,"Bioplastic":0.9,"Composite":0.3}


def unique_material_names(n):
    names = set()
    while len(names) < n:
        names.add(f"{random.choice(ADJECTIVES)}-{random.choice(MAT_NOUNS)} "
                  f"{random.choice(MAT_TYPES)} {random.choice(SUFFIXES)}")
    return list(names)


def generate_materials(n=2000):
    names = unique_material_names(n)
    types = [random.choice(MAT_TYPES) for _ in range(n)]
    rows  = []
    for name, t in zip(names, types):
        strength = random.randint(20, 100)
        wt_cap   = round(random.uniform(0.5, 50.0), 2)
        cost     = round(TYPE_COST[t] * random.uniform(0.7, 1.8) + strength * 0.02, 4)
        bio      = round(min(1.0, TYPE_BIO[t] + random.uniform(-0.1, 0.1)), 4)
        co2      = round(TYPE_CO2[t] * random.uniform(0.6, 1.6) + wt_cap * 0.01, 4)
        recycle  = round(random.uniform(10, 95), 2)
        rows.append(dict(material_name=name, type=t, strength_score=strength,
                         weight_capacity=wt_cap, cost_per_unit=cost,
                         biodegradability_score=bio, co2_emission_score=co2,
                         recyclability_percentage=recycle))
    return pd.DataFrame(rows)


def save_csv(df, filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    df.to_csv(path, index=False)
    print(f"  Saved {len(df)} rows → {path}")


def insert_materials(df):
    conn = get_connection()
    cur  = conn.cursor()
    inserted = 0
    for _, row in df.iterrows():
        try:
            cur.execute("""
                INSERT INTO materials
                    (material_name,type,strength_score,weight_capacity,
                     cost_per_unit,biodegradability_score,co2_emission_score,
                     recyclability_percentage)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (material_name) DO NOTHING
            """, (row.material_name, row.type, int(row.strength_score),
                  row.weight_capacity, row.cost_per_unit,
                  row.biodegradability_score, row.co2_emission_score,
                  row.recyclability_percentage))
            inserted += cur.rowcount
        except Exception as e:
            conn.rollback()
            print(f"  Skip '{row.material_name}': {e}")
    conn.commit()
    cur.close()
    conn.close()
    print(f"  Inserted {inserted} materials into DB")


if __name__ == "__main__":
    print("Initialising DB tables...")
    init_db()
    print("Generating materials (2000)...")
    df = generate_materials(2000)
    save_csv(df, "materials.csv")
    insert_materials(df)
    print("Done.")
