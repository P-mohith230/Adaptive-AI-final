# AdaptiveAI Finance Controller: Technical Architecture Manual

> **Product Name:** AdaptiveAI Finance Controller  
> **Target Track:** Razorpay AI Buildathon 2026 — Track 04 (AI Finance Controller)  
> **Positioning:** *"From transaction data to verified financial intelligence."*  
> **Foundation:** Securo Open-Source Finance Engine (AGPL-3.0)

---

## 1. Executive Summary & Challenge Mandate

AdaptiveAI Finance Controller is an autonomous merchant financial control and reconciliation platform built specifically to satisfy the **Razorpay Buildathon Track 04** challenge:

> *"Build an agent that closes one finance-ops loop across a 50+ record batch of synthetic data, reporting its match rate and the exceptions it could not resolve."*

Modern businesses struggle with the gap between:
1. **Internal Expected Orders (Merchant ERP/Ledger):** Orders placed, invoice commitments, promised net revenue.
2. **Payment Gateway Captures (Razorpay):** Transactions authorized, fees deducted, international card surcharges, tax withholdings.
3. **Bank Settlements (Payouts):** Net deposits, UTR numbers, settlement timing windows (T+1/T+2).

AdaptiveAI Finance Controller automates this entire loop through **deterministic 3-way reconciliation**, **AI-driven exception investigation**, **financial-impact prioritization**, **human-in-the-loop review**, and an **immutable audit trail**.

---

## 2. High-Level System Architecture

```
                       ┌─────────────────────────────────────┐
                       │   Razorpay Gateway (API / Webhook)  │
                       │   Payments • Settlements • Refunds  │
                       └──────────────────┬──────────────────┘
                                          │
                                          ▼
                       ┌─────────────────────────────────────┐
                       │      Razorpay Connector Layer       │
                       │ • Test-Mode REST Client             │
                       │ • HMAC-SHA256 Signature Verify      │
                       │ • Idempotency Guard (Deduplication) │
                       └──────────────────┬──────────────────┘
                                          │
                                          ▼
                       ┌─────────────────────────────────────┐
                       │    Event / Data Normalizer Layer    │
                       │ Converts raw paise to INR Decimals  │
                       └──────────────┬───────────────┬──────┘
                                      │               │
                                      ▼               ▼
                       ┌─────────────────────┐ ┌─────────────────────┐
                       │ Canonical Database  │ │   Merchant Ledger   │
                       │ (Razorpay Gateway)  │ │  (Expected Orders)  │
                       └──────────────┬──────┘ └──────┬──────────────┘
                                      │               │
                                      └───────┬───────┘
                                              │
                                              ▼
                       ┌─────────────────────────────────────┐
                       │   DETERMINISTIC 3-WAY MATCH ENGINE  │
                       │  Python Decimal Exact Arithmetic    │
                       │  Zero LLM Hallucinations / Rounding │
                       └──────────────────┬──────────────────┘
                                          │
                     ┌────────────────────┴────────────────────┐
                     │                                         │
                     ▼                                         ▼
        ┌─────────────────────────┐               ┌─────────────────────────┐
        │     AUTO_RECONCILED     │               │       EXCEPTIONS        │
        │   Matches All Rules     │               │  Mismatches, Fees, Etc. │
        └─────────────────────────┘               └────────────┬────────────┘
                                                               │
                                                               ▼
                                                  ┌─────────────────────────┐
                                                  │ AI EXCEPTION CONTROLLER │
                                                  │ • Root-Cause Classifier │
                                                  │ • Evidence Synthesizer  │
                                                  │ • Confidence Scorer     │
                                                  │ • Action Recommender    │
                                                  └────────────┬────────────┘
                                                               │
                                                               ▼
                                                  ┌─────────────────────────┐
                                                  │   HUMAN-IN-THE-LOOP     │
                                                  │ Transaction Decision    │
                                                  │ Card: [Approve][Reject] │
                                                  └────────────┬────────────┘
                                                               │
                                                               ▼
                                                  ┌─────────────────────────┐
                                                  │   IMMUTABLE AUDIT LOG   │
                                                  │ Append-Only Compliance  │
                                                  └─────────────────────────┘
```

---

## 3. The 3-Way Reconciliation Engine

The reconciliation engine operates on three independent data feeds:
- `MerchantLedgerEntry`: Expected order details, gross amount, expected fee schedule, promised net.
- `CanonicalTransaction (Payment)`: Captured payment ID, authorized amount, deducted MDR fee, GST, payment method.
- `CanonicalTransaction (Settlement)`: Bank settlement ID, payout amount, settlement timing.

### Verification Rule Bitmask
1. `order_matched`: Order ID in merchant ledger matches Razorpay order reference.
2. `payment_matched`: Payment ID captured and authorized by gateway.
3. `currency_matched`: Currency codes match (default `INR`).
4. `amount_matched`: Base transaction amount matches within tolerance threshold ($\le ₹0.50$).
5. `fee_matched`: Deducted gateway fee matches expected MDR schedule ($\le ₹2.00$ tolerance).
6. `settlement_found`: Valid settlement transaction found linking the payment to bank payout.
7. `timing_acceptable`: Captured transaction is within normal settlement delay ($\le 2$ days).
8. `is_duplicate`: Zero redundant payments for the same order reference.

