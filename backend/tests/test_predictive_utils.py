from predictive_utils import predict_upcoming_issues


def test_predict_upcoming_issues_returns_scores():
    complaints = [
        {
            "category": "wifi",
            "location": "Block A",
            "created_at": __import__("datetime").datetime.utcnow(),
        },
        {
            "category": "wifi",
            "location": "Block A",
            "created_at": __import__("datetime").datetime.utcnow(),
        },
        {
            "category": "electrical",
            "location": "Library",
            "created_at": __import__("datetime").datetime.utcnow(),
        },
    ]
    result = predict_upcoming_issues(complaints, location="Block A", months_ahead=2, top_n=3)
    assert isinstance(result, list)
    assert len(result) >= 1
    assert all("risk_score" in item for item in result)
