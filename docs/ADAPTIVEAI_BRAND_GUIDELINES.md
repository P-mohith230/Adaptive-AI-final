# AdaptiveAI Brand Guidelines

## 1. Brand Overview

### Brand Name
**AdaptiveAI Finance Controller**

### Short Name
**AdaptiveAI**

### Product Positioning
*AI-powered financial control for modern merchants.*

### Core Message
> **Reconcile. Verify. Explain. Act.**  
> *From transaction data to verified financial intelligence.*

---

## 2. Visual Principles

1. **Precision & Trust First**  
   Financial operators and merchant CFOs require absolute audit confidence. Visual elements prioritize sharp geometry, high contrast, crisp data density, and unambiguous status indicators.
2. **Deterministic Grounding**  
   AI capabilities are represented not as magical or decorative, but as continuous mathematical verification loops grounded in double-entry general ledger truth.
3. **Institutional Elegance**  
   Modern institutional fintech aesthetic: deep obsidian and navy surfaces, subtle slate borders (`#1E293B`), restrained lighting, and an intelligent electric blue accent (`#2563EB`).
4. **Zero Fluff & Zero Childish Imagery**  
   No cute mascots, generic robots, cryptocurrency neons, or casual consumer budgeting metaphors.

---

## 3. Logo Usage

The AdaptiveAI mark combines a continuous closed reconciliation ribbon, multi-stream transaction vectors, and an upward verification checkmark.

### Logo Variants
- **Primary Full Wordmark**: Vector mark alongside `AdaptiveAI` bold wordmark and `FINANCE CONTROLLER` tracking subline. Used on documentation, marketing, and the desktop login brand panel.
- **Compact Mark**: Standalone vector geometry. Used for sidebars, mobile headers, browser tabs, and app icons.
- **Monochrome Version**: Renders cleanly with `currentColor` for dark and light UI themes.

### Sizing & Aspect Ratios
- **Scalability**: Designed on a 32x32 / 460x460 responsive vector grid, rendering without distortion at `16x16`, `32x32`, `48x48`, `64x64`, `128x128`, `256x256`, and `512x512`.
- **Clear Space**: Maintain clear space equal to at least 25% of the mark's width on all four sides.

---

## 4. Favicon

- **Geometric Form**: Dark obsidian container (`#0B0F17`) with the electric cyan/blue adaptive loop and verification strike.
- **Micro-Scale Optimization**: Formulated without micro-text to remain instantly recognizable at `16x16` and `32x32` browser tabs.
- **Asset Suite**:
  - `favicon.svg` — Infinite resolution vector favicon
  - `favicon.ico` — Multi-layered Windows/browser icon (`16x16`, `32x32`, `48x48`)
  - `favicon-16x16.png`, `favicon-32x32.png`, `favicon-96x96.png` — Crisp raster backups
  - `apple-touch-icon.png` (180x180) & `android-icon-192x192.png` — Mobile PWA icons

---

## 5. Color System

### Primary Institutional Foundation
| Token | Hex | Usage |
|---|---|---|
| **Obsidian Slate (Dark Surface)** | `#0B0F17` | Canvas background, auth brand panel, favicon ground |
| **Deep Charcoal** | `#0F172A` | Sidebar background, elevated card base |
| **Precision Slate Border** | `#1E293B` | Subtle card borders, dividers, table boundaries |
| **Foreground Text** | `#F8FAFC` | Primary headlines and high-emphasis numbers |
| **Muted Slate** | `#94A3B8` | Subtitles, field labels, metadata descriptions |

### Intelligent Accents
| Token | Hex | Usage |
|---|---|---|
| **Electric Cobalt** | `#2563EB` | Primary brand action, active navigation, key CTA |
| **Cyan Telemetry** | `#38BDF8` / `#06B6D4` | AI signals, stream gradients, active node glows |

