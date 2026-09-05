# Security Model & Policy

**Project:** AdaptiveAI Finance Controller  
**Classification:** Security Architecture & Vulnerability Disclosure  
**Effective Date:** September 2026  

---

## 1. Security Architecture & Threat Model

AdaptiveAI Finance Controller processes sensitive commercial payment telemetry, merchant order books, and bank settlement statements. Security is architected into every layer:

### 1.1 Secrets & API Credential Isolation
- **Environment Separation:** All credentials (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, `GROQ_API_KEY`, `SECRET_KEY`) are managed strictly via environment variables or secret vaults.
- **Zero Hardcoded Secrets:** Code is scanned using pre-commit hooks and static analysis tools to prevent credential leakage.
- **Role Isolation:** Application components only have access to the credentials required for their specific function.

### 1.2 Razorpay Webhook Security & Idempotency
- **HMAC-SHA256 Signature Verification:** Every incoming webhook is cryptographically authenticated using the merchant's webhook secret before being handed to ingestion handlers.
- **Replay Protection:** Webhook event IDs (`X-Razorpay-Event-Id`) are tracked in Redis/PostgreSQL with expiration timestamps, immediately dropping replayed or duplicate payloads.
- **Timing Attack Resistance:** Signature comparisons utilize constant-time comparison algorithms (`hmac.compare_digest`).

### 1.3 Financial Data Isolation & Tenant Boundaries
- **Workspace-Level RBAC:** Every merchant entity is isolated by a strict `workspace_id` foreign key barrier enforced at the database query level.
- **Zero Cross-Tenant Leakage:** Queries automatically filter by the authenticated user's active workspace.

### 1.4 AI Reliability & Execution Sandboxing
- **Read-Only Context Injection:** The AI controller receives sanitized, read-only transaction context.
- **No Direct Mutation Authority:** The AI model cannot execute database writes or API refund calls directly. All AI outputs are treated as **untrusted proposals** requiring human-in-the-loop review.
- **Prompt Injection Defense:** Strict input sanitization prevents customer order notes or transaction descriptions from hijacking system instructions.

---

## 2. Supported Versions

| Version | Supported | Security Updates |
| :--- | :---: | :--- |
| `1.0.x` (Buildathon Release) | **YES** | Active security fixes |
| Upstream `< 0.15.0` | NO | Replaced by AdaptiveAI Controller |

---

## 3. Vulnerability Reporting & Responsible Disclosure

We appreciate responsible disclosure of any security vulnerabilities found in AdaptiveAI Finance Controller.

### How to Report
Please **do not report security issues via public GitHub issues**.

Submit your disclosure via:
- **Private Security Advisory:** Use the GitHub Security Advisory tab on the repository (`https://github.com/P-mohith230/Adaptive-AI-final/security/advisories/new`).
- **Security Contact:** Email: `pagadalamohith85@gmail.com`

### What to Include
- Detailed description of the vulnerability.
- Proof of Concept (PoC) or step-by-step reproduction instructions.
- Potential impact on merchant data or financial integrity.
- Proposed remediation (if available).

### Response SLA
- **Initial Acknowledgment:** Within 24-48 hours.
- **Severity Assessment & Triage:** Within 5 business days.
- **Coordinated Fix & Disclosure:** 30 to 90 days depending on severity.
