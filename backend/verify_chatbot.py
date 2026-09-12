import sys
from datetime import datetime, timedelta

sys.path.insert(0, r'C:\Users\DEVA PRASATH\OneDrive\Desktop\compass\backend')

import main
from database import db

# reset in-memory data
try:
    db._collections = {}
except Exception:
    pass


def add_complaint(cid, desc, loc, status, created_days_ago=0, resolved_days_ago=None):
    created = datetime.utcnow() - timedelta(days=created_days_ago)
    resolved = None if resolved_days_ago is None else datetime.utcnow() - timedelta(days=resolved_days_ago)
    complaint = {
        '_id': cid,
        'id': cid,
        'student_id': 99,
        'anonymous': False,
        'description': desc,
        'location': loc,
        'category': 'electrical' if 'electrical' in desc.lower() else 'other',
        'department': 'Electrical Team',
        'urgency': 0.6,
        'frequency': 1,
        'days_open': 5,
        'status': status,
        'draft_message': None,
        'admin_approved': False,
        'created_at': created,
        'updated_at': created,
        'resolved_at': resolved,
        'priority_score': 45.0,
    }
    db['complaints'].insert_one(complaint)


add_complaint(1, 'Electrical wiring issue in Block A corridor', 'Block A', 'resolved', 12, 2)
add_complaint(2, 'Light fixture failure in A Block', 'A Block', 'submitted', 4)
add_complaint(3, 'Power outage near Block-A entrance', 'block-a', 'in_progress', 7)

block_a = main.chat_answer('Is Block A rectified?', [main.serialize_complaint(c) for c in db['complaints'].find()])
block_z = main.chat_answer('Is Block Z rectified?', [main.serialize_complaint(c) for c in db['complaints'].find()])

print('BLOCK_A=', block_a)
print('BLOCK_Z=', block_z)
print('GEMINI_KEY_PRESENT=', bool(main.GEMINI_API_KEY))
