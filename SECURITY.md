# Security Policy

## Supported Versions

| Version | Supported |
| :--- | :---: |
| 1.0.x (AdaptiveAI Finance Controller) | :white_check_mark: |
| < 1.0.0 (Legacy Upstream) | :x: |

---

## Reporting a Vulnerability

If you discover a security vulnerability in **AdaptiveAI Finance Controller**, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please submit a report through:
1. **GitHub Private Vulnerability Reporting:** Open an advisory on the repository under Security > Advisories.
2. **Security Contact Email:** `pagadalamohith85@gmail.com`

### What to Include
- Detailed description of the vulnerability.
- Precise steps to reproduce or a Proof of Concept (PoC).
- Affected endpoints or components.
- Potential impact on merchant financial data, reconciliation integrity, or secrets.
- Suggested fix (if any).

### Response SLA
- **Acknowledgment:** Within 48 hours.
- **Triage & Status Update:** Within 7 business days.
- **Remediation & Coordinated Release:** Coordinated with the reporter prior to public announcement.

---

## Financial Data & Secret Safety
- **Never commit real credentials:** Ensure `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, and `GROQ_API_KEY` are kept in local `.env` files and never pushed to source control.
- **Webhook Authenticity:** Always verify HMAC-SHA256 signatures on all incoming webhook callbacks.
- **AI Safety:** Large Language Models are strictly explanatory; all financial math and transaction approvals must pass deterministic verification and human-in-the-loop review.

For detailed security architecture and threat models, see [`docs/SECURITY.md`](./docs/SECURITY.md).
