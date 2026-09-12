from __future__ import annotations

import os
from typing import Optional

try:
    from transformers import pipeline
except Exception:
    pipeline = None

CAMPUS_LABELS = [
    "flooding",
    "electrical damage",
    "broken furniture",
    "wifi equipment",
    "unsafe area",
    "water leak",
    "cleaning issue",
    "general maintenance",
]


def classify_photo(photo_path: str) -> Optional[str]:
    if not photo_path or not os.path.exists(photo_path):
        return None
    if pipeline is None:
        return None
    try:
        classifier = pipeline(
            "zero-shot-image-classification",
            model="openai/clip-vit-base-patch32",
            candidate_labels=CAMPUS_LABELS,
        )
        result = classifier(photo_path)
        if not result:
            return None
        best = result[0]
        label = str(best.get("label") or "").strip().lower()
        if label == "flooding":
            return "plumbing"
        if label == "electrical damage":
            return "electrical"
        if label == "broken furniture":
            return "hostel"
        if label == "wifi equipment":
            return "wifi"
        if label == "unsafe area":
            return "safety"
        if label == "water leak":
            return "plumbing"
        if label == "cleaning issue":
            return "hostel"
        if label == "general maintenance":
            return "other"
        return label or None
    except Exception:
        return None
