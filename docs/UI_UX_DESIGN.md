# CloudGuard DR — UI/UX Design Specification

**Version:** 2.0 (Ethereal Glass)
**Date:** August 24, 2026
**Project:** CloudGuard DR — Dashboard UI/UX
**Aesthetic:** Ethereal Glass — dark tech, premium SaaS, glassmorphism

---

## 1. Design Principles

1. **Score first, details second** — A manager should understand system health in under 5 seconds
2. **Failures are visually loud** — Red for failures, not hidden behind green summaries
3. **Comparison reads left-to-right** — Like a table, not scrolling between pages
4. **Dark, glass, technical** — AI startup + developer docs + premium SaaS aesthetic with glassmorphism
5. **Engineering product feel** — Dense typography, monospace numbers, terminal UI elements

---

## 2. Color System

### Backgrounds

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-primary` | `#050508` | Main page background (OLED-grade) |
| `--bg-secondary` | `#0c0c10` | Secondary sections, sidebars |
| `--bg-card` | `rgba(15, 15, 20, 0.7)` | Card backgrounds (glass) |
| `--bg-elevated` | `rgba(20, 20, 28, 0.8)` | Elevated cards, modals (glass) |
| `--bg-input` | `#0a0a0e` | Form inputs |
| `--bg-hover` | `rgba(255, 255, 255, 0.03)` | Hover states |
| `--bg-glass` | `rgba(255, 255, 255, 0.03)` | Glass surfaces |
| `--bg-glass-hover` | `rgba(255, 255, 255, 0.06)` | Glass hover |
| `--border-primary` | `rgba(255, 255, 255, 0.06)` | Card borders (hairline) |
| `--border-muted` | `rgba(255, 255, 255, 0.04)` | Subtle separators |
| `--border-glass` | `rgba(255, 255, 255, 0.08)` | Glass card borders |

### Text

| Token | Hex | Usage |
|-------|-----|-------|
| `--text-primary` | `#e8e8ec` | Headings, important text |
| `--text-secondary` | `#8a8a95` | Body text, descriptions |
| `--text-muted` | `#505060` | Labels, timestamps |
| `--text-code` | `#6a6a78` | Monospace text, IDs |

### Accent

| Token | Value | Usage |
|-------|-------|-------|
| `--accent-primary` | `#10b981` | Buttons, links, active states, graph lines (teal) |
| `--accent-hover` | `#34d399` | Hover states |
| `--accent-muted` | `rgba(16, 185, 129, 0.1)` | Subtle teal backgrounds |
| `--accent-glow` | `rgba(16, 185, 129, 0.15)` | Glow effects |
| `--accent-subtle` | `rgba(16, 185, 129, 0.05)` | Ultra-subtle teal tints |

### Status

| Token | Hex | Usage |
|-------|-----|-------|
| `--status-pass` | `#10b981` | Passed tests, improvements (matches accent) |
| `--status-fail` | `#f43f5e` | Failed tests, regressions (rose) |
| `--status-warn` | `#f59e0b` | Incomplete runs, warnings |
| `--status-info` | `#6366f1` | In-progress states (indigo) |

---

## 3. Typography

### Font Stack

```css
/* Primary — Outfit */
--font-primary: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;

/* Monospace — JetBrains Mono (for code, numbers, terminal UI) */
--font-mono: 'JetBrains Mono', 'IBM Plex Mono', monospace;
```

### Type Scale

| Level | Size (Desktop) | Size (Mobile) | Weight | Line Height | Letter Spacing |
|-------|---------------|---------------|--------|-------------|----------------|
| Hero | 48–64px | 36–44px | 600–700 | 0.95–1.05 | -0.02em |
| H1 | 32–40px | 28–34px | 600 | 1.1 | -0.01em |
| H2 | 24–28px | 22–26px | 600 | 1.2 | -0.01em |
| H3 | 18–20px | 16–18px | 600 | 1.3 | 0 |
| Body | 14–17px | 14–15px | 400 | 1.5–1.7 | 0 |
| Small | 12–13px | 11–12px | 400 | 1.4 | 0 |
| Label | 10–12px | 9–11px | 500 | 1.2 | 0.08–0.15em (uppercase) |
| Code | 12–14px | 11–13px | 400 | 1.5 | 0 |

### Typography Rules

