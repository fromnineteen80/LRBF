# LRBF Project State

**Last Updated:** 2025-10-31  
**Current Phase:** Phase 0 - Railyard + EOD Backend

## Status
**Status:** Building - 6 of 19 components complete
**Next Action:** Build Component 7 (Exit Logic Engine) in backend/core/exit_logic_engine.py. Implement tiered exit system: T1 (+0.75%) → CROSS (+1.00%) → momentum (+1.25%) → T2 (+1.75%), dead zone timeouts, stop loss (-0.5%). Commit: 'Phase 0: Add exit logic engine'


---

## 🚨 CRITICAL HANDOFF INSTRUCTIONS FOR FUTURE CLAUDE

**Current Issue:** Token threshold approaching (124k used, 130k threshold). Future Claude sessions will be stateless and need detailed guidance.

### Why This Matters

Each new Claude session has **ZERO memory** of previous work. Without detailed component plans, future Claude will:
- Make phantom references to non-existent methods
- Skip critical institutional research (trading_strategy_explainer.md)
- Implement wrong logic (simple T1/T2 instead of tiered T1→CROSS→momentum→T2)
- Repeat mistakes documented in common-pitfalls.md
- Use emulation coding (discussing instead of building)
- Fail verification steps

### Research Required BEFORE Building Each Component

**MANDATORY reading order (30 min minimum):**

1. **Trading Strategy Explainer** (docs/explainers/trading_strategy_explainer.md)
   - Contains exit logic, cooldowns, risk limits
   - CRITICAL for Components 7-9, 12, 15-17
   
2. **Morning Report Explainer** (docs/explainers/morning_report_explainer.md)
   - Contains forecast structure, 16 scoring categories
   - CRITICAL for Components 11, 12, 14
   
3. **Common Pitfalls** (/mnt/skills/user/lrbf-skill/references/common-pitfalls.md)
   - Documents all past failure modes
   - MUST read before every component
   
4. **Development Workflow** (/mnt/skills/user/lrbf-skill/references/development-workflow.md)
   - Verification requirements, GitHub workflow
   - Reality checks before claiming complete

### Four MANDATORY Elements Per Component Plan

Every component plan MUST include these four sections:

#### 1. MANDATORY PRE-WORK Section
```markdown
### 🚨 MANDATORY PRE-WORK (DO THIS FIRST OR FAIL)

**BEFORE writing any code, you MUST:**

1. Read specific explainers (with exact sections to focus on)
2. Review existing components (verify methods exist with grep)
3. Read common-pitfalls.md (understand failure modes)
```

**Purpose:** Forces future Claude to gather institutional knowledge BEFORE coding. Prevents assumptions.

#### 2. CRITICAL CHECKPOINT Section
```markdown
### 🛑 CRITICAL CHECKPOINT (STOP HERE UNTIL COMPLETE)

**YOU CANNOT PROCEED TO CODING UNTIL YOU:**

1. ✅ Read and confirmed understanding (checklist)
2. ✅ Verified methods exist (grep with line numbers)
3. ✅ Aware of ALL critical pitfalls (list them)

**WHEN COMMITTING, YOU MUST REPORT:**
[Pre-commit verification report template]
```

**Purpose:** Creates hard stop. Future Claude must verify everything before proceeding. Must report findings to user.

#### 3. CRITICAL PITFALLS Table
```markdown
### 🚨 CRITICAL PITFALLS (Read Before Coding)

| ❌ WRONG | ✅ RIGHT |
|----------|----------|
| Common mistake 1 | Correct approach 1 |
| Common mistake 2 | Correct approach 2 |
```

**Purpose:** Visual reminder of past failures. Shows exactly what NOT to do and what TO do.

#### 4. Step-by-Step Implementation with Verification
```markdown
### 📋 Step-by-Step Implementation

**STEP 1: Verify Dependencies (5 min)**
```bash
# Exact grep commands to verify methods exist
grep "def method_name" file.py
```

**STEP 2: Create file.py (30 min)**
[Complete code implementation]

**STEP 3-5:** Test, integrate, commit with verification
```

**Purpose:** Provides complete executable plan. No ambiguity. Future Claude knows exactly what to build.

### Components Needing Plans (12-19)

