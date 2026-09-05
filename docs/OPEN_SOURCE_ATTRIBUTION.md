# Open-Source Attribution & Upstream Heritage

**Project:** AdaptiveAI Finance Controller  
**Derivative Status:** Extended derivative work based on Securo  
**License:** GNU Affero General Public License v3.0 (GNU AGPL-3.0)  
**Upstream Project:** Securo (`https://github.com/securo-finance/securo`)  

---

## 1. Upstream Attribution Notice

AdaptiveAI Finance Controller is built upon the open-source **Securo** codebase, developed by the Securo community and maintainers under the GNU Affero General Public License v3.0.

We express our sincere gratitude to the original Securo creators and open-source contributors for developing a robust, privacy-first personal finance foundation, including its multi-workspace architecture, clean FastAPI application structure, and responsive React frontend.

In full compliance with Sections 4 and 5 of the GNU AGPL-3.0:
1. **License Continuity:** The entire project remains licensed under the GNU AGPL-3.0. A complete copy of the license is preserved in the root [`LICENSE`](../LICENSE) file.
2. **Prominent Notices of Modification:** All files modified or created for AdaptiveAI Finance Controller carry appropriate headers and documentation detailing our extensions.
3. **No Authorship Falsification:** We do not claim original authorship of upstream Securo components. Original copyright notices remain in place.
4. **Source Code Availability:** Full source code for all modifications and components is made available in this repository.

---

## 2. Upstream / Inherited Components

The following foundational subsystems were inherited from the upstream Securo project:

| Subsystem | Upstream Implementation | Upstream Role |
| :--- | :--- | :--- |
| **FastAPI Backend Framework** | `backend/app/main.py`, `backend/app/core/` | Application bootstrapping, database session management (`asyncpg`), Celery task runner, Redis integration. |
| **User Authentication & RBAC** | `backend/app/api/auth.py`, `fastapi-users` | JWT authentication, local password hashing, WebAuthn/passkey handlers, multi-workspace isolation. |
| **Core Accounting Schema** | `backend/app/models/` | Base workspace, account, transaction, and category models. |
| **React + Vite Frontend Shell** | `frontend/src/` | Base layout shell, theme toggle (dark/light), Radix UI primitives, Tailwind styling, React Query client. |
| **Multi-Format Ingestion Foundation** | `backend/app/services/importer/` | Base parser abstractions for OFX, QIF, CAMT.053, and generic banking CSVs. |
| **Deployment Infrastructure** | `docker-compose.yml`, `charts/` | Docker Compose orchestration and Helm chart definitions for PostgreSQL, Redis, and workers. |

---

## 3. AdaptiveAI Project Contributions & Original Innovations

Built specifically for the **Razorpay AI Buildathon Track 04 (AI Finance Controller)**, the following subsystems were designed, implemented, and contributed by the AdaptiveAI engineering team:

### 3.1 Razorpay Payment Gateway & Telemetry Integration
- **Razorpay API Connector:** Direct integration with Razorpay Payments, Orders, and Settlements APIs.
- **Webhook Idempotency Engine:** Webhook ingestion pipeline with HMAC-SHA256 signature verification and redis-backed replay attack defense.
- **Canonical Payment Model:** Normalization layer mapping raw Razorpay telemetry into standardized merchant ledger primitives.

### 3.2 3-Way Deterministic Reconciliation Engine
- **Triple-Stream Matching:** Mathematical matching algorithm reconciling:
  1. Internal Merchant Orders (ERP / Order Management System).
  2. Razorpay Gateway Captured Payments & Platform Fee Deductions.
  3. Bank Settlement Credits (Bank Statement MT940 / CAMT feeds).
- **Tolerance & Window Rules:** Configurable fee tolerance checking and settlement delay window matching (+1 to +3 business days).
- **Match State Classification:** Automated status tagging (`MATCHED`, `FEE_DISCREPANCY`, `TIMING_DELAY`, `MISSING_BANK_CREDIT`, `MISSING_PAYMENT`).

### 3.3 Financial Exception & Root Cause Engine
- **Automated Exception Queuing:** Dynamic categorization of discrepancies with financial-impact prioritization (high-value float delays surfaced first).
- **Anomaly Detection:** Flagging fee overcharges exceeding contractual MDR (Merchant Discount Rate) thresholds.
- **Evidence Extraction:** Deterministic assembly of transaction metadata, gateway trace IDs, and bank reference numbers (UTR) for every anomaly.

