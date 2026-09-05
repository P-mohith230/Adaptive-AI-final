import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Upload,
  Download,
  Play,
  CheckCircle2,
  RefreshCw,
  ShieldCheck,
  Building2,
  Receipt,
  FileDown,
} from 'lucide-react'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent } from '@/components/ui/card'
import { reconciliation } from '@/lib/api'

interface ReconciliationCsvModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface ModalBatchResult {
  match_rate?: string | number
  total_records?: number
  matched_records?: number
  unresolved_count?: number
  ledger_sync?: {
    synced_clean?: number
    synced_exceptions?: number
  }
}

export function ReconciliationCsvModal({ open, onOpenChange }: ReconciliationCsvModalProps) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const [activeTab, setActiveTab] = useState<'generate' | 'upload'>('generate')
  const [recordCount, setRecordCount] = useState('100')
  const [ordersFile, setOrdersFile] = useState<File | null>(null)
  const [paymentsFile, setPaymentsFile] = useState<File | null>(null)
  const [bankFile, setBankFile] = useState<File | null>(null)
  const [resultData, setResultData] = useState<ModalBatchResult | null>(null)

  // 1. Download sample CSV files
  const downloadSampleMutation = useMutation({
    mutationFn: async (total: number) => {
      const data = await reconciliation.getSampleCsvs(total)
      return data
    },
    onSuccess: (data) => {
      const downloadFile = (content: string, filename: string) => {
        const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      }

      if (data.merchant_orders_csv) {
        downloadFile(data.merchant_orders_csv, 'merchant_orders_sample.csv')
      }
      if (data.razorpay_payments_csv) {
        downloadFile(data.razorpay_payments_csv, 'razorpay_payments_sample.csv')
      }
      if (data.bank_settlement_csv) {
        downloadFile(data.bank_settlement_csv, 'bank_settlement_sample.csv')
      }

      toast.success('3 Sample CSV templates downloaded successfully!')
    },
    onError: (err: Error) => {
      toast.error('Failed to download sample templates', { description: err.message })
    },
  })

  // 2. Generate & Reconcile Synthetic Batch
  const generateBatchMutation = useMutation({
    mutationFn: async (count: number) => {
      const sample = await reconciliation.getSampleCsvs(count)
      const res = await reconciliation.importCsvBatch(
        sample.merchant_orders_csv,
        sample.razorpay_payments_csv,
        sample.bank_settlement_csv
      )
      return res
    },
    onSuccess: (res) => {
      setResultData(res)
      toast.success(`Batch processed: ${res.matched_records}/${res.total_records} matched!`, {
        description: `Synced ${res.ledger_sync?.synced_clean || 0} clean entries to AdaptiveAI Ledger.`,
      })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-kpi'] })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-records'] })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-batches'] })
      queryClient.invalidateQueries({ queryKey: ['financial-queries'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
    },
    onError: (err: Error) => {
      toast.error('Batch generation failed', { description: err.message })
    },
  })

  // 3. Upload & Ingest User CSV files
  const uploadBatchMutation = useMutation({
    mutationFn: async () => {
      if (!ordersFile || !paymentsFile) {
        throw new Error('Please select both Merchant Orders and Razorpay Payments CSV files.')
      }

      const ordersText = await ordersFile.text()
      const paymentsText = await paymentsFile.text()
      const bankText = bankFile ? await bankFile.text() : undefined

      const res = await reconciliation.importCsvBatch(ordersText, paymentsText, bankText)
      return res
    },
    onSuccess: (res) => {
      setResultData(res)
      toast.success(`Batch uploaded & reconciled: ${(Number(res.match_rate) * 100).toFixed(1)}% match rate!`, {
        description: `Synced to AdaptiveAI general ledger.`,
      })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-kpi'] })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-records'] })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-batches'] })
      queryClient.invalidateQueries({ queryKey: ['financial-queries'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
    },
    onError: (err: Error) => {
      toast.error('Upload failed', { description: err.message })
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30">
              Razorpay Track 04
            </Badge>
            <Badge variant="secondary" className="font-mono text-xs">
              3-Way CSV Reconciliation
            </Badge>
          </div>
          <DialogTitle className="text-xl font-bold tracking-tight mt-1">
            Import 3-Way Reconciliation Batch
          </DialogTitle>
          <DialogDescription>
            Closes the finance loop across Merchant Orders, Razorpay Captured Payments, and Bank Settlements.
            Automatically pushes verified entries into AdaptiveAI General Ledger.
          </DialogDescription>
        </DialogHeader>

        {/* Results Banner if completed */}
        {resultData && (
          <Card className="border-emerald-500/30 bg-emerald-500/5">
            <CardContent className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  <span className="font-semibold text-foreground">Reconciliation Loop Completed</span>
                </div>
                <Badge className="bg-emerald-500/20 text-emerald-600 border-emerald-500/40">
                  Match Rate: {(Number(resultData.match_rate) * 100).toFixed(1)}%
                </Badge>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                <div className="bg-background/80 p-2 rounded border">
                  <div className="text-muted-foreground">Total Processed</div>
                  <div className="text-base font-bold text-foreground">{resultData.total_records}</div>
                </div>
                <div className="bg-background/80 p-2 rounded border">
                  <div className="text-muted-foreground">Clean Matches</div>
                  <div className="text-base font-bold text-emerald-500">{resultData.matched_records}</div>
                </div>
                <div className="bg-background/80 p-2 rounded border">
                  <div className="text-muted-foreground">Exceptions</div>
                  <div className="text-base font-bold text-amber-500">{resultData.unresolved_count}</div>
                </div>
                <div className="bg-background/80 p-2 rounded border">
                  <div className="text-muted-foreground">Ledger Synced</div>
                  <div className="text-base font-bold text-primary">
                    {(resultData.ledger_sync?.synced_clean || 0) + (resultData.ledger_sync?.synced_exceptions || 0)} rows
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 pt-1">
                <Button
                  size="sm"
                  variant="default"
                  className="gap-1.5"
                  onClick={() => {
                    onOpenChange(false)
                    navigate('/reconciliation')
                  }}
                >
                  <ShieldCheck className="h-3.5 w-3.5" />
                  Review Exceptions
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1.5"
                  onClick={() => {
                    onOpenChange(false)
                    navigate('/transactions')
                  }}
                >
                  <Receipt className="h-3.5 w-3.5" />
                  View in /transactions
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1.5"
                  onClick={() => {
                    onOpenChange(false)
                    navigate('/accounts')
                  }}
                >
                  <Building2 className="h-3.5 w-3.5" />
                  View Bank & Clearing /accounts
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'generate' | 'upload')} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="generate">Instant 50+ Synthetic Batch</TabsTrigger>
            <TabsTrigger value="upload">Upload Custom CSV Files</TabsTrigger>
          </TabsList>

          {/* Tab 1: Instant Synthetic Batch */}
          <TabsContent value="generate" className="space-y-4 pt-2">
            <div className="rounded-lg border p-4 bg-muted/20 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-foreground">Synthetic 50+ Fintech Dataset</h4>
                  <p className="text-xs text-muted-foreground">
                    Generates realistic e-commerce merchant orders, Razorpay gateway charges (MDR fees, GST), and bank settlement credits with controlled anomalies.
                  </p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row items-end gap-3 pt-1">
                <div className="w-full sm:w-52 space-y-1.5">
                  <Label className="text-xs font-semibold text-foreground">Batch Size</Label>
                  <Select value={recordCount} onValueChange={setRecordCount}>
                    <SelectTrigger className="h-10">
                      <SelectValue placeholder="Select size" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="50">50 Records (Track 04 min)</SelectItem>
                      <SelectItem value="100">100 Records (Standard)</SelectItem>
                      <SelectItem value="150">150 Records (Heavy load)</SelectItem>
                      <SelectItem value="250">250 Records (Stress test)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button
                  className="h-10 flex-1 w-full bg-emerald-600 hover:bg-emerald-700 text-white gap-2 font-medium shadow-sm"
                  onClick={() => generateBatchMutation.mutate(parseInt(recordCount, 10))}
                  disabled={generateBatchMutation.isPending}
                >
                  {generateBatchMutation.isPending ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Generating & Reconciling...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 fill-current" />
                      Run 3-Way Reconciliation & Sync Ledger
                    </>
                  )}
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between border-t pt-3">
              <span className="text-xs text-muted-foreground">Want to inspect raw CSV files?</span>
              <Button
                variant="ghost"
                size="sm"
                className="gap-1.5 text-xs"
                onClick={() => downloadSampleMutation.mutate(parseInt(recordCount, 10))}
                disabled={downloadSampleMutation.isPending}
              >
                <Download className="h-3.5 w-3.5" />
                Download 3 Sample CSV Files
              </Button>
            </div>
          </TabsContent>

          {/* Tab 2: Upload CSV Files */}
          <TabsContent value="upload" className="space-y-4 pt-2">
            <div className="space-y-3">
              {/* Merchant Orders CSV */}
              <div className="border rounded-md p-3 space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label className="text-xs font-semibold text-foreground">1. Merchant Orders CSV *</Label>
                  <span className="text-[10px] text-muted-foreground">order_id, invoice_id, gross_amount...</span>
                </div>
                <input
                  type="file"
                  accept=".csv"
                  className="text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-primary/10 file:text-primary hover:file:bg-primary/20 w-full"
                  onChange={(e) => setOrdersFile(e.target.files?.[0] || null)}
                />
              </div>

              {/* Razorpay Payments CSV */}
              <div className="border rounded-md p-3 space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label className="text-xs font-semibold text-foreground">2. Razorpay Payments CSV *</Label>
                  <span className="text-[10px] text-muted-foreground">payment_id, order_id, amount, fee, tax...</span>
                </div>
                <input
                  type="file"
                  accept=".csv"
                  className="text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-primary/10 file:text-primary hover:file:bg-primary/20 w-full"
                  onChange={(e) => setPaymentsFile(e.target.files?.[0] || null)}
                />
              </div>

              {/* Bank Settlement Statement CSV */}
              <div className="border rounded-md p-3 space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label className="text-xs font-semibold text-foreground">3. Bank Settlement Statement CSV (Optional)</Label>
                  <span className="text-[10px] text-muted-foreground">settlement_utr, settlement_id, net_credit_amount...</span>
                </div>
                <input
                  type="file"
                  accept=".csv"
                  className="text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-primary/10 file:text-primary hover:file:bg-primary/20 w-full"
                  onChange={(e) => setBankFile(e.target.files?.[0] || null)}
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5 text-xs"
                onClick={() => downloadSampleMutation.mutate(50)}
                disabled={downloadSampleMutation.isPending}
              >
                <FileDown className="h-3.5 w-3.5" />
                Download Sample CSV Templates
              </Button>

              <Button
                className="gap-2"
                onClick={() => uploadBatchMutation.mutate()}
                disabled={uploadBatchMutation.isPending || !ordersFile || !paymentsFile}
              >
                {uploadBatchMutation.isPending ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Ingesting...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    Ingest & Reconcile
                  </>
                )}
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
