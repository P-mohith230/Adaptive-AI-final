# Securo: Developer & Architecture Master Manual (Historical Upstream Reference)

> **HISTORICAL REFERENCE NOTICE:**  
> This document is an archived historical technical manual from the upstream **Securo** project (`v0.15.0`). It is retained for open-source architectural reference and provenance tracking under the GNU AGPL-3.0.  
> **For the active AdaptiveAI Finance Controller project, please refer to the root [README.md](../../README.md) and [docs/ARCHITECTURE.md](../ARCHITECTURE.md).**

---

**Securo** is a self-hosted, privacy-first personal and business finance platform. It runs on your own infrastructure, offering full financial visibility across accounts, transactions, investments, and invoices without surrendering a single byte to third parties.

---

## 1. System Overview & Problem Solved

Traditional finance applications monetize user financial data, lock users into proprietary clouds, and provide rigid, one-size-fits-all accounting. Securo solves this by providing:
- **Absolute Data Sovereignty**: Self-hosted under the GNU AGPL-3.0 license.
- **Unified Personal & Business Ledger**: Granular workspaces with strict role-based data isolation.
- **Intelligent Ingestion**: Robust multi-format statement parser (OFX, QIF, CAMT.053, CSV) with deterministic SHA-256 deduplication.
- **Autonomous AI Capabilities**: Local-first AI assistants integrated via the Model Context Protocol (MCP), providing zero-hallucination server-side financial queries, structured mutation proposals with human-in-the-loop verification, and private RAG.

---

## 2. Technology Stack & Key Libraries

| Component | Technology | Role in Securo |
|---|---|---|
| **Frontend Framework** | React 19.2 + TypeScript + Vite 8.2 | Single-page application with lazy-loaded route chunking |
| **Styling & Components**| Tailwind CSS v4 + Radix UI Primitives | Modern dark-mode interface with customizable design tokens |
| **Frontend State** | TanStack React Query v5 + Context API | Server-state caching, automatic invalidation, and UI context |
| **Data Visualization** | Recharts v3.7 | Interactive Net Worth trends, cash flow, and category sparklines |
| **Backend Framework** | FastAPI 0.141 + Starlette | High-performance asynchronous REST API with OpenAPI generation |
| **Data Layer** | SQLAlchemy 2.0 (Async) + asyncpg | Type-safe declarative ORM with connection pooling |
| **Migrations** | Alembic 1.19 | Sequential schema versioning (85 migrations) |
| **Database** | PostgreSQL 16/18 with `pgvector` | Relational tables, JSON documents, and vector embeddings |
| **Async Queue** | Redis 8 + Celery 5.6 | Background bank synchronization, FX updates, and recurring tasks |
| **Authentication** | FastAPI Users, WebAuthn, PyOTP, PyJWT | Passkeys, TOTP 2FA, JWT sessions, and OIDC Single Sign-On |
| **Document Generation** | ReportLab 5.0 | High-fidelity invoice PDF rendering without native C dependencies |
| **AI Runtime** | Anthropic / OpenAI / Ollama / FastEmbed | Local embeddings, MCP JSON-RPC tool calling, and SSE chat |

---

## 3. Repository Directory Structure

```
securo/
├── backend/
│   ├── alembic/              # 85 schema migrations
│   ├── app/
│   │   ├── api/              # 38 FastAPI router modules
│   │   ├── core/             # Auth, DB engine, config, rate limiting, workspace isolation
│   │   ├── models/           # 30 Declarative SQLAlchemy 2.0 ORM models
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── services/         # 42 Business logic, calculations, and rule services
│   │   ├── tasks/            # Celery asynchronous worker tasks
│   │   ├── providers/        # Bank sync adapters (Pluggy, Enable Banking, SimpleFIN)
│   │   └── agents/           # AI runtime, MCP client, and RAG services
│   ├── mcp_server/           # Standalone Model Context Protocol JSON-RPC 2.0 tool server
│   └── tests/                # 141 comprehensive pytest modules
├── frontend/
│   ├── src/
│   │   ├── pages/            # 31 View pages (Dashboard, Invoices, Transactions, etc.)
│   │   ├── components/       # 78 Reusable UI components, charts, and dialogs
│   │   ├── contexts/         # React Contexts (Auth, Workspace, Collection Filters)
│   │   ├── lib/              # Axios client (api.ts), formatters, i18n
│   │   └── types/            # TypeScript interface definitions
├── docs/                     # Architectural specifications and diagrams
├── start-securo.ps1          # One-click native Windows startup script
└── stop-securo.ps1           # One-click native Windows shutdown script
```

