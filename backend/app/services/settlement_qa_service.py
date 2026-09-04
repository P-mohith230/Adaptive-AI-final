import logging
import os
import re
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.reconciliation import (
    ReconciliationBatch,
    ReconciliationException,
    ReconciliationRecord,
)
from app.services.reconciliation_ledger_bridge import ReconciliationLedgerBridge

logger = logging.getLogger(__name__)


class SettlementQAService:
    """Settlement Q&A Agent for Razorpay Track 04.
    Answers natural language queries about settlements, fee structures, discrepancies,
    payout delays, and forward cash positions.
    Integrates with Groq API when GROQ_API_KEY is configured, or runs via
    deterministic domain-financial reasoning.
    """

    @classmethod
    async def ask_settlement_agent(
        cls,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        question: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        question_lower = question.lower().strip()

        # 1. Gather live context
        latest_batch = await session.scalar(
            select(ReconciliationBatch)
            .where(ReconciliationBatch.workspace_id == workspace_id)
            .order_by(desc(ReconciliationBatch.created_at))
            .limit(1)
        )

        cash_fc = await ReconciliationLedgerBridge.calculate_cash_position_forecast(
            session=session,
            workspace_id=workspace_id,
        )

        records = []
        if latest_batch:
            records = (
                await session.scalars(
                    select(ReconciliationRecord)
                    .options(selectinload(ReconciliationRecord.exception))
                    .where(ReconciliationRecord.batch_id == latest_batch.id)
                )
            ).all()

        exceptions = [r for r in records if r.status != "AUTO_RECONCILED"]

        # Check if GROQ_API_KEY is available (from Settings, os.environ, or .env file)
        settings = get_settings()
        groq_api_key = getattr(settings, "groq_api_key", "") or os.environ.get("GROQ_API_KEY", "")
        if not groq_api_key:
            # Fallback to direct file inspection if process environment was initialized before .env edit
            for env_candidate in [
                Path(__file__).resolve().parents[2] / ".env",
                Path(__file__).resolve().parents[3] / ".env",
            ]:
                if env_candidate.exists():
                    try:
                        for line in env_candidate.read_text(encoding="utf-8").splitlines():
                            line_strip = line.strip()
                            if line_strip.startswith("GROQ_API_KEY="):
                                groq_api_key = line_strip.split("=", 1)[1].strip().strip("\"'")
                                break
                    except Exception as env_err:
                        logger.debug(f"Could not read {env_candidate}: {env_err}")
                if groq_api_key:
                    break

        if groq_api_key and len(groq_api_key) > 10:
            preferred_model = getattr(settings, "groq_model", "") or os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
            candidate_models = [
                preferred_model,
                "openai/gpt-oss-120b",
                "qwen/qwen3.8-27b",
                "openai/gpt-oss-20b",
                "groq/compound",
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
            ]
            models_to_try = list(dict.fromkeys(m for m in candidate_models if m))

            system_prompt = (
                "You are the Chief AI Finance Controller for an Indian enterprise merchant processing via Razorpay on Securo. "
                "You are professional, articulate, polite, and financially astute.\n\n"
                "Guidelines:\n"
                "- If the user is greeting you (e.g. 'hi', 'hello', 'hey', 'good morning'), introducing themselves (e.g. 'my name is Mohith'), "
                "or asking conversational questions ('who are you?', 'how are you?', 'what is my name?'):\n"
                "  * Respond conversationally, naturally, and warmly.\n"
                "  * Acknowledge their greeting or name directly and politely (e.g. 'Hello Mohith! Great to meet you. I am your Securo AI Finance Controller...').\n"
                "  * Briefly offer to assist with payment reconciliation, settlement tracking, Razorpay MDR fees, or cash position forecasting.\n"
                "  * DO NOT dump giant unsolicited financial tables or audit memos on simple conversational greetings.\n"
                "- When the user asks about financial data, reconciliation, match rates, orders, anomalies, cash flow, or settlements:\n"
                "  * Use the provided verified multi-source financial context to answer accurately with exact figures in INR, root-cause diagnosis, and actionable resolution steps.\n"
                "- Maintain conversational continuity: remember and refer to the user's name and previous messages in the conversation when appropriate."
            )

            messages_payload = [{"role": "system", "content": system_prompt}]

            # Add multi-turn conversation history
            if history:
                for item in history[-8:]:
                    h_role = "user" if item.get("role") == "user" else "assistant"
                    h_content = item.get("content", "")
                    if h_content and isinstance(h_content, str):
                        # Filter out internal prompt prefixes if they were echoed
                        clean_content = h_content.strip()
                        if clean_content:
                            messages_payload.append({"role": h_role, "content": clean_content})

            user_message_content = f"""Verified Multi-Source Financial Context (Ground-Truth Ledger State):
- Batch Total Records: {latest_batch.total_records if latest_batch else 0}
- Match Rate: {float(latest_batch.match_rate) * 100 if latest_batch else 0:.1f}%
- Unresolved Exceptions: {len(exceptions)}
- Trapped Financial Exposure: INR {latest_batch.financial_exposure if latest_batch else 0}
- Liquid Bank Balance (HDFC Operating A/C): INR {cash_fc['liquid_bank_balance']}
- In-Transit Gateway Float: INR {cash_fc['in_transit_clearing_balance']}
- Net Cash Position: INR {cash_fc['net_cash_position']}
- Key Exceptions: {[f"Order {e.order_id}: {e.status} (Exposure: INR {e.financial_impact})" for e in exceptions[:5]]}

User Query:
"{question}"
"""
            messages_payload.append({"role": "user", "content": user_message_content})

            async with httpx.AsyncClient(timeout=25.0) as client:
                for model in models_to_try:
                    try:
                        req_payload = {
                            "model": model,
                            "messages": messages_payload,
                            "temperature": 0.3,
                            "max_tokens": 800,
                        }
                        headers = {
                            "Authorization": f"Bearer {groq_api_key}",
                            "Content-Type": "application/json",
                            "User-Agent": "Securo-Finance-Controller/1.0",
                        }
                        resp = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            json=req_payload,
                            headers=headers,
                        )
                        if resp.status_code == 200:
                            resp_json = resp.json()
                            answer = resp_json["choices"][0]["message"]["content"]
                            logger.info(f"Groq settlement QA query succeeded with model {model}")
                            return {
                                "answer": answer,
                                "provider": f"Groq AI ({model})",
                                "sources": [
                                    "Razorpay Gateway API",
                                    "HDFC Bank Statement (MT940)",
                                    "Securo Multi-Source General Ledger",
                                ],
                            }
                        else:
                            logger.warning(
                                f"Groq model {model} returned HTTP {resp.status_code}: {resp.text}"
                            )
                            if resp.status_code in (400, 404):
                                continue
                            else:
                                break
                    except Exception as groq_err:
                        logger.warning(f"Groq API call failed for model {model}: {groq_err}")
                        continue

        # 2. Local Deterministic Financial NLP Engine (100% offline reliable)
        # Case A: Name Introduction (e.g., "my name is Mohith", "i am Mohith", "call me Mohith")
        name_match = re.search(r"(?:my name is|i am|call me)\s+([a-zA-Z]+)", question_lower)
        if name_match:
            user_name = name_match.group(1).capitalize()
            return {
                "answer": (
                    f"Hello **{user_name}**! Pleasure to meet you.\n\n"
                    f"I am your **Securo AI Finance Controller**. I monitor your multi-rail payment flows across "
                    f"Merchant Order Ledgers, Razorpay Gateway settlements, and HDFC bank accounts.\n\n"
                    f"Currently, your workspace has a verified **{float(latest_batch.match_rate) * 100 if latest_batch else 0:.1f}% match rate** "
                    f"across {latest_batch.total_records if latest_batch else 0} records. How can I assist you today?"
                ),
                "provider": "AI Finance Controller (Deterministic Engine)",
                "sources": ["Securo Workspace Session"],
            }

        # Case B: Greetings (e.g., "hi", "hello", "hey", "good morning")
        greeting_tokens = ["hi", "hello", "hey", "good morning", "good evening", "good afternoon", "greetings", "howdy", "sup"]
        if any(question_lower == g or question_lower.startswith(f"{g} ") or question_lower.startswith(f"{g},") or question_lower.startswith(f"{g}!") for g in greeting_tokens):
            return {
                "answer": (
                    f"Hello! Great to connect with you.\n\n"
                    f"I am your **AdaptiveAI Finance Controller**. I can help you with:\n"
                    f"- **3-Way Reconciliation & Exceptions:** Inspect why specific orders failed or analyze your current {float(latest_batch.match_rate) * 100 if latest_batch else 0:.1f}% match rate.\n"
                    f"- **MDR Fee & GST Audits:** Verify contractual 2% + 18% GST deductions against gateway debits.\n"
                    f"- **Settlement Tracking & Cash Forecasting:** Monitor liquid bank cash (₹{cash_fc['liquid_bank_balance']:,.2f}) and in-transit float.\n\n"
                    f"What would you like to explore?"
                ),
                "provider": "AI Finance Controller (Deterministic Engine)",
                "sources": ["Securo Workspace Session"],
            }

        # Case C: Identity Inquiry (e.g., "who are you", "what can you do", "what is your name")
        if any(w in question_lower for w in ["who are you", "what can you do", "what are you", "your name"]):
            return {
                "answer": (
                    f"I am the **AdaptiveAI Finance Controller** for Securo.\n\n"
                    f"I autonomously close the finance-operations loop for merchant payment processing via Razorpay by:\n"
                    f"1. **Reconciling 3-way transactions** (Merchant Orders vs. Gateway captured payments vs. Bank MT940 credits).\n"
                    f"2. **Diagnosing root causes** for fee discrepancies, missing settlements, and timing differences.\n"
                    f"3. **Providing real-time liquidity forecasting** and exposure prioritization with zero arithmetic hallucinations.\n\n"
                    f"Ask me about any specific order (e.g. `order_DEMO_1012`), fee deductions, or current cash positions."
                ),
                "provider": "AI Finance Controller (Deterministic Engine)",
                "sources": ["Securo Multi-Source Ledger"],
            }

        # Case D: Cash position / forecasting
        if any(w in question_lower for w in ["cash", "liquidity", "forecast", "position", "bank balance", "float"]):
            answer = (
                f"**Cash Position & Liquidity Summary:**\n"
                f"- **Verified Liquid Bank Cash (HDFC):** ₹{cash_fc['liquid_bank_balance']:,.2f}\n"
                f"- **In-Transit Gateway Float (T+2 cutoff):** ₹{cash_fc['in_transit_clearing_balance']:,.2f}\n"
                f"- **At-Risk Trapped Exceptions:** ₹{cash_fc['at_risk_trapped_exposure']:,.2f}\n"
                f"- **Net Reliable Working Capital:** ₹{cash_fc['net_cash_position']:,.2f}\n\n"
                f"*Projected Inflow for next business day:* ₹{cash_fc['daily_forecast_7d'][0]['expected_settlement_inflow']:,.2f} scheduled via NEFT/RTGS settlement batch."
            )
            return {
                "answer": answer,
                "provider": "AI Finance Controller (Deterministic Engine)",
                "sources": ["HDFC Operating Ledger", "Razorpay Clearing Account"],
            }

        # Case E: Specific order query (e.g., "order 1012" or "order_DEMO_1012")
        order_match = re.search(r"(\d{4})", question)
        if order_match:
            num = order_match.group(1)
            target = next((r for r in records if num in r.order_id), None)
            if target:
                reason = target.exception.reason if target.exception else "No anomaly recorded."
                rec_action = target.exception.recommendation if target.exception else "Auto-reconciled cleanly."
                answer = (
                    f"**Audit Finding for Order {target.order_id}:**\n"
                    f"- **Reconciliation Status:** `{target.status}`\n"
                    f"- **Expected (Merchant Ledger):** ₹{target.amount_delta + (target.payment_transaction_id and Decimal('0') or target.financial_impact):,.2f}\n"
                    f"- **Financial Exposure:** ₹{target.financial_impact:,.2f}\n"
                    f"- **Diagnosis:** {reason}\n"
                    f"- **Recommended Controller Action:** {rec_action}"
                )
                return {
                    "answer": answer,
                    "provider": "AI Finance Controller (Audit Synthesizer)",
                    "sources": [f"Order Record {target.order_id}", "Exception Engine"],
                }

        # Case F: Fees & MDR questions
        if any(w in question_lower for w in ["fee", "mdr", "gst", "commission", "charge", "tax"]):
            fee_exceptions = [e for e in exceptions if e.status == "FEE_DISCREPANCY"]
            answer = (
                f"**Fee & Commission Analysis:**\n"
                f"- Standard contracted MDR rate: **2.00% + 18% GST** (effective 2.36% on gross sales).\n"
                f"- In the latest batch of {latest_batch.total_records if latest_batch else 0} transactions, "
                f"we identified **{len(fee_exceptions)} fee anomalies** (e.g., unauthorized 3.5% international card surcharges).\n"
                f"- Total excess fee deduction flagged for dispute: **₹{sum(e.financial_impact for e in fee_exceptions):,.2f}**.\n"
                f"- *Recommendation:* Auto-generate dispute ticket with Razorpay Merchant Operations citing contractual schedule."
            )
            return {
                "answer": answer,
                "provider": "AI Finance Controller (Deterministic Engine)",
                "sources": ["Fee Schedule Contract", "Payment Webhook Raw Logs"],
            }

        # Case G: Missing settlements or payout delays
        if any(w in question_lower for w in ["delay", "missing", "settle", "utr", "unsettled", "payout"]):
            missing = [e for e in exceptions if e.status in ("MISSING_SETTLEMENT", "TIMING_DIFFERENCE")]
            answer = (
                f"**Settlement & Payout Audit:**\n"
                f"- **{len(missing)} transactions** have not yet settled into the HDFC bank operating account.\n"
                f"- Total unsettled capital: **₹{sum(e.financial_impact for e in missing):,.2f}**.\n"
                f"- Breakdown: Transactions captured within T+2 cutoff are classified as *In-Transit Liquidity*. "
                f"Transactions exceeding 48 hours without UTR generation are flagged as *Missing Settlements* requiring bank inquiry."
            )
            return {
                "answer": answer,
                "provider": "AI Finance Controller (Deterministic Engine)",
                "sources": ["HDFC Bank MT940 Feed", "Razorpay Settlement APIs"],
            }

        # Case H: General Executive Summary
        return {
            "answer": (
                f"**Executive Briefing:**\n"
                f"- Current batch match rate: **{float(latest_batch.match_rate) * 100 if latest_batch else 0:.1f}%**.\n"
                f"- Total processed: **{latest_batch.total_records if latest_batch else 0} transactions**.\n"
                f"- Total unresolved exceptions: **{len(exceptions)} items** with an exposure of **₹{latest_batch.financial_exposure if latest_batch else 0:,.2f}**.\n"
                f"- Liquid cash available today: **₹{cash_fc['liquid_bank_balance']:,.2f}**.\n"
                f"All clean records have been automatically synchronized to your Securo general ledger (`/transactions` and `/accounts`)."
            ),
            "provider": "AI Finance Controller (Deterministic Engine)",
            "sources": ["Securo Multi-Source Ledger"],
        }