- **Dense technical typography system** — strong contrast between large headlines and tiny labels
- Labels are uppercase with increased letter spacing
- Monospace font for all numbers, IDs, timestamps, and technical data
- Hero headings are compact and tight (line-height 0.95–1.05)

---

## 4. Spacing System

Base unit: **8px**

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Micro spacing |
| `--space-2` | 8px | Inline elements |
| `--space-3` | 12px | Compact padding |
| `--space-4` | 16px | Standard padding |
| `--space-5` | 20px | Card padding |
| `--space-6` | 24px | Section padding |
| `--space-8` | 32px | Large spacing |
| `--space-10` | 40px | Section gaps |
| `--space-16` | 64px | Major section gaps |
| `--space-20` | 80px | Between page sections |
| `--space-24` | 120px | Hero sections |

---

## 5. Components

### 5.1 Navigation Bar

```
┌──────────────────────────────────────────────────────────────────────┐
│   ● CGDR │ Dashboard  Runs  Compare  Clients  Settings │ ☀/🌙     │
└──────────────────────────────────────────────────────────────────────┘
```

- **Floating glass pill** centered at top, `sticky top: 16px`
- Background: `rgba(10, 10, 14, 0.8)` with `backdrop-filter: blur(24px) saturate(1.4)`
- Border: `1px solid rgba(255, 255, 255, 0.06)`, `border-radius: 9999px`
- Shadow: `0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.04)`
- Nav items: 12px, Outfit, weight 400, icons + labels
- Active item: teal text + subtle teal bg pill
- Logo: "CG**DR**" abbreviated, 12px bold monospace, green live dot
- Theme toggle: Sun/Moon icon button (32px)
- Mobile (< 768px): labels hidden, icons only; hamburger menu overlay
- Dividers: 1px `rgba(255, 255, 255, 0.06)` between logo, nav items, and theme toggle

### 5.2 Score Card (Dashboard Hero)

```
┌─────────────────────────────────────────────────────────┐
│  LATEST RUN                                        ●    │
│                                                         │
│  ██████████████████████░░░░░░  82                       │
│                                                         │
│  RTO: 2m 34s (target: 5m)    RPO: 45s (target: 1m)    │
│                                                         │
│  STATUS: PASSED                    2026-08-22 08:00 UTC │
└─────────────────────────────────────────────────────────┘
```

- Card: glass bg (`rgba(15, 15, 20, 0.7)`), `backdrop-filter: blur(24px)`, glass border
- Score number: 72px, JetBrains Mono, weight 800, with ambient glow radial gradient
- Score color: teal if ≥ 70, yellow if 50–69, rose if < 50
- Progress bar: thin (3px), gradient teal fill with glow shadow, gray track
- RTO/RPO: monospace, displayed as stacked glass metric cards with check/cross indicators
- Status badge: small pill, teal bg for PASSED, rose bg for FAILED
- Score animates from 0 to value over 800ms on mount
- Padding: 32px

### 5.3 Trend Line (Score Over Time)

```
┌─────────────────────────────────────────────────────────┐
│  RESILIENCE TREND                              Last 10  │
│                                                         │
│  100│                                                    │
│   80│        ●───●───●               ●───●               │
│   60│───●───╯                   ●───╯                   │
│   40│                                                    │
│   20│                                                    │
│     └──────────────────────────────────────────────      │
│       Aug 1  Aug 8  Aug 15  Aug 22                      │
└─────────────────────────────────────────────────────────┘
```

- Line chart: thin (2px) blue line, blue dots at data points
- Grid lines: `#202020`, dashed
- Axis labels: 10px, JetBrains Mono, `#666666`
- Hover: show tooltip with run ID, score, timestamp
- Chart library: Chart.js or Recharts (lightweight)

### 5.4 Run List Table

```
┌──────────────────────────────────────────────────────────────────┐
│  RUN ID        STATUS    SCORE   RTO      RPO      DATE        │
├──────────────────────────────────────────────────────────────────┤
│  run-a1b2c3    PASSED    82      2m 34s   45s      Aug 22 08:00│
│  run-d4e5f6    FAILED    45      8m 12s   2m 30s   Aug 15 08:00│
│  run-g7h8i9    PASSED    91      1m 45s   30s      Aug 08 08:00│
└──────────────────────────────────────────────────────────────────┘
```

