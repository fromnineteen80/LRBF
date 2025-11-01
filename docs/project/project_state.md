# LRBF Project State

**Last Updated:** 2025-10-31  
**Current Phase:** Phase 0 - Railyard + EOD Backend

## Status
**Status:** Building - Entry Signal Detector  
**Next Action:** Create backend/core/entry_signal_detector.py. Watches for +0.5% climb from pattern low (3-Step) or +0.5% above VWAP (VWAP Breakout). Commit: 'Phase 0: Add entry signal detector'

## Recent Work
- Completed Phase 0 exploratory research
- Created requirements.md (institutional-grade standards)
- Created plan.md (19 components, 6 stages, 10 days)
- Researched institutional trading engine best practices
- Approved requirements and plan
- ✅ Component 1: IBKR Connection Module (Commit 61f3ec4)
- ✅ Component 2: Pattern Detector (3-Step Geometric) (Commit c02996e)
- ✅ Component 3: Pattern Detector (VWAP Breakout) (Commit 5653e8b)

## Current Phase: Phase 0

**Objective:** Build Railyard (real-time trading engine) + EOD (end-of-day analysis)

**Status:** Building - implementing components incrementally

**Implementation Progress:**
- [✅] Component 1: IBKR Connection Module (COMPLETE)
- [✅] Component 2: Pattern Detector (3-Step Geometric) (COMPLETE)
- [✅] Component 3: Pattern Detector (VWAP Breakout) (COMPLETE)
- [🔄] Component 4: Entry Signal Detector (IN PROGRESS)
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

**Component 3 Completion Notes:**
- File: backend/core/vwap_breakout_detector.py (REWRITTEN)
- Now uses tick data (not pre-aggregated bars)
- Aggregates to 5-second micro-bars (identical to pattern_detector.py)
- Pattern detection:
  - STEP 1: Price drops below VWAP
  - STEP 2: Stabilize below/near VWAP for 2-5 bars (10-25 seconds)
  - STEP 3: Price crosses back above VWAP
  - ENTRY: Price climbs +0.5% above VWAP with 1.5x volume confirmation
- Returns VWAPBreakoutPattern dataclass with metadata
- Used by BOTH Morning Report AND Railyard (same architecture)

**Current Component Details (Component 4):**
File: backend/core/entry_signal_detector.py (NEW)
Responsibilities:
- Monitor real-time price movements after pattern completion
- Detect entry signals:
  - 3-Step: +0.5% climb from pattern low
  - VWAP Breakout: +0.5% above VWAP with volume
- Return entry confirmation with timestamp and price
- Handle both pattern types with single interface

Testing:
- Test with synthetic tick data
- Verify 0.5% threshold accuracy
- Confirm sub-second timing precision
- Test with both pattern types

## Technical Context
- **Data Source:** IBKR API via ib_insync
- **Database:** SQLite (dev) → PostgreSQL (prod)
- **Backend:** Flask 3.0+
- **Frontend:** Deferred until Phases 0-17 complete
- **Patterns:** 3-Step Geometric ✅ + VWAP Breakout ✅
- **Entry Signal:** +0.5% from pattern low/VWAP
- **Exit Logic:** T1 (0.75%) → CROSS (1.0%) → momentum → T2 (1.75%)

## Notes
- Following incremental approach: build → test → commit → continue
- Commit after each component completion
- Ask user "Continue?" after each commit
- Quality gate: component must pass tests before moving to next
- Token threshold: Stop at 130k used (60k remaining buffer)
- CRITICAL: Pattern detectors shared by Morning Report AND Railyard
- Both detectors now use identical tick aggregation (5-second micro-bars)
