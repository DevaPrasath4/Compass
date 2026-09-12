"""
Generates synthetic training data since no real historical complaint
dataset exists yet. Run once (train_models.py calls this automatically).
"""
import random
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

CATEGORY_TEMPLATES = {
    "wifi": [
        "wifi is not working in {loc}", "internet keeps disconnecting in {loc}",
        "no network connection in {loc} hostel room", "wifi router down at {loc}",
        "very slow internet speed near {loc}", "cannot connect to campus wifi in {loc}",
        "wifi signal is extremely weak in {loc}", "broadband connection lost in {loc} block",
    ],
    "plumbing": [
        "water leakage in {loc} bathroom", "tap is broken in {loc}",
        "no water supply in {loc} hostel", "pipe burst near {loc}",
        "washroom flooding in {loc}", "drainage blocked in {loc}",
        "toilet is not flushing in {loc}", "water is leaking from ceiling in {loc}",
    ],
    "electrical": [
        "power outage in {loc}", "fan not working in {loc} room",
        "light bulb fused in {loc}", "short circuit spark seen near {loc}",
        "switchboard sparking in {loc}", "socket not working in {loc}",
        "electricity fluctuation in {loc} block", "AC not cooling in {loc} hostel room",
    ],
    "hostel": [
        "mess food quality is poor in {loc}", "room cleaning not done in {loc}",
        "bed frame broken in {loc} hostel room", "pest infestation in {loc} hostel",
        "hostel gate locked too early at {loc}", "laundry service delayed in {loc}",
        "furniture damaged in {loc} room", "noise disturbance at night in {loc}",
    ],
    "safety": [
        "broken staircase railing near {loc}", "no security guard at {loc} gate at night",
        "fire extinguisher missing in {loc} block", "cctv not working near {loc}",
        "unsafe wiring exposed near {loc}", "dark unlit pathway near {loc} at night",
        "stray dogs causing issues near {loc}", "emergency exit blocked in {loc}",
    ],
    "other": [
        "parking space issue near {loc}", "notice board not updated in {loc}",
        "library book unavailable requested from {loc}", "canteen overcrowded near {loc}",
        "general maintenance request for {loc}", "signage missing near {loc}",
    ],
}

LOCATIONS = ["Block A", "Block B", "Block C", "Block D", "Hostel 1", "Hostel 2",
             "Main Building", "Library", "Canteen", "Sports Complex", "Girls Hostel", "Boys Hostel"]

URGENT_WORDS = ["fire", "spark", "sparking", "shock", "flooding", "burst", "unsafe",
                "emergency", "exposed wiring", "no security", "blocked exit"]


def make_category_dataset(n_per_class=120):
    rows = []
    for cat, templates in CATEGORY_TEMPLATES.items():
        for _ in range(n_per_class):
            t = random.choice(templates)
            loc = random.choice(LOCATIONS)
            rows.append({"text": t.format(loc=loc), "category": cat})
    df = pd.DataFrame(rows).sample(frac=1, random_state=42).reset_index(drop=True)
    return df


def urgency_score_from_text(text):
    score = 0.15
    for w in URGENT_WORDS:
        if w in text:
            score += 0.3
    return min(score + random.uniform(0, 0.15), 1.0)


def make_priority_dataset(n=1500):
    """
    Features: urgency (0-1, from text signal), frequency (how many similar
    complaints merged via dedup), days_open.
    Target: priority_score (0-100) generated from a weighted formula the
    RandomForest is trained to approximate, so feature_importances_ stay
    interpretable and explainable to the admin.
    """
    rows = []
    df_cat = make_category_dataset(n_per_class=max(1, n // 6))
    for _, r in df_cat.sample(n, replace=True, random_state=1).iterrows():
        urgency = urgency_score_from_text(r["text"])
        frequency = np.random.choice([1, 1, 1, 2, 2, 3, 4, 5, 8, 12],
                                      p=[0.35, 0.15, 0.1, 0.1, 0.08, 0.07, 0.06, 0.04, 0.03, 0.02])
        days_open = np.random.choice(range(0, 15))
        noise = np.random.normal(0, 4)
        priority = (
            urgency * 55
            + min(frequency, 10) * 3.2
            + min(days_open, 10) * 1.8
            + noise
        )
        priority = float(np.clip(priority, 0, 100))
        rows.append({
            "urgency": urgency,
            "frequency": frequency,
            "days_open": days_open,
            "priority_score": priority,
        })
    return pd.DataFrame(rows)
