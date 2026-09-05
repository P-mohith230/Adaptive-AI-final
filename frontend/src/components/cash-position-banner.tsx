import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Building2,
  AlertTriangle,
  Wallet,
  ArrowUpRight,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import { reconciliation } from '@/lib/api'

export function CashPositionBanner({ showSyncButton = true }: { showSyncButton?: boolean }) {
  const queryClient = useQueryClient()

  const { data: forecast, isLoading } = useQuery({
    queryKey: ['cash-forecast'],
    queryFn: reconciliation.getCashForecast,
    refetchInterval: 15000,
  })

  const syncMutation = useMutation({
    mutationFn: async () => {
      const res = await reconciliation.syncLedger()
      return res
    },
    onSuccess: (res) => {
      toast.success(
        `AdaptiveAI Ledger Synced: ${res.synced_clean || 0} posted, ${res.synced_exceptions || 0} suspense exceptions`,
        { description: 'Bank & Clearing account balances updated.' }
      )
      queryClient.invalidateQueries({ queryKey: ['cash-forecast'] })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-kpi'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
    },
    onError: (err: Error) => {
      toast.error('Sync failed', { description: err.message })
    },
  })

  if (isLoading || !forecast) {
    return null
  }

  const liquid = Number(forecast.liquid_bank_balance || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  const inTransit = Number(forecast.in_transit_clearing || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  const exposure = Number(forecast.unresolved_exception_exposure || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  const netWorking = Number(forecast.net_reliable_cash_position || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })

  return (
    <Card className="border-border/60 bg-gradient-to-r from-card via-card to-primary/5 shadow-sm overflow-hidden">
      <CardContent className="p-4 sm:p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4 mb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Wallet className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-foreground text-sm sm:text-base">
                  Real-Time Cash Position & Liquidity Engine
                </h3>
                <Badge variant="outline" className="bg-emerald-500/10 text-emerald-600 border-emerald-500/30 text-[11px]">
                  Live Ledger Bridge
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                Grounded in verified HDFC Operating settlements and Razorpay T+2 float calculations.
              </p>
            </div>
          </div>

          {showSyncButton && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5 text-xs h-8"
                onClick={() => syncMutation.mutate()}
                disabled={syncMutation.isPending}
              >
                <RefreshCw className={`h-3.5 w-3.5 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
                Sync with AdaptiveAI Core Ledger
              </Button>
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
          {/* 1. Liquid Bank Cash */}
          <div className="bg-background/80 rounded-lg p-3.5 border border-border/50 flex flex-col justify-between min-h-[104px]">
            <div className="flex items-center justify-between text-muted-foreground text-xs mb-1">
              <span className="font-medium">Liquid Bank Cash</span>
              <Building2 className="h-4 w-4 text-emerald-500 shrink-0" />
            </div>
            <div>
              <div className="text-lg sm:text-xl font-extrabold text-foreground font-mono tabular-nums">₹{liquid}</div>
              <div className="text-[11px] text-muted-foreground mt-0.5">
                Settled in HDFC Operating Account
              </div>
            </div>
          </div>

          {/* 2. In-Transit Float */}
          <div className="bg-background/80 rounded-lg p-3.5 border border-border/50 flex flex-col justify-between min-h-[104px]">
            <div className="flex items-center justify-between text-muted-foreground text-xs mb-1">
              <span className="font-medium">In-Transit Float</span>
              <ArrowUpRight className="h-4 w-4 text-blue-500 shrink-0" />
            </div>
            <div>
              <div className="text-lg sm:text-xl font-extrabold text-blue-500 font-mono tabular-nums">₹{inTransit}</div>
              <div className="text-[11px] text-muted-foreground mt-0.5">
                T+2 Razorpay Gateway Clearing
              </div>
            </div>
          </div>

          {/* 3. At-Risk Trapped Exposure */}
          <div className="bg-background/80 rounded-lg p-3.5 border border-border/50 flex flex-col justify-between min-h-[104px]">
            <div className="flex items-center justify-between text-muted-foreground text-xs mb-1">
              <span className="font-medium">Trapped Exposure</span>
              <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
            </div>
            <div>
              <div className="text-lg sm:text-xl font-extrabold text-amber-500 font-mono tabular-nums">₹{exposure}</div>
              <div className="text-[11px] text-muted-foreground mt-0.5">
                Pending investigation & dispute
              </div>
            </div>
          </div>

          {/* 4. Net Reliable Working Capital */}
          <div className="bg-primary/5 rounded-lg p-3.5 border border-primary/20 flex flex-col justify-between min-h-[104px]">
            <div className="flex items-center justify-between text-muted-foreground text-xs mb-1">
              <span className="font-medium text-foreground">Net Working Capital</span>
              <ShieldCheck className="h-4 w-4 text-primary shrink-0" />
            </div>
            <div>
              <div className="text-lg sm:text-xl font-extrabold text-primary font-mono tabular-nums">₹{netWorking}</div>
              <div className="text-[11px] text-muted-foreground mt-0.5">
                Available liquidity after risk haircut
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
