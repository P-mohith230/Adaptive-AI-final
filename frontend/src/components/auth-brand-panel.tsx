import { AdaptiveLogo } from '@/components/brand/adaptive-logo'
import { CheckCircle2, ShieldCheck, Zap } from 'lucide-react'

/**
 * AdaptiveAI Finance Controller - Auth Brand Panel
 * Institutional fintech visualization depicting transaction streams,
 * reconciliation nodes, verified settlement vectors, and AI intelligence signals.
 */
export function AuthBrandPanel() {
  return (
    <div className="relative hidden overflow-hidden p-12 text-white lg:flex lg:flex-col lg:justify-between bg-[#0B0F17] border-r border-border/40 select-none">
      {/* Background Architectural Grid */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.035]"
        style={{
          backgroundImage: `linear-gradient(#38BDF8 1px, transparent 1px), linear-gradient(to right, #38BDF8 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
        }}
      />

      {/* Subtle Deep Radial Ambient Lighting */}
      <div
        aria-hidden
        className="pointer-events-none absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full opacity-20 blur-3xl"
        style={{
          background: 'radial-gradient(circle, #2563EB 0%, rgba(15, 23, 42, 0) 70%)',
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-40 -right-40 w-[600px] h-[600px] rounded-full opacity-15 blur-3xl"
        style={{
          background: 'radial-gradient(circle, #06B6D4 0%, rgba(15, 23, 42, 0) 70%)',
        }}
      />

      {/* Top Header Wordmark */}
      <div className="relative z-10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AdaptiveLogo size={32} />
          <div className="flex flex-col">
            <span className="text-xl font-bold tracking-tight text-white leading-none">
              Adaptive<span className="text-blue-400 font-extrabold">AI</span>
            </span>
            <span className="text-[10px] font-semibold tracking-widest text-slate-400 uppercase mt-1">
              Finance Controller
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-[11px] font-medium text-blue-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>Institutional Core</span>
        </div>
      </div>

      {/* Center: Abstract Financial Control & Reconciliation Visualization */}
      <div className="relative z-10 my-auto py-8">
        <div className="relative w-full max-w-[480px] mx-auto">
          {/* Abstract Vector Network */}
          <svg
            viewBox="0 0 480 260"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="w-full h-auto drop-shadow-2xl"
          >
            <defs>
              <linearGradient id="stream-merchant" x1="20" y1="40" x2="240" y2="130" gradientUnits="userSpaceOnUse">
                <stop stopColor="#38BDF8" stopOpacity="0.8" />
                <stop offset="1" stopColor="#2563EB" stopOpacity="0.4" />
              </linearGradient>
              <linearGradient id="stream-gateway" x1="20" y1="130" x2="240" y2="130" gradientUnits="userSpaceOnUse">
                <stop stopColor="#60A5FA" stopOpacity="0.9" />
                <stop offset="1" stopColor="#2563EB" stopOpacity="0.5" />
              </linearGradient>
              <linearGradient id="stream-bank" x1="20" y1="220" x2="240" y2="130" gradientUnits="userSpaceOnUse">
                <stop stopColor="#34D399" stopOpacity="0.8" />
                <stop offset="1" stopColor="#10B981" stopOpacity="0.4" />
              </linearGradient>
              <linearGradient id="settlement-vector" x1="240" y1="130" x2="450" y2="130" gradientUnits="userSpaceOnUse">
                <stop stopColor="#2563EB" />
                <stop offset="1" stopColor="#10B981" />
              </linearGradient>
            </defs>

            {/* Input Streams: Merchant Orders, Gateway Telemetry, Bank MT940 */}
            <path d="M 40,50 Q 140,50 240,130" stroke="url(#stream-merchant)" strokeWidth="2.5" strokeDasharray="6 4" />
            <path d="M 40,130 L 240,130" stroke="url(#stream-gateway)" strokeWidth="3" />
            <path d="M 40,210 Q 140,210 240,130" stroke="url(#stream-bank)" strokeWidth="2.5" strokeDasharray="6 4" />

            {/* Ingestion Nodes */}
            <circle cx="40" cy="50" r="7" fill="#0F172A" stroke="#38BDF8" strokeWidth="2" />
            <text x="56" y="54" fill="#94A3B8" fontSize="11" fontFamily="monospace" fontWeight="500">
              MERCHANT ORDERS
            </text>

            <circle cx="40" cy="130" r="7" fill="#0F172A" stroke="#60A5FA" strokeWidth="2" />
            <text x="56" y="134" fill="#94A3B8" fontSize="11" fontFamily="monospace" fontWeight="500">
              GATEWAY TELEMETRY
            </text>

            <circle cx="40" cy="210" r="7" fill="#0F172A" stroke="#34D399" strokeWidth="2" />
            <text x="56" y="214" fill="#94A3B8" fontSize="11" fontFamily="monospace" fontWeight="500">
              BANK SETTLEMENT (MT940)
            </text>

            {/* Central Deterministic Reconciliation Nexus */}
            <circle cx="240" cy="130" r="34" fill="#0F172A" stroke="#2563EB" strokeWidth="2" />
            <circle cx="240" cy="130" r="26" fill="#1E293B" stroke="#38BDF8" strokeWidth="1.5" strokeDasharray="3 3" />
            <circle cx="240" cy="130" r="14" fill="#2563EB" />
            <circle cx="240" cy="130" r="6" fill="#FFFFFF" />

            {/* Verified Settlement & Intelligence Vector Outflow */}
            <path d="M 274,130 L 440,130" stroke="url(#settlement-vector)" strokeWidth="3.5" />

            {/* Output Verified Ledger Nodes */}
            <circle cx="440" cy="130" r="8" fill="#0F172A" stroke="#10B981" strokeWidth="2.5" />
            <path d="M 436,130 L 439,133 L 445,127" stroke="#10B981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <text x="360" y="112" fill="#10B981" fontSize="11" fontFamily="sans-serif" fontWeight="600">
              VERIFIED MATCH
            </text>

            {/* Exception Isolation Branch */}
            <path d="M 264,146 Q 340,200 440,200" stroke="#F59E0B" strokeWidth="1.8" strokeDasharray="4 3" />
            <circle cx="440" cy="200" r="6" fill="#0F172A" stroke="#F59E0B" strokeWidth="2" />
            <text x="350" y="222" fill="#F59E0B" fontSize="10" fontFamily="sans-serif" fontWeight="500">
              AI EXCEPTION QUEUE
            </text>
          </svg>

          {/* Micro Telemetry Metrics Card */}
          <div className="mt-4 grid grid-cols-3 gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
            <div>
              <span className="block text-[10px] uppercase tracking-wider text-slate-400 font-medium">Reconciliation</span>
              <span className="text-sm font-bold text-emerald-400 font-mono">3-Way Match</span>
            </div>
            <div>
              <span className="block text-[10px] uppercase tracking-wider text-slate-400 font-medium">Throughput</span>
              <span className="text-sm font-bold text-blue-400 font-mono">1,282 rec/s</span>
            </div>
            <div>
              <span className="block text-[10px] uppercase tracking-wider text-slate-400 font-medium">Arithmetic Check</span>
              <span className="text-sm font-bold text-cyan-400 font-mono">0.0% Variance</span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Copy: Core Value Proposition */}
      <div className="relative z-10 max-w-md space-y-4">
        <div className="space-y-2">
          <h2 className="text-3xl font-semibold tracking-tight text-white leading-tight">
            Financial control, <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-300 to-emerald-400">
              intelligently automated.
            </span>
          </h2>
          <p className="text-sm leading-relaxed text-slate-400">
            Reconcile transactions, investigate exceptions, and turn payment data into verified financial intelligence.
          </p>
        </div>

        {/* Institutional Trust Indicators */}
        <div className="flex items-center gap-4 pt-2 border-t border-slate-800/80 text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 size={14} className="text-emerald-400 shrink-0" />
            <span>Deterministic Match</span>
          </div>
          <div className="flex items-center gap-1.5">
            <ShieldCheck size={14} className="text-blue-400 shrink-0" />
            <span>Audit-Ready Ledger</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Zap size={14} className="text-cyan-400 shrink-0" />
            <span>Sub-second SLA</span>
          </div>
        </div>
      </div>
    </div>
  )
}
