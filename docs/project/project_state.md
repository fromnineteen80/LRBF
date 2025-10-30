# LRBF Project State

**Last Updated:** 2025-10-30  
**Current Phase:** Phase 0 - Railyard + EOD Backend

## Status
**Status:** Exploratory needed  
**Next Action:** Discuss Phase 0 requirements and create plan

## Recent Work
- Set up lrbf-skill with automatic GitHub access and project state loading
- Added quality standards (JPMorgan quant + Robinhood engineer test)
- Added project state status model (Exploratory/Building/Testing/Complete)
- Documented all 32 phases (0-31)
- Created explainers for trading strategy, morning report, data pipeline
- Moved phases folder to docs/phases/
- Created docs/TECH_SPECS.md for quick reference

## Current Phase: Phase 0

**Objective:** Build Railyard (real-time trading engine) + EOD (end-of-day analysis)

**What Phase 0 Includes:**
- Railyard backend (pattern monitoring, entry/exit logic, risk management)
- EOD backend (daily analysis, metrics calculation)
- API endpoints: /api/railyard-data, /api/eod-data
- Integration testing: Database → API chains

**Current Status Detail:**
Phase 0 has NOT been explored yet. Need to:
1. Read docs/explainers/trading_strategy_explainer.md
2. Read docs/explainers/morning_report_explainer.md
3. Read docs/explainers/data_pipeline_explainer.md
4. Research institutional best practices for trading engines
5. Propose requirements.md (what needs to be built)
6. Propose plan.md (how to build it)
7. Get user approval
8. THEN commit requirements.md + plan.md to docs/phases/phase_0/

## Next Session

When you say "use lrbf-skill to continue working on our app":
- Claude will read this Status: "Exploratory needed"
- Claude will automatically start exploratory process
- Claude will propose requirements and plan for discussion
- You approve, then Claude commits them
- Status updates to "Building - [first task]"

## Blockers
None currently

## Technical Context
- **Data Source:** IBKR API via ib_insync
- **Database:** SQLite (dev) → PostgreSQL (prod)
- **Backend:** Flask 3.0+
- **Frontend:** Deferred until Phases 0-17 complete
- **Trading Patterns:** 3-Step Geometric + VWAP Breakout
- **Exit Logic:** T1 (0.75%) → CROSS (1.0%) → momentum → T2 (1.75%)

## Dependencies
Phase 0 is the foundation - no dependencies

## Notes
- Existing backend/core/railyard.py needs complete overhaul
- Existing backend/reports/eod_reporter.py needs complete overhaul
- All HTML templates are alpha and will be rebuilt with Material Design 3
- Frontend work (Phases 18-31) deferred until backend complete
- DEPRECATED: Capitalise.ai, yfinance (use IBKR API only)
