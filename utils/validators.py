import re


def validate_signup(data):
    name  = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    pwd   = data.get("password", "")
    if not name:
        return False, "Name is required."
    if not email or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return False, "Valid email is required."
    if not phone or not re.match(r"^\+?[\d\s\-]{7,15}$", phone):
        return False, "Valid phone number is required."
    if len(pwd) < 6:
        return False, "Password must be at least 6 characters."
    return True, ""


def validate_login(data):
    email = data.get("email", "").strip()
    pwd   = data.get("password", "")
    if not email:
        return False, "Email is required."
    if not pwd:
        return False, "Password is required."
    return True, ""


def validate_recommend(data):
    required = ["product_category", "product_weight", "fragility",
                "shipping_distance", "durability_score",
                "biodegradability_score", "recyclability_percent",
                "co2_emission_score"]
    for f in required:
        if f not in data or str(data[f]).strip() == "":
            return False, f"Missing field: {f}"
    try:
        if float(data["product_weight"]) <= 0:
            return False, "Product weight must be positive."
        if float(data["shipping_distance"]) < 0:
            return False, "Shipping distance cannot be negative."
        if not (0 <= float(data["durability_score"]) <= 100):
            return False, "Durability score must be 0–100."
        if not (0 <= float(data["biodegradability_score"]) <= 1):
            return False, "Biodegradability score must be 0–1."
        if not (0 <= float(data["recyclability_percent"]) <= 100):
            return False, "Recyclability must be 0–100."
        if float(data["co2_emission_score"]) < 0:
            return False, "CO₂ score cannot be negative."
    except (ValueError, TypeError):
        return False, "All numeric fields must be valid numbers."
    return True, ""
