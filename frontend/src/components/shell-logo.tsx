interface ShellLogoProps {
  size?: number
  className?: string
}

/**
 * AdaptiveAI Finance Controller Primary Vector Mark
 * Continuous adaptive dual-arc loop and precision verification vector
 */
export function ShellLogo({ size = 24, className }: ShellLogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 460 460"
      preserveAspectRatio="xMidYMid meet"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="AdaptiveAI Mark"
    >
      <g fill="currentColor" stroke="none">
        {/* Adaptive Continuous Flow Loop - Upper Curve */}
        <path d="M 230,45 C 130,45 60,115 60,215 C 60,265 85,310 125,340 C 135,348 148,342 148,330 C 148,322 142,315 135,310 C 105,285 86,252 86,215 C 86,130 148,71 230,71 C 312,71 374,130 374,215 C 374,248 358,280 332,302 C 324,308 322,318 326,327 C 330,336 341,340 350,333 C 382,305 400,262 400,215 C 400,115 330,45 230,45 Z" />

        {/* Verification Check & Ascending Settlement Vector */}
        <path d="M 120,240 C 112,232 100,232 92,240 C 84,248 84,260 92,268 L 180,356 C 188,364 200,364 208,356 L 388,140 C 396,132 396,120 388,112 C 380,104 368,104 360,112 L 194,312 L 120,240 Z" />

        {/* Precision Reconciliation Core Node */}
        <circle cx="230" cy="215" r="32" />
      </g>
    </svg>
  )
}
