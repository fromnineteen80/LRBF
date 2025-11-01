# LRBF Project State

**Last Updated:** 2025-10-31  
**Current Phase:** Phase 0 - Railyard + EOD Backend

## Status
**Status:** Building - Pattern Detectors  
**Next Action:** Add VWAP Breakout pattern detector to backend/core/vwap_breakout_detector.py. Test with 20-day historicals. Commit: 'Phase 0: Add VWAP Breakout pattern detector'

## Recent Work
- Completed Phase 0 exploratory research
- Created requirements.md (institutional-grade standards)
- Created plan.md (19 components, 6 stages, 10 days)
- Researched institutional trading engine best practices
- Approved requirements and plan
- ✅ Component 1: IBKR Connection Module (Commit c61f3ec4)
- ✅ Component 2: Pattern Detector (3-Step Geometric) - Fixed entry threshold (Commit c02996e)

## Current Phase: Phase 0

**Objective:** Build Railyard (real-time trading engine) + EOD (end-of-day analysis)

**Status:** Building - implementing components incrementally

**Implementation Progress:**
- [✅] Component 1: IBKR Connection Module (COMPLETE)
- [✅] Component 2: Pattern Detector (3-Step Geometric) (COMPLETE)
- [🔄] Component 3: Pattern Detector (VWAP Breakout) (IN PROGRESS)
- [ ] Component 4: Entry Signal Detector
- [ ] Component 5: Filter System (7 presets)
- [ ] Component 6: Position Manager
- [ ] Component 7: Exit Logic Engine
- [ ] Component 8: Risk Management System
- [ ] Component 9: Daily Loss Limit & Kill Switch
- [ ] Component 10: Cooldown Manager
- [ ] Component 11: Metrics Calculator
- [ ] Component 12: Forecast Accuracy Analyzer
- [ ] Component 13: EOD Reporter
- [ ] Component 14: Database Integration Layer
- [ ] Component 15: API Endpoints
- [ ] Component 16: End-to-End Testing
- [ ] Component 17: Error Handling & Logging
- [ ] Component 18: Monitoring & Observability
- [ ] Component 19: Documentation & User Guide

**Component 2 Completion Notes:**
- File: backend/core/pattern_detector.py (EXISTS, updated)
- Fixed entry confirmation threshold: 1.5% → 0.5% (per trading_strategy_explainer.md)
- Correctly implements 3-Step Geometric pattern:
  - STEP 1: Decline ≥1.0% from 3min high
  - STEP 2: 50% recovery of decline
  - STEP 3: 50% retracement of recovery
- Used by BOTH Morning Report (20-day historicals) AND Railyard (real-time)
- Aggregates ticks into 5-second micro-bars for pattern scanning
- Returns pattern metadata for entry signal detection

**Current Component Details (Component 3):**
File: backend/core/vwap_breakout_detector.py (NEW)
Responsibilities:
- Detect VWAP breakout patterns from tick data
- Pattern: Price breaks above VWAP with volume confirmation
- Used by Morning Report for 20-day analysis
- Used by Railyard for real-time detection
- Must match same tick aggregation approach as 3-Step detector

Testing:
- Test with 20-day historical data
- Verify pattern detection accuracy
- Confirm compatibility with Morning Report
- Test real-time tick processing

## Technical Context
- **Data Source:** IBKR API via ib_insync
- **Database:** SQLite (dev) → PostgreSQL (prod)
- **Backend:** Flask 3.0+
- **Frontend:** Deferred until Phases 0-17 complete
- **Patterns:** 3-Step Geometric ✅ + VWAP Breakout 🔄
- **Exit Logic:** T1 (0.75%) → CROSS (1.0%) → momentum → T2 (1.75%)

## Notes
- Following incremental approach: build → test → commit → continue
- Commit after each component completion
- Ask user "Continue?" after each commit
- Quality gate: component must pass tests before moving to next
- Token threshold: Stop at 130k used (60k remaining buffer)
- CRITICAL: Pattern detectors shared by Morning Report AND Railyard
- Entry confirmation fixed to 0.5% (was incorrectly 1.5%)
