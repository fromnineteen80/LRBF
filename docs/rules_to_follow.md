## 0) Prime Directives

- Do not blind-code, skip steps, drift scope, or "tweak" when full-scope work is required.  
- Maintain vertical integration (**backend → API → frontend → MD3**). No standalone or disconnected code.  
- If something is unclear, do not assume. Trace back to the phase plan and source doc; log an explicit question and park the task until answered.  
- Never insert undefined variables, unclosed tags, or partial logic. All logic must compile and pass validation.  
- When editing existing code, do not introduce new elements or variables unless explicitly requested.  
- All work must compile cleanly under our real toolchain; mock-ups and pseudo-behavior are forbidden.  
- Every task must trace to a phase and artifact; maintain end-to-end traceability.  

---

## 0.1) Policy Matrix Reference (authoritative)

- Before any task, read and comply with `/docs/policy_matrix.yaml`.  
- If the matrix and prose ever conflict, the **matrix rules take precedence**.  
- CI and code review enforce compliance with the matrix.  

---

## 0.2) Full-File Reading Discipline

- When asked to read or edit a file, **read the entire file from beginning to end, every time.**  
- Do not skim or infer context. Do not modify structure, headings, comments, fenced blocks, or formatting.  
- Edits must be minimal-diff and limited to the requested lines; no new elements, IDs, or variables unless explicitly requested.  


# Rules to Follow

## 0) Prime Directives

* Do not blind-code, skip steps, drift scope, or "tweak" when full-scope work is required.
* If something is unclear, do not assume. Trace back to the phase plan and source doc; log an explicit question in the issue and park the task until answered.
* Every task has a through-line back to a phase and artifact. Maintain traceability end-to-end.

## 1) Phase Gates & Traceability

* All work must be mapped to a **Phase → Epic → Issue → PR** chain.
* Each **PR** includes: Phase ID, acceptance criteria, test evidence, and any schema/contract diffs.
* **Definition of Ready**: linked spec, inputs defined, success criteria measurable.
* **Definition of Done**: feature works, tests pass, docs updated, dashboards/KPIs wired, and data logged to the core schema (trades, KPIs, governance).

## 2) Repo & Environments (Flask + Material Web / MD3)

- Monorepo layout: `/backend`, `/frontend`, `/workers`, `/etl`, `/infra`, `/packages`, plus `/docs`.  
- One-command local run (`Makefile`), `.env.example` committed; secrets via env/manager only.  
- Branching: `main` (protected), `dev`, short-lived feature branches; squash merge with conventional commits.  

---

### Frontend UI
- Uses **Material Web (Material Design 3)** web components from the **vendored repo only** (no CDN/NPM).  
- **Vendored path:** `/packages/material-web` (Git submodule pinned to a commit)  
- **Import alias used in builds:** `@lrbf/material-web`  
- **No emulation** of MD3 in plain HTML/CSS – use `<md-*>` elements exclusively for UI.

---

### Flask specifics
- Server-rendered templates in `/backend/templates` (Jinja2) may use `<md-*>` tags directly.  
- Static assets served from `/backend/static/assets` (built by the `/frontend` pipeline).  
- All UI reads colors, typography, and spacing from MD3 tokens defined in **Section 13.2**.

---

### Tooling & enforcement
- **Frontend:** Vite + TypeScript build in `/frontend`; outputs to `/backend/static/assets`.  
- **Lint:** ESLint for TypeScript – deny imports that start with `@material/web` or any external URL for MD3 (allow only `@lrbf/material-web`).  
- **Python:** ruff, black, and mypy (or your chosen equivalents) in CI; forbid unused imports and dead code.  

#### CI checks
- `<md-*>` tags present in diffs for UI pages/templates.  
- No mock data in production paths (only `/tests/mock_test_only`).  
- Build artifact exists and is non-empty: `/backend/static/assets/*`.

---

