import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Bot,
  Building2,
  CheckCircle2,
  Coins,
  FileSpreadsheet,
  History,
  Landmark,
  Play,
  Receipt,
  RefreshCw,
  Scale,
  ShieldCheck,
  Sparkles,
  Upload,
  Zap,
} from 'lucide-react'
import { toast } from 'sonner'

import { reconciliation } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ReconciliationCsvModal } from '@/components/reconciliation-csv-modal'
import { CashPositionBanner } from '@/components/cash-position-banner'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ControllerChatDialog } from '@/components/controller-chat-dialog'
import type { ReconciliationKPISummary, ReconciliationRecord } from '@/types/reconciliation'

export default function FinanceControlCenterPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [batchSize, setBatchSize] = useState<string>('100')
  const [chatOpen, setChatOpen] = useState<boolean>(false)
  const [csvModalOpen, setCsvModalOpen] = useState<boolean>(false)

  // 1. Fetch live KPI summary
  const { data: kpi } = useQuery<ReconciliationKPISummary>({
    queryKey: ['reconciliation-kpi'],
    queryFn: reconciliation.getKPI,
    refetchInterval: 10000,
  })

  // 2. Fetch high-priority exceptions
  const { data: exceptions, isLoading: exceptionsLoading } = useQuery<ReconciliationRecord[]>({
    queryKey: ['reconciliation-high-priority-exceptions'],
    queryFn: () => reconciliation.getRecords({ limit: 6, status: undefined }),
  })

  // 3. Demo Run Mutation
  const demoRunMutation = useMutation({
    mutationFn: (size: number) => reconciliation.runDemo(size),
    onSuccess: (batch) => {
      toast.success(
        `Closed finance loop on ${batch.total_records} records in ${batch.duration_ms}ms at ${batch.throughput_rps} rec/sec!`,
        { description: `Verified Match Rate: ${(Number(batch.match_rate) * 100).toFixed(1)}%` }
      )
      queryClient.invalidateQueries({ queryKey: ['reconciliation-kpi'] })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-high-priority-exceptions'] })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-records'] })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-batches'] })
      queryClient.invalidateQueries({ queryKey: ['cash-forecast'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
    },
    onError: (err: any) => {
      toast.error('Reconciliation run failed', { description: err.message || 'Unknown error' })
    },
  })

  const handleRunDemo = () => {
    demoRunMutation.mutate(parseInt(batchSize, 10))
  }

  const matchRatePercent = kpi ? (Number(kpi.match_rate) * 100).toFixed(1) : '0.0'
  const exposureInr = kpi ? Number(kpi.total_financial_exposure).toLocaleString('en-IN') : '0'

  return (
    <div className="flex-1 space-y-6 p-6">
      {/* Flagship Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30">
              Razorpay Buildathon • Track 04
            </Badge>
            <Badge variant="secondary" className="flex items-center gap-1 font-mono text-xs">
              <Zap className="h-3 w-3 text-amber-500" />
              Autonomous Finance Ops
            </Badge>
          </div>
          <h1 className="text-3xl font-bold tracking-tight mt-1 text-foreground">
            AdaptiveAI Finance Control Center
          </h1>
          <p className="text-muted-foreground text-sm">
            From transaction data to verified financial intelligence • Deterministic 3-Way Reconciliation & AI Investigation
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            className="h-9 gap-1.5 text-xs font-medium border-primary/30 hover:bg-primary/5"
            onClick={() => setChatOpen(true)}
          >
            <Bot className="h-4 w-4 text-primary" />
            Ask Controller
          </Button>

          <Button
            size="sm"
            className="h-9 gap-1.5 text-xs bg-primary hover:bg-primary/90 text-primary-foreground font-medium shadow-sm"
            onClick={() => setCsvModalOpen(true)}
          >
            <Upload className="h-4 w-4" />
            Ingest 3-Way CSV Batch
          </Button>

          <div className="flex items-center rounded-md border border-border bg-card shadow-sm overflow-hidden h-9">
            <Select value={batchSize} onValueChange={setBatchSize}>
              <SelectTrigger className="h-9 border-0 rounded-none bg-transparent shadow-none w-[125px] text-xs font-medium focus:ring-0 focus:ring-offset-0">
                <SelectValue placeholder="Batch size" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="50">50 Records</SelectItem>
                <SelectItem value="100">100 Records</SelectItem>
                <SelectItem value="150">150 Records</SelectItem>
                <SelectItem value="250">250 Records</SelectItem>
              </SelectContent>
            </Select>

            <Button
              size="sm"
              className="h-9 rounded-none bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium gap-1.5 px-3 border-l border-border"
              onClick={handleRunDemo}
              disabled={demoRunMutation.isPending}
            >
              {demoRunMutation.isPending ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  Executing...
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5 fill-current" />
                  Run Demo
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Match Rate */}
        <Card className="border-primary/20 bg-gradient-to-br from-card to-primary/5">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Verified Match Rate</CardTitle>
            <ShieldCheck className="h-5 w-5 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-foreground">{matchRatePercent}%</div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
              <span className="text-emerald-500 font-semibold">{kpi?.matched_records ?? 0}</span> matched of {kpi?.total_records ?? 0} total records
            </p>
          </CardContent>
        </Card>

        {/* Financial Exposure */}
        <Card className="border-amber-500/20 bg-gradient-to-br from-card to-amber-500/5">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Financial Exposure</CardTitle>
            <Coins className="h-5 w-5 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-amber-500">₹{exposureInr}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Total unresolved value across {kpi?.unresolved_count ?? 0} exceptions
            </p>
          </CardContent>
        </Card>

        {/* Breakdown: Auto vs AI */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Automation Breakdown</CardTitle>
            <Sparkles className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-emerald-500">{kpi?.auto_reconciled ?? 0}</span>
              <span className="text-xs text-muted-foreground">Auto</span>
              <span className="text-muted-foreground">/</span>
              <span className="text-2xl font-bold text-sky-500">{kpi?.ai_assisted ?? 0}</span>
              <span className="text-xs text-muted-foreground">AI Assisted</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Zero arithmetic hallucinations • Propose-first review
            </p>
          </CardContent>
        </Card>

        {/* Measured Throughput */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Measured Throughput</CardTitle>
            <Activity className="h-5 w-5 text-cyan-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-foreground">
              {kpi ? Number(kpi.latest_throughput_rps).toFixed(0) : '0'} <span className="text-sm font-normal text-muted-foreground">rec/sec</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Processed in {kpi?.latest_duration_ms ?? 0}ms across 3-way matching rules
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Live Cash Position & Liquidity Engine */}
      <CashPositionBanner />

      {/* Main Content Layout */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Left 2 Cols: High-Risk Exceptions Queue */}
        <Card className="md:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
                High-Priority Financial Exceptions Queue
              </CardTitle>
              <CardDescription>
                Exceptions prioritized by calculated financial exposure (Amount × Risk Weight × Aging)
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={() => navigate('/reconciliation')} className="gap-1">
              View All Records <ArrowRight className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            {exceptionsLoading ? (
              <div className="py-8 text-center text-muted-foreground">Loading exceptions...</div>
            ) : !exceptions || exceptions.filter((r) => r.status !== 'AUTO_RECONCILED').length === 0 ? (
              <div className="py-12 text-center">
                <CheckCircle2 className="h-10 w-10 text-emerald-500 mx-auto mb-2" />
                <p className="font-medium text-foreground">All transactions successfully reconciled!</p>
                <p className="text-xs text-muted-foreground mt-1">Zero unresolved exposure across all active settlement batches.</p>
              </div>
            ) : (
              <div className="rounded-md border overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[140px]">Order ID</TableHead>
                      <TableHead className="w-[150px]">Anomaly Type</TableHead>
                      <TableHead className="w-[130px]">Status</TableHead>
                      <TableHead className="w-[110px] text-right">Exposure</TableHead>
                      <TableHead className="w-[100px] text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {exceptions
                      .filter((r) => r.status !== 'AUTO_RECONCILED')
                      .slice(0, 5)
                      .map((record) => (
                        <TableRow key={record.id} className="cursor-pointer hover:bg-muted/50 transition-colors" onClick={() => navigate('/reconciliation')}>
                          <TableCell className="font-mono text-xs font-semibold">{record.order_id}</TableCell>
                          <TableCell className="text-xs text-muted-foreground truncate max-w-[150px]">
                            {(record.exception?.ai_classification || record.status)?.replace(/_/g, ' ')}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={
                                record.status === 'AI_PROPOSED'
                                  ? 'border-purple-500/30 bg-purple-500/10 text-purple-600 text-[10px]'
                                  : record.status === 'DISPUTED'
                                  ? 'border-rose-500/30 bg-rose-500/10 text-rose-600 text-[10px]'
                                  : 'border-amber-500/30 bg-amber-500/10 text-amber-600 text-[10px]'
                              }
                            >
                              {record.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs font-bold text-amber-500 tabular-nums">
                            ₹{Number(record.financial_impact).toLocaleString('en-IN')}
                          </TableCell>
                          <TableCell className="text-right">
                            <Button size="sm" variant="ghost" className="h-7 text-xs px-2 text-primary hover:text-primary hover:bg-primary/10">
                              Investigate →
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

        {/* Right 1 Col: Autonomous Agent Architecture & AdaptiveAI Core */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-purple-500" />
                Autonomous Engine Loop
              </CardTitle>
              <CardDescription>Track 04 Challenge Architecture</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs text-muted-foreground">
              <div className="flex gap-3">
                <div className="p-2 rounded-lg bg-primary/10 text-primary">1</div>
                <div>
                  <span className="font-semibold text-foreground">3-Way Deterministic Ingestion</span>
                  <p>Matches Orders, Gateway captured payments, and Bank settlement credits.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="p-2 rounded-lg bg-primary/10 text-primary">2</div>
                <div>
                  <span className="font-semibold text-foreground">Automated Root Cause Diagnosis</span>
                  <p>Detects MDR fee overcharges, timing float mismatches, and orphan payouts.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="p-2 rounded-lg bg-primary/10 text-primary">3</div>
                <div>
                  <span className="font-semibold text-foreground">Cash Position Forecaster</span>
                  <p>Projects liquid HDFC balance vs trapped settlement float and working capital.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="p-2 rounded-lg bg-primary/10 text-primary">4</div>
                <div>
                  <span className="font-semibold text-foreground">AdaptiveAI General Ledger Sync</span>
                  <p>Posts double-entry journals directly into AdaptiveAI Accounts & Transactions.</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">Controller Workstations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-between" onClick={() => navigate('/reconciliation')}>
                <span className="flex items-center gap-2">
                  <Scale className="h-4 w-4 text-primary" />
                  3-Way Reconciliation Workstation
                </span>
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button variant="outline" className="w-full justify-between" onClick={() => navigate('/merchant-ledger')}>
                <span className="flex items-center gap-2">
                  <FileSpreadsheet className="h-4 w-4 text-emerald-500" />
                  Merchant Expected Ledger
                </span>
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button variant="outline" className="w-full justify-between" onClick={() => navigate('/audit-trail')}>
                <span className="flex items-center gap-2">
                  <History className="h-4 w-4 text-amber-500" />
                  Immutable Audit Trail
                </span>
                <ArrowRight className="h-4 w-4" />
              </Button>

              <div className="pt-2 pb-1 border-t text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                AdaptiveAI Core Modules
              </div>
              <Button variant="ghost" className="w-full justify-between h-9 text-xs" onClick={() => navigate('/transactions')}>
                <span className="flex items-center gap-2">
                  <Receipt className="h-3.5 w-3.5 text-sky-500" />
                  Ledger Transactions (/transactions)
                </span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
              <Button variant="ghost" className="w-full justify-between h-9 text-xs" onClick={() => navigate('/accounts')}>
                <span className="flex items-center gap-2">
                  <Building2 className="h-3.5 w-3.5 text-emerald-500" />
                  Bank & Clearing Accounts (/accounts)
                </span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
              <Button variant="ghost" className="w-full justify-between h-9 text-xs" onClick={() => navigate('/reports')}>
                <span className="flex items-center gap-2">
                  <BarChart3 className="h-3.5 w-3.5 text-indigo-500" />
                  Cashflow & Reports (/reports)
                </span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
              <Button variant="ghost" className="w-full justify-between h-9 text-xs" onClick={() => navigate('/assets')}>
                <span className="flex items-center gap-2">
                  <Landmark className="h-3.5 w-3.5 text-purple-500" />
                  Assets & Net Worth (/assets)
                </span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Controller Chat Dialog */}
      <ControllerChatDialog open={chatOpen} onOpenChange={setChatOpen} />

      {/* 3-Way CSV Batch Import & Ledger Sync Modal */}
      <ReconciliationCsvModal open={csvModalOpen} onOpenChange={setCsvModalOpen} />
    </div>
  )
}
