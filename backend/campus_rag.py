"""Campus knowledge base used as a lightweight retrieval layer for complaint routing.
This acts as a simple RAG-style context store with records for important campus
locations, buildings, facilities, and service responsibilities.
"""

from __future__ import annotations

from rag.vector_store import semantic_retrieve

CAMPUS_KB = [
    {
        "name": "Block A",
        "type": "academic-block",
        "details": "Main academic block with classrooms, faculty rooms, and laboratory corridors. Common complaints include WiFi outages, electrical issues, and blocked pathways.",
        "keywords": ["block a", "block-a", "a block", "academic block", "classroom", "lab", "faculty", "wifi", "network"],
        "team": "IT Team",
    },
    {
        "name": "Block B",
        "type": "academic-block",
        "details": "Contains lecture halls and student support offices. Usually reports include strong WiFi demand, lighting faults, and cleaning requests.",
        "keywords": ["block b", "block-b", "b block", "lecture hall", "office", "support office", "wifi", "light"],
        "team": "IT Team",
    },
    {
        "name": "Block C",
        "type": "academic-block",
        "details": "Hosts the engineering and computing labs. Common requests include power issues, internet failures, and projector or wiring defects.",
        "keywords": ["block c", "block-c", "c block", "engineering", "computing", "lab", "projector", "power", "network"],
        "team": "Electrical Team",
    },
    {
        "name": "Block D",
        "type": "academic-block",
        "details": "Used for administration and student services. Frequent issues include access problems, lighting failures, and water supply disruptions.",
        "keywords": ["block d", "block-d", "d block", "admin", "office", "services", "security", "water", "light"],
        "team": "Facilities Team",
    },
    {
        "name": "Library",
        "type": "study-space",
        "details": "Student reading hall with study areas, printers, and digital access points. WiFi and lighting issues are common here.",
        "keywords": ["library", "reading hall", "study room", "printer", "wifi", "internet", "lights"],
        "team": "IT Team",
    },
    {
        "name": "Canteen",
        "type": "food-area",
        "details": "Main food court serving students and staff. Complaints often cover water supply, drainage, cleaning, and crowding issues.",
        "keywords": ["canteen", "food court", "mess", "food", "water", "drainage", "cleaning", "queue"],
        "team": "Maintenance Team",
    },
    {
        "name": "Hostel 1",
        "type": "residence",
        "details": "Boys hostel with shared washrooms, corridors, and room maintenance needs. Frequent complaints include water leakage, sanitation, and hostel cleanliness.",
        "keywords": ["hostel 1", "boys hostel", "room", "bathroom", "toilet", "water", "hostel"],
        "team": "Hostel Team",
    },
    {
        "name": "Hostel 2",
        "type": "residence",
        "details": "Girls hostel with room maintenance, water supply, and safety checks around common areas and entrances.",
        "keywords": ["hostel 2", "girls hostel", "room", "bathroom", "water", "safety", "hostel"],
        "team": "Hostel Team",
    },
    {
        "name": "Main Building",
        "type": "administrative",
        "details": "Administrative hub for admissions, accounts, and campus offices. Issues include access control, power interruptions, and maintenance.",
        "keywords": ["main building", "administration", "admissions", "accounts", "office", "access", "power"],
        "team": "Facilities Team",
    },
    {
        "name": "Sports Complex",
        "type": "recreational",
        "details": "Sports facilities and gym area. Complaints often involve lighting, water points, and maintenance of equipment.",
        "keywords": ["sports complex", "gym", "ground", "field", "water", "lights", "equipment"],
        "team": "Maintenance Team",
    },
    {
        "name": "Girls Hostel",
        "type": "residence",
        "details": "Residential space for female students with hostel support needs, sanitation checks, and safety monitoring.",
        "keywords": ["girls hostel", "female hostel", "hostel", "safety", "room", "water", "bathroom"],
        "team": "Hostel Team",
    },
    {
        "name": "Boys Hostel",
        "type": "residence",
        "details": "Residential block for male students with common services and routine facility maintenance routines.",
        "keywords": ["boys hostel", "male hostel", "hostel", "room", "bathroom", "water", "maintenance"],
        "team": "Hostel Team",
    },
    {
        "name": "Security Gate",
        "type": "safety-area",
        "details": "Main campus entrance checkpoint. Safety complaints include gate issues, poor lighting, lack of security staff, and entry control failures.",
        "keywords": ["gate", "security gate", "entrance", "access", "security", "guard", "light", "safety"],
        "team": "Safety Team",
    },
    {
        "name": "Auditorium",
        "type": "event-area",
        "details": "Large event venue with stage, AV equipment, and power needs. Complaints can involve lighting, sound, and network setups.",
        "keywords": ["auditorium", "hall", "event", "sound", "light", "projector", "network"],
        "team": "IT Team",
    },
    {
        "name": "Science Block",
        "type": "academic-block",
        "details": "Laboratory and practical learning area. Common issues include electrical faults, water supply breaks, and ventilation problems.",
        "keywords": ["science block", "science", "lab", "practical", "power", "water", "ventilation"],
        "team": "Electrical Team",
    },
]


def retrieve_campus_context(location: str, description: str = "") -> list[dict]:
    query = (location or "") + " " + (description or "")
    try:
        hits = semantic_retrieve(query, k=3, collection_name="campus_kb")
        if hits:
            results = []
            for hit in hits:
                payload = {"name": hit.get("name") or hit.get("text") or "Campus knowledge", "team": hit.get("team") or "Facilities Team"}
                payload.update({
                    "details": hit.get("details") or hit.get("text") or "Campus context",
                    "keywords": hit.get("keywords") or [],
                    "score": float(hit.get("score") or 0.0),
                })
                results.append(payload)
            return results
    except Exception:
        pass

    query_lower = query.lower()
    matches = []
    for item in CAMPUS_KB:
        score = 0
        if item["name"].lower() in query_lower:
            score += 5
        for keyword in item["keywords"]:
            if keyword in query_lower:
                score += 2
        if description and any(token in description.lower() for token in ["wifi", "internet", "router", "network", "water", "leak", "pipe", "power", "light", "fan", "safety", "security", "hostel"]):
            if any(token in description.lower() for token in ["wifi", "internet", "router", "network"]) and "IT Team" == item["team"]:
                score += 2
            if any(token in description.lower() for token in ["water", "leak", "pipe", "toilet", "drain"]) and "Maintenance Team" == item["team"]:
                score += 2
            if any(token in description.lower() for token in ["power", "light", "fan", "socket", "spark"]) and "Electrical Team" == item["team"]:
                score += 2
            if any(token in description.lower() for token in ["hostel", "room", "mess", "noise", "cleaning"]) and "Hostel Team" == item["team"]:
                score += 2
            if any(token in description.lower() for token in ["security", "safety", "gate", "fire", "exit"]) and "Safety Team" == item["team"]:
                score += 2
        if score:
            item_copy = dict(item)
            item_copy["score"] = score
            matches.append(item_copy)

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:3]
