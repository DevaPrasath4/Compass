# Compass — Campus Complaint Tracking Platform

Compass is a two-role campus issue tracker for students/faculty and admins. It allows complaints to be reported, classified, deduplicated, prioritized, and resolved with a clear status flow from Submitted to In Progress to Resolved.

## Setup

1. Create a local environment file from the example:

   ```bash
   cp .env.example .env
   ```

2. Install dependencies:

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Train the ML models:

   ```bash
   python ml/train_models.py
   ```

4. Start the API:

   ```bash
   uvicorn main:app --reload
   ```

5. Open the frontend through the backend root, usually at:

   ```text
   http://localhost:8000/
   ```

## Environment variables

Use the values in the repository root `.env` file (or a local `.env` inside `backend` if preferred). The required variables are documented in [backend/.env.example](backend/.env.example) and also in the repo root [.env.example](.env.example).

Important settings:

- `MONGODB_URI`: MongoDB connection string; do not hardcode it in source
- `JWT_SECRET_KEY`: server-side secret for signed JWTs
- `GEMINI_API_KEY`: optional; if absent, the app falls back to templates
- `SMTP_*`: optional real SMTP config; if absent, email is logged to a local file

## Honest ML / data status

This project uses real trained models for the core pipeline, clear local RAG/vector-search fallbacks, and explicit optional-service fallbacks for external APIs.

### Real, trained models

- Category classification: a scikit-learn Logistic Regression pipeline trained on synthetic complaint text
- Priority scoring: a Random Forest regressor trained on synthetic urgency/frequency/days-open data
- Duplicate detection: semantic vector search backed by local Chroma + SentenceTransformer embeddings when available; falls back to TF-IDF similarity if the vector store is unavailable
- Forecasting: a lightweight seasonal regression trained on synthetic monthly complaint history and saved under [backend/ml/models](backend/ml/models)

These are created in [backend/ml/train_models.py](backend/ml/train_models.py) and saved under [backend/ml/models](backend/ml/models).

### Rule-based heuristics

- Department inference in [backend/ml_utils.py](backend/ml_utils.py)
- Urgency scoring and fallback category mapping in [backend/ml_utils.py](backend/ml_utils.py)
- Campus KB fallback retrieval in [backend/campus_rag.py](backend/campus_rag.py)

These are intentionally not the primary classifier. The model prediction decides the category whenever it yields a valid app category; the keyword rules are used as a fallback only when the model output is mismatched, empty, or the embedding stack is unavailable.

### LLM and email fallbacks

- Gemini is optional; if `GEMINI_API_KEY` is missing, resolution drafting and admin natural-language answer generation fall back to templates
- Email is real SMTP when `SMTP_*` credentials are configured; otherwise it is logged into the local `emails_sent.log` file
- Vision classification uses a local Hugging Face zero-shot image classifier as an offline stand-in for a hosted NVIDIA model; swap it out with a hosted API by editing [backend/vision_utils.py](backend/vision_utils.py)

## Demo setup

To seed the local in-memory database with demo users and complaint data:

```bash
cd backend
python seed_demo_data.py
```

Alternatively, after starting the app, you can hit the local login route with the demo credentials seeded by the app.

## Demo script

1. Open the app at http://localhost:8000/
2. Register a student and log in
3. Submit two complaints about the same issue in the same room to confirm dedup merge
4. Open the admin dashboard and review priority sorting
5. Resolve a complaint and confirm the student sees the notification and email log
6. Ask a natural-language admin query
7. Open the predicted issues panel and inspect the risk confidence range
8. Check the campus pulse and leaderboard panels
9. Review the admin summary and weekly email trigger
10. Log out and log back in as the seeded admin to confirm the full flow

## Security and secrets

The repository now includes `.gitignore` rules that block `.env`, database files, `__pycache__`, uploads, and generated node artifacts.

Passwords are hashed with bcrypt, not raw SHA-256. Auth tokens include an expiry and are checked on every request.

> Rotate these credentials immediately: the repo previously contained a real-looking MongoDB connection string and a hardcoded secret in history/config. Any secret values in prior copies should be replaced before deployment.

## Synthetic data provenance

The training data generator is stored at [backend/ml/generate_synthetic_data.py](backend/ml/generate_synthetic_data.py). It clearly labels the source as synthetic. The app does not pretend the dataset is a real production dataset; it is a reproducible placeholder for training and demo purposes.

## Feature coverage

- Student/faculty registration and login
- Complaint submission with description, location, optional upload, and anonymous flag
- Duplicate merging into an open complaint record
- Student progress tracker and streak counter
- Admin queue sorted by priority score
- Draft/approve/resolve workflow with email logging or sending
- Admin aggregate overview and natural-language complaint query that works even without a Gemini key
- Admin chatbot grounded in complaint retrieval and deterministic status facts before any LLM response is generated
- Rolling watch-list logic over recent complaint history is included as a lightweight trend check in the backend data layer

## Admin chatbot

The admin chatbot is RAG-grounded: it first retrieves the most relevant complaints by location and issue context, then computes deterministic status facts from those matches before the LLM is asked to respond. This reduces hallucination and makes yes/no location checks such as “Is Block A rectified?” rely on actual complaint records instead of guesswork.

It is optional-Gemini by design. If `GEMINI_API_KEY` is configured, the model can refine the response using the retrieved facts and complaint summaries. If the key is absent, the app falls back to a deterministic template that explicitly states the number of open, in-progress, and resolved reports.

Current strengths: location + status prompts such as “Is Block A rectified?”, “What is the status of electrical issues?”, and follow-up questions that refer to the same complaint history.

Current limitations: it is intentionally not a general multi-location comparison engine and does not do date-range math beyond what is already available in the retrieved complaint metadata. That scope is kept honest and explicit rather than overclaimed.

## How to switch each fallback to the real service

- MongoDB: set `MONGODB_URI` to your Atlas/hosted instance and ensure the app is pointed at that database
- Gemini: set `GEMINI_API_KEY` and optionally `GEMINI_MODEL`
- SMTP: set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM`

## Run checklist

Before considering this app complete:

- register a student and an admin
- submit two complaints about the same issue in one location and confirm they merge
- create an urgent complaint and confirm the priority score is above a routine one
- resolve a complaint as admin and confirm the student can see the Resolved status
- ask the admin query endpoint a basic question and confirm it returns a real aggregate answer
- verify no actual secret credentials remain in the repository
