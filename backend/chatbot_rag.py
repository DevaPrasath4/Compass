import json
import re
from collections import Counter
from datetime import datetime

from ml_utils import _generate_with_gemini


_STATUS_TOKENS = {
    "resolved": {"resolved", "rectified", "fixed", "completed", "closed"},
    "in_progress": {"in progress", "progress", "working", "investigating", "under review"},
    "submitted": {"submitted", "new", "open", "pending"},
}


def _normalize_text(value: str) -> str:
    if value is None:
        return ""
    text = str(value).lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _location_tokens(value: str) -> set[str]:
    text = _normalize_text(value)
    if not text:
        return set()
    tokens = {
        token for token in text.split() if token and token not in {"a", "an", "the"}
    }
    return tokens


def _extract_location_hint(query: str) -> str:
    text = (query or "").strip()
    if not text:
        return ""
    q = _normalize_text(text)
    if not q:
        return ""

    patterns = [
        r"\bblock\s*[- ]?\s*[a-z]\b",
        r"\b[a-z]\s+block\b",
        r"\bmain building\b",
        r"\blibrary\b",
        r"\bcanteen\b",
        r"\bhostel\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, q, flags=re.IGNORECASE)
        if match:
            return match.group(0).strip()

    for token in ["Block A", "Block B", "Block C", "Block D", "Main Building", "Library", "Canteen", "Hostel"]:
        if token.lower() in text.lower():
            return token
    return ""


def _extract_block_code(value: str) -> str | None:
    text = _normalize_text(value or "")
    if not text:
        return None
    for pattern in [r"\bblock\s*[- ]?\s*([a-z])\b", r"\b([a-z])\s+block\b"]:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).lower()
    return None


def _location_similarity(query: str, location: str) -> float:
    q_tokens = _location_tokens(query)
    loc_tokens = _location_tokens(location)
    if not q_tokens or not loc_tokens:
        if not q_tokens and not loc_tokens:
            return 0.0
        return 0.0
    q_norm = _normalize_text(query)
    loc_norm = _normalize_text(location)
    if q_norm and q_norm in loc_norm:
        return 1.0
    if loc_norm and loc_norm in q_norm:
        return 1.0
    overlap = len(q_tokens & loc_tokens)
    if overlap:
        return min(1.0, overlap / max(len(q_tokens | loc_tokens), 1))
    raw_q = re.sub(r"[^a-z0-9]", "", q_norm)
    raw_loc = re.sub(r"[^a-z0-9]", "", loc_norm)
    if raw_q and raw_loc and (raw_q in raw_loc or raw_loc in raw_q):
        return 1.0
    return 0.0


def _status_intent(query: str) -> str | None:
    q = _normalize_text(query)
    if not q:
        return None
    lowered = q.lower()
    for intent, words in _STATUS_TOKENS.items():
        if any(word in lowered for word in words):
            return intent
    return None


def retrieve_relevant_complaints(query: str, complaints: list[dict], k: int = 8) -> list[dict]:
    if not complaints:
        return []

    q_text = (query or "").strip()
    query_norm = _normalize_text(q_text)
    status_intent = _status_intent(q_text)
    q_tokens = set(re.findall(r"[a-z0-9]+", query_norm))
    q_tokens = {token for token in q_tokens if token not in {"is", "are", "the", "a", "an", "what", "when", "where", "why", "how", "this", "that", "about", "status"}}
    location_hint = _extract_location_hint(q_text)
    location_hint_norm = _normalize_text(location_hint)

    if location_hint_norm:
        query_block = _extract_block_code(location_hint)
        explicit_matches = []
        for complaint in complaints:
            location = str(complaint.get("location") or "")
            complaint_block = _extract_block_code(location)
            if query_block and complaint_block and query_block == complaint_block:
                explicit_matches.append(complaint)
            elif not query_block and (
                _location_similarity(location_hint, location) > 0.35 or location_hint_norm in _normalize_text(location)
            ):
                explicit_matches.append(complaint)
        if not explicit_matches:
            return []
        complaints = explicit_matches

    scored: list[dict] = []
    for complaint in complaints:
        location = str(complaint.get("location") or "")
        description = str(complaint.get("description") or "")
        category = str(complaint.get("category") or "")
        status = str(complaint.get("status") or "").lower()
        text = f"{location} {description} {category}"
        doc_tokens = set(re.findall(r"[a-z0-9]+", _normalize_text(text)))
        score = 0.0

        loc_score = _location_similarity(q_text, location)
        if loc_score:
            score += 12 * loc_score

        overlap = len(q_tokens & doc_tokens)
        if overlap:
            score += overlap * 1.5

        if query_norm and query_norm in _normalize_text(text):
            score += 4

        if status_intent:
            if status_intent == "resolved" and status == "resolved":
                score += 2
            if status_intent == "in_progress" and status == "in_progress":
                score += 2
            if status_intent == "submitted" and status == "submitted":
                score += 2

        if location and location.lower() in q_text.lower():
            score += 5
        if any(word in q_text.lower() for word in ["rectified", "resolved", "fixed", "done"]):
            if status == "resolved":
                score += 3

        if location_hint_norm:
            if _location_similarity(location_hint, location) <= 0.35 and location_hint_norm not in _normalize_text(location):
                score = 0.0

        if score > 0:
            item = dict(complaint)
            item["_score"] = score
            scored.append(item)

    if not scored:
        return []

    top = sorted(scored, key=lambda item: item.get("_score", 0), reverse=True)
    return top[:k]