- Header: uppercase labels, 10px, `#666666`, letter-spacing 0.1em
- Rows: 14px, `#F5F5F5`
- Hover: row bg changes to `#1A1A1A`
- Status: colored dot + text
- Score: JetBrains Mono, colored by value
- Clickable rows → Run Detail page
- Checkbox column for comparison selection (hidden by default)

### 5.5 Comparison View (Side-by-Side)

```
┌──────────────────────────────────────────────────────────────────┐
│  COMPARE RUNS                                             [↓ CSV]│
│                                                                  │
│  SELECT: [Run a1b2c3 ▾]  vs  [Run d4e5f6 ▾]                    │
│                                                                  │
├──────────────────────┬────────────────────┬──────────────────────┤
│  METRIC              │  RUN A1B2C3        │  RUN D4E5F6          │
├──────────────────────┼────────────────────┼──────────────────────┤
│  Score               │  82                │  45  ▼ (-37)        │
│  RTO                 │  2m 34s            │  8m 12s ▲ (+5m 38s) │
│  RPO                 │  45s               │  2m 30s ▲ (+1m 45s) │
│  HTTPS Valid         │  ✓                 │  ✓                   │
│  Response Time       │  142ms             │  318ms ▲ (+176ms)   │
│  DNS Failover        │  ✓                 │  ✗                   │
│  Status              │  PASSED            │  FAILED              │
├──────────────────────┴────────────────────┴──────────────────────┤
│                                                                  │
│  DELTA SUMMARY                                                   │
│  ─────────────────────────────────────────────                   │
│  Score regressed by 37 points                                    │
│  RTO exceeded target by 3m 12s                                   │
│  DNS failover is broken                                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

- Table: thin borders (`1px solid #292929`), no shadows
- Deltas: green text for improvement, red text for regression
- Arrows: ▲ for worse (higher RTO/RPO = worse), ▼ for better
- Delta column appears only when values differ
- Selectors: dark dropdowns with blue accent border on focus
- Responsive: stacks to cards below 768px

### 5.6 Status Badges

```
PASSED    →  Green pill (#22C55E bg, white text, 4px 8px padding)
FAILED    →  Red pill (#EF4444 bg, white text)
INCOMPLETE → Yellow pill (#F59E0B bg, dark text)
IN-PROGRESS → Blue pill (#3B82F6 bg, white text, pulsing animation)
```

- Always use text + color (never color alone for accessibility)
- Font: 11px, weight 600, uppercase, letter-spacing 0.05em
- Border-radius: 4px

### 5.7 Buttons

**Primary Button:**
```css
background: var(--accent-primary); /* #10b981 teal */
color: #050508;
font-size: 13px;
font-weight: 600;
padding: 10px 20px;
border-radius: 9999px; /* pill */
border: none;
box-shadow: 0 0 20px rgba(16, 185, 129, 0.15);
```

**Secondary Button:**
```css
background: var(--bg-glass); /* rgba(255,255,255,0.03) */
backdrop-filter: blur(12px);
color: var(--text-secondary);
border: 1px solid var(--border-glass);
border-radius: 9999px;
```

**Danger Button:**
```css
background: var(--status-fail); /* #f43f5e */
color: white;
font-weight: 600;
border-radius: 9999px;
```

- **Pill-shaped buttons** with glass architecture
- Hover: `translateY(-1px)`, increased glow shadow, `::before` gradient overlay
- Active: `scale(0.96) translateY(1px)`, reduced shadow
- Disabled: 40% opacity, no pointer cursor, no transform

### 5.8 Form Inputs

```css
background: var(--bg-input); /* #0a0a0e */
border: 1px solid var(--border-primary);
color: var(--text-primary);
font-size: 14px;
padding: 10px 14px;
border-radius: var(--radius-sm); /* 8px */
outline: none;

/* Focus */
border-color: var(--accent-primary); /* #10b981 */
outline: none;
box-shadow: 0 0 0 3px var(--accent-subtle), 0 0 20px rgba(16, 185, 129, 0.05);
```

### 5.9 Skeleton Loading States

- Use animated shimmer effect on `#151515` background
- Skeleton shapes match actual content (rectangles for text, circles for scores)
- Animation: `opacity 0.3 → 0.6 → 0.3` over 1.5s, ease-in-out

### 5.10 Empty States

```
┌─────────────────────────────────────────────────┐
│                                                 │
│           [No test runs yet]                    │
│                                                 │
│     Run your first DR test to get started.      │
│                                                 │
│           [ Run First Test ]                    │
│                                                 │
└─────────────────────────────────────────────────┘
```