### API integration
- UI must consume **live backend endpoints** (Flask/FastAPI) and real schemas; no inline JSON except in `/tests/mock_test_only`.  
- Any new UI that implies new data must ship with the corresponding **backend contract and tests** (see Sections 1, 10, and 11).


## 3) Data Governance is Non-Optional

* Log every tick/trade/outcome to the unified schema; no silent paths, no ephemeral data.
* Keep immutable ledgers + code version hash per trading day; reconcile to IBKR confirms; 7-year retention.
* KPIs (Sharpe, Sortino, Calmar, drawdowns, hit rate, missed entries) roll up daily to investor-facing reports.
* Transparency, auditability, and ML-readiness are baseline qualities of every change.

## 4) Capital & Risk Controls (hard stops)

* Respect deployment plan (80/20 → 50/50 taper), daily loss cap −1.5%, no overnights. Any breach halts trading automatically.
* Track buying power, excess liquidity, leverage, SMA, and loss-cap flag each polling interval; auto-stop if thresholds hit.

## 5) Market Data & Health SLOs

* Use certified feeds and freshness rules (e.g., fresh tick ≤ 2 s) for decisions; stale data = no trade.
* Monitor NTP offset, feed latency/uptime, missing ticks, and loop integrity; investigate before resuming.

## 6) Morning Lineup & Forecast Discipline

* Morning symbol selection computes liquidity, volatility, VWAP confluence, reward-to-risk, halt risk, and **Dead-Zone Score**; only the composite-ranked top set passes to execution.
* Forecasts use previous 20 sessions to set expected trade counts and ROI bands; track error and model drift intraday.
* Apply dead-zone filters and penalties to protect time/capital efficiency.

## 7) Trade Lifecycle Logging (zero exceptions)

At entry/exit log: VWAP deviation, stage, OB imbalance, slippage, hold time, VWAP efficiency, intraday VWAP drift, latency attribution (signal→ack, ack→fill).

## 8) Live Monitoring UX Must Show…

Per-position status, dead-zone timer, opportunity cost, and actionable recommendations at 5/10/15-minute thresholds.

## 9) Change Control & Promotions

* No code moves to prod without: (a) reproducible backtests on ≥ 3 years intraday, (b) independent validation, (c) versioned artifact + immutable ledger write.
* Separate dev vs live environments; live is closed and timestamped to the millisecond.

## 10) Contracts, Schemas, and Migrations

* Treat SQL and API contracts as product. All schema changes must be backwards-compatible or ship with migration plan and data backfill.
* On deploy, run integrity checks; failure = auto-rollback.

## 11) Testing & Quality Bars

* Unit (calc correctness), integration (IBKR endpoints), property tests (idempotent entries), and golden files for forecasts.
* Performance budget: selection/forecast run < 5 min; live loop cycle time within latency SLOs.

## 12) Security & Secrets

* No secrets in code or commits. Use env/secrets manager. MFA for repos. Least-privilege infra access.

## 13) UX & Design

* **Component System**: Use **Material Web (MD3)** components directly (`<md-filled-button>`, `<md-outlined-text-field>`, etc.). No custom HTML/CSS that only looks like MD3.
* **Tokens & Motion**: Use MD3 elevation, state layers, density, focus, and motion defaults. Only adjust via documented MD3 theming hooks.
* **Color & Vibe**: Match a **Claude-like** feel – calm neutrals, ample white space, restrained accent usage, soft elevation, rounded corners.

  * Provide light + dark themes; default to light; auto-switch by OS preference.
  * Keep AA contrast minimums at all times.
* **Allowed customization**: typography scale, radius, spacing – consistent across pages; no component internal overrides.

**Recommended color tokens (Claude-like vibe)**

*Light theme*

