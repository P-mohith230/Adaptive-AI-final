# Contributing to AdaptiveAI Finance Controller

Thank you for your interest in contributing to **AdaptiveAI Finance Controller**!

This project is an enterprise-grade financial reconciliation, exception intelligence, and merchant operations platform built for the **Razorpay AI Buildathon (Track 04: AI Finance Controller)**.

---

## 1. Project Overview

AdaptiveAI Finance Controller autonomous closes the merchant finance-ops loop across three streams:
1. Internal Merchant ERP / Order Management System orders.
2. Razorpay Payment Gateway captures, fees, and settlements.
3. Bank statement settlement credits (MT940 / CAMT feeds).

We combine **deterministic mathematical matching** with **Groq Llama-3.3-70b AI exception investigation** and **human-in-the-loop decision cards**.

---

## 2. Development Philosophy

1. **Deterministic Financial Truth:** Arithmetic, fee calculations, and ledger balances are strictly computed by deterministic Python code. LLMs never calculate balances.
2. **Auditability by Design:** Every exception resolution, adjustment, and state mutation must leave an immutable record in the audit trail.
3. **Safety & Zero Disruption:** Real merchant money is at stake; all financial edge cases (negative values, currency conversions, decimal rounding) must be covered with tests.

---

## 3. Repository Structure

```text
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI route handlers (reconciliation, ledger, webhooks, evaluation)
│   │   ├── core/           # Config, database engine, security primitives
│   │   ├── models/         # SQLAlchemy ORM models (reconciliation batches, exceptions, audit)
│   │   ├── schemas/        # Pydantic validation schemas
│   │   └── services/       # Core business logic (reconciliation, Groq AI, forecast, evaluation)
│   └── tests/              # Pytest test suite
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable UI components, Decision Cards, Chat Drawer, Brand
│   │   ├── pages/          # Primary views (Workstation, Exceptions, Forecasting, Audit)
│   │   └── lib/            # API clients, hooks, and utilities
├── docs/                   # Architecture, security, evaluation, and provenance documentation
└── docker-compose.yml      # Local multi-container development stack
```

---

## 4. Development Environment

Follow [`docs/DEVELOPMENT.md`](./docs/DEVELOPMENT.md) for full setup instructions:
- Python 3.11+ with virtual environment (`requirements.txt`).
- Node.js 20+ / 22+ with npm.
- PostgreSQL 15+ & Redis 7+.

---

## 5. Branch Naming Conventions

Use clear, structured branch names:
- `feature/razorpay-reconciliation`
- `feature/exception-engine`
- `feature/decision-cards`
- `fix/webhook-idempotency`
- `fix/fee-rounding-precision`
- `docs/evaluation-benchmark`
- `test/synthetic-batch-runner`

---

## 6. Commit Convention

We enforce standard [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` A new feature or capability (e.g., `feat: add T+2 settlement delay forecasting`).
- `fix:` A bug fix (e.g., `fix: prevent duplicate event ingestion on webhook replay`).
- `refactor:` Code change that neither fixes a bug nor adds a feature.
- `docs:` Documentation changes only (e.g., `docs: update architecture manual`).
- `test:` Adding or updating tests.
- `chore:` Maintenance tasks, dependency updates, or build configs.
- `perf:` Performance optimizations (e.g., `perf: optimize 3-way match batch throughput`).
- `security:` Security hardening or secret isolation.

---

## 7. Pull Request Requirements

When submitting a Pull Request, you must complete the PR template with:
1. **Description:** Clear summary of changes.
2. **Problem & Solution:** What financial or operational issue this solves.
3. **Testing:** Commands executed and test results.
4. **Screenshots / Recordings:** Required for any frontend or UI modifications.
5. **Database Migration Notes:** If modifying SQLAlchemy models, include the Alembic revision.
6. **API Changes:** Document any additions or updates to FastAPI endpoints.
7. **Security Considerations:** Ensure no credentials, keys, or private tokens are leaked.

---

## 8. Financial Safety Rules

To maintain financial integrity, all contributors must adhere to the following non-negotiable rules:

- :x: **DO NOT use LLMs for authoritative financial arithmetic.** LLMs may explain discrepancies, but `decimal.Decimal` in Python must perform all calculations.
- :x: **DO NOT hardcode financial results or match rates.** All metrics must be computed dynamically from dataset inputs.
- :x: **DO NOT expose credentials.** Never commit Razorpay API keys, webhook secrets, or Groq tokens.
- :x: **DO NOT bypass reconciliation validation.** All match transitions must pass tolerance checks.
- :x: **DO NOT modify audit records silently.** The audit trail is write-only and tamper-evident.

---

## 9. AI Development Rules

- Any AI-generated code or prompts must be peer-reviewed.
- System prompts for the Groq AI Controller must specify strict ground-truth constraints to eliminate hallucinations.
- All AI responses exposed in the UI must clearly indicate that they are AI-generated suggestions subject to human approval.

---

## 10. Open-Source Attribution & License

- AdaptiveAI Finance Controller is a derivative work based on the open-source **Securo** project (`https://github.com/securo-finance/securo`), licensed under **GNU AGPL-3.0**.
- Contributors must respect upstream copyright notices and license obligations.
- Do not claim independent authorship of upstream code. See [`docs/OPEN_SOURCE_ATTRIBUTION.md`](./docs/OPEN_SOURCE_ATTRIBUTION.md).