### Semantic Financial Status
| State | Hex | Usage |
|---|---|---|
| **Verified / Success** | `#10B981` | 3-way matched records, healthy balances, posted ledger journals |
| **Exception / Warning** | `#F59E0B` | Fee variances, timing float delays, manual approval required |
| **Discrepancy / Critical** | `#EF4444` | Missing gateway captures, unauthorized deductions, negative cash |
| **In-Transit / Info** | `#3B82F6` | Razorpay T+2 clearing float, queued payouts |

---

## 6. Typography

- **Primary Typeface**: `Geist Sans`, `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`.
- **Monospace Financial Numerics**: Monospace font (`Geist Mono`, `monospace`, `tabular-nums`) for currency amounts, transaction IDs, UTR numbers, and match rates.
- **Hierarchy**:
  - Display Title: 24px - 32px (Semi-bold, letter-spacing `-0.02em`)
  - Section Headings: 16px - 18px (Semi-bold)
  - Dashboard Body: 13px - 14px (Regular, leading relaxed)
  - Micro Badges & Labels: 10px - 11px (Medium / Semi-bold, uppercase tracking `0.12em`)

---

## 7. Iconography

- Minimalist Lucide stroke icons styled at `1.5px` - `2px` stroke weight.
- Never use filled emoji or inconsistent third-party cartoon icons.
- Icons serve functional clarity: `Scale` for Reconciliation, `ShieldCheck` for Audit Trail, `FileSpreadsheet` for Expected Ledger, `Building2` for Banks.

---

## 8. Illustration Style

- **Abstract Vector Networks**: Multi-tiered transaction streams connecting through geometric reconciliation nodes.
- **Technical Non-Photorealistic Art**: Precision dashed arcs, glowing nexus nodes, and flow vectors.
- **Strictly Prohibited**: Stock photos of office workers, cartoon robots, floating piggy banks, crypto coins.

---

## 9. Login Experience

- **Desktop (>= 1024px)**: Elegant two-column layout. The left column presents the high-contrast `AuthBrandPanel` showcasing the transaction stream visualization, trust metrics (`3-Way Match`, `1,282 rec/s`, `0.0% Variance`), and value pillars. The right column displays the clean, focused authentication card.
- **Mobile (< 1024px)**: Brand panel gracefully collapses. The authentication card takes center stage with the compact AdaptiveAI mark and headline: *"Financial control, intelligently automated."*
- **Auth Integrity**: Full retention of Passkeys (WebAuthn), TOTP 2FA, Passwords, and Enterprise OIDC SSO.

---

## 10. Dashboard Experience

- **Institutional Terminology**:
  - *Financial Overview* → **Finance Control Center**
  - *Budgets* → **Financial Controls**
  - *Reports* → **Financial Intelligence**
  - *Reconciliation* → **3-Way Reconciliation Workstation**
  - *Ledger* → **Merchant Expected Ledger**
- **High Density & Legibility**:
  - Key performance indicators (Match Rate, Unresolved Exceptions, Trapped Cash Float) pinned prominently.
  - Tabular data formatted with fixed columns, alignment, and hover inspection.

---

## 11. Accessibility (WCAG 2.1 AA)

- All text meets or exceeds a `4.5:1` contrast ratio against dark and light surfaces.
- All non-decorative iconography and action buttons feature descriptive `aria-label` or screen-reader tooltips.
- Visual illustrations include `aria-hidden="true"` so assistive technologies focus on interactive form controls.
- Keyboard navigation with visible focus rings (`ring-2 ring-primary`) across all controls.

---

## 12. Do / Don't

| Do | Don't |
|---|---|
| Use **AdaptiveAI Finance Controller** as full name | Don't use Securo, Securo Finance, or personal budgeting names |
| Use tabular numbers for financial figures | Don't use variable-width fonts for currency figures |
| Keep the color palette disciplined (Obsidian + Slate + Electric Blue) | Don't use multi-colored rainbow gradients or neons |
| Retain AGPL-3.0 open-source legal attribution | Don't remove third-party copyright headers from libraries |
| Use abstract, vector financial stream illustrations | Don't use generic robot icons or human stock photos |