- Centered, generous whitespace
- Large muted icon (optional)
- Clear call-to-action button

### 5.11 Error States

```
┌─────────────────────────────────────────────────┐
│                                                 │
│           ⚠ Couldn't load this report           │
│                                                 │
│     Check your connection and try again.        │
│                                                 │
│           [ Retry ]                             │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 6. Page Layouts

### 6.1 Dashboard Page

```
┌─────────────────────────────────────────────────────────────────────┐
│  NAV BAR                                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DASHBOARD                                                          │
│  Automated Disaster Recovery Testing                                │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  LATEST RUN SCORE CARD                                      │    │
│  │  Score: 82 | Status: PASSED | RTO: 2m34s | RPO: 45s       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌──────────────────────────────┐  ┌──────────────────────────┐    │
│  │  SCORE TREND LINE            │  │  QUICK STATS             │    │
│  │  (last 10 runs)              │  │  Total Runs: 24          │    │
│  │                              │  │  Pass Rate: 75%          │    │
│  │                              │  │  Avg Score: 76           │    │
│  └──────────────────────────────┘  └──────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  RECENT RUNS TABLE                                         │    │
│  │  (last 5 runs, clickable rows)                             │    │
│  │  [View All Runs →]                                         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  [ Compare Runs ]  [ Run New Test ]                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  FOOTER                                                             │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Run Detail Page

```
┌─────────────────────────────────────────────────────────────────────┐
│  NAV BAR                                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ← Back to Runs                                                     │
│                                                                     │
│  RUN DETAIL: run-a1b2c3                                             │
│  Aug 22, 2026 · 08:00 UTC · ec2-termination                        │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  SCORE: 82          STATUS: PASSED                         │    │
│  │                                                             │    │
│  │  RTO: 2m 34s (target: 5m) ✓                                │    │
│  │  RPO: 45s (target: 1m) ✓                                   │    │
│  │                                                             │    │
│  │  TARGET: i-0abc123def456                                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  STAGE TIMELINE                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ● Inject    ● Monitor    ● Measure    ● Score    ● Report │    │
│  │  08:00:00    08:00:12    08:02:44     08:02:45   08:02:46  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  [ View Full Report ]  [ Compare with... ]                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.3 Runs List Page

```
┌─────────────────────────────────────────────────────────────────────┐
│  NAV BAR                                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  RUNS                                                      [New Test]│
│                                                                     │
│  FILTERS: [Status ▾] [Fault Type ▾] [Date Range]                   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Select runs to compare: [Compare Selected (0)]            │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │  □  run-a1b2c3    PASSED    82     2m34s   45s    Aug 22  │    │
│  │  □  run-d4e5f6    FAILED    45     8m12s   2m30s  Aug 15  │    │
│  │  □  run-g7h8i9    PASSED    91     1m45s   30s    Aug 08  │    │
│  │  □  run-j0k1l2    PASSED    88     2m00s   40s    Aug 01  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  [ ← Previous ]  Page 1 of 5  [ Next → ]                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.4 New Audit Page

```
┌─────────────────────────────────────────────────────────────────────┐
│  NAV BAR                                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  NEW AUDIT                                                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  AUDIT TYPE                                                │    │
│  │                                                             │    │
│  │  ○ Full DR Test (Fault Injection)                          │    │
│  │  ● External Site Audit (Health Check Only)                 │    │
│  │                                                             │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │                                                             │    │
│  │  TARGET URL                                                 │    │
│  │  ┌───────────────────────────────────────────────────┐      │    │
│  │  │ https://example.com                               │      │    │
│  │  └───────────────────────────────────────────────────┘      │    │
│  │                                                             │    │
│  │  [ Run Audit ]                                             │    │
│  │                                                             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.5 Settings Page (Admin)

```
┌─────────────────────────────────────────────────────────────────────┐
│  NAV BAR                                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SETTINGS                                                           │
│                                                                     │
│  THRESHOLDS                                                         │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  RTO Target (seconds):  [ 300 ]                            │    │
│  │  RPO Target (seconds):  [ 60  ]                            │    │
│  │  Score Threshold:       [ 70  ]                            │    │
│  │                                                             │    │
│  │  [ Save Changes ]                                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ALERTS                                                             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  SNS Topic: CloudGuardDR-Alerts                             │    │
│  │  Email: admin@example.com                                   │    │
│  │  [ Update Email ]                                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  SCHEDULE                                                           │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Test Schedule: Weekly (Monday 08:00 UTC)                   │    │
│  │  [ Modify Schedule ]                                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ALERT HISTORY                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Aug 15 — RTO exceeded target (8m 12s > 5m)                │    │
│  │  Aug 01 — Score below threshold (62 < 70)                  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Responsive Behavior

### Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Desktop | ≥ 1024px | Full layout, side-by-side panels |
| Tablet | 768–1023px | Stacked layout, full-width cards |
| Mobile | < 768px | Single column, hamburger nav |

### Mobile-Specific

- **Nav:** Hamburger menu, full-screen overlay
- **Score Card:** Full width, score centered
- **Trend Line:** Horizontally scrollable, not compressed
- **Run Table:** Stacked cards (one per run) instead of table rows
- **Comparison:** Stacked cards (one per item) instead of side-by-side
- **Buttons:** Full width, stacked vertically
- **Side padding:** 20px

---

## 8. Accessibility

| Requirement | Implementation |
|-------------|---------------|
| **Color contrast** | Minimum 4.5:1 ratio for all text |
| **Status indicators** | Color + text label (never color alone) |
| **Keyboard navigation** | All interactive elements reachable via Tab |
| **Focus states** | Visible blue outline on focused elements |
| **Screen reader** | ARIA labels on all interactive elements |
| **Reduced motion** | Respect `prefers-reduced-motion` media query |
| **Alt text** | Descriptive alt text on all meaningful images |
| **Form labels** | All inputs have associated labels |

---

## 9. Animation & Transitions

### Scroll Animations (Fade-In)

```css
/* Entry animation */
.animate-in {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 600ms ease, transform 600ms ease;
}

.animate-in.visible {
  opacity: 1;
  transform: translateY(0);
}
```

### Micro-Interactions

| Element | Animation | Duration |
|---------|-----------|----------|
| Button hover | Background lighten | 150ms |
| Row hover | Background change | 150ms |
| Card appear | Fade in + slide up | 500ms |
| Score counter | Count up from 0 | 800ms |
| Status badge | Pulse (in-progress only) | 2s loop |
| Page transition | Fade | 300ms |

### Reduced Motion

All animations respect `prefers-reduced-motion: reduce` — instant transitions instead.

---

## 10. Theme Support (Dark Default + Light Mode)

The application defaults to dark mode but includes a **light theme** toggled via the navbar.

- Dark theme: OLED-grade blacks, teal accents, glass surfaces
- Light theme: Warm whites, adjusted teal accents, subtle glass effects
- Theme stored in `localStorage` (`cloudguard_theme`)
- Respects `prefers-color-scheme` system preference on first visit
- All glass effects, shadows, and borders have light-theme counterparts in `[data-theme="light"]`

**Rationale:** While dark mode is the default for technical dashboards, supporting light mode improves accessibility and user preference flexibility.

---

## 11. Iconography

- Use **Lucide React** icons (consistent, minimal, technical feel)
- Icon size: 16px (inline), 20px (standalone), 24px (navigation)
- Color: inherit from parent (`currentColor`)

---

## 12. Charts & Data Visualization

### Score Trend Line
- Library: **Recharts** (React-native, lightweight)
- Line: 2px, blue (`#2563EB`)
- Dots: 6px circles, blue fill
- Grid: dashed, `#202020`
- Axis labels: JetBrains Mono, 10px, `#666666`
- Tooltip: dark card (`#1A1A1A`), blue border, monospace values

### Score Distribution (Optional Post-MVP)
- Horizontal bar chart
- Blue bars, gray background
- Labels: monospace

---

## 13. File Structure (Frontend)

