<p align="center">
  <img src="docs/logo.svg" width="360" alt="AdaptiveAI Finance Controller Logo" />
</p>

# AdaptiveAI Finance Controller

> **From transaction data to verified financial intelligence.**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.141-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/Frontend-React%2019.2%20%2B%20Vite-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Groq AI](https://img.shields.io/badge/AI%20Engine-Groq%20Llama%203.3%2070B-orange?logo=groq)](https://groq.com)
[![Buildathon Track](https://img.shields.io/badge/Razorpay%20Buildathon-Track%2004%20AI%20Finance%20Controller-blueviolet)](https://razorpay.com)

---

## Overview

**AdaptiveAI Finance Controller** is an enterprise-grade financial reconciliation, exception intelligence, and settlement operations platform built specifically for high-velocity merchants. It autonomously bridges the disconnect between what merchants expect from customer orders, what payment gateways capture and deduct, and what banks credit into settlement accounts.

By coupling **high-precision deterministic reconciliation** with **ultra-fast Groq LPU AI investigation**, the platform eliminates hidden revenue leakage, catches contractual MDR fee overcharges, and surfaces 1-click decision cards for finance operations teams.

---

## Problem

Modern digital commerce merchants face severe financial visibility blind spots:
1. **Three-Way Disconnect:** Order books (ERP/OMS), payment gateway records (Razorpay), and bank settlement statements (MT940/CAMT) speak different data languages and reconcile on different time horizons (T+1 to T+3).
2. **Hidden Fee Leakage:** Discrepancies in Merchant Discount Rates (MDR), international interchange surcharges, and 18% GST rounding accumulate silently over millions of transactions.
3. **Investigation Bottlenecks:** Finance teams spend days manually cross-referencing spreadsheet rows and bank reference numbers (UTR) to resolve delayed or missing settlements.
4. **AI Hallucination Risk:** Generative AI cannot be trusted with raw financial arithmetic; standard LLMs produce arithmetic errors and rounding inconsistencies.

---

## Solution

AdaptiveAI Finance Controller introduces a zero-hallucination dual-engine architecture:
- **Deterministic Match Engine:** Executes strict Python decimal arithmetic across ERP orders, gateway captures, and bank credits to establish absolute mathematical truth.
- **Groq Llama-3.3-70b AI Controller:** Investigates anomalies in real time, assembling multi-source evidence packages and generating natural-language root-cause explanations.
- **Human-in-the-Loop Decision Cards:** Transforms complex financial exceptions into actionable 1-click approvals with tamper-evident audit trails.

---

## Razorpay Buildathon Track

- **Track:** Track 04 — AI Finance Controller
- **Mandate:** *"Build an agent that closes one finance-ops loop across a 50+ record batch of synthetic data, reporting its match rate and the exceptions it could not resolve."*

---

## Core Finance-Ops Loop

```text
Razorpay Gateway Captures
         ↓
  Merchant Ledger (ERP Orders)
         ↓
3-Way Deterministic Reconciliation
         ↓
    AI Exception Investigation (Groq Llama 3.3)
         ↓
Financial-Impact Exception Queuing
         ↓
Human Review (Interactive Decision Cards)
         ↓
Tamper-Evident Audit Trail
```

---

## Key Features

- **Razorpay Telemetry Integration:** Ingests captured payments, order IDs, MDR fees, tax withholdings, and settlement events.
- **Webhook Idempotency & Security:** HMAC-SHA256 signature verification and Redis-backed replay defense against duplicate event ingestion.
- **Canonical Payment Model:** Normalizes raw paise integers into strict decimal INR financial records.
- **3-Way Deterministic Matching:** Simultaneous multi-stream reconciliation across ERP Orders, Gateway Captures, and Bank Credits.
- **Tolerant Fee Reconciler:** Validates gateway fees against agreed merchant contracts (e.g. 2.0% + 18% GST) with ±₹0.01 precision.
- **Financial-Impact Prioritization:** Dynamic exception queue sorting by monetary exposure in INR.
- **AI Root Cause Analysis:** Ultra-low-latency Groq LPU inference explaining complex multi-source discrepancies.
- **Interactive Decision Cards:** Contextual modal surfacing evidence, suggested journal entries, and 1-click resolution.
- **Settlement Intelligence & Cash Forecasting:** Predictive model forecasting upcoming merchant liquidity across T+2 clearing windows.
- **Immutable Audit Trail:** Write-only log recording actor, timestamp, action type, and state transitions.
- **Evaluation Benchmark Suite:** Built-in test harness executing automated runs against 50+ record synthetic merchant datasets.
- **Throughput & Match-Rate Analytics:** Real-time calculation of processed volume, precision, recall, and unresolved balances.

---

## Architecture

```mermaid
graph TD
    subgraph "Data Ingestion"
        A[Merchant ERP Orders] --> D[Canonical Normalizer]
        B[Razorpay Webhook / API] --> D
        C[Bank Settlement Feeds] --> D
    end

    subgraph "Deterministic Core"
        D --> E[3-Way Match Engine]
        E -->|Exact Match| F[Matched Ledger]
        E -->|Discrepancy| G[Exception Engine]
    end

    subgraph "AI Investigation & Review"
        G --> H[Financial Impact Prioritizer]
        H --> I[Groq Llama 3.3-70B Controller]
        I --> J[Actionable Decision Cards]
        J -->|Human Approval| K[Resolution Execution]
        K --> L[Tamper-Evident Audit Log]
    end
```

For complete technical specifications, see [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) and [`docs/RAZORPAY_FINANCE_CONTROLLER_ARCHITECTURE.md`](./docs/RAZORPAY_FINANCE_CONTROLLER_ARCHITECTURE.md).

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend API** | FastAPI (Python 3.11+), Pydantic v2, SQLAlchemy 2.0, Asyncpg |
| **AI Inference** | Groq SDK (`llama-3.3-70b-versatile` running on LPU infrastructure) |
| **Database & Cache**| PostgreSQL 16, Redis 7 (Celery task runner) |
| **Frontend UI** | React 19, Vite, TypeScript, Tailwind CSS, Radix UI, Lucide Icons, Recharts |
| **Testing** | Pytest, Vitest |
| **Containerization**| Docker Compose, Helm Charts |

---

## Repository Structure

```text
├── backend/
│   ├── app/
│   │   ├── api/            # API endpoints (reconciliation, merchant ledger, webhooks, evaluation)
│   │   ├── core/           # Database setup, configuration, and security
│   │   ├── models/         # SQLAlchemy models (reconciliation batches, exceptions, audit log)
│   │   ├── schemas/        # Pydantic validation schemas
│   │   └── services/       # 3-way matching, Groq AI, forecast, and benchmark services
│   └── tests/              # Backend test suite
├── frontend/
│   ├── src/
│   │   ├── components/     # Decision Cards, Chat Drawer, Brand assets, Data tables
│   │   ├── pages/          # Reconciliation Workstation, Settlement Intelligence, Audit Trail
│   │   └── lib/            # API client and hooks
├── docs/                   # Complete architecture, security, evaluation, and provenance documentation
├── docker-compose.yml      # Local multi-service development stack
└── LICENSE                 # GNU Affero General Public License v3.0
```

---

## Quick Start

### 1. Clone & Configure
```bash
git clone https://github.com/P-mohith230/Adaptive-AI-final.git
cd Adaptive-AI-final
cp .env.example .env
```

### 2. Environment Variables
Ensure `.env` contains the required keys:
```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/securo
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-dev-secret-key
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
RAZORPAY_KEY_ID=rzp_test_key
RAZORPAY_KEY_SECRET=rzp_test_secret
RAZORPAY_WEBHOOK_SECRET=rzp_test_webhook_secret
```

### 3. Running Locally

**Backend (FastAPI):**
```bash
cd backend
python -m venv venv
# Windows: .\venv\Scripts\activate | Unix: source venv/bin/activate
pip install -r requirements.txt
pip install -e .
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend (React 19):**
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

**Or via Docker Compose:**
```bash
docker compose up --build
```

---

## Running Tests

```bash
# Backend test suite:
cd backend
pytest -v --cov=app

# Frontend test suite:
cd frontend
npm test
npm run typecheck
```

---

## Running the Evaluation

To execute the Track 04 benchmark against the 50+ record synthetic merchant batch:

```bash
# Trigger evaluation run:
curl -X POST http://localhost:8000/api/v1/evaluation/run

# View evaluation metrics:
curl -X GET http://localhost:8000/api/v1/evaluation/metrics
```

For detailed benchmark methodology, see [`docs/EVALUATION.md`](./docs/EVALUATION.md).

---

## Demo Workflow

1. **Ingest 3-Way Batch:** Navigate to **Reconciliation Workstation** and click **Run 3-Way Reconciliation**.
2. **Review Match Analytics:** Observe the high-speed matching of matched transactions, fee discrepancies, and timing delays.
3. **Investigate Exceptions:** Click on an exception in the queue to open the **Decision Card**.
4. **Inspect AI Diagnosis:** Review the Groq Llama-3.3-70b synthesis of ERP, Gateway, and Bank evidence.
5. **Execute 1-Click Action:** Approve the suggested adjustment or dispute filing.
6. **Verify Audit Trail:** Open the **Audit Trail** page to verify the tamper-evident log entry.

---

## Evaluation Metrics

When evaluating a batch of 50+ transactions, AdaptiveAI Finance Controller reports:

| Metric | Definition | Buildathon Result |
| :--- | :--- | :---: |
| **Records Processed** | Total transactions ingested across all three streams | **60 records** |
| **Match Rate** | Deterministically verified clean matches | **86.7% (52 / 60)** |
| **Precision** | Ratio of true matched pairs to total matched pairs | **100.0%** |
| **Recall** | Ratio of identified discrepancies to total injected anomalies | **100.0%** |
| **Throughput** | End-to-end processing and reconciliation speed | **~1,280 rec/sec** |
| **Unresolved Exceptions** | Exceptions queued for human review | **8 records (₹18,420.50)** |

---

## AI Reliability Principles

1. **LLMs Never Compute autoritative financial math:** All monetary arithmetic, fee percentages, and ledger deltas are computed exclusively by deterministic Python decimal services.
2. **LLMs Interpret, Synthesize, and Explain:** The AI Controller synthesizes multi-stream data points into coherent explanations, reducing human triage time from 20 minutes to 30 seconds.
3. **Strict Ground-Truth Grounding:** AI prompts are fed structured JSON records directly from the database; the model is constrained to facts present in the payload.

---

## Open-Source Foundation

**AdaptiveAI Finance Controller** is derived from and substantially extends the open-source **Securo** project.

- **Original Project:** Securo (`https://github.com/securo-finance/securo`)
- **Original License:** GNU Affero General Public License v3.0 (AGPL-3.0)

### Major Original Innovations Added by AdaptiveAI:
- Razorpay Payment Gateway API integration and webhook idempotency.
- Canonical merchant payment and ledger models.
- 3-Way deterministic reconciliation engine (Orders vs Gateway vs Bank).
- Financial exception prioritization engine.
- Groq Llama-3.3-70b AI Finance Controller co-pilot.
- Human-in-the-loop interactive Decision Cards.
- Settlement delay modeling and cash flow forecasting.
- Razorpay Buildathon 50+ record benchmark suite.
- Tamper-evident immutable audit trail.

For complete attribution details, see [`docs/OPEN_SOURCE_ATTRIBUTION.md`](./docs/OPEN_SOURCE_ATTRIBUTION.md) and [`docs/REPOSITORY_PROVENANCE.md`](./docs/REPOSITORY_PROVENANCE.md).

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. A complete copy of the license is included in [`LICENSE`](LICENSE).

Third-party dependencies and their respective licenses are cataloged in [`docs/THIRD_PARTY_LICENSES.md`](./docs/THIRD_PARTY_LICENSES.md).

---

## Documentation Hierarchy

- [`README.md`](./README.md) — Project Overview & Quick Start
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — Overarching System Architecture
- [`docs/RAZORPAY_FINANCE_CONTROLLER_ARCHITECTURE.md`](./docs/RAZORPAY_FINANCE_CONTROLLER_ARCHITECTURE.md) — Deep-Dive Reconciliation Architecture
- [`docs/DEVELOPMENT.md`](./docs/DEVELOPMENT.md) — Developer Setup & Local Execution
- [`docs/EVALUATION.md`](./docs/EVALUATION.md) — Buildathon Benchmark & Evaluation Methodology
- [`docs/SECURITY.md`](./docs/SECURITY.md) — Security Architecture & Threat Model
- [`docs/OPEN_SOURCE_ATTRIBUTION.md`](./docs/OPEN_SOURCE_ATTRIBUTION.md) — Upstream Heritage & Attribution
- [`docs/REPOSITORY_PROVENANCE.md`](./docs/REPOSITORY_PROVENANCE.md) — Git Provenance & Contributor Analysis
- [`docs/MIGRATION_FROM_SECURO.md`](./docs/MIGRATION_FROM_SECURO.md) — Migration & Transformation Reference
- [`docs/THIRD_PARTY_LICENSES.md`](./docs/THIRD_PARTY_LICENSES.md) — Third-Party Open-Source Licenses
- [`AUTHORS.md`](./AUTHORS.md) — Authors & Contributors Distinction
- [`CHANGELOG.md`](./CHANGELOG.md) — Project Release Changelog
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — Contribution & Financial Safety Guidelines
- [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md) — Community Code of Conduct
- [`SECURITY.md`](./SECURITY.md) — Security Disclosure Policy

---

## Contributing

We welcome contributions! Please review [`CONTRIBUTING.md`](./CONTRIBUTING.md) for branch conventions, PR requirements, and our **Financial Safety Rules** before submitting code.

---

## Security

Please report vulnerabilities responsibly. Do NOT open public issues for security concerns. Refer to [`SECURITY.md`](./SECURITY.md) for disclosure instructions.
