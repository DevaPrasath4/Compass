import datetime
import os

from database import db, next_id, hash_password


def seed_demo_data():
    users = db["users"]
    if users.find_one({"email": "admin@compass.local"}) is None:
        admin_id = next_id("users")
        users.insert_one({
            "_id": admin_id,
            "id": admin_id,
            "name": "Compass Admin",
            "email": "admin@compass.local",
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "streak_count": 0,
            "last_active_date": None,
        })

    if users.find_one({"email": "student1@compass.local"}) is None:
        student1 = next_id("users")
        users.insert_one({
            "_id": student1,
            "id": student1,
            "name": "Aisha Rao",
            "email": "student1@compass.local",
            "password_hash": hash_password("student123"),
            "role": "student",
            "streak_count": 0,
            "last_active_date": None,
        })

    if users.find_one({"email": "student2@compass.local"}) is None:
        student2 = next_id("users")
        users.insert_one({
            "_id": student2,
            "id": student2,
            "name": "Rohit Nair",
            "email": "student2@compass.local",
            "password_hash": hash_password("student123"),
            "role": "student",
            "streak_count": 0,
            "last_active_date": None,
        })

    complaints = db["complaints"]
    if complaints.find_one({}) is None:
        now = datetime.datetime.utcnow()
        rows = [
            ("Wifi is down in Block A and students cannot connect", "Block A", "wifi", "student1@compass.local", "submitted"),
            ("Heavy rain caused flooding in the Hostel 2 corridor", "Hostel 2", "plumbing", "student2@compass.local", "resolved"),
            ("Power outage in the library reading room", "Library", "electrical", "student1@compass.local", "in_progress"),
            ("Broken furniture in Boys Hostel room 204", "Boys Hostel", "hostel", "student2@compass.local", "submitted"),
            ("Security gate is unmanned after 9 pm", "Security Gate", "safety", "student1@compass.local", "submitted"),
        ]
        for idx, (description, location, category, email, status) in enumerate(rows):
            complaint_id = next_id("complaints")
            complaints.insert_one({
                "_id": complaint_id,
                "id": complaint_id,
                "student_id": 2 if idx % 2 else 3,
                "anonymous": False,
                "description": description,
                "location": location,
                "category": category,
                "department": {
                    "wifi": "IT Team",
                    "plumbing": "Maintenance Team",
                    "electrical": "Electrical Team",
                    "hostel": "Hostel Team",
                    "safety": "Safety Team",
                }.get(category, "Facilities Team"),
                "urgency": 0.6 + idx * 0.1,
                "frequency": 1,
                "days_open": idx + 1,
                "status": status,
                "draft_message": None,
                "admin_approved": status == "resolved",
                "created_at": now - datetime.timedelta(days=idx * 4),
                "updated_at": now,
                "resolved_at": now - datetime.timedelta(days=1) if status == "resolved" else None,
                "priority_score": 35 + idx * 10,
            })


if __name__ == "__main__":
    seed_demo_data()
    print("Demo data seeded.")