def _format_summary(c: dict) -> dict:
    created = c.get("created_at")
    resolved = c.get("resolved_at")
    return {
        "id": c.get("id"),
        "location": c.get("location"),
        "description": c.get("description"),
        "status": c.get("status"),
        "category": c.get("category"),
        "created_at": created.isoformat() if hasattr(created, "isoformat") else created,
        "resolved_at": resolved.isoformat() if hasattr(resolved, "isoformat") else resolved,
    }


def compute_status_facts(query: str, retrieved: list[dict]) -> dict:
    matches = retrieved or []
    total_matching = len(matches)
    resolved_count = sum(1 for item in matches if str(item.get("status") or "").lower() == "resolved")
    in_progress_count = sum(1 for item in matches if str(item.get("status") or "").lower() == "in_progress")
    open_count = sum(1 for item in matches if str(item.get("status") or "").lower() == "submitted")
    is_fully_resolved = total_matching > 0 and resolved_count == total_matching

    open_ages = [
        int(item.get("days_open") or 0)
        for item in matches
        if str(item.get("status") or "").lower() in {"submitted", "in_progress"}
    ]
    oldest_open_days = max(open_ages) if open_ages else 0

    resolution_dates = [
        item.get("resolved_at")
        for item in matches
        if str(item.get("status") or "").lower() == "resolved"
        and item.get("resolved_at") is not None
    ]
    max_resolution = None
    if resolution_dates:
        valid_dates = []
        for value in resolution_dates:
            if hasattr(value, "isoformat"):
                valid_dates.append(value)
            elif isinstance(value, str):
                try:
                    valid_dates.append(datetime.fromisoformat(value.replace("Z", "+00:00")))
                except ValueError:
                    pass
        if valid_dates:
            max_resolution = max(valid_dates)

    return {
        "query": query,
        "total_matching": total_matching,
        "resolved_count": resolved_count,
        "open_count": open_count,
        "in_progress_count": in_progress_count,
        "is_fully_resolved": is_fully_resolved,
        "oldest_open_days": oldest_open_days,
        "most_recent_resolution_date": max_resolution.isoformat() if hasattr(max_resolution, "isoformat") else max_resolution,
        "matched_complaints": [_format_summary(item) for item in matches],
    }


def _fallback_answer_for_facts(message: str, facts: dict) -> str:
    location_hint = _extract_location_hint(message) or "the matched reports"
    if facts["total_matching"] == 0:
        if location_hint and location_hint != "the matched reports":
            return f"I can't answer this. No complaint data was found for {location_hint}."
        return "I can't answer this."

    if facts["is_fully_resolved"]:
        if location_hint and location_hint != "the matched reports":
            return f"All {facts['total_matching']} reports for {location_hint} are resolved — {location_hint} is rectified."
        return f"All {facts['total_matching']} matched reports are resolved — the issue is fully rectified."

    if facts["open_count"] + facts["in_progress_count"] > 0:
        total_open = facts["open_count"] + facts["in_progress_count"]
        if location_hint and location_hint != "the matched reports":
            return (
                f"{location_hint} has {total_open} open reports and {facts['resolved_count']} resolved out of "
                f"{facts['total_matching']} total — it is not fully rectified yet."
            )
        return (
            f"There are {total_open} open reports and {facts['resolved_count']} resolved out of "
            f"{facts['total_matching']} total — it is not fully rectified yet."
        )

    return "The data does not confirm a full resolution yet."


def chat_answer(message: str, complaints: list[dict], history: list[dict] | None = None) -> dict:
    cleaned_message = (message or "").strip()
    if not cleaned_message:
        return {"answer": "Please ask a question about the complaint data.", "facts": {"total_matching": 0}, "sources": []}

    retrieved = retrieve_relevant_complaints(cleaned_message, complaints, k=8)
    facts = compute_status_facts(cleaned_message, retrieved)
    sources = [
        {
            "id": item.get("id"),
            "location": item.get("location"),
            "category": item.get("category"),
            "status": item.get("status"),
            "description": item.get("description"),
        }
        for item in retrieved[:5]
    ]

    prompt = (
        "You are a campus admin assistant. Use only the complaint data in the prompt. "
        "Do not invent status or facts. If nothing matches, say so clearly. "
        "Never claim an issue is resolved unless the data confirms it.\n\n"
        f"Conversation history:\n{json.dumps(history or [], ensure_ascii=False)}\n\n"
        f"Computed facts:\n{json.dumps(facts, default=str, ensure_ascii=False)}\n\n"
        f"Matched complaints:\n{json.dumps([_format_summary(item) for item in retrieved[:8]], default=str, ensure_ascii=False)}\n\n"
        f"User question: {cleaned_message}"
    )

    ai_text = _generate_with_gemini(prompt)
    answer = ai_text.strip() if ai_text else _fallback_answer_for_facts(cleaned_message, facts)

    return {"answer": answer, "facts": facts, "sources": sources}
