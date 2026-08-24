# CloudGuard DR — UI/UX Design Specification

**Version:** 1.0 (MVP)
**Date:** August 22, 2026
**Project:** CloudGuard DR — Dashboard UI/UX

---

## 1. Design Principles

1. **Score first, details second** — A manager should understand system health in under 5 seconds
2. **Failures are visually loud** — Red for failures, not hidden behind green summaries
3. **Comparison reads left-to-right** — Like a table, not scrolling between pages
4. **Dark, minimal, technical** — AI startup + developer docs + premium SaaS aesthetic
5. **Engineering product feel** — Dense typography, monospace numbers, terminal UI elements

---

## 2. Color System

### Backgrounds

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg-primary` | `#0A0A0A` | Main page background |
| `--bg-secondary` | `#111111` | Secondary sections, sidebars |
| `--bg-card` | `#151515` | Card backgrounds |
| `--bg-elevated` | `#1A1A1A` | Elevated cards, modals |
| `--bg-input` | `#0D0D0D` | Form inputs |
| `--border-primary` | `#292929` | Card borders, dividers |
| `--border-muted` | `#202020` | Subtle separators |

### Text

| Token | Hex | Usage |
|-------|-----|-------|
| `--text-primary` | `#F5F5F5` | Headings, important text |
| `--text-secondary` | `#A1A1A1` | Body text, descriptions |
| `--text-muted` | `#666666` | Labels, timestamps |
| `--text-code` | `#8B8B8B` | Monospace text, IDs |

### Accent

| Token | Hex | Usage |
|-------|-----|-------|
| `--accent-primary` | `#2563EB` | Buttons, links, active states, graph lines |
| `--accent-hover` | `#3B82F6` | Hover states |
| `--accent-muted` | `rgba(37,99,235,0.15)` | Subtle blue backgrounds |

### Status

| Token | Hex | Usage |
|-------|-----|-------|
| `--status-pass` | `#22C55E` | Passed tests, improvements |
| `--status-fail` | `#EF4444` | Failed tests, regressions |
| `--status-warn` | `#F59E0B` | Incomplete runs, warnings |
| `--status-info` | `#3B82F6` | In-progress states |

---

## 3. Typography

### Font Stack

```css
/* Primary — Inter */
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Monospace — JetBrains Mono (for code, numbers, terminal UI) */
--font-mono: 'JetBrains Mono', 'IBM Plex Mono', 'Fira Code', monospace;
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
┌─────────────────────────────────────────────────────────────────────┐
│  CLOUDGUARD   Dashboard   Runs   Compare   Settings         [Avatar]│
├─────────────────────────────────────────────────────────────────────┤
```

- Background: `#0A0A0A` with `1px solid #222` bottom border
- Height: 56px
- Nav items: 13px, Inter, weight 400
- Active item: blue text + 2px blue bottom border
- Logo: 14px bold, monospace
- Avatar: 32px circle, shows initial
- No hamburger on desktop; hamburger menu on mobile (< 768px)

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

- Card: `#151515` bg, `1px solid #292929`
- Score number: 64px, JetBrains Mono, weight 700
- Score color: blue if ≥ 70, yellow if 50–69, red if < 50
- Progress bar: thin (4px), blue fill, gray track
- RTO/RPO: monospace, with colored dot (green = under target, red = over)
- Status badge: small pill, green bg for PASSED, red bg for FAILED
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
background: #2563EB;
color: white;
font-size: 13px;
font-weight: 500;
padding: 8px 16px;
border-radius: 4px;
border: none;
height: 38px;
```

**Secondary Button:**
```css
background: transparent;
color: #A1A1A1;
border: 1px solid #292929;
```

**Danger Button:**
```css
background: #EF4444;
color: white;
```

- No pill-shaped buttons (sharp, technical feel)
- Hover: lighten by 10%
- Disabled: 50% opacity, no pointer cursor

### 5.8 Form Inputs

```css
background: #0D0D0D;
border: 1px solid #292929;
color: #F5F5F5;
font-size: 14px;
padding: 8px 12px;
border-radius: 4px;
height: 38px;

/* Focus */
border-color: #2563EB;
outline: none;
box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
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

## 10. Dark Mode (Default — No Light Mode)

The entire application is dark-mode only. No theme toggle.

**Rationale:** The product is a technical monitoring tool. Dark mode is the standard for dashboards, terminals, and engineering tools.

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
| **React Router v6** | Client-side routing |
| **Recharts** | Charts and data visualization |
| **Lucide React** | Icons |
| **CSS Modules** | Scoped styling (or Tailwind — TBD) |
| **Axios** | HTTP client |
| **AWS Amplify** (or raw Cognito SDK) | Authentication |

---

## 15. Design Tokens (CSS Variables)

```css
:root {
  /* Backgrounds */
  --bg-primary: #0A0A0A;
  --bg-secondary: #111111;
  --bg-card: #151515;
  --bg-elevated: #1A1A1A;
  --bg-input: #0D0D0D;

  /* Borders */
  --border-primary: #292929;
  --border-muted: #202020;
  --border-focus: #2563EB;

  /* Text */
  --text-primary: #F5F5F5;
  --text-secondary: #A1A1A1;
  --text-muted: #666666;
  --text-code: #8B8B8B;

  /* Accent */
  --accent-primary: #2563EB;
  --accent-hover: #3B82F6;
  --accent-muted: rgba(37, 99, 235, 0.15);

  /* Status */
  --status-pass: #22C55E;
  --status-fail: #EF4444;
  --status-warn: #F59E0B;
  --status-info: #3B82F6;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-16: 64px;
  --space-20: 80px;
  --space-24: 120px;

  /* Typography */
  --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'IBM Plex Mono', 'Fira Code', monospace;

  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;

  /* Shadows */
  --shadow-card: none; /* Use borders, not shadows */
  --shadow-elevated: none;

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 300ms ease;
  --transition-slow: 600ms ease;
}
```
