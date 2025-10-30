# LRBF Project State

**Last Updated:** 2025-10-30  
**Current Phase:** Phase 0 - Railyard + EOD Backend  
**Status:** 🔨 In Progress

## Recent Work
- Set up lrbf-skill for Claude development
- Documented all 32 phases (0-31)
- Established GitHub API workflow
- Created explainers for trading strategy, morning report, data pipeline
- Moved phases folder to docs/phases/

## Current Phase: Phase 0

**Objective:** Build Railyard (real-time trading engine) + EOD (end-of-day analysis)

**Components:**
- backend/core/railyard.py (exists but needs complete overhaul)
- backend/reports/eod_reporter.py (exists but needs complete overhaul)
- API endpoints: /api/railyard-data, /api/eod-data
- Integration testing: Database → API

**Progress:**
- [ ] Exploratory session (requirements.md + plan.md)
- [ ] Get user approval
- [ ] Implement Railyard backend
- [ ] Implement EOD backend
- [ ] Create API endpoints
- [ ] Integration testing
- [ ] Create completion.md

## Blockers
None currently

## Next Priorities
1. Conduct exploratory session for Phase 0
2. Read docs/explainers/trading_strategy_explainer.md
3. Read docs/explainers/morning_report_explainer.md
4. Read docs/explainers/data_pipeline_explainer.md
5. Create docs/phases/phase_0/requirements.md
6. Create docs/phases/phase_0/plan.md
7. Get user approval to proceed

## Technical Context
- **Data Source:** IBKR API via ib_insync
- **Database:** SQLite (dev) → PostgreSQL (prod)
- **Backend:** Flask 3.0+
- **Frontend:** Deferred until Phases 0-17 complete
- **Trading Patterns:** 3-Step Geometric + VWAP Breakout
- **Exit Logic:** T1 (0.75%) → CROSS (1.0%) → momentum → T2 (1.75%)

## Dependencies
Phase 0 is the foundation - no dependencies

## File Structure
See FILE_TREE.txt for complete structure

## Notes
- All HTML templates are alpha and will be rebuilt with Material Design 3
- Frontend work (Phases 18-31) deferred until backend complete
- Correct React template at prototypes/react-dashboard.html
- DEPRECATED: Capitalise.ai, yfinance (use IBKR API only)
