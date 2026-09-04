import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowRight,
  Bot,
  Check,
  CheckCircle2,
  Clock,
  Search,
  Sparkles,
  Upload,
  X,
} from 'lucide-react'
import { toast } from 'sonner'

import { reconciliation } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogFooter,
} from '@/components/ui/dialog'
import { ControllerChatDialog } from '@/components/controller-chat-dialog'
import { ReconciliationCsvModal } from '@/components/reconciliation-csv-modal'
import { CashPositionBanner } from '@/components/cash-position-banner'
import type { ReconciliationRecord, TransactionDecisionCardData } from '@/types/reconciliation'

export default function ReconciliationPage() {
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()

  const [activeTab, setActiveTab] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [selectedRecordId, setSelectedRecordId] = useState<string | null>(searchParams.get('recordId'))
  const [chatOpen, setChatOpen] = useState(false)
  const [csvModalOpen, setCsvModalOpen] = useState(false)
  const [reviewNotes, setReviewNotes] = useState('')

  // 1. Fetch records
  const { data: records, isLoading: recordsLoading } = useQuery<ReconciliationRecord[]>({
    queryKey: ['reconciliation-records', activeTab],
    queryFn: () => {
      let statusFilter: string | undefined = undefined
      if (activeTab === 'exceptions') statusFilter = undefined // Filter client side
      else if (activeTab === 'mismatch') statusFilter = 'MISMATCH'
      else if (activeTab === 'fees') statusFilter = 'FEE_DISCREPANCY'
      else if (activeTab === 'settlement') statusFilter = 'MISSING_SETTLEMENT'
      else if (activeTab === 'auto') statusFilter = 'AUTO_RECONCILED'

      return reconciliation.getRecords({ limit: 150, status: statusFilter })
    },
  })

  // 2. Fetch decision card for selected record
  const { data: decisionCard, isLoading: cardLoading } = useQuery<TransactionDecisionCardData>({
    queryKey: ['transaction-decision-card', selectedRecordId],
    queryFn: () => reconciliation.getDecisionCard(selectedRecordId!),
    enabled: Boolean(selectedRecordId),
  })

  // 3. Review Mutation
  const reviewMutation = useMutation({
    mutationFn: ({ recordId, action, notes }: { recordId: string; action: 'APPROVE' | 'REJECT' | 'RESOLVE'; notes?: string }) =>
      reconciliation.reviewRecord(recordId, action, notes),
    onSuccess: (updated) => {
      toast.success(`Action applied: ${updated.resolution_status.toUpperCase()}`, {
        description: 'Immutable record appended to Audit Trail',
      })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-records'] })
      queryClient.invalidateQueries({ queryKey: ['transaction-decision-card', selectedRecordId] })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-kpi'] })
      setSelectedRecordId(null)
    },
    onError: (err: any) => {
      toast.error('Review action failed', { description: err.message })
    },
  })

  // Filter records
  const filteredRecords = (records || []).filter((r) => {
    if (activeTab === 'exceptions' && r.status === 'AUTO_RECONCILED') return false
    if (!searchTerm.trim()) return true
    const term = searchTerm.toLowerCase()
    return (
      r.order_id?.toLowerCase().includes(term) ||
      r.payment_id?.toLowerCase().includes(term) ||
      r.status.toLowerCase().includes(term) ||
      r.exception?.ai_classification?.toLowerCase().includes(term)
    )
  })

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'AUTO_RECONCILED':
        return <Badge className="bg-emerald-500/15 text-emerald-600 border-emerald-500/30 hover:bg-emerald-500/20">AUTO RECONCILED</Badge>
      case 'MISMATCH':
        return <Badge variant="destructive">AMOUNT MISMATCH</Badge>
      case 'FEE_DISCREPANCY':
        return <Badge className="bg-amber-500/15 text-amber-600 border-amber-500/30 hover:bg-amber-500/20">FEE DISCREPANCY</Badge>
      case 'MISSING_SETTLEMENT':
        return <Badge className="bg-purple-500/15 text-purple-600 border-purple-500/30 hover:bg-purple-500/20">MISSING SETTLEMENT</Badge>
      case 'TIMING_DIFFERENCE':
        return <Badge className="bg-blue-500/15 text-blue-600 border-blue-500/30 hover:bg-blue-500/20">TIMING DIFFERENCE</Badge>
      case 'DUPLICATE':
        return <Badge variant="destructive">DUPLICATE CHARGE</Badge>
      case 'MISSING_PAYMENT':
        return <Badge className="bg-rose-500/15 text-rose-600 border-rose-500/30 hover:bg-rose-500/20">MISSING PAYMENT</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="flex-1 space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30">
              Deterministic 3-Way Reconciliation
            </Badge>
            <Badge variant="secondary" className="font-mono text-xs">
              Merchant Ledger ⟷ Razorpay Gateway ⟷ Bank Settlements
            </Badge>
          </div>
          <h1 className="text-2xl font-bold tracking-tight mt-1 text-foreground">
            Reconciliation & Exception Workstation
          </h1>
          <p className="text-muted-foreground text-sm">
            Inspect verified matches, drill down into numerical discrepancies, and approve AI root-cause recommendations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="default"
            className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground"
            onClick={() => setCsvModalOpen(true)}
          >
            <Upload className="h-4 w-4" />
            Ingest 3-Way CSV Batch
          </Button>
          <Button variant="outline" className="gap-2" onClick={() => setChatOpen(true)}>
            <Bot className="h-4 w-4 text-primary" />
            Ask Controller
          </Button>
        </div>
      </div>

      {/* Real-Time Cash Position & Liquidity Engine */}
      <CashPositionBanner />

      {/* Filter Tabs & Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full sm:w-auto">
          <TabsList>
            <TabsTrigger value="all">All Records</TabsTrigger>
            <TabsTrigger value="exceptions" className="flex items-center gap-1.5">
              Exceptions
              <span className="px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-600 text-[10px] font-bold">
                {records ? records.filter((r) => r.status !== 'AUTO_RECONCILED').length : 0}
              </span>
            </TabsTrigger>
            <TabsTrigger value="mismatch">Amount Mismatches</TabsTrigger>
            <TabsTrigger value="fees">Fee Deltas</TabsTrigger>
            <TabsTrigger value="settlement">Missing Payouts</TabsTrigger>
            <TabsTrigger value="auto">Auto-Matched</TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search order ID, payment ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Records Table */}
      <Card>
        <CardContent className="p-0">
          {recordsLoading ? (
            <div className="py-16 text-center text-muted-foreground">Loading reconciliation dataset...</div>
          ) : filteredRecords.length === 0 ? (
            <div className="py-16 text-center">
              <CheckCircle2 className="h-10 w-10 text-muted-foreground/50 mx-auto mb-2" />
              <p className="font-medium text-foreground">No records match the current filter</p>
              <p className="text-sm text-muted-foreground">Select another tab or run the demo reconciliation from Control Center.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[125px]">Order ID</TableHead>
                    <TableHead className="w-[130px]">Gateway Payment</TableHead>
                    <TableHead className="w-[120px]">Settlement ID</TableHead>
                    <TableHead className="w-[140px]">Status</TableHead>
                    <TableHead className="w-[105px] text-right">Amount Delta</TableHead>
                    <TableHead className="w-[105px] text-right">Exposure (₹)</TableHead>
                    <TableHead className="w-[150px]">AI Diagnosis</TableHead>
                    <TableHead className="w-[95px]">Resolution</TableHead>
                    <TableHead className="w-[105px] text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRecords.map((rec) => (
                    <TableRow
                      key={rec.id}
                      className="cursor-pointer hover:bg-muted/50 transition-colors"
                      onClick={() => setSelectedRecordId(rec.id)}
                    >
                      <TableCell className="font-mono text-xs font-semibold text-foreground">{rec.order_id || 'N/A'}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">{rec.payment_id || '—'}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">{rec.settlement_id || '—'}</TableCell>
                      <TableCell>{getStatusBadge(rec.status)}</TableCell>
                      <TableCell className="text-right font-mono text-xs tabular-nums">
                        {Number(rec.amount_delta) !== 0 ? (
                          <span className="text-destructive font-semibold">₹{Number(rec.amount_delta).toLocaleString('en-IN')}</span>
                        ) : Number(rec.fee_delta) !== 0 ? (
                          <span className="text-amber-500 font-medium">Fee: ₹{Number(rec.fee_delta).toFixed(2)}</span>
                        ) : (
                          <span className="text-emerald-500 font-semibold inline-flex items-center justify-end gap-1">
                            <Check className="h-3 w-3 inline" /> ₹0.00
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs font-bold tabular-nums">
                        {Number(rec.financial_impact) > 0 ? (
                          <span className="text-amber-500">₹{Number(rec.financial_impact).toLocaleString('en-IN')}</span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {rec.exception ? (
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs font-medium text-foreground">{rec.exception.ai_classification}</span>
                            <span className="text-[10px] font-mono text-emerald-500 font-semibold">
                              {(Number(rec.exception.confidence) * 100).toFixed(0)}%
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">Deterministic ✓</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-[10px] uppercase font-mono">
                          {rec.resolution_status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button size="sm" variant="ghost" className="h-7 text-xs gap-1">
                          Decision Card <ArrowRight className="h-3.5 w-3.5" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Signature Transaction Decision Card Dialog ("Why did this not reconcile?") */}
      <Dialog open={Boolean(selectedRecordId)} onOpenChange={(open) => !open && setSelectedRecordId(null)}>
        <DialogContent className="max-w-3xl sm:max-w-3xl max-h-[90vh] overflow-y-auto p-6">
          {cardLoading || !decisionCard ? (
            <div className="py-12 text-center text-muted-foreground">Loading decision card...</div>
          ) : (
            <div className="space-y-6">
              {/* Header */}
              <div className="border-b pb-4">
                <div className="flex items-center gap-2 pr-12">
                  <Badge variant="outline" className="text-xs border-primary/30 text-primary">
                    FINANCIAL CONTROL DECISION CARD
                  </Badge>
                  <span className="text-xs font-mono text-muted-foreground">ID: {decisionCard.record_id.slice(0, 8)}</span>
                </div>
                <div className="flex items-center justify-between gap-4 mt-2">
                  <h2 className="text-2xl font-bold font-mono">Transaction {decisionCard.order_id || 'Record'}</h2>
                  <div className="shrink-0">
                    {getStatusBadge(decisionCard.status)}
                  </div>
                </div>
                <div className="flex flex-wrap gap-4 text-xs font-mono text-muted-foreground mt-1.5">
                  <span>Payment: {decisionCard.payment_id || 'Not Recorded'}</span>
                  <span>Settlement: {decisionCard.settlement_id || 'Pending'}</span>
                </div>
              </div>

              {/* Financial Variance Grid */}
              <div className="grid grid-cols-3 gap-3 p-4 bg-muted/40 rounded-xl border">
                <div className="flex flex-col justify-between min-h-[90px]">
                  <span className="text-[10px] uppercase text-muted-foreground font-semibold block">Merchant Expected</span>
                  <div className="my-1 text-xl font-bold font-mono text-foreground tabular-nums">
                    ₹{Number(decisionCard.expected_amount).toLocaleString('en-IN')}
                  </div>
                  <span className="text-[11px] text-muted-foreground block font-mono">
                    Exp. Fee: ₹{Number(decisionCard.expected_fee).toFixed(2)}
                  </span>
                </div>
                <div className="flex flex-col justify-between min-h-[90px]">
                  <span className="text-[10px] uppercase text-muted-foreground font-semibold block">Razorpay Captured</span>
                  <div className="my-1 text-xl font-bold font-mono text-foreground tabular-nums">
                    ₹{Number(decisionCard.actual_amount).toLocaleString('en-IN')}
                  </div>
                  <span className="text-[11px] text-muted-foreground block font-mono">
                    Act. Fee: ₹{Number(decisionCard.actual_fee).toFixed(2)}
                  </span>
                </div>
                <div className="flex flex-col justify-between min-h-[90px]">
                  <span className="text-[10px] uppercase text-amber-500 font-semibold block">Exposure / Variance</span>
                  <div className="my-1 text-xl font-bold font-mono text-amber-500 tabular-nums">
                    ₹{Number(decisionCard.financial_exposure).toLocaleString('en-IN')}
                  </div>
                  <span className="text-[11px] text-muted-foreground block font-mono">
                    Delta: ₹{Number(decisionCard.amount_variance).toLocaleString('en-IN')}
                  </span>
                </div>
              </div>

              {/* Verified Deterministic Checks */}
              <div>
                <h4 className="text-xs uppercase font-semibold text-muted-foreground mb-2">Deterministic Verification Checks</h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  <div className={`p-2.5 min-h-[42px] rounded-lg border flex items-center gap-2 text-xs font-medium ${decisionCard.checks.order_matched ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600' : 'bg-destructive/10 border-destructive/30 text-destructive'}`}>
                    {decisionCard.checks.order_matched ? <Check className="h-4 w-4 shrink-0" /> : <X className="h-4 w-4 shrink-0" />}
                    <span>Order ID Matched</span>
                  </div>
                  <div className={`p-2.5 min-h-[42px] rounded-lg border flex items-center gap-2 text-xs font-medium ${decisionCard.checks.payment_matched ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600' : 'bg-destructive/10 border-destructive/30 text-destructive'}`}>
                    {decisionCard.checks.payment_matched ? <Check className="h-4 w-4 shrink-0" /> : <X className="h-4 w-4 shrink-0" />}
                    <span>Payment Captured</span>
                  </div>
                  <div className={`p-2.5 min-h-[42px] rounded-lg border flex items-center gap-2 text-xs font-medium ${decisionCard.checks.amount_matched ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600' : 'bg-destructive/10 border-destructive/30 text-destructive'}`}>
                    {decisionCard.checks.amount_matched ? <Check className="h-4 w-4 shrink-0" /> : <X className="h-4 w-4 shrink-0" />}
                    <span>Base Amount Matched</span>
                  </div>
                  <div className={`p-2.5 min-h-[42px] rounded-lg border flex items-center gap-2 text-xs font-medium ${decisionCard.checks.fee_matched ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600' : 'bg-amber-500/10 border-amber-500/30 text-amber-600'}`}>
                    {decisionCard.checks.fee_matched ? <Check className="h-4 w-4 shrink-0" /> : <AlertTriangle className="h-4 w-4 shrink-0" />}
                    <span>MDR Fee Schedule</span>
                  </div>
                  <div className={`p-2.5 min-h-[42px] rounded-lg border flex items-center gap-2 text-xs font-medium ${decisionCard.checks.currency_matched ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600' : 'bg-destructive/10 border-destructive/30 text-destructive'}`}>
                    {decisionCard.checks.currency_matched ? <Check className="h-4 w-4 shrink-0" /> : <X className="h-4 w-4 shrink-0" />}
                    <span>Currency (INR)</span>
                  </div>
                  <div className={`p-2.5 min-h-[42px] rounded-lg border flex items-center gap-2 text-xs font-medium ${decisionCard.checks.settlement_found ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600' : 'bg-purple-500/10 border-purple-500/30 text-purple-600'}`}>
                    {decisionCard.checks.settlement_found ? <Check className="h-4 w-4 shrink-0" /> : <Clock className="h-4 w-4 shrink-0" />}
                    <span>Bank Settlement</span>
                  </div>
                </div>
              </div>

              {/* AI Controller Investigation Box */}
              <div className="p-4 rounded-xl border border-primary/30 bg-primary/5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-primary" />
                    <span className="font-semibold text-sm text-foreground">AI Controller Diagnosis</span>
                    <Badge variant="secondary" className="font-mono text-xs">
                      {decisionCard.ai_classification}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-1.5 font-mono text-xs text-emerald-600 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 font-bold">
                    Confidence: {(Number(decisionCard.ai_confidence) * 100).toFixed(1)}%
                  </div>
                </div>

                <p className="text-sm leading-relaxed text-foreground/90 font-sans">
                  {decisionCard.ai_reason}
                </p>

                <div className="p-3 bg-background/80 rounded-lg border border-primary/20 text-xs text-foreground">
                  <span className="font-semibold text-primary block mb-0.5">Recommended Next Action:</span>
                  {decisionCard.ai_recommendation}
                </div>
              </div>

              {/* Synthesized Evidence Items */}
              {decisionCard.evidence_items && decisionCard.evidence_items.length > 0 && (
                <div>
                  <h4 className="text-xs uppercase font-semibold text-muted-foreground mb-2">Cross-System Verified Evidence</h4>
                  <div className="space-y-2">
                    {decisionCard.evidence_items.map((item, idx) => (
                      <div key={idx} className="p-3 rounded-lg border bg-muted/20 text-xs flex justify-between items-center font-mono">
                        <div>
                          <span className="font-bold text-foreground block">{item.source}</span>
                          <span className="text-muted-foreground">{item.reference}</span>
                        </div>
                        <div className="text-right">
                          {item.expected_amount && <div className="text-foreground">Expected: {item.expected_amount}</div>}
                          {item.captured_amount && <div className="text-foreground">Captured: {item.captured_amount}</div>}
                          {item.settled_amount && <div className="text-foreground">Settled: {item.settled_amount}</div>}
                          <span className="text-[10px] text-muted-foreground block">{item.date || item.payout_time}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Human-In-The-Loop Approval Actions */}
              <DialogFooter className="flex-col sm:flex-row gap-2 border-t pt-4">
                <div className="flex-1">
                  <Input
                    placeholder="Add audit justification notes (optional)..."
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    className="text-xs h-9"
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="text-destructive hover:bg-destructive/10"
                    onClick={() => reviewMutation.mutate({ recordId: decisionCard.record_id, action: 'REJECT', notes: reviewNotes })}
                    disabled={reviewMutation.isPending}
                  >
                    Reject
                  </Button>
                  <Button
                    className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1.5"
                    onClick={() => reviewMutation.mutate({ recordId: decisionCard.record_id, action: 'APPROVE', notes: reviewNotes })}
                    disabled={reviewMutation.isPending}
                  >
                    <Check className="h-4 w-4" />
                    Approve AI Recommendation
                  </Button>
                </div>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Controller Chat Drawer */}
      <ControllerChatDialog open={chatOpen} onOpenChange={setChatOpen} />

      {/* 3-Way CSV Batch Import & Ledger Sync Modal */}
      <ReconciliationCsvModal open={csvModalOpen} onOpenChange={setCsvModalOpen} />
    </div>
  )
}