### Exception Taxonomy
| Status Code | Description | Typical Root Cause |
| :--- | :--- | :--- |
| `AUTO_RECONCILED` | All 8 rules satisfied | Clean payment and settlement matching expectations. |
| `MISMATCH` | Order ID matches, but captured amount differs | Applied partial discount code, currency conversion discrepancy, or order modification. |
| `FEE_DISCREPANCY` | Base amount matches, but fee delta $> ₹2.00$ | International card surcharge, corporate card tier, or dynamic MDR rate change. |
| `MISSING_SETTLEMENT` | Payment captured $>3$ days ago with no settlement | Bank account hold, compliance verification, or batch settlement failure. |
| `TIMING_DIFFERENCE` | Payment captured recently ($<2$ days) pending payout | Standard T+1 / T+2 settlement sweep cycle. No financial risk. |
| `DUPLICATE` | Multiple payment IDs for a single order reference | Customer double-clicked checkout button or retry race condition. |
| `MISSING_PAYMENT` | Order exists in merchant ledger with no gateway charge | Abandoned checkout or paid via out-of-band payment channel. |
| `UNRESOLVED` | Insufficient cross-system matching attributes | Corrupted identifier or complex multi-order refund requiring manual review. |

---

## 4. AI Exception Controller & Evidence Synthesis

The AI Controller does **NOT** perform arithmetic. All differences and exposures are computed deterministically. The AI agent performs **root-cause classification, structured evidence synthesis, confidence estimation, and action recommendation**.

### Signature "Transaction Decision Card" Data Structure
```json
{
  "record_id": "8a52f9c1-...",
  "order_id": "order_DEMO_1012",
  "payment_id": "pay_DEMO_9128",
  "settlement_id": "set_DEMO_4182",
  "expected_amount": "28000.00",
  "actual_amount": "25000.00",
  "amount_variance": "3000.00",
  "expected_fee": "660.80",
  "actual_fee": "590.00",
  "financial_exposure": "3000.00",
  "checks": {
    "order_matched": true,
    "payment_matched": true,
    "currency_matched": true,
    "amount_matched": false,
    "fee_matched": true,
    "settlement_found": true
  },
  "ai_classification": "AMOUNT_MISMATCH",
  "ai_confidence": "0.9820",
  "ai_reason": "Merchant ledger expected ₹28,000.00 for order order_DEMO_1012, but Razorpay captured ₹25,000.00. Numerical variance of ₹3,000.00 (undercharged).",
  "ai_recommendation": "Verify order pricing in merchant system or check if a partial promo code / coupon was applied at checkout.",
  "evidence_items": [
    {
      "source": "Merchant Internal Ledger",
      "reference": "Order #order_DEMO_1012",
      "expected_amount": "₹28,000.00",
      "expected_fee": "₹660.80",
      "date": "2026-09-02 14:15:00 UTC"
    },
    {
      "source": "Razorpay Payment Gateway",
      "reference": "Payment ID pay_DEMO_9128",
      "captured_amount": "₹25,000.00",
      "gateway_fee": "₹590.00",
      "status": "captured",
      "date": "2026-09-02 14:16:12 UTC"
    }
  ]
}
```

---

## 5. Financial-Impact-Aware Prioritization

Exceptions are prioritized based on financial risk:
$$\text{Priority Score} = \text{Financial Exposure} \times \text{Risk Weight} \times \text{Aging Factor}$$

- **High Priority:** Amount mismatches and duplicate payments directly affecting merchant revenue ($₹1,000+$).
- **Medium Priority:** Missing settlements past the T+2 bank payout window.
- **Low Priority:** Timing differences within the normal settlement cycle.

---

## 6. Webhook Idempotency & Gateway Resilience

1. **HMAC Signature Verification:** Incoming webhooks validate `X-Razorpay-Signature` against `RAZORPAY_WEBHOOK_SECRET` via `hmac.new(sha256)`.
2. **Idempotency Guard:** Every event ID is logged in `razorpay_webhook_events`. If a duplicate arrives, the system safely ignores it with HTTP 200 OK and flags `is_duplicate = true`.
3. **Exponential Backoff:** The Razorpay client automatically handles rate-limiting (HTTP 429) and network failures using exponential backoff retry.

---

## 7. Open-Source Attribution

This project builds upon the **Securo** personal and business finance repository:
- **Original Project:** Securo Finance (`securo-finance/securo`)
- **License:** GNU Affero General Public License v3.0 (AGPL-3.0)
- **Modifications for Razorpay Track 04:**
  - Razorpay REST API connector and webhook idempotency handler
  - Merchant internal expected ledger
  - Canonical financial transaction normalization
  - Deterministic 3-way reconciliation engine
  - AI exception investigator and evidence synthesizer
  - Financial-impact prioritization
  - Human-in-the-loop transaction decision card
  - Immutable audit trail
  - 50–250 record dynamic evaluation harness