```
--md-sys-color-surface:#F7F7F8;
--md-sys-color-on-surface:#121316;
--md-sys-color-surface-variant:#EDEEF0;
--md-sys-color-outline:#D1D3D7;
--md-sys-color-primary:#6E63FF;
--md-sys-color-on-primary:#FFFFFF;
--md-sys-color-secondary:#5C606A;
--md-sys-color-tertiary:#2F7D5A;
--md-sys-color-error:#BA1A1A;
--radius-lg:12px;
--radius-sm:8px;
--spacing-unit:8px;
```

*Dark theme*

```
--md-sys-color-surface:#0F1012;
--md-sys-color-on-surface:#E9EAEC;
--md-sys-color-surface-variant:#202226;
--md-sys-color-outline:#2B2E33;
--md-sys-color-primary:#8F86FF;
--md-sys-color-on-primary:#0B0B0C;
--md-sys-color-secondary:#A5AAB4;
--md-sys-color-tertiary:#5DB894;
--md-sys-color-error:#FF5449;
--radius-lg:12px;
--radius-sm:8px;
--spacing-unit:8px;
```

**Usage example**

```tsx
export default function Example() {
  return (
    <main style={{ padding:'var(--spacing-unit) calc(var(--spacing-unit)*2)' }}>
      <md-outlined-card style={{ borderRadius:'var(--radius-lg)', padding:'24px' }}>
        <h2 style={{ marginTop:0 }}>Quick Action</h2>
        <md-filled-button aria-label="Run Forecast">Run Forecast</md-filled-button>
        <md-outlined-text-field label="Symbol" style={{ marginLeft:16 }}></md-outlined-text-field>
      </md-outlined-card>
    </main>
  );
}
```

## 13.1) Design QA Checklist

* Page uses only `<md-*>` elements for core UI.
* Colors read from `--md-sys-color-*` tokens only; no hard-coded hex.
* Spacing on 8 pt grid; card/dialog radius = 12 px.
* Primary accent used sparingly.
* Light/dark switch verified; contrast AA passes both.

## 13.2) Claude-Aligned Color Spec (exact)

* **Primary accent** must match Claude's orange: `hsl(14.88 62.32% 59.41%)` = `#D87757`.
* Use Material Web tokens only; no hard-coded hex.

**Light**

