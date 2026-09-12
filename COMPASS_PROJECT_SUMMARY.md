# Compass — Campus Problem Intelligence Platform
**Hackathon Project Summary | Campusathon 2026 (PS5: Campus Problem Intelligence)**

---

## 1. Implemented Features (End-to-End)

### Student & Faculty Portal
- **Authentication**: JWT token registration and login ([auth.py](file:///c:/Users/Dharshan/Downloads/compass%20%282%29/compass/backend/auth.py)).
- **Complaint Submission** ([student.html](file:///c:/Users/Dharshan/Downloads/compass%20%282%29/compass/frontend/student.html)):
  - Multi-field submission: description, location, anonymous flag, and photo attachment.
  - Image verification and zero-shot photo classification.
- **Real-Time Status Tracking**:
  - Live badges: `Submitted`, `In Progress`, `Resolved`.
  - Visual breakdown of priority score, days open, urgency, frequency, and assigned department.
- **Engagement & Gamification**:
  - **Activity Streak**: Daily login/reporting streak counter (`streak_count`).
  - **Campus Leaderboard**: Ranks top reporters and awards badges (*First Reporter*, *Active Reporter*, *Problem Solver*).
  - **Public Community Feed**: Anonymized activity stream of resolved and active campus issues.
- **In-App Notifications**: Real-time alerts when complaint status changes.
- **Post-Resolution Feedback**: 1–5 star rating and comment form available once an issue is resolved.
- **Nearby Issue Predictions**: Panel showing predicted upcoming campus issues scoped by location.

### Administrative Portal
- **Overview Dashboard** ([admin.html](file:///c:/Users/Dharshan/Downloads/compass%20%282%29/compass/frontend/admin.html)):
  - Metrics: Total complaints, status distribution, average priority score, most reported location, and location watch list.
- **Priority-Sorted Triage List**:
  - Complaints dynamically ordered by `priority_score`.
  - Displays reporter details (if non-anonymous), location, department, days open, urgency, and frequency.
- **Resolution Workflow**:
  - **Start Work**: Transitions status to `in_progress` and alerts the student.
  - **Draft Resolution**: Invokes LLM/template engine to generate a personalized resolution note.
  - **Approve & Resolve**: Marks ticket `resolved`, triggers in-app notification, and dispatches email update.
- **Search & Natural Language Query**: `/api/admin/query` searches complaint text, status, and category.
- **RAG-Powered AI Assistant Widget** ([app.js](file:///c:/Users/Dharshan/Downloads/compass%20%282%29/compass/frontend/js/app.js)):
  - Floating chat assistant with suggestion buttons ("Is Block A rectified?").
  - Conversation history tracking, status fact extraction, and source complaint citation pills.
- **Predictive Risk & Forecasting**: Runs seasonal regression pipeline to predict issue risks by location and category.
- **On-Demand Summary Email**: Admins can trigger an immediate weekly summary broadcast.

---

## 2. Architecture & Pipeline Flow

```
[ Student Form Submit / Photo Upload ]
                 │
                 ▼
[ FastAPI Endpoint POST /api/complaints ]
                 │
                 ├──► Text Category Model (LogisticRegression)
                 ├──► Image Vision Classifier (CLIP zero-shot)
                 └──► Urgency Calculation (Keyword + Weight Rules)
                 │
                 ▼
[ LangGraph Reactive Pipeline (agents/graph.py) ]
                 │
        ┌────────┴────────┐
        ▼                 ▼
[ Duplicate Check ]   [ Route & Priority ]
 (ChromaDB / TF-IDF)   (Infer Department + Random Forest Priority Score)
        │                 │
        ├──► If Duplicate: Merges ticket & increments frequency counter (+1)
        └──► If New: Saves to DB + Indexes into Vector Store (upsert_documents)
                 │
                 ▼
[ Admin Dashboard Triage -> Start -> Draft Resolution (Gemini) -> Resolve ]
                 │
                 ▼
[ In-App Notification + Student Email (SMTP / Log) + Feedback Loop ]
```

1. **Ingestion & Multimodal Analysis**: Report text is analyzed for category and urgency; photo attachments are classified via CLIP zero-shot vision.
2. **LangGraph Pipeline Execution** ([graph.py](file:///c:/Users/Dharshan/Downloads/compass%20%282%29/compass/backend/agents/graph.py)):
   - `classify_node` $\rightarrow$ `dedup_node` $\rightarrow$ `route_node` $\rightarrow$ `priority_node`.
   - If duplicate detected at location, pipeline halts early (`update_existing`), merges into existing ticket, and increments frequency.
   - If new ticket, assigns responsible department (`IT`, `Electrical`, `Maintenance`, `Hostel`, `Safety`, `Facilities`), calculates priority score, and indexes into ChromaDB vector store.
3. **Resolution & Feedback**: Admin triages by priority, drafts response with Gemini, approves resolution, and triggers email + notification.

---

## 3. Technology Stack

- **Frontend**: Vanilla HTML5, CSS3 (custom CSS variables, responsive design), Vanilla JavaScript (ES6 `async/fetch`, DOM manipulation, floating chat widget).
- **Backend**: Python 3.11, **FastAPI**, **Uvicorn**, **Pydantic**, **SlowAPI** (rate limiting), **APScheduler** (background scheduler).
- **Database**:
  - **MongoDB** (`pymongo`) primary database.
  - In-Memory RAM MongoDB Proxy ([_FallbackClient](file:///c:/Users/Dharshan/Downloads/compass%20%282%29/compass/backend/database.py#L151-L168)) for local demo execution when MongoDB server is offline.
- **Machine Learning**:
  - Category Classifier: `scikit-learn` `Pipeline` (TF-IDF + `LogisticRegression`) saved in `category_model.joblib`.
  - Priority Regressor: `scikit-learn` `RandomForestRegressor` saved in `priority_model.joblib`.
  - Duplicate Vectorizer: `scikit-learn` `TfidfVectorizer` saved in `dedup_vectorizer.joblib`.
  - Forecasting Model: `scikit-learn` `DecisionTreeRegressor` saved in `forecast_model.joblib`.
- **LLM**: **Google Gemini API** (`google-generativeai` / `google.genai`, default model `gemini-2.5-flash`).
- **Vector DB & Embeddings**: **ChromaDB** (`PersistentClient`) + **SentenceTransformers** (`all-MiniLM-L6-v2`).
- **Vision**: **Hugging Face Transformers** (`openai/clip-vit-base-patch32` zero-shot classification) + **Pillow** (`PIL`).
- **Email Service**: Python `smtplib` with TLS support.
- **Authentication**: Signed JWT tokens (`python-jose` / manual HMAC-SHA256) and `passlib` (bcrypt password hashing).

---

## 4. Real Models vs. Fallbacks vs. Optional Services

| Component | Primary Method | Fallback Behavior |
| :--- | :--- | :--- |
| **Category Classification** | Trained Logistic Regression Model | Keyword matching ([_fallback_category_from_text](file:///c:/Users/Dharshan/Downloads/compass%20%282%29/compass/backend/ml_utils.py#L87-L99)) |
| **Priority Scoring** | Trained Random Forest Regressor | Formula: `(urgency * 40) + (frequency * 15) + (days_open * 5)` |
| **Duplicate Detection** | ChromaDB + SentenceTransformers Embeddings | TF-IDF Cosine Similarity vectorizer |
| **Vision Classification** | Hugging Face CLIP Zero-Shot Model | Skips vision and defaults to text classification |
| **LLM (Resolution/Chat)** | Google Gemini API (`GEMINI_API_KEY`) | Deterministic rule-based template engine ([_fallback_answer_for_facts](file:///c:/Users/Dharshan/Downloads/compass%20%282%29/compass/backend/chatbot_rag.py#L247-L272)) |
| **Email Delivery** | Real SMTP (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`) | Logs emails to local JSON file ([emails_sent.log](file:///c:/Users/Dharshan/Downloads/compass%20%282%29/compass/backend/email_service.py#L20-L22)) |
| **Database** | MongoDB Server (`MONGODB_URI`) | In-Memory RAM database proxy with demo seed data ([seed_demo_data.py](file:///c:/Users/Dharshan/Downloads/compass%20%282%29/compass/backend/seed_demo_data.py)) |

---

## 5. Mocked vs. Production-Ready State

- **Production-Ready**:
  - Full REST API with CORS, rate limiting, and input validation.
  - Secure JWT authentication & password hashing pipeline.
  - Complete MongoDB database integration layer.
  - Trained scikit-learn ML models for categorization, priority, and forecasting.
  - Real SMTP email sender and real ChromaDB vector store.
- **Mocked / Demo Enhancements**:
  - **In-Memory Mongo Fallback**: Simulates MongoDB in RAM if no live Mongo instance is detected.
  - **Email Log File**: Saves sent emails to `emails_sent.log` if live SMTP credentials aren't set.
  - **Static Seasonal Priors**: Hardcoded multiplier table `SEASONAL_PRIORS` to boost forecasting accuracy when complaint history is small.

---

## 6. Code Gaps & TODOs

1. **Scikit-Learn Version Warning**: Models were saved with `scikit-learn 1.5.2`, while runtime environment uses `1.9.0`. (Fix: re-run `python ml/train_models.py`).
2. **Local Image Storage**: Photos are stored on local disk (`backend/uploads/`) rather than cloud storage (S3/Cloudinary).
3. **No Self-Service Admin Sign-Up**: Student UI only allows registering standard student accounts; admin accounts must be created via API payload or seeding script.
4. **Missing Password Reset Endpoint**: Password reset endpoints are missing from `main.py`.

---

## 7. Plain-English Summary for Hackathon Judges

> **Compass** is an intelligent, full-stack campus problem intelligence platform designed to transform how universities manage infrastructure and student grievances. By combining multimodal zero-shot computer vision for photo evidence, machine learning for automated category classification and priority scoring, and vector search for instant duplicate complaint merging, Compass eliminates manual triage bottlenecks. Administrators get a centralized dashboard powered by predictive seasonal issue forecasting and a RAG-backed natural language AI assistant for real-time status insights, while students enjoy transparent tracking, notifications, and gamified campus activity streaks—delivering a proactive, closed-loop resolution system for modern campus management.
