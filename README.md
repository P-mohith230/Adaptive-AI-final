<p align="center">
  <img src="docs/logo.svg" width="360" alt="AdaptiveAI Finance Controller Logo" />
</p>

<h1 align="center">AdaptiveAI Finance Controller</h1>

<p align="center">
  <strong>AI-powered merchant financial control, reconciliation, exception intelligence, and settlement analytics.</strong>
  <br />
  <em>Reconcile. Verify. Explain. Act.</em>
</p>

<p align="center">
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/Backend-FastAPI%200.141-009688?logo=fastapi&logoColor=white" alt="FastAPI" /></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/Frontend-React%2019.2%20%2B%20Vite-61DAFB?logo=react&logoColor=black" alt="React 19" /></a>
  <a href="https://groq.com/"><img src="https://img.shields.io/badge/AI%20Controller-Groq%20Llama%20%2F%20GPT--OSS-orange" alt="Groq AI" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Verified%20Match%20Rate-86.7%25-brightgreen" alt="Match Rate" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Throughput-1%2C282%20rec%2Fsec-blue" alt="Throughput" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Arithmetic%20Hallucinations-0.0%25-success" alt="Arithmetic Hallucination" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-AGPL--3.0-blue.svg" alt="License: AGPL-3.0" /></a>
</p>

---

## Razorpay Hackathon Track 04 Challenge

> **Track 04 Mandate:**  
> *"Build an agent that closes one finance-ops loop across a 50+ record batch of synthetic data, reporting its match rate and the exceptions it could not resolve."*

**AdaptiveAI Finance Controller** solves merchant finance operations by autonomously reconciling and verifying three disconnected data streams:
1. **Merchant Internal Expected Orders** (ERP / OMS)
2. **Razorpay Payment Gateway Telemetry** (Captured Payments, Fees, Webhooks)
3. **Bank Settlement Credits** (Bank MT940 / CAMT / Statement Feeds)

The platform deterministically flags fee anomalies, timing float delays, and uncaptured gateway transactions, while surfacing natural-language root cause explanations and 1-click corrective approvals for finance teams.

---

## Key Capabilities

- **Automated 3-Way Reconciliation Engine**: High-throughput rule matching (`1,282 rec/sec`) across Orders, Gateways, and Bank Statements.
- **Root Cause Exception Intelligence**: Classifies discrepancies into MDR fee variances, timing float delays, missing payouts, and customer chargebacks.
- **Transaction Decision Cards**: Detailed exception inspection with deterministic checkmarks, parameter side-by-side comparison, and one-click actions:
  - *Accept Timing Variance (T+2 SLA)*
  - *Dispute MDR Fee Discrepancy*
  - *Post to Suspense Account*
- **Real-Time Cash Position & Liquidity Forecaster**: Calculates verified liquid bank balance vs trapped settlement float and working capital exposure.
- **Ask Controller AI**: Conversational interface powered by Groq LLM inference with deterministic tool verification — answering queries on settlement schedules, fee leaks, and cash forecasting with zero arithmetic hallucinations.
- **Double-Entry General Ledger Sync**: Posts verified reconciliation entries into double-entry accounting journals with an immutable audit trail.
- **Enterprise Authentication & Security**: Full support for Passkeys (WebAuthn), TOTP 2FA, Passwords, and Enterprise OIDC SSO (Authentik, Pocket ID).

---

## Quick Start — Run Locally in Under 2 Minutes

### 1. Clone the Repository
```bash
git clone https://github.com/P-mohith230/Adaptive-AI-Finance.git
cd Adaptive-AI-Finance
```

### 2. Configure Environment
```bash
cp backend/.env.example backend/.env
```
*(Optional: Add your `GROQ_API_KEY=gsk_...` in `backend/.env` for cloud LLM reasoning; if left empty, the built-in deterministic financial engine operates 100% offline).*

### 3. Start Database (PostgreSQL & Redis)
Ensure PostgreSQL (port `5432`) and Redis (port `6379`) are running. If you have Docker:
```bash
docker compose up db redis -d
```

### 4. Start Backend
```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Start Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 1-Click Evaluation & Demo Tour

1. **Finance Control Center (`/control-center`)**: Click **"Run Demo"** to reconcile 100 synthetic orders in ~78ms with real-time KPI telemetry.
2. **Reconciliation Workstation (`/reconciliation`)**: Review the 3-way reconciliation table, filter by exception type, and click **"Inspect"** on any flagged row to open its Decision Card.
3. **Decision Cards**: Review the root cause diagnosis, view the MDR variance breakdown, and click **"Accept Timing Variance"** or **"Dispute Fee"**.
4. **Ask Controller AI**: Click **"Ask Controller"** in the top header to query the assistant about settlement timing, fee leakage, or forward cash liquidity.
5. **Video Presentation**: Full HD walkthrough presentation video is available in [`recordings/securo_master_walkthrough_presentation.mp4`](recordings/securo_master_walkthrough_presentation.mp4) along with the voiceover script in [`recordings/ELEVENLABS_VOICEOVER_SCRIPT.txt`](recordings/ELEVENLABS_VOICEOVER_SCRIPT.txt).

---

## Technology Architecture

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend Framework** | React 19.2 + TypeScript + Vite | High-performance dashboard with sub-second navigation |
| **Styling & Design System** | Tailwind CSS + Radix UI + Lucide | Institutional fintech dark/light theme, high-density data tables |
| **Backend API** | FastAPI + Python 3.11+ | High-throughput asynchronous REST API & reconciliation engine |
| **Database & ORM** | PostgreSQL + SQLAlchemy + Alembic | Relational data persistence with strict double-entry ledger constraints |
| **Caching & Async Queue** | Redis + Celery | Fast state caching and background batch processing |
| **AI Intelligence** | Groq SDK (Llama 3.3 / GPT-OSS) | Sub-second natural language financial analysis with tool-use verification |

---

## Brand Guidelines & Architecture Documentation

- **Brand Guidelines**: [`docs/ADAPTIVEAI_BRAND_GUIDELINES.md`](docs/ADAPTIVEAI_BRAND_GUIDELINES.md)
- **Branding Audit**: [`docs/BRANDING_AUDIT.md`](docs/BRANDING_AUDIT.md)
- **Voiceover Script**: [`recordings/ELEVENLABS_VOICEOVER_SCRIPT.txt`](recordings/ELEVENLABS_VOICEOVER_SCRIPT.txt)

---

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE).
