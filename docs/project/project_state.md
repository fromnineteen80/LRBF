# LRBF Project State

**Last Updated:** 2025-10-30  
**Current Phase:** Phase 0 - Railyard + EOD Backend

## Status
**Status:** Exploratory needed  
**Next Action:** Research institutional trading engine best practices. Read docs/explainers/trading_strategy_explainer.md, morning_report_explainer.md, data_pipeline_explainer.md. Create DRAFT requirements.md + plan.md in docs/phases/phase_0/. Commit drafts. Wait for user review and approval.

## Recent Work
- Set up lrbf-skill with automatic triggers
- Added quality standards (JPMorgan quant + Robinhood engineer)
- Added project state status model
- Optimized token usage: commit drafts (not long chat proposals), batch commit verification, update project_state.md only at session boundaries
- Moved phases to docs/phases/
- Created docs/TECH_SPECS.md

## Current Phase: Phase 0

**Objective:** Build Railyard (real-time trading engine) + EOD (end-of-day analysis)

**Status:** Exploratory phase - need to research, draft requirements/plan, get approval

**Next Steps:**
1. Research institutional best practices for trading engines
2. Read all three explainers
3. Create DRAFT requirements.md (what to build)
4. Create DRAFT plan.md (how to build it)
5. Commit both as drafts
6. User reviews files in repo
7. User requests changes or approves
8. Update files based on feedback
9. When approved, update Status to "Building - [first task]"

## Technical Context
- **Data Source:** IBKR API via ib_insync
- **Database:** SQLite (dev) → PostgreSQL (prod)
- **Backend:** Flask 3.0+
- **Frontend:** Deferred until Phases 0-17 complete
- **Patterns:** 3-Step Geometric + VWAP Breakout
- **Exit Logic:** T1 (0.75%) → CROSS (1.0%) → momentum → T2 (1.75%)

## Notes
- Existing railyard.py and eod_reporter.py need complete overhaul
- All HTML templates will be rebuilt with MD3
- DEPRECATED: Capitalise.ai, yfinance
