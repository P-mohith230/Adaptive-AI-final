import { cn } from '@/lib/utils'

export interface AdaptiveLogoProps {
  size?: number
  className?: string
  variant?: 'mark' | 'full'
  showBadge?: boolean
}

/**
 * AdaptiveAI Finance Controller Official Mark & Wordmark
 *
 * Geometric Identity:
 * - Continuous dual-arc adaptive loop representing perpetual closed-loop reconciliation
 * - Intersecting transaction vectors symbolizing flow and settlement precision
 * - Integrated upward verification check structure
 */
export function AdaptiveLogo({
  size = 24,
  className,
  variant = 'mark',
  showBadge = false,
}: AdaptiveLogoProps) {
  const mark = (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn('shrink-0 select-none', className)}
      aria-label="AdaptiveAI Logo"
    >
      <defs>
        <linearGradient id="adaptive-primary" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
          <stop stopColor="#38BDF8" />
          <stop offset="0.5" stopColor="#2563EB" />
          <stop offset="1" stopColor="#1D4ED8" />
        </linearGradient>
        <linearGradient id="adaptive-accent" x1="10" y1="26" x2="26" y2="6" gradientUnits="userSpaceOnUse">
          <stop stopColor="#06B6D4" />
          <stop offset="1" stopColor="#60A5FA" />
        </linearGradient>
      </defs>

      {/* Primary Adaptive Flow Loop */}
      <path
        d="M6 21C4.8 19.2 4 16.8 4 14C4 8.5 8.5 4 14 4C19 4 23.2 7.6 23.9 12.5"
        stroke="url(#adaptive-primary)"
        strokeWidth="3.2"
        strokeLinecap="round"
      />

      {/* Interlocking Verified Settlement Arm & Upward Verification Check */}
      <path
        d="M8.5 16.5L13 21C14.5 22.5 17 22.5 18.5 21L27.5 11"
        stroke="url(#adaptive-accent)"
        strokeWidth="3.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Central Precision Nexus Node */}
      <circle cx="14" cy="13.5" r="2.2" fill="#38BDF8" />
    </svg>
  )

  if (variant === 'mark') {
    return mark
  }

  return (
    <div className={cn('flex items-center gap-2.5 select-none', className)}>
      {mark}
      <div className="flex flex-col">
        <div className="flex items-center gap-1.5">
          <span className="font-bold text-base tracking-tight text-foreground leading-none">
            Adaptive<span className="text-blue-500 font-extrabold">AI</span>
          </span>
          {showBadge && (
            <span className="text-[9px] font-semibold tracking-wider uppercase px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-500 border border-blue-500/20">
              Controller
            </span>
          )}
        </div>
        <span className="text-[9px] font-medium tracking-widest text-muted-foreground uppercase leading-none mt-0.5">
          Finance Controller
        </span>
      </div>
    </div>
  )
}