```css
:root {
  /* Primary */
  --md-sys-color-primary: #D87757;          /* from HSL(14.88 62.32% 59.41%) */
  --md-sys-color-on-primary: #FFFFFF;
  --md-sys-color-primary-container: #FFDDD1;
  --md-sys-color-on-primary-container: #3E1500;

  /* Surfaces */
  --md-sys-color-surface: #F4F3EE;          /* Claude "Pampas" */
  --md-sys-color-on-surface: #3A3A39;       /* your neutral black */
  --md-sys-color-surface-variant: #B1ADA1;  /* Claude "Cloudy" */
  --md-sys-color-on-surface-variant: #4A4845;

  /* Secondary / Tertiary (stylistic, keep if you like) */
  --md-sys-color-secondary: #6B7B8C;
  --md-sys-color-on-secondary: #FFFFFF;
  --md-sys-color-secondary-container: #D4E3F4;
  --md-sys-color-on-secondary-container: #1A2937;

  --md-sys-color-tertiary: #5A7A5F;
  --md-sys-color-on-tertiary: #FFFFFF;
  --md-sys-color-tertiary-container: #DDF4DF;
  --md-sys-color-on-tertiary-container: #172119;

  /* Error */
  --md-sys-color-error: #BA1A1A;
  --md-sys-color-on-error: #FFFFFF;
  --md-sys-color-error-container: #FFDAD6;
  --md-sys-color-on-error-container: #410002;

  /* Additional surfaces */
  --md-sys-color-surface-dim: #DDD9D3;
  --md-sys-color-surface-bright: #FFFBF7;
  --md-sys-color-surface-container-lowest: #FFFFFF;
  --md-sys-color-surface-container-low: #F7F3ED;
  --md-sys-color-surface-container: #F1EDE7;
  --md-sys-color-surface-container-high: #EBE7E1;
  --md-sys-color-surface-container-highest: #E6E1DC;

  /* Outline / inverse */
  --md-sys-color-outline: #7D7A75;
  --md-sys-color-outline-variant: #CFC9C1;
  --md-sys-color-inverse-surface: #3A3A39;     /* for dark-filled buttons */
  --md-sys-color-inverse-on-surface: #F5F0EA;
  --md-sys-color-inverse-primary: #FFB68E;

  /* Background (legacy) */
  --md-sys-color-background: #F4F3EE;
  --md-sys-color-on-background: #3A3A39;

  /* Typography & spacing */
  --font-display: "Roboto Flex", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Arial, sans-serif; /* UI/data/headings/sidebar */
  --font-body: "Roboto Serif", ui-serif, Georgia, "Times New Roman", serif;                               /* body paragraphs only */

  --color-body: #3A3A39;  /* general body text */
  --color-meta: #B1ADA1;  /* small metadata on cards/tooltips */

  --spacing-compact-unit: 6px;  /* compact line/padding rhythm */
  --radius-ui-lg: 10px;         /* subtle corners */
  --radius-ui-sm: 6px;

  /* Typographic hierarchy (small sizes, condensed line heights) */
  --type-title-size: 28px; --type-title-lh: 32px; --type-title-wt: 700;
  --type-h1-size:    24px; --type-h1-lh:    28px; --type-h1-wt:    650;
  --type-h2-size:    20px; --type-h2-lh:    24px; --type-h2-wt:    600;
  --type-h3-size:    18px; --type-h3-lh:    22px; --type-h3-wt:    600;
  --type-h4-size:    16px; --type-h4-lh:    20px; --type-h4-wt:    600;

  --type-body-lg-size: 14px; --type-body-lg-lh: 20px; --type-body-lg-wt: 400;
  --type-body-sm-size: 13px; --type-body-sm-lh: 18px; --type-body-sm-wt: 400;

  --type-label-size:   12px; --type-label-lh:   16px; --type-label-wt:   600;
  --type-meta-size:    11px; --type-meta-lh:    16px; --type-meta-wt:    500;
}
```

**Dark**

```css
@media (prefers-color-scheme:dark){
  :root {
    --md-sys-color-primary:#D87757;
    --md-sys-color-on-primary:#0B0B0C;
    --md-sys-color-surface:#0F1012;
    --md-sys-color-on-surface:#E9EAEC;
    --md-sys-color-surface-variant:#202226;
    --md-sys-color-outline:#2B2E33;
    --md-sys-color-secondary:#A5AAB4;
    --md-sys-color-tertiary:#5DB894;
    --md-sys-color-error:#FF5449;
  }
}
```

**Notes**

* `#D87757` is the only allowed orange for CTAs and key highlights like buttons.
* Roboto Flex is the universal display/UI/data font. Roboto Serif is used for body text only (not headers or sidebars).
* Use `#B1ADA1` for small metadata and `#3A3A39` for general body text.
* Keep typography compact (smaller sizes, condensed line spacing, tight margins).
* Rounded corners must remain subtle (10px / 6px).
* Keep accent usage minimal; maintain Claude-like calm neutral feel.
* WCAG AA contrast required in light and dark themes.


**Notes**

* `#D87757` is the only allowed orange for CTAs and key highlights like buttons.
* Keep accent usage minimal; maintain Claude-like calm neutral feel.
* WCAG AA contrast required in light and dark themes.

## 13.3) Color Enforcement

* CI rejects non-whitelisted accent oranges (`#DA7756`, `#DE7356`, `#CD6F47`, etc.). Only `#D87757` permitted.
* Lint forbids inline hex in JSX/TSX; enforce tokens via CSS variables.
* Visual QA snapshot tests for light/dark themes on key pages (home, forecast, live monitor, reports).

---

✅ **This is the full, current rule set – Sections 0 through 13.3.**
You can now commit this file exactly as-is to `/docs/rules-to-follow.md`.
