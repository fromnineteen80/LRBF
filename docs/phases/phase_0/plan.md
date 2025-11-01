# Phase 0 Implementation Plan

**Status:** IN PROGRESS - Components 1-6 Complete  
**Created:** 2025-10-31  
**Last Updated:** 2025-11-01

---

## Components 1-6: ✅ COMPLETE

1. **IBKR Connection Module** - backend/data/ibkr_connector_insync.py (Commit 4d8af40)
2. **Pattern Detector (3-Step)** - backend/core/pattern_detector.py (Commit ac1107b)
3. **Pattern Detector (VWAP)** - backend/core/vwap_breakout_detector.py (Commit 5653e8b)
4. **Entry Signal Detector** - backend/core/entry_signal_detector.py (Commit 714e505)
5. **Filter System (7 presets)** - backend/core/filter_engine.py (Commit d243ef5)
6. **Position Manager** - backend/core/position_manager.py (Commit 416d5d5)

---

## Component 7: Exit Logic Engine (NEXT)

**File**: `backend/core/exit_logic_engine.py`

### Purpose
Monitor open positions and determine when to exit based on tiered exit logic from trading_strategy_explainer.md.

### Tiered Exit System (CRITICAL - from trading strategy)

```
Entry → T1 (+0.75%) → CROSS (+1.00%) → Momentum (+1.25%) → T2 (+1.75%)
         ↓ LOCK        ↓ LOCK            ↓ GO FOR T2        ↓ EXIT
         
Falls below locked floor? → Exit at previous milestone
```

**Example Trade Flow**:
1. Entry at $150.00
2. Hits $151.13 (+0.75%) → **T1 LOCKED** → Floor = $151.13
3. Hits $151.50 (+1.00%) → **CROSS LOCKED** → Floor = $151.50
4. Hits $151.88 (+1.25%) → **MOMENTUM CONFIRMED** → Going for T2
5. Hits $152.63 (+1.75%) → **T2 EXIT** ✅

**Alternate Scenario** (Falls back):
- At CROSS ($151.50), price falls back to $151.45
- Below CROSS floor → **EXIT AT CROSS (+1.00%)** ✅

### Dead Zone Timeouts (Adaptive per profit level)

From trading_strategy_explainer.md:

| Profit Level | Timeout | Action |
|--------------|---------|--------|
| Below T1 | 3 min | Exit if any positive gain |
| At T1 | 4 min | Exit at T1 |
| At CROSS | 4 min | Exit at CROSS |
| After momentum | 6 min | Exit at best available |

### Implementation Requirements

**Class Structure**:
```python
class ExitLogicEngine:
    def __init__(self, position_manager, ibkr_connector):
        self.pm = position_manager
        self.ibkr = ibkr_connector
        self.milestone_tracker = {}  # Track which milestone each position reached
        self.dead_zone_tracker = {}  # Track how long position stuck
        
    def monitor_position(self, ticker, current_price, timestamp):
        """
        Check exit conditions for a position.
        Returns: (should_exit: bool, exit_reason: str, exit_price: float)
        """
        
    def check_stop_loss(self, position, current_price):
        """Immediate exit if -0.5% from entry."""
        
    def check_t1_hit(self, position, current_price):
        """Lock T1 floor if +0.75% reached."""
        
    def check_cross_hit(self, position, current_price):
        """Lock CROSS floor if +1.00% reached."""
        
    def check_momentum_confirmed(self, position, current_price):
        """Confirm momentum if +1.25% reached."""
        
    def check_t2_hit(self, position, current_price):
        """Exit if +1.75% reached."""
        
    def check_floor_breach(self, position, current_price):
        """Exit if falls below locked floor."""
        
    def check_dead_zone_timeout(self, position, current_price, timestamp):
        """Exit if stuck too long without progress."""
        
    def execute_exit(self, ticker, exit_price, exit_reason):
        """Submit exit order via Position Manager."""
```

### Critical Pitfalls to Avoid

**From common-pitfalls.md**:

1. **DON'T**: Implement simple T1/T2 without CROSS and momentum
   - **DO**: Full tiered system: T1 → CROSS → momentum → T2

2. **DON'T**: Use fixed dead zone timeout for all levels
   - **DO**: Adaptive timeouts based on profit level (3/4/4/6 min)

3. **DON'T**: Exit immediately when T1 hit
   - **DO**: Lock T1 as floor, continue pursuing CROSS/T2

4. **DON'T**: Forget to track which milestone each position reached
   - **DO**: Maintain state for each position's milestone progress

### Testing Scenarios (from trading_strategy_explainer.md)

**Test 1: Full Success Path**
- Entry: $150.00
- Hit T1: $151.13 (+0.75%)
- Hit CROSS: $151.50 (+1.00%)
- Hit momentum: $151.88 (+1.25%)
- Hit T2: $152.63 (+1.75%)
- **Expected**: Exit at T2 (+1.75%)

**Test 2: Return to CROSS**
- Entry: $150.00
- Hit T1: $151.13
- Hit CROSS: $151.50
- Momentum NOT confirmed (stays at $151.60)
- Falls back to $151.45
- **Expected**: Exit at CROSS (+1.00%)

**Test 3: Dead Zone at T1**
- Entry: $150.00
- Hit T1: $151.13
- Stuck at $151.10-$151.15 for 4+ minutes
- **Expected**: Exit at T1 (+0.75%) after 4 min timeout

**Test 4: Stop Loss**
- Entry: $150.00
- Price drops to $149.25
- **Expected**: Exit at stop loss (-0.5%)

**Test 5: Below T1 Dead Zone**
- Entry: $150.00
- Price at $150.30 (+0.20%) for 3+ minutes
- **Expected**: Exit at +0.20% after 3 min timeout

### Integration Points

**Inputs**:
- Position data from Position Manager
- Real-time prices from IBKR tick stream
- Timestamps for dead zone tracking

**Outputs**:
- Exit orders to Position Manager
- Exit reason for logging
- Milestone tracking for EOD analysis

### Success Criteria

✅ All 5 test scenarios pass  
✅ Tiered floors enforced correctly  
✅ Dead zone timeouts work per level  
✅ Stop loss triggers at -0.5%  
✅ Exit orders submitted <100ms  
✅ No phantom references to missing methods  
✅ Integration tested with Position Manager  
✅ Logged to database with exit reason  

### Commit Message
```
Phase 0: Add exit logic engine with tiered system (T1→CROSS→momentum→T2)

- Implement full tiered exit logic per trading_strategy_explainer.md
- Add adaptive dead zone timeouts (3/4/4/6 min by level)
- Lock floors at T1 (+0.75%) and CROSS (+1.00%)
- Momentum confirmation at +1.25% before pursuing T2
- Stop loss at -0.5%
- Tested with 5 scenarios from explainer
```

---

## Components 8-19: TODO

*(To be detailed in subsequent updates)*