**Remaining components without detailed plans:**
- Component 12: EOD Reporter
- Component 13: Database Integration Layer  
- Component 14: API Endpoints
- Component 15: End-to-End Testing
- Component 16: Error Handling & Logging
- Component 17: Monitoring & Observability
- Component 18: Documentation & User Guide
- Component 19: Final Integration & Verification

**Each needs all four elements above.**

### Verification Before Proceeding

Future Claude, before building ANY component, you must:

1. ✅ Read this CRITICAL HANDOFF INSTRUCTIONS section
2. ✅ Confirm component plan has all 4 mandatory elements
3. ✅ Complete MANDATORY PRE-WORK (read explainers)
4. ✅ Complete CRITICAL CHECKPOINT (verify methods, report to user)
5. ✅ Build according to step-by-step plan (no deviations)
6. ✅ Test with all scenarios listed
7. ✅ Provide pre-commit verification report to user

**If ANY element is missing, STOP and ask user for guidance.**

---

## Recent Work
- ✅ Component 1: IBKR Connection Module (Commit 61f3ec4)
- ✅ Component 2: Pattern Detector (3-Step Geometric) (Commit c02996e)
- ✅ Component 3: Pattern Detector (VWAP Breakout) (Commit 5653e8b)
- ✅ Component 4: Entry Signal Detector (Commit 714e505)
- ✅ Component 5: Filter System (7 presets) (Commit db26cd0)
- ✅ Component 6: Position Manager (Commit ae917ef)

## Current Phase: Phase 0

**Objective:** Build Railyard (real-time trading engine) + EOD (end-of-day analysis)

**Status:** Building - 6 of 19 components complete

**Implementation Progress:**
- [✅] Component 1: IBKR Connection Module (COMPLETE)
- [✅] Component 2: Pattern Detector (3-Step Geometric) (COMPLETE)
- [✅] Component 3: Pattern Detector (VWAP Breakout) (COMPLETE)
- [✅] Component 4: Entry Signal Detector (COMPLETE)
- [✅] Component 5: Filter System (7 presets) (COMPLETE)
- [✅] Component 6: Position Manager (COMPLETE)
- [🔄] Component 7: Exit Logic Engine (IN PROGRESS)
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

**Component 5 Completion Notes:**
- File: backend/core/filter_engine.py (REWRITTEN)
- Added 7 presets for Morning Report forecast generation:
  1. default - No filters, baseline performance
  2. conservative - All filters ON, tight thresholds (max win rate)
  3. aggressive - Minimal filters, loose thresholds (max frequency)
  4. choppy - S/R focused, optimized for range-bound markets
  5. trending - Momentum focused, optimized for directional markets
  6. abtest - Experimental combinations for testing
  7. vwap_breakout - VWAP breakout strategy specific
- Each preset has specific filter configurations:
  - min_decline_pct, entry_threshold_pct
  - require_volume_confirmation, volume_multiplier
  - check_vwap_proximity, vwap_proximity_pct
  - avoid_first_30min, avoid_last_30min
- Morning Report uses all 7 presets to generate forecast scenarios
- User selects which preset to trade with at 9:00 AM

**Components 1-5 Summary:**
✅ IBKR Connection - Streaming, reconnection, fill tracking
✅ 3-Step Geometric - Pattern detection from tick data
✅ VWAP Breakout - Pattern detection from tick data
✅ Entry Signal - Monitors +0.5% threshold confirmation
✅ Filter System - 7 presets for forecast generation

## Technical Context
- **Data Source:** IBKR API via ib_insync
- **Database:** SQLite (dev) → PostgreSQL (prod)
- **Backend:** Flask 3.0+
- **Patterns:** 3-Step Geometric ✅ + VWAP Breakout ✅
- **Entry Signal:** +0.5% threshold ✅
- **Filters:** 7 presets ✅
- **Exit Logic:** T1 (0.75%) → CROSS (1.0%) → momentum → T2 (1.75%)

## Token Status
- **Used:** 125k / 190k (66%)
- **Remaining:** 65k
- **Threshold:** 130k used (stop at 60k remaining buffer)
- **Buffer Available:** 17k tokens before threshold

## Notes
- Following incremental approach: build → test → commit → continue
- Commit after each component completion
- Quality gate: component must pass tests before moving to next
- Token threshold: Approaching limit, may need to stop soon
- CRITICAL: All components shared by Morning Report AND Railyard
