export interface ReconciliationBatch {
  id: string
  workspace_id: string
  batch_code: string
  dataset_type: string
  total_records: number
  matched_records: number
  auto_reconciled: number
  ai_assisted: number
  unresolved_count: number
  match_rate: string | number
  precision_rate: string | number
  recall_rate: string | number
  financial_exposure: string | number
  duration_ms: number
  throughput_rps: string | number
  status: string
  created_at: string
}

export interface ReconciliationException {
  id: string
  record_id: string
  ai_classification: string
  confidence: string | number
  reason: string
  evidence_json?: Record<string, unknown>
  recommendation: string
  review_status: string
  reviewed_at?: string
  created_at: string
}

export interface ReconciliationRecord {
  id: string
  batch_id: string
  order_id?: string
  payment_id?: string
  settlement_id?: string
  status: string
  amount_delta: string | number
  fee_delta: string | number
  checks_json?: Record<string, unknown>
  priority_score: string | number
  financial_impact: string | number
  resolution_status: string
  created_at: string
  exception?: ReconciliationException
}

export interface ReconciliationAuditLog {
  id: string
  record_id?: string
  action: string
  actor: string
  decision: string
  reason: string
  evidence_json?: Record<string, unknown>
  confidence?: string | number
  agent_version: string
  previous_state?: string
  new_state?: string
  created_at: string
}

export interface TransactionDecisionCardData {
  record_id: string
  order_id?: string
  payment_id?: string
  settlement_id?: string
  status: string
  expected_amount: string | number
  actual_amount: string | number
  amount_variance: string | number
  expected_fee: string | number
  actual_fee: string | number
  fee_variance: string | number
  financial_exposure: string | number
  checks: {
    order_matched: boolean
    payment_matched: boolean
    currency_matched: boolean
    amount_matched: boolean
    fee_matched: boolean
    settlement_found: boolean
  }
  ai_classification: string
  ai_confidence: string | number
  ai_reason: string
  ai_recommendation: string
  evidence_items: Array<{
    source: string
    reference: string
    expected_amount?: string
    captured_amount?: string
    settled_amount?: string
    expected_fee?: string
    gateway_fee?: string
    method?: string
    status?: string
    date?: string
    payout_time?: string
  }>
  resolution_status: string
}

export interface ReconciliationKPISummary {
  total_records: number
  matched_records: number
  auto_reconciled: number
  ai_assisted: number
  unresolved_count: number
  match_rate: string | number
  total_financial_exposure: string | number
  latest_duration_ms: number
  latest_throughput_rps: string | number
  high_priority_exceptions_count: number
  dataset_type: string
  last_reconciled_at?: string
}

export interface MerchantLedgerEntry {
  id: string
  workspace_id: string
  order_id: string
  invoice_id?: string
  customer_reference?: string
  expected_amount: string | number
  expected_currency: string
  expected_fee: string | number
  expected_tax: string | number
  expected_net_amount: string | number
  expected_status: string
  transaction_date: string
  source: string
  metadata_json?: Record<string, unknown>
  created_at: string
  updated_at: string
}
