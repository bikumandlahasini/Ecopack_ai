def sustainability_score(bio, recycle, co2, cost):
    """Returns 0–100 score. Higher = more sustainable."""
    s = bio * 30 + (recycle / 100.0) * 25 + max(0, 25 - co2 * 10) + max(0, 20 - cost * 2)
    return round(min(max(s, 0), 100), 2)


def rank_materials(materials, product_weight, fragility):
    frag_w = {"Low": 0.8, "Medium": 1.0, "High": 1.3}.get(fragility, 1.0)
    scored = []
    for m in materials:
        cap_ok = 1.0 if m["weight_capacity"] >= product_weight else 0.5
        sus    = sustainability_score(m["biodegradability_score"],
                                      m["recyclability_percentage"],
                                      m["co2_emission_score"],
                                      m["cost_per_unit"])
        strength_bonus = (m["strength_score"] / 100.0) * frag_w * 10
        scored.append({**m,
                       "sustainability_score": sus,
                       "composite_score": round(sus + strength_bonus * cap_ok, 2)})
    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored
