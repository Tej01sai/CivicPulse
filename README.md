# Smart Resource Allocation — Community Intelligence Platform

A Gen AI-powered platform that aggregates scattered community data and matches volunteers to urgent local needs in real-time.

## 🚀 Quick Start (Development)

### Prerequisites
- **Python 3.11+** (with pip)
- **Node.js 18+** (with npm)
- **PostgreSQL 14+** (with pgvector extension)
- **Auth0 Account** (free tier OK for hackathon)
- **Anthropic API Key**
- **Pinecone Account** (free tier: 1M vectors)
- **Twilio Account** (sandbox mode OK for demo)

### Setup Backend

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your Auth0, Anthropic, Pinecone, Twilio, and DATABASE_URL

# 4. Initialize database
python -m app.db.init_db

# 5. Seed test data (optional)
python seed_data.py

# 6. Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run at `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.

### Setup Frontend

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Configure environment
cp .env.example .env.local
# Edit with Auth0 and API URLs

# 3. Start dev server
npm run dev
```

Frontend will run at `http://localhost:5173`.

---

## 🏗️ Project Structure

```
smart-resource-allocation/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment template
│   ├── seed_data.py             # Test data generation
│   └── app/
│       ├── config.py             # Environment config
│       ├── models/               # SQLAlchemy ORM models
│       ├── schemas/              # Pydantic request/response schemas
│       ├── services/             # Business logic (LLM, embeddings, matching)
│       ├── routers/              # API endpoints
│       ├── auth/                 # Auth0 JWT verification
│       └── db/                   # Database setup
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── .env.example              # Environment template
│   └── src/
│       ├── main.tsx              # React entry point
│       ├── App.tsx               # Router setup
│       ├── pages/                # Page components
│       ├── components/           # Reusable UI components
│       ├── hooks/                # Custom React hooks
│       └── lib/                  # Utils (API client, Auth0 config)
├── README.md                     # This file
└── .gitignore
```

---

## 📡 API Endpoints

### Public
- `GET /needs` — All needs (paginated, sorted by urgency_score)
- `GET /needs/{id}` — Single need detail
- `GET /volunteers` — All volunteers

### Protected (Auth0 JWT required)
- `POST /intake/parse` — Parse raw text → extract structured need
- `GET /matches/{volunteer_id}` — Top 5 needs for volunteer
- `POST /assignments` — Assign volunteer to need
- `GET /assignments` — List assignments
- `POST /alerts/trigger` — Admin alert trigger

---

## 🤖 How It Works

1. **Ingestion:** Survey text/photo → Claude API extracts structured need
2. **Deduplication:** Embeddings query Pinecone (cosine sim > 0.85)
3. **Ranking:** Urgency score calculated (formula in PRD)
4. **Matching:** Volunteer skills vs. need skills via embeddings
5. **Alerting:** SMS + in-app notification for CRITICAL needs

---

## 🧪 Quick Test

```bash
# Terminal 1: Start backend
cd backend && uvicorn main:app --reload

# Terminal 2: Start frontend
cd frontend && npm run dev

# Terminal 3: Test API
curl http://localhost:8000/needs
```

---

## 🚢 Deployment

- **Backend → Railway**
- **Frontend → Vercel**
- **DB → Railway PostgreSQL**

See deployment docs in PRD § 10.

---

## 📝 For Judges

Demo highlights:
- ✅ <5 min: Paper survey → AI-parsed → volunteer assigned
- ✅ Real-time deduplication (25-30% of needs are duplicates)
- ✅ Semantic volunteer matching (skills, not just availability)
- ✅ Multi-channel alerts (SMS + in-app + Slack)
- ✅ Impact tracking (end-to-end visibility)

**Tech Stack:** FastAPI + React 18 + PostgreSQL + Claude API + Pinecone + Auth0 + Twilio

---

**Next Steps:** Read `PRD_Smart_Resource_Allocation.md` for complete specs.
