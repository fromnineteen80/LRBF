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