### 3.4 AI Finance Controller (LLM Intelligence with Zero-Hallucination Boundary)
- **Groq Llama-3.3-70b-versatile Integration:** Asynchronous streaming financial co-pilot capable of contextual query answering and root-cause explanation.
- **Strict Separation of Concerns:**
  - *LLMs never calculate financial balances or match records.*
  - *Deterministic Python services perform all arithmetic and state transitions.*
  - *LLMs synthesize evidence, explain complex multi-gateway discrepancies, and draft customer support communications.*
- **Structured Action Output:** Generates structured JSON proposal payloads validated by Pydantic schemas.

### 3.5 Human-in-the-Loop Decision Cards
- **Interactive Resolution Cards:** Actionable UI cards for financial operators providing:
  - Problem summary and financial impact.
  - Assembled evidence from all 3 data streams.
  - Recommended resolution (e.g., "Post fee adjustment of ₹15.20", "Escalate uncredited UTR to HDFC Bank", "Retry settlement").
  - 1-click operator approval with complete audit logging.

### 3.6 Settlement Intelligence & Cash Flow Forecasting
- **T+2 Settlement Delay Modeling:** Predictive engine projecting upcoming merchant liquidity based on historical gateway clearing cycles.
- **Float Analysis:** Quantification of working capital trapped in transit across payment gateways.

### 3.7 Evaluation & Benchmark Suite
- **Track 04 Benchmark Runner:** Autonomous evaluation service executing against 50+ record synthetic merchant datasets.
- **Standardized Metrics Reporting:** Computes records processed, deterministic match rate, precision, recall, throughput (records/second), and unresolved exception value.

### 3.8 Tamper-Evident Audit Trail
- **Immutable Log:** Every reconciliation state transition, exception escalation, and human approval is logged with actor ID, timestamp, and previous/new state snapshots.

---

## 4. File-Level Modification Summary

| Path | Modification Type | Description |
| :--- | :--- | :--- |
| `backend/app/api/reconciliation.py` | **NEW** | API endpoints for 3-way reconciliation batches and exception queue. |
| `backend/app/api/merchant_ledger.py` | **NEW** | API endpoints for canonical merchant orders and gateway transactions. |
| `backend/app/api/settlement.py` | **NEW** | API endpoints for settlement tracking and liquidity forecasting. |
| `backend/app/api/evaluation.py` | **NEW** | API endpoints for running Track 04 benchmarks and retrieving metrics. |
| `backend/app/api/groq_controller.py` | **NEW** | Groq-powered AI controller chat endpoint with financial context. |
| `backend/app/services/reconciliation_service.py` | **NEW** | Deterministic 3-way matching and fee discrepancy calculation engine. |
| `backend/app/services/groq_service.py` | **NEW** | Groq client wrapper with structured prompt engineering and fallback. |
| `backend/app/services/ai_controller_service.py` | **NEW** | Exception analysis and resolution proposal generation service. |
| `backend/app/services/evaluation_service.py` | **NEW** | Benchmark test runner with synthetic dataset generator. |
| `backend/app/services/forecast_service.py` | **NEW** | Settlement delay and cash flow liquidity forecasting service. |
| `backend/app/models/reconciliation.py` | **NEW** | Database schema for reconciliation batches, exceptions, and audit entries. |
| `frontend/src/pages/reconciliation.tsx` | **NEW** | Financial controller workstation with 3-way reconciliation tabs. |
| `frontend/src/pages/settlement-intelligence.tsx`| **NEW** | Settlement delays and liquidity forecasting visualization page. |
| `frontend/src/pages/audit-trail.tsx` | **NEW** | Immutable audit log viewer with actor filtering and state diffs. |
| `frontend/src/components/reconciliation/` | **NEW** | Decision card modal, CSV import dialog, and match statistics badges. |
| `frontend/src/components/chat/groq-chat-drawer.tsx`| **NEW** | Floating AI Finance Controller chat assistant. |
| `frontend/src/components/brand/` | **NEW** | AdaptiveAI Finance Controller vector logos, emblems, and auth panels. |
| `docs/` | **NEW/UPDATED** | Comprehensive system architecture, evaluation, security, and attribution docs. |