---

## 4. How the System Works

### 1. Workspace Multi-Tenancy & Isolation
Every financial record (`Account`, `Transaction`, `Invoice`, `Category`, `Rule`, `Agent`) is scoped to a `workspace_id`. The client sends the active workspace via the `X-Workspace-Id` HTTP header. The backend dependency `current_writable_workspace` validates that the authenticated user possesses `owner`, `editor`, or `manager` privileges before permitting mutations.

### 2. Statement Ingestion & Deduplication
When statements are imported:
1. `import_service.py` normalizes file encodings and repairs malformed SGML/XML tags.
2. Missing IDs receive a deterministic SHA-1 hash.
3. Every record is checked against the database using external IDs or composite transaction hashes:
   $$\text{Hash} = \text{SHA256}(\text{account\_id} + \text{date} + \text{amount} + \text{description})$$
4. The rule engine evaluates conditions (merchant names, amount bounds) and assigns categories, payees, or transfer flags before committing.

### 3. Invoicing Ledger System
Securo decouples stored human decisions from derived financial facts:
- **Stored Status**: `draft` (unissued), `open` (issued), `void` (cancelled), `uncollectible` (written off).
- **Derived State**: Computed dynamically based on allocations and due dates (`paid`, `partial`, `overdue`).
- **Allocations**: The `invoice_allocations` table links real bank transaction credits to invoices, recording the reconciliation strategy used.

### 4. AI Agents & Model Context Protocol (MCP)
- **Tool-Driven Execution**: Agents discover capabilities from the built-in MCP server (`localhost:8765/mcp`).
- **Zero-Hallucination Mathematics**: System prompts forbid models from doing mental math over transaction lists; they must query the SQL-backed `aggregate` tool.
- **The Propose-First Safety Pattern**: Action tools (`propose_create_transaction`, `propose_categorize`, etc.) do not execute writes. They return structured previews that the web client renders as interactive diff cards with **Apply** buttons.
- **Embedded RAG**: Documents uploaded to agents are chunked and embedded using FastEmbed (`paraphrase-multilingual-MiniLM-L12-v2`), indexed via vector similarity in PostgreSQL, and retrieved via `search_knowledge_base`.

---

## 5. Local Setup & Execution

### Option A: Native Windows / PowerShell (Recommended for Non-Docker Environments)
This repository includes automated scripts to run PostgreSQL and Redis in user-space via Scoop without requiring Administrator privileges:

1. **Start all services**:
   ```powershell
   .\start-securo.ps1
   ```
2. **Access the application**:
   - Web App: [http://localhost:5173](http://localhost:5173)
   - FastAPI Documentation: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
3. **Stop all services**:
   ```powershell
   .\stop-securo.ps1
   ```

### Option B: Docker Compose
If you have Docker Desktop installed:
```bash
cp .env.example .env
docker compose up --build
```
Open [http://localhost:3000](http://localhost:3000) and complete the initial setup wizard.

---

## 6. Running Automated Tests

### Backend Tests
```bash
cd backend
.\.venv\Scripts\Activate.ps1
pytest -v
```

### Frontend Tests
```bash
cd frontend
npm run test
npm run typecheck
npm run lint
```

---

## 7. Extension Architecture for Fintech & Buildathons

Securo was architected with modular seams specifically suited for extending into an **AI Finance Controller**:

1. **Multi-Source Reconciliation**: Extend `backend/app/services/import_service.py` and `invoice_service.py` with an automated 3-way reconciliation engine matching payment gateway transaction logs, bank settlements, and merchant order records.
2. **Settlement Q&A Agent**: Expose custom tools in `backend/mcp_server/tools/` allowing the AI runtime to query settlement delays, fee breakdowns, and payout batch discrepancies using natural language.
3. **Cash Flow Forecaster**: Extend `backend/app/services/report_service.py` to project 30/60/90-day liquidity balances by combining actual bank balances with pending receivables and recurring commitments.
4. **Jurisdiction Tax Matching**: Add an Indian fiscal pack (`backend/app/fiscal/packs/in.py`) supporting GSTIN validation, HSN/SAC verification, and automated TDS deductions.

---

## 8. License

Securo is licensed under the [GNU Affero General Public License v3.0](LICENSE). Any modifications or derivative works used over a network service must also be made publicly available under the AGPL-3.0.
