# AI Agent Technical Context & Operating Guidelines: Securo

> **Audience:** Autonomous AI coding agents, code generation models, and pair programmers.  
> **Purpose:** Authoritative rules, conventions, invariants, and guardrails to prevent regressions and maintain codebase integrity.

---

## 1. Project Purpose & High-Level Architecture

Securo is a privacy-first, self-hosted financial manager written in **Python (FastAPI + SQLAlchemy 2.0)** on the backend and **React 19 (TypeScript + Vite + Tailwind CSS v4)** on the frontend. It uses **PostgreSQL (with pgvector)** for relational and vector data, and **Redis + Celery** for asynchronous task execution.

Every record in Securo belongs to a **Workspace** (`personal` or `business`), and tenant isolation is enforced at the service and query layers via `workspace_id`.

---

## 2. Invariant Rules: Things You Must NEVER Do

1. **NEVER use Python `float` or JavaScript `number` for Money**:
   - In Python, ALWAYS use `decimal.Decimal`.
   - In PostgreSQL, ALWAYS use `Numeric(precision=15, scale=2)` or `Numeric(20, 10)` for FX rates.
   - In TypeScript, represent currency amounts as strings or format them using `@/lib/format.ts`.
2. **NEVER Query Financial Tables without `workspace_id`**:
   - Accounts, Transactions, Categories, Rules, Invoices, Payees, and Agents are workspace-scoped. Omitting `workspace_id` causes cross-tenant data leaks.
3. **NEVER Mutate Database State in Conversational AI Tools**:
   - AI agent tools in `backend/mcp_server/tools/proposals.py` MUST follow the **Propose-First Pattern**. They create preview payloads. The user clicks **Apply** in the web UI, which calls the standard REST API.
4. **NEVER Store Derived Invoicing Statuses**:
   - Invoices only store human decisions: `draft`, `open`, `void`, `uncollectible`.
   - Never create columns or migrations for `paid`, `partial`, or `overdue`. These MUST be computed dynamically via `invoice_service.derive_state()`.
5. **NEVER Trust LLMs to Sum Numbers**:
   - Models hallucinate arithmetic over lists of transactions. All financial aggregates must be calculated via SQL queries (such as the `aggregate` tool in `mcp_server/tools/aggregate.py`).

---

## 3. Directory Layout & Module Responsibilities

```
securo/
├── backend/
│   ├── alembic/versions/     # Migration scripts. MUST follow sequential naming (e.g., 086_...).
│   ├── app/
│   │   ├── api/              # FastAPI routers. Keep controllers thin; delegate to services.
│   │   ├── core/             # Auth, DB, config, workspace context, rate limiting.
│   │   ├── models/           # Declarative SQLAlchemy ORM entities using Mapped[T].
│   │   ├── schemas/          # Pydantic v2 schemas for request validation & serialization.
│   │   ├── services/         # Encapsulated domain business logic. Pure functions or async methods.
│   │   ├── tasks/            # Celery background tasks.
│   │   ├── providers/        # External sync providers (bank sync, market prices, FX).
│   │   └── agents/           # LLM providers, conversation storage, RAG embeddings, executor.
│   ├── mcp_server/           # Built-in Model Context Protocol server exposing tools to LLMs.
│   └── tests/                # Pytest suites. Run with aiosqlite in-memory database.
├── frontend/
│   ├── src/
│   │   ├── pages/            # Page-level components. Lazy-loaded in App.tsx.
│   │   ├── components/       # Reusable UI components. Use Radix primitives + Tailwind v4.
│   │   ├── contexts/         # AuthContext, WorkspaceContext, CollectionFilterContext.
│   │   ├── lib/api.ts        # Single source of truth for all frontend API calls.
│   │   └── types/index.ts    # Single source of truth for all TypeScript models.
```

---

## 4. Coding Conventions

### Backend (Python)
- **Typing**: Use standard Python 3.11+ type hints (`list[str]`, `dict[str, Any]`, `X | None`).
- **SQLAlchemy 2.0**:
  - Always use `Mapped[T]` and `mapped_column()`.
  - Use `select(Model).where(...)` syntax; avoid legacy query syntax.
  - For async operations, always use `await session.execute(...)` or `await session.scalar(...)`.
- **Error Handling**: Raise `fastapi.HTTPException(status_code=..., detail=...)` in API routers; raise domain exceptions in services.

### Frontend (TypeScript / React)
- **Components**: Functional components using React 19 hooks.
- **Server State**: Always use TanStack React Query (`useQuery`, `useMutation`).
- **Cache Invalidation**: After mutations, call helpers from `@/lib/invalidate-queries.ts` to keep the UI in sync.
- **Styling**: Use Tailwind CSS utility classes and `cn()` from `@/lib/utils.ts` for conditional class merging.

---

## 5. Development & Testing Commands

### Backend Commands
```powershell
# From backend directory with active .venv:
.\.venv\Scripts\Activate.ps1

# Run full test suite:
pytest

# Run a specific test file:
pytest tests/test_transactions_api.py

# Run database migrations:
alembic upgrade head

# Create a new migration revision:
alembic revision -m "add_reconciliation_tables"

# Lint and typecheck:
ruff check .
ty
```

### Frontend Commands
```bash
# From frontend directory:
npm run dev           # Start Vite dev server on port 5173
npm run test          # Run Vitest test suite
npm run typecheck     # Verify TypeScript types
npm run lint          # Run ESLint
npm run build         # Production bundle build
```

---

## 6. How to Extend Securo for Fintech & Buildathon Workflows

When implementing features such as an **AI Finance Controller**, follow these structural patterns:

1. **Adding a New Domain Model**:
   - Create `backend/app/models/new_entity.py` inheriting from `Base`.
   - Ensure `workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)`.
   - Export the model in `backend/app/models/__init__.py`.
   - Create an Alembic migration in `backend/alembic/versions/`.
2. **Adding Business Logic**:
   - Create `backend/app/services/new_entity_service.py`.
   - Accept `AsyncSession` and `workspace_id` as primary arguments.
3. **Exposing Endpoints**:
   - Create `backend/app/api/new_entity.py`.
   - Guard write operations with `ctx: WorkspaceContext = Depends(current_writable_workspace)`.
   - Register the router in `backend/app/main.py`.
4. **Exposing Tools to AI Agents**:
   - Define tools in `backend/mcp_server/tools/new_tools.py` using the `@tool` decorator.
   - For mutation actions, prefix the tool with `propose_` and return structured proposal dictionaries.
   - Register the tool in `backend/mcp_server/main.py`.
5. **Connecting Frontend Views**:
   - Add API methods in `frontend/src/lib/api.ts`.
   - Add TypeScript types in `frontend/src/types/index.ts`.
   - Create pages in `frontend/src/pages/` and register lazy routes in `frontend/src/App.tsx`.
