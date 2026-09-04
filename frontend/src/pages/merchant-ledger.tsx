import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Database,
  FileSpreadsheet,
  Globe,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
} from 'lucide-react'
import { toast } from 'sonner'

import { merchantLedger } from '@/lib/api'
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import type { MerchantLedgerEntry } from '@/types/reconciliation'

export default function MerchantLedgerPage() {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [createOpen, setCreateOpen] = useState(false)

  // Form state
  const [orderId, setOrderId] = useState('')
  const [invoiceId, setInvoiceId] = useState('')
  const [customerRef, setCustomerRef] = useState('')
  const [amount, setAmount] = useState('5000.00')

  // 1. Fetch ledger entries
  const { data: entries, isLoading } = useQuery<MerchantLedgerEntry[]>({
    queryKey: ['merchant-ledger-entries'],
    queryFn: () => merchantLedger.getEntries({ limit: 100 }),
  })

  // 2. Sync Razorpay Mutation
  const syncMutation = useMutation({
    mutationFn: merchantLedger.syncRazorpay,
    onSuccess: (res) => {
      toast.success(res.message || 'Razorpay test mode sync completed!', {
        description: `Synced ${res.synced_payments} payments and ${res.synced_settlements} settlements`,
      })
      queryClient.invalidateQueries({ queryKey: ['merchant-ledger-entries'] })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-records'] })
    },
    onError: (err: any) => {
      toast.error('Sync failed', { description: err.message })
    },
  })

  // 3. Create Entry Mutation
  const createMutation = useMutation({
    mutationFn: (payload: any) => merchantLedger.createEntry(payload),
    onSuccess: () => {
      toast.success('Expected order added to merchant ledger')
      queryClient.invalidateQueries({ queryKey: ['merchant-ledger-entries'] })
      setCreateOpen(false)
      setOrderId('')
      setInvoiceId('')
      setCustomerRef('')
    },
  })

  const handleCreate = () => {
    const amt = parseFloat(amount) || 0
    const fee = amt * 0.0236 // 2% + 18% GST
    const net = amt - fee
    createMutation.mutate({
      order_id: orderId || `order_MANUAL_${Date.now().toString().slice(-4)}`,
      invoice_id: invoiceId || `INV-${Date.now().toString().slice(-4)}`,
      customer_reference: customerRef || 'direct_customer@acme.com',
      expected_amount: amt,
      expected_currency: 'INR',
      expected_fee: fee,
      expected_tax: fee * 0.18,
      expected_net_amount: net,
      expected_status: 'captured',
      transaction_date: new Date().toISOString(),
      source: 'merchant_erp',
    })
  }

  const filteredEntries = (entries || []).filter((e) => {
    if (!searchTerm.trim()) return true
    const term = searchTerm.toLowerCase()
    return (
      e.order_id.toLowerCase().includes(term) ||
      e.invoice_id?.toLowerCase().includes(term) ||
      e.customer_reference?.toLowerCase().includes(term)
    )
  })

  return (
    <div className="flex-1 space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30">
              Source of Truth
            </Badge>
            <Badge variant="secondary" className="font-mono text-xs">
              Expected Financial Events
            </Badge>
          </div>
          <h1 className="text-2xl font-bold tracking-tight mt-1 text-foreground">Merchant Expected Ledger</h1>
          <p className="text-muted-foreground text-sm">
            What the merchant expects to happen (orders, promised nets, invoice terms) prior to gateway capture and settlement.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            className="gap-2"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            <RefreshCw className={`h-4 w-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
            Sync Razorpay Gateway
          </Button>

          <Button className="gap-2 bg-primary text-primary-foreground" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" />
            Add Expected Order
          </Button>
        </div>
      </div>

      {/* Integration Status Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
              <Globe className="h-5 w-5" />
            </div>
            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold block">Razorpay Connector</span>
              <span className="text-sm font-bold text-foreground">API Test Mode Active</span>
            </div>
          </div>
          <Badge className="bg-emerald-500/15 text-emerald-600 border-emerald-500/30">CONNECTED</Badge>
        </Card>

        <Card className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold block">Webhook Idempotency</span>
              <span className="text-sm font-bold text-foreground">HMAC-SHA256 Guard</span>
            </div>
          </div>
          <Badge variant="outline" className="text-xs font-mono">ACTIVE</Badge>
        </Card>

        <Card className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold block">Ledger Records</span>
              <span className="text-sm font-bold text-foreground">{entries?.length ?? 0} Expected Orders</span>
            </div>
          </div>
          <Badge variant="secondary" className="text-xs">STORED</Badge>
        </Card>
      </div>

      {/* Search & Filter */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search order, invoice, customer..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Ledger Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="py-16 text-center text-muted-foreground">Loading merchant ledger...</div>
          ) : filteredEntries.length === 0 ? (
            <div className="py-16 text-center">
              <FileSpreadsheet className="h-10 w-10 text-muted-foreground/50 mx-auto mb-2" />
              <p className="font-medium text-foreground">No ledger entries found</p>
              <p className="text-sm text-muted-foreground">Add an expected order or run the demo reconciliation to populate data.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[140px]">Order ID</TableHead>
                    <TableHead className="w-[130px]">Invoice Ref</TableHead>
                    <TableHead className="w-[170px]">Customer</TableHead>
                    <TableHead className="w-[130px] text-right">Expected Amount</TableHead>
                    <TableHead className="w-[110px] text-right">Expected Fee</TableHead>
                    <TableHead className="w-[130px] text-right">Expected Net</TableHead>
                    <TableHead className="w-[110px]">Status</TableHead>
                    <TableHead className="w-[100px] text-right">Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEntries.map((e) => (
                    <TableRow key={e.id}>
                      <TableCell className="font-mono text-xs font-semibold text-foreground">{e.order_id}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">{e.invoice_id || '—'}</TableCell>
                      <TableCell className="text-xs truncate max-w-[170px]">{e.customer_reference || 'Guest Checkout'}</TableCell>
                      <TableCell className="text-right font-mono font-bold text-foreground tabular-nums">
                        ₹{Number(e.expected_amount).toLocaleString('en-IN')}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs text-muted-foreground tabular-nums">
                        ₹{Number(e.expected_fee).toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right font-mono font-semibold text-emerald-600 tabular-nums">
                        ₹{Number(e.expected_net_amount).toLocaleString('en-IN')}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-[10px] uppercase font-mono">
                          {e.expected_status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right text-xs text-muted-foreground font-mono">
                        {new Date(e.transaction_date).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Order Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add Expected Order</DialogTitle>
            <DialogDescription>Record a new expected transaction in the merchant internal ledger</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label>Order ID</Label>
              <Input placeholder="e.g. order_MCH_1082" value={orderId} onChange={(e) => setOrderId(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Invoice Number</Label>
              <Input placeholder="e.g. INV-2026-082" value={invoiceId} onChange={(e) => setInvoiceId(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Customer Reference</Label>
              <Input placeholder="e.g. client@example.com" value={customerRef} onChange={(e) => setCustomerRef(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Expected Amount (₹ INR)</Label>
              <Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={createMutation.isPending}>Save to Ledger</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
