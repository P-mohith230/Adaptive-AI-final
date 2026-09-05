# Developer Setup & Contribution Guide

**Platform:** AdaptiveAI Finance Controller  
**Audience:** Software Engineers, Finance-Ops Developers, Evaluators  
**Last Updated:** September 2026  

---

## 1. Prerequisites

Before setting up AdaptiveAI Finance Controller, ensure your workstation meets the following requirements:

- **Node.js:** v20.x or v22.x LTS (`node -v` and `npm -v`)
- **Python:** v3.11 or higher (`python --version`)
- **PostgreSQL:** v15 or v16 (Local service or Docker container)
- **Redis:** v7.x (Local service or Docker container)
- **Git:** v2.30+

---

## 2. Environment Configuration

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/P-mohith230/Adaptive-AI-Finance.git
   cd Adaptive-AI-Finance
   ```

2. **Configure Backend Environment:**
   Create `.env` in the repository root or in `backend/.env`:
   ```bash
   cp .env.example .env
   ```

   Key environment variables:
   ```ini
   # Database & Redis
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/securo
   REDIS_URL=redis://localhost:6379/0

   # Security & Auth
   SECRET_KEY=dev-secret-change-in-production
   DEBUG=true

   # Groq AI Controller (Required for AI Investigation & Explanations)
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=llama-3.3-70b-versatile

   # Razorpay Gateway Integration (Test Mode)
   RAZORPAY_KEY_ID=rzp_test_your_key_id
   RAZORPAY_KEY_SECRET=your_razorpay_secret
   RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

   # Frontend URL
   FRONTEND_URL=http://localhost:5173
   ```

---

## 3. Running Locally (Without Docker)

### 3.1 Backend Setup (FastAPI)
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run database migrations
alembic upgrade head

# Start FastAPI dev server (Port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.2 Frontend Setup (React 19 + Vite)
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server (Port 5173)
npm run dev
```

The application is now accessible at `http://localhost:5173`.  
Backend OpenAPI interactive documentation is available at `http://localhost:8000/docs`.

---

## 4. Running with Docker Compose

To launch the full stack including PostgreSQL, Redis, Celery worker, backend API, and frontend:
```bash
docker compose up --build
```
- Web Application: `http://localhost:3000`
- API Backend: `http://localhost:8000`

---

## 5. Running the Automated Evaluation

To execute the Razorpay Buildathon Track 04 evaluation against the 50+ record synthetic merchant batch:

```bash
# Via cURL / API:
curl -X POST http://localhost:8000/api/v1/evaluation/run

# Inspect metrics:
curl -X GET http://localhost:8000/api/v1/evaluation/metrics
```

Or run the Python test harness directly:
```bash
cd backend
pytest app/tests/test_evaluation.py -v
```

---

## 6. Running Tests & Code Quality Checks

### 6.1 Backend Tests
```bash
cd backend
pytest -v --cov=app
```

### 6.2 Frontend Tests & Linting
```bash
cd frontend
# Run unit tests
npm test

# Type-check TypeScript
npm run typecheck

# Lint with ESLint
npm run lint
```

---

## 7. Development Guidelines

1. **Deterministic Calculations:** Never introduce LLM calls to compute fees, balances, or match scores. All monetary calculations must use `decimal.Decimal`.
2. **Audit Logging:** Any endpoint that mutates financial transaction state or approves an exception must write to the `AuditTrail` table.
3. **Idempotency:** Webhook handlers must check event IDs before processing to prevent duplicate state mutation.