```
frontend/src/
├── components/
│   ├── Dashboard/
│   │   ├── ScoreCard.tsx
│   │   ├── TrendLine.tsx
│   │   ├── QuickStats.tsx
│   │   └── RecentRuns.tsx
│   ├── RunDetail/
│   │   ├── RunHeader.tsx
│   │   ├── ScoreBreakdown.tsx
│   │   ├── StageTimeline.tsx
│   │   └── ReportLink.tsx
│   ├── Comparison/
│   │   ├── ComparisonTable.tsx
│   │   ├── DeltaHighlight.tsx
│   │   └── RunSelector.tsx
│   ├── NewAudit/
│   │   ├── AuditForm.tsx
│   │   └── AuditTypeToggle.tsx
│   ├── Settings/
│   │   ├── ThresholdForm.tsx
│   │   ├── AlertConfig.tsx
│   │   └── AlertHistory.tsx
│   ├── Layout/
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx (optional)
│   │   └── Footer.tsx
│   └── shared/
│       ├── StatusBadge.tsx
│       ├── Skeleton.tsx
│       ├── EmptyState.tsx
│       ├── ErrorState.tsx
│       └── Button.tsx
├── hooks/
│   ├── useRuns.ts
│   ├── useRun.ts
│   ├── useCompare.ts
│   └── useAuth.ts
├── utils/
│   ├── api.ts
│   ├── format.ts
│   └── constants.ts
├── context/
│   └── AuthContext.tsx
├── pages/
│   ├── Dashboard.tsx
│   ├── Runs.tsx
│   ├── RunDetail.tsx
│   ├── Compare.tsx
│   ├── NewAudit.tsx
│   └── Settings.tsx
├── styles/
│   ├── globals.css
│   ├── variables.css
│   └── components.css
├── App.tsx
└── main.tsx
```

---

## 14. Tech Stack (Frontend)

| Tool | Purpose |
|------|---------|
| **React 18** | UI framework |
| **TypeScript** | Type safety |
| **Vite** | Build tool / dev server |
| **React Router v7** | Client-side routing |
| **Custom SVG Charts** | Lightweight inline SVG trend charts (no external chart library) |
| **Lucide React** | Icons |
| **Vanilla CSS** | Global styles with CSS custom properties (design tokens) |
| **Axios** | HTTP client with JWT interceptor |
| **Cognito JWT** | Authentication via localStorage token |

---

## 15. Design Tokens (CSS Variables)

```css
:root {
  /* Backgrounds (OLED-grade darks) */
  --bg-primary: #050508;
  --bg-secondary: #0c0c10;
  --bg-card: rgba(15, 15, 20, 0.7);
  --bg-elevated: rgba(20, 20, 28, 0.8);
  --bg-input: #0a0a0e;
  --bg-hover: rgba(255, 255, 255, 0.03);
  --bg-glass: rgba(255, 255, 255, 0.03);
  --bg-glass-hover: rgba(255, 255, 255, 0.06);

  /* Borders (subtle hairlines) */
  --border-primary: rgba(255, 255, 255, 0.06);
  --border-muted: rgba(255, 255, 255, 0.04);
  --border-focus: var(--accent-primary);
  --border-glass: rgba(255, 255, 255, 0.08);

  /* Text */
  --text-primary: #e8e8ec;
  --text-secondary: #8a8a95;
  --text-muted: #505060;
  --text-code: #6a6a78;

  /* Accent (teal) */
  --accent-primary: #10b981;
  --accent-hover: #34d399;
  --accent-muted: rgba(16, 185, 129, 0.1);
  --accent-glow: rgba(16, 185, 129, 0.15);
  --accent-subtle: rgba(16, 185, 129, 0.05);

  /* Status */
  --status-pass: #10b981;
  --status-fail: #f43f5e;
  --status-warn: #f59e0b;
  --status-info: #6366f1;

  /* Spacing (8px base) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
  --space-20: 80px;
  --space-24: 96px;

  /* Typography */
  --font-primary: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'IBM Plex Mono', monospace;

  /* Border Radius */
  --radius-xs: 6px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-2xl: 24px;
  --radius-pill: 9999px;

  /* Transitions (spring-like cubic bezier) */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-spring: cubic-bezier(0.32, 0.72, 0, 1);
  --transition-fast: 200ms var(--ease-out-expo);
  --transition-normal: 400ms var(--ease-out-expo);
  --transition-slow: 700ms var(--ease-out-expo);
  --transition-spring: 500ms var(--ease-out-back);

  /* Shadows (tinted to background) */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);
  --shadow-glow: 0 0 40px rgba(16, 185, 129, 0.08);
  --shadow-inset: inset 0 1px 0 rgba(255, 255, 255, 0.04);

  /* Glass */
  --glass-blur: blur(24px) saturate(1.4);
  --glass-border: 1px solid rgba(255, 255, 255, 0.06);
  --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
}
```
