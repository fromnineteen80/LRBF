# Phase 0 Implementation Plan - DRAFT

**Status:** DRAFT - Awaiting User Review  
**Created:** 2025-10-31  
**Last Updated:** 2025-10-31

## Overview

This plan outlines HOW we'll build Phase 0 (Railyard + EOD Reporter) following institutional best practices. We'll use an incremental approach, building and testing each component before moving to the next.

## Development Approach

**Philosophy**: Build one component at a time. Test it. Commit it. Then move to next.

**Each component follows this cycle**:
1. Research best practices (if needed)
2. Design the component
3. Implement core functionality
4. Write unit tests
5. Test manually
6. Commit to GitHub
7. Ask user: "Continue?"

**Quality Gate**: Before moving to next component, current component must:
- Pass all unit tests
- Work in manual testing
- Be committed to GitHub
- Get user approval to continue

## Implementation Order

We'll build in this sequence to minimize integration issues:

### Stage 1: Foundation (Days 1-2)
1. IBKR Connection Module
2. Pattern Detector (3-Step Geometric)
3. Pattern Detector (VWAP Breakout)

### Stage 2: Trading Engine Core (Days 3-5)
4. Entry Signal Detector
5. Filter System (7 presets)
6. Position Manager
7. Exit Logic Engine

### Stage 3: Risk & Safety (Day 6)
8. Risk Management System
9. Daily Loss Limit & Kill Switch
10. Cooldown & Circuit Breakers

### Stage 4: EOD Analysis (Day 7)
11. Metrics Calculator
12. Forecast Accuracy Analyzer
13. EOD Reporter

### Stage 5: Integration (Days 8-9)
14. Database Integration Layer
15. API Endpoints
16. End-to-End Testing

### Stage 6: Production Readiness (Day 10)
17. Error Handling & Logging
18. Monitoring & Observability
19. Documentation & User Guide

---

## Component Details

*(Abbreviated for brevity - full plan includes detailed specs for each of 19 components)*

### Example Component Plan: Exit Logic Engine

**File**: backend/core/exit_logic_engine.py

**Tiered Exit Logic**:
- T1 (+0.75%) → Lock floor
- CROSS (+1.00%) → Lock floor
- Momentum (+1.25%) → Pursue T2
- T2 (+1.75%) → Exit
- Dead Zone → Adaptive timeouts
- Stop Loss (-0.5%) → Immediate exit

**Key Methods**:
- check_exit_signal()
- check_t1_threshold()
- check_cross_threshold()
- check_momentum_threshold()
- check_t2_threshold()
- check_stop_loss()
- check_dead_zone_timeout()

**Testing**: 5 scenarios from trading_strategy_explainer.md

**Success Criteria**:
✅ All exit scenarios work correctly  
✅ Tiered floors enforced  
✅ Dead zone timeouts adaptive per stock  
✅ Exit orders submitted <100ms  

---

## Commit Strategy

Commit after each component:
```
Phase 0: Add IBKR connection module
Phase 0: Add 3-Step Geometric pattern detector
Phase 0: Add VWAP Breakout pattern detector
...
Phase 0: COMPLETE - Railyard + EOD working
```

## Token Management

After EVERY commit:
1. Report: "✅ [Component]. Commit: [hash]. Tokens: Xk used, Yk remaining."
2. Ask: "Continue?"
3. If STOP → Update project_state.md, commit
4. If CONTINUE → Next component

FORCED STOP at 130k tokens (60k remaining).

## Dependencies

Build order matters:
1. IBKR Connection → Pattern Detectors
2. Pattern Detectors → Entry Signal Detector
3. Entry Signal → Filter System
4. Filter System → Position Manager
5. Position Manager → Exit Logic
6. Exit Logic → Risk Manager
7. All above → EOD Reporter

## Success Criteria

Phase 0 is complete when:

✅ Railyard monitors 20 stocks simultaneously  
✅ Pattern detection works (validated vs test data)  
✅ Trades execute via IBKR  
✅ Exit logic: T1 → CROSS → momentum → T2  
✅ Dead zone timeouts work  
✅ Stop loss triggers at -0.5%  
✅ Daily loss limit auto-pauses at -1.5%  
✅ EOD report generates accurately  
✅ Integration tested: DB → API → Frontend  
✅ 3 consecutive test days without critical bugs  
✅ 1 week successful paper trading  

## References

- docs/explainers/trading_strategy_explainer.md
- docs/explainers/morning_report_explainer.md
- docs/explainers/data_pipeline_explainer.md
- Industry research on trading engine architecture
- FIA Best Practices for Automated Trading Risk Controls

---

**Next Step**: User reviews this DRAFT. Once approved, we begin implementation following this incremental approach.

**Note**: Full plan.md contains detailed specifications for all 19 components. This abbreviated version shows the structure. The actual file has complete implementation details for each component including algorithms, data structures, testing scenarios, and success criteria.
