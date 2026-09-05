# Changelog

All notable changes to the **AdaptiveAI Finance Controller** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-05: AdaptiveAI Finance Controller — Initial Buildathon Release

### Overview
This milestone release transforms the open-source personal finance foundation into an enterprise-grade **AI Finance Controller**, built for the **Razorpay AI Buildathon 2026 (Track 04: AI Finance Controller)**.

---

### New Project Functionality (AdaptiveAI Original Innovations)

#### Razorpay Payment Gateway & Webhook Pipeline
- **Added** Razorpay Payments, Orders, and Settlements API connector (`backend/app/api/merchant_ledger.py`).
- **Added** HMAC-SHA256 signature verification on all incoming webhook payloads (`backend/app/api/webhooks.py`).
- **Added** Redis-backed event deduplication (`X-Razorpay-Event-Id`) preventing replay attacks.
- **Added** Canonical payment model converting raw paise amounts into high-precision INR decimals.

#### 3-Way Deterministic Reconciliation Engine
- **Added** 3-stream simultaneous reconciliation matching Merchant ERP Orders, Razorpay Gateway Captures, and Bank Settlement MT940 credits (`backend/app/services/reconciliation_service.py`).
- **Added** Tolerant fee engine verifying Merchant Discount Rates (MDR) and 18% GST against contract terms with ±₹0.01 precision.
- **Added** Settlement timing window evaluator matching deposits across T+1, T+2, and T+3 business day clearing intervals.
- **Added** Automated state tagging: `MATCHED`, `FEE_DISCREPANCY`, `TIMING_DELAY`, `MISSING_BANK_CREDIT`, `MISSING_PAYMENT`.

#### Financial Exception Investigation & Prioritization
- **Added** Financial-impact prioritization algorithm sorting exceptions by monetary exposure in INR.
- **Added** Automated evidence extraction compiling order ID, payment ID, gateway fee, GST, and bank UTR into unified investigation packages.

#### Groq-Powered AI Controller Assistant
- **Added** Groq Llama-3.3-70b-versatile asynchronous streaming integration with <500ms first-token latency (`backend/app/services/groq_service.py`).
- **Added** Zero-hallucination arithmetic boundary: LLMs strictly explain and summarize; deterministic Python services compute all numbers.
- **Added** Conversational floating co-pilot drawer with real-time financial context injection (`frontend/src/components/chat/groq-chat-drawer.tsx`).

#### Human-in-the-Loop Decision Cards & Audit Trail
- **Added** Interactive Decision Card modal surfacing evidence, root-cause diagnosis, and 1-click approvals (`frontend/src/components/reconciliation/DecisionCardModal.tsx`).
- **Added** Tamper-evident, immutable audit trail logging operator ID, action type, timestamp, and before/after states (`frontend/src/pages/audit-trail.tsx`).

#### Settlement Intelligence & Forecasting
- **Added** Working capital float projection and T+2 settlement delay forecasting (`backend/app/services/forecast_service.py`, `frontend/src/pages/settlement-intelligence.tsx`).

#### Evaluation Framework (Track 04 Benchmark)
- **Added** Autonomous benchmark runner evaluating batches of 50+ synthetic transactions.
- **Added** Real-time reporting of records processed, match rate, precision, recall, throughput (records/sec), and unresolved exception value.

#### Visual Identity & Workstation UI
- **Added** Complete branding suite: Midnight Navy & Electric Cyan palette, vector reconciliation emblem, and responsive two-column authentication panel.
- **Added** 3-Way Reconciliation Workstation with live filtering, CSV import modal, and status badges.

---

### Inherited Open-Source Foundation (From Securo v0.15.0)

- **FastAPI Backend Framework:** Base application bootstrapping, dependency injection, and asyncpg PostgreSQL pool.
- **Database Schema & Migrations:** Base Alembic migration pipeline and workspace data isolation.
- **Task Runner:** Celery task scheduler with Redis broker.
- **Authentication Scaffolding:** Base JWT handling and password hashing.
- **Frontend Infrastructure:** React 19, Vite, Tailwind CSS layout, Radix UI primitives, and dark/light mode toggle.
