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

---

### 🚨 MANDATORY PRE-WORK (DO THIS FIRST OR FAIL)

**BEFORE writing any code, you MUST:**

1. **Read the trading strategy explainer** (20 minutes):
   ```bash
   Read: docs/explainers/trading_strategy_explainer.md
   Focus on: "Exit Logic Example (Real Trade)" section
   Understand: T1 (+0.75%) → CROSS (+1.00%) → momentum (+1.25%) → T2 (+1.75%)
   Understand: Dead zone timeouts (3/4/4/6 min by level)
   ```

2. **Review existing components** (verify these files exist and study their APIs):
   ```bash
   View: backend/core/position_manager.py
   Check methods: get_position(), exit_position(), get_all_positions()
   
   View: backend/data/ibkr_connector_insync.py
   Check methods: stream_ticks(), get_current_price()
   
   View: backend/core/filter_engine.py
   Check: momentum_threshold_pct is defined (should be 1.25%)
   ```

3. **Read common pitfalls** (avoid past mistakes):
   ```bash
   Read: /mnt/skills/user/lrbf-skill/references/common-pitfalls.md
   Focus on: "Complex Code Over Simple Solutions" section
   Focus on: "Phantom References" section
   ```

**⚠️ If you skip this pre-work, you WILL make mistakes that require rework.**


---

### 🛑 CRITICAL CHECKPOINT (STOP HERE UNTIL COMPLETE)

**YOU CANNOT PROCEED TO CODING UNTIL YOU:**

1. ✅ **Read and confirmed understanding of:**
   - [ ] docs/explainers/trading_strategy_explainer.md (ALL exit logic examples)
   - [ ] /mnt/skills/user/lrbf-skill/references/common-pitfalls.md (ALL pitfall sections)
   - [ ] backend/core/position_manager.py (verified methods exist)
   - [ ] backend/data/ibkr_connector_insync.py (verified methods exist)

2. ✅ **Verified these methods exist (grep each one):**
   - [ ] position_manager.get_position()
   - [ ] position_manager.exit_position()
   - [ ] position_manager.get_all_positions()
   - [ ] ibkr_connector.get_current_price()
   - [ ] ibkr_connector.stream_ticks()

3. ✅ **Aware of ALL critical pitfalls:**
   - [ ] Not implementing CROSS (+1.00%) milestone
   - [ ] Not implementing momentum (+1.25%) confirmation
   - [ ] Using fixed dead zone timeout instead of adaptive (3/4/4/6 min)
   - [ ] Exiting immediately at T1 instead of locking floor
   - [ ] Not tracking milestone state for each position
   - [ ] Making phantom references to non-existent methods
   - [ ] Using complex custom logic instead of simple if/elif

**WHEN COMMITTING THIS COMPONENT, YOU MUST REPORT:**

```
Component 7 Complete - Pre-Commit Verification Report:

✅ Read trading_strategy_explainer.md - understood tiered exit system
✅ Read common-pitfalls.md - aware of all 7 critical pitfalls
✅ Verified position_manager.get_position() exists (line X)
✅ Verified position_manager.exit_position() exists (line Y)
✅ Verified ibkr_connector.get_current_price() exists (line Z)
✅ Implemented 4 milestones: T1/CROSS/momentum/T2
✅ Implemented adaptive timeouts: 3/4/4/6 min
✅ All 5 test scenarios pass
✅ Integration test passes
✅ No phantom references found

Commit: [hash]
Ready for user confirmation.
```

**If you cannot check ALL boxes above, DO NOT COMMIT. Ask user for guidance.**

---
---

### 🎯 Purpose

Monitor open positions in real-time and execute exits based on tiered logic from trading_strategy_explainer.md.

**NOT a simple T1/T2 system**. This is a **4-milestone tiered system** with adaptive timeouts.

---

### 📊 Tiered Exit Logic (CRITICAL - Study This)

```
Entry Price
    ↓
    ├─ Stop Loss -0.5% → EXIT (loss)
    ├─ Below T1: stuck 3 min → EXIT at any positive
    ├─ T1 +0.75% → LOCK FLOOR, continue to CROSS
    ├─ At T1: stuck 4 min → EXIT at T1
    ├─ CROSS +1.00% → LOCK FLOOR, look for momentum
    ├─ At CROSS: stuck 4 min → EXIT at CROSS
    ├─ Momentum +1.25% → CONFIRMED, pursue T2
    ├─ After momentum: stuck 6 min → EXIT at best
    └─ T2 +1.75% → EXIT (win)
    
Falls below locked floor at any time? → EXIT at previous milestone
```

**Example from trading_strategy_explainer.md**:
- Entry: $150.00
- T+1m: $151.13 (+0.75%) → **T1 HIT, floor locked at $151.13**
- T+2m: $151.50 (+1.00%) → **CROSS HIT, floor locked at $151.50**
- T+3m: $151.88 (+1.25%) → **MOMENTUM CONFIRMED, going for T2**
- T+4m: $152.63 (+1.75%) → **T2 HIT, EXIT** ✅

---

### 🚨 CRITICAL PITFALLS (Read Before Coding)

**From common-pitfalls.md and past failures:**

| ❌ WRONG | ✅ RIGHT |
|----------|----------|
| Simple T1/T2 system | Full 4-milestone tiered system |
| Exit immediately at T1 | Lock T1 as floor, pursue CROSS |
| Fixed dead zone timeout | Adaptive: 3/4/4/6 min by level |
| No milestone tracking | Track state for EACH position |
| Assume methods exist | Verify ALL method calls exist first |
| Complex custom logic | Use simple if/elif chain |

**Reality Check Questions** (ask yourself these):
- ❓ Did I verify Position Manager has exit_position() method?
- ❓ Did I verify IBKR connector has get_current_price() method?
- ❓ Did I implement ALL 4 milestones (T1, CROSS, momentum, T2)?
- ❓ Did I implement adaptive dead zone timeouts (not fixed)?
- ❓ Did I test with the 5 scenarios from trading_strategy_explainer.md?

---

### 📋 Step-by-Step Implementation

**STEP 1: Verify Dependencies (5 min)**

```bash
# Check Position Manager methods exist
grep "def exit_position" backend/core/position_manager.py
grep "def get_position" backend/core/position_manager.py

# Check IBKR connector methods exist
grep "def get_current_price" backend/data/ibkr_connector_insync.py
grep "def stream_ticks" backend/data/ibkr_connector_insync.py

# If ANY grep returns nothing → METHOD DOES NOT EXIST
# Read those files to find the actual method names
```

**STEP 2: Create exit_logic_engine.py (30 min)**

```python
"""
Exit Logic Engine - Component 7

Implements tiered exit system from trading_strategy_explainer.md:
T1 (+0.75%) → CROSS (+1.00%) → momentum (+1.25%) → T2 (+1.75%)

Author: The Luggage Room Boys Fund
Date: November 2025
"""

from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MilestoneState:
    """Track milestone progress for a position."""
    reached_t1: bool = False
    reached_cross: bool = False
    reached_momentum: bool = False
    t1_timestamp: Optional[datetime] = None
    cross_timestamp: Optional[datetime] = None
    momentum_timestamp: Optional[datetime] = None
    locked_floor: float = 0.0  # Current locked profit floor
    last_price_update: Optional[datetime] = None
    time_at_current_level: float = 0.0  # Seconds stuck at current level


class ExitLogicEngine:
    """
    Monitors positions and executes exits based on tiered logic.
    
    Usage:
        engine = ExitLogicEngine(position_manager, ibkr_connector)
        should_exit, reason, price = engine.check_exit_conditions(
            ticker='AAPL',
            current_price=151.50,
            timestamp=datetime.now()
        )
    """
    
    def __init__(self, position_manager, ibkr_connector):
        """
        Initialize exit logic engine.
        
        Args:
            position_manager: PositionManager instance
            ibkr_connector: IBKRConnectorInsync instance
        """
        self.pm = position_manager
        self.ibkr = ibkr_connector
        
        # Track milestone progress for each position
        self.milestone_states: Dict[str, MilestoneState] = {}
        
        # Exit thresholds (from trading_strategy_explainer.md)
        self.STOP_LOSS_PCT = 0.5  # -0.5%
        self.T1_PCT = 0.75  # +0.75%
        self.CROSS_PCT = 1.0  # +1.00%
        self.MOMENTUM_PCT = 1.25  # +1.25%
        self.T2_PCT = 1.75  # +1.75%
        
        # Dead zone timeouts (adaptive by level)
        self.DEAD_ZONE_BELOW_T1 = 180  # 3 minutes (seconds)
        self.DEAD_ZONE_AT_T1 = 240  # 4 minutes
        self.DEAD_ZONE_AT_CROSS = 240  # 4 minutes
        self.DEAD_ZONE_AFTER_MOMENTUM = 360  # 6 minutes
        
        logger.info("ExitLogicEngine initialized")
    
    def check_exit_conditions(
        self,
        ticker: str,
        current_price: float,
        timestamp: datetime
    ) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Check if position should exit.
        
        Args:
            ticker: Stock symbol
            current_price: Current price
            timestamp: Current timestamp
        
        Returns:
            (should_exit, exit_reason, exit_price)
        """
        # Get position
        position = self.pm.get_position(ticker)
        if not position:
            return False, None, None
        
        # Initialize milestone state if new position
        if ticker not in self.milestone_states:
            self.milestone_states[ticker] = MilestoneState(
                locked_floor=position.entry_price * (1 - self.STOP_LOSS_PCT / 100)
            )
        
        state = self.milestone_states[ticker]
        entry_price = position.entry_price
        
        # Calculate current P&L %
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # --- CHECK 1: Stop Loss (-0.5%) ---
        if pnl_pct <= -self.STOP_LOSS_PCT:
            return True, "stop_loss", entry_price * (1 - self.STOP_LOSS_PCT / 100)
        
        # --- CHECK 2: Update Milestones ---
        if not state.reached_t1 and pnl_pct >= self.T1_PCT:
            state.reached_t1 = True
            state.t1_timestamp = timestamp
            state.locked_floor = entry_price * (1 + self.T1_PCT / 100)
            logger.info(f"{ticker}: T1 HIT (+{self.T1_PCT}%) - Floor locked at ${state.locked_floor:.2f}")
        
        if state.reached_t1 and not state.reached_cross and pnl_pct >= self.CROSS_PCT:
            state.reached_cross = True
            state.cross_timestamp = timestamp
            state.locked_floor = entry_price * (1 + self.CROSS_PCT / 100)
            logger.info(f"{ticker}: CROSS HIT (+{self.CROSS_PCT}%) - Floor locked at ${state.locked_floor:.2f}")
        
        if state.reached_cross and not state.reached_momentum and pnl_pct >= self.MOMENTUM_PCT:
            state.reached_momentum = True
            state.momentum_timestamp = timestamp
            logger.info(f"{ticker}: MOMENTUM CONFIRMED (+{self.MOMENTUM_PCT}%) - Going for T2")
        
        # --- CHECK 3: T2 Target (+1.75%) ---
        if state.reached_momentum and pnl_pct >= self.T2_PCT:
            return True, "T2", entry_price * (1 + self.T2_PCT / 100)
        
        # --- CHECK 4: Floor Breach (falls below locked floor) ---
        if current_price <= state.locked_floor:
            if state.reached_cross:
                return True, "CROSS_return", state.locked_floor
            elif state.reached_t1:
                return True, "T1_return", state.locked_floor
            else:
                return True, "stop_loss", state.locked_floor
        
        # --- CHECK 5: Dead Zone Timeouts ---
        # Update time tracking
        if state.last_price_update:
            time_delta = (timestamp - state.last_price_update).total_seconds()
            if abs(current_price - state.locked_floor) / state.locked_floor < 0.003:  # Within 0.3%
                state.time_at_current_level += time_delta
            else:
                state.time_at_current_level = 0  # Reset if moving
        
        state.last_price_update = timestamp
        
        # Check timeout based on current level
        if state.reached_momentum:
            timeout = self.DEAD_ZONE_AFTER_MOMENTUM
            level = "after_momentum"
        elif state.reached_cross:
            timeout = self.DEAD_ZONE_AT_CROSS
            level = "at_CROSS"
        elif state.reached_t1:
            timeout = self.DEAD_ZONE_AT_T1
            level = "at_T1"
        else:
            timeout = self.DEAD_ZONE_BELOW_T1
            level = "below_T1"
        
        if state.time_at_current_level >= timeout:
            logger.info(f"{ticker}: Dead zone timeout ({level}) - {state.time_at_current_level:.0f}s >= {timeout}s")
            
            # Exit at best available
            if pnl_pct > 0:
                exit_price = max(current_price, state.locked_floor)
                return True, f"dead_zone_{level}", exit_price
        
        # No exit conditions met
        return False, None, None
    
    def execute_exit(
        self,
        ticker: str,
        exit_price: float,
        exit_reason: str
    ) -> Tuple[bool, str]:
        """
        Execute exit for a position.
        
        Args:
            ticker: Stock symbol
            exit_price: Exit price
            exit_reason: Reason for exit
        
        Returns:
            (success, message)
        """
        success, message = self.pm.exit_position(ticker, exit_price, exit_reason)
        
        # Clean up milestone state
        if ticker in self.milestone_states:
            del self.milestone_states[ticker]
        
        return success, message
    
    def monitor_all_positions(self, timestamp: Optional[datetime] = None):
        """
        Monitor all active positions and execute exits as needed.
        
        This should be called every tick update (real-time monitoring).
        
        Args:
            timestamp: Current timestamp (uses datetime.now() if None)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        positions = self.pm.get_all_positions()
        
        for position in positions:
            ticker = position.ticker
            
            # Get current price
            try:
                current_price = self.ibkr.get_current_price(ticker)
                if current_price is None:
                    continue
                
                # Check exit conditions
                should_exit, reason, exit_price = self.check_exit_conditions(
                    ticker, current_price, timestamp
                )
                
                if should_exit:
                    logger.info(f"Exit signal: {ticker} @ ${exit_price:.2f} - {reason}")
                    self.execute_exit(ticker, exit_price, reason)
                    
            except Exception as e:
                logger.error(f"Error monitoring {ticker}: {e}")
```

**STEP 3: Test with 5 Scenarios (20 min)**

Create `tests/test_exit_logic_engine.py`:

```python
# Test 1: Full success T1→CROSS→momentum→T2
# Test 2: Return to CROSS
# Test 3: Dead zone at T1
# Test 4: Stop loss
# Test 5: Below T1 dead zone

# (Implementation details for each test)
```

**STEP 4: Integration Test (10 min)**

```python
# Test with Position Manager
# Test with IBKR connector
# Test monitor_all_positions()
```

**STEP 5: Commit (5 min)**

```bash
git add backend/core/exit_logic_engine.py
git add tests/test_exit_logic_engine.py
git commit -m "Phase 0: Add exit logic engine with tiered system (T1→CROSS→momentum→T2)

- Implement full 4-milestone tiered exit logic per trading_strategy_explainer.md
- Add adaptive dead zone timeouts (3/4/4/6 min by level)
- Lock floors at T1 (+0.75%) and CROSS (+1.00%)
- Momentum confirmation at +1.25% before pursuing T2
- Stop loss at -0.5%
- Track milestone state for each position
- Tested with 5 scenarios from explainer"
git push origin main
```

---

### ✅ Success Criteria (All Must Pass)

- [ ] Read trading_strategy_explainer.md (verified)
- [ ] Verified Position Manager methods exist (verified)
- [ ] Verified IBKR connector methods exist (verified)
- [ ] Implemented 4 milestones: T1, CROSS, momentum, T2
- [ ] Implemented adaptive dead zone timeouts: 3/4/4/6 min
- [ ] Floor locks at T1 and CROSS
- [ ] Falls below floor triggers exit
- [ ] Stop loss at -0.5% works
- [ ] Test 1 passes (full success)
- [ ] Test 2 passes (return to CROSS)
- [ ] Test 3 passes (dead zone at T1)
- [ ] Test 4 passes (stop loss)
- [ ] Test 5 passes (below T1 dead zone)
- [ ] No phantom references (all methods verified)
- [ ] Integration test with Position Manager works
- [ ] Commit pushed to GitHub
- [ ] User confirmed commit visible in GitHub Desktop

---

### 🔍 Verification Steps (Do After Coding)

```bash
# 1. Check file exists
ls -la backend/core/exit_logic_engine.py

# 2. Check for phantom references
python3 -c "
import sys
sys.path.append('.')
from backend.core.exit_logic_engine import ExitLogicEngine
print('✅ No import errors')
"

# 3. Run tests
python3 tests/test_exit_logic_engine.py

# 4. Check commit
git log -1 --oneline
```

---

## Component 8: Risk Management System

**File**: `backend/core/risk_manager.py`

---

### 🚨 MANDATORY PRE-WORK (DO THIS FIRST OR FAIL)

**BEFORE writing any code, you MUST:**

1. **Read the trading strategy explainer** (15 minutes):
   ```bash
   Read: docs/explainers/trading_strategy_explainer.md
   Focus on: "Guardrails active" section
   Focus on: Daily loss limit (-1.5%)
   Focus on: Per-trade stop loss (-0.5%)
   Note: "If daily loss hits -1.5%, stop all trading"
   ```

2. **Review existing components** (verify these files exist and study their APIs):
   ```bash
   View: backend/core/position_manager.py
   Check methods: get_all_positions(), close_all_positions(), get_total_unrealized_pnl()
   
   View: backend/models/database.py
   Check methods: get_daily_fills(), get_daily_summary()
   Note: Need to verify if these methods exist or what they're actually called
   
   View: backend/data/ibkr_connector_insync.py
   Check methods: get_account_balance()
   ```

3. **Read common pitfalls** (avoid past mistakes):
   ```bash
   Read: /mnt/skills/user/lrbf-skill/references/common-pitfalls.md
   Focus on: "Phantom References" section
   Focus on: "Assumption-Based Development" section
   Focus on: "Marking Complete Without Testing" section
   ```

**⚠️ If you skip this pre-work, you WILL create risk management that doesn't actually protect capital.**

---

### 🛑 CRITICAL CHECKPOINT (STOP HERE UNTIL COMPLETE)

**YOU CANNOT PROCEED TO CODING UNTIL YOU:**

1. ✅ **Read and confirmed understanding of:**
   - [ ] docs/explainers/trading_strategy_explainer.md (daily loss limit section)
   - [ ] /mnt/skills/user/lrbf-skill/references/common-pitfalls.md (ALL pitfall sections)
   - [ ] backend/core/position_manager.py (verified methods exist)
   - [ ] backend/models/database.py (verified fill retrieval methods exist)

2. ✅ **Verified these methods exist (grep each one):**
   - [ ] position_manager.get_all_positions()
   - [ ] position_manager.close_all_positions()
   - [ ] position_manager.get_total_unrealized_pnl()
   - [ ] database.get_todays_fills() OR database.get_daily_fills() (find actual name)
   - [ ] ibkr_connector.get_account_balance()

3. ✅ **Aware of ALL critical pitfalls:**
   - [ ] Not actually calculating realized P&L from database
   - [ ] Using unrealized P&L instead of realized P&L for daily loss
   - [ ] Not including commission in loss calculation
   - [ ] Checking daily loss once instead of continuously
   - [ ] Not providing clear kill switch for emergency stops
   - [ ] Assuming methods exist without verification
   - [ ] Not testing emergency stop scenario

**WHEN COMMITTING THIS COMPONENT, YOU MUST REPORT:**

```
Component 8 Complete - Pre-Commit Verification Report:

✅ Read trading_strategy_explainer.md - understood daily loss limit (-1.5%)
✅ Read common-pitfalls.md - aware of all 7 critical pitfalls
✅ Verified position_manager.close_all_positions() exists (line X)
✅ Verified database.[method_name]() exists (line Y)
✅ Verified ibkr_connector.get_account_balance() exists (line Z)
✅ Implemented continuous daily loss monitoring
✅ Implemented emergency kill switch
✅ Uses REALIZED P&L from database (not unrealized)
✅ Includes commission in loss calculation
✅ Test scenario 1 passes (normal trading below limit)
✅ Test scenario 2 passes (hits -1.5% limit, stops trading)
✅ Test scenario 3 passes (emergency kill switch)
✅ Integration test passes
✅ No phantom references found

Commit: [hash]
Ready for user confirmation.
```

**If you cannot check ALL boxes above, DO NOT COMMIT. Ask user for guidance.**

---

### 🎯 Purpose

Monitor cumulative realized P&L and enforce risk limits to protect capital:
- **Daily loss limit**: Stop all trading if realized loss reaches -1.5% of capital
- **Kill switch**: Immediate emergency stop that closes all positions
- **Continuous monitoring**: Check limits after every fill

**NOT just checking once**. This is **continuous real-time monitoring** with automatic shutdown.

---

### 📊 Risk Limits (CRITICAL - Study This)

```
Starting Capital: $50,000
    ↓
Daily Loss Limit: -$750 (-1.5%)
    ↓
    ├─ Realized P&L > -$750 → ✅ Continue trading
    ├─ Realized P&L ≤ -$750 → 🛑 STOP ALL TRADING
    │   ├─ Close all open positions
    │   ├─ Mark system as HALTED
    │   ├─ Reject all new entry signals
    │   └─ Log emergency stop event
    └─ Kill switch activated → 🛑 EMERGENCY STOP
        └─ Same as above but triggered manually
```

**Example from trading_strategy_explainer.md**:
- Starting capital: $50,000
- Trade 1: -$200 (loss)
- Trade 2: +$150 (win)
- Trade 3: -$300 (loss)
- Trade 4: -$400 (loss)
- **Cumulative realized P&L: -$750 (-1.5%)**
- **System halts automatically, closes all positions**

---

### 🚨 CRITICAL PITFALLS (Read Before Coding)

**From common-pitfalls.md and institutional risk management:**

| ❌ WRONG | ✅ RIGHT |
|----------|----------|
| Check daily loss once | Continuous monitoring after every fill |
| Use unrealized P&L | Use REALIZED P&L from database fills |
| Ignore commission | Include commission in loss calculation |
| Soft warning only | Hard stop - reject all new trades |
| Let positions run | Close ALL positions when limit hit |
| No emergency override | Implement kill switch for manual stop |
| Check at EOD only | Check in real-time after each fill |

**Reality Check Questions** (ask yourself these):
- ❓ Did I verify database method for getting today's fills exists?
- ❓ Am I using REALIZED P&L (from closed trades) not unrealized?
- ❓ Am I including commission in the loss calculation?
- ❓ Does the system actually PREVENT new trades after halt?
- ❓ Does it CLOSE all positions, not just stop opening new ones?
- ❓ Did I test the emergency scenario where -1.5% is hit?

---

### 📋 Step-by-Step Implementation

**STEP 1: Verify Dependencies (5 min)**

```bash
# Check Position Manager methods exist
grep "def close_all_positions" backend/core/position_manager.py
grep "def get_all_positions" backend/core/position_manager.py
grep "def get_total_unrealized_pnl" backend/core/position_manager.py

# Check Database methods exist (find actual method name)
grep "def get.*fill" backend/models/database.py
# Look for methods that return today's fills or daily summary

# Check IBKR connector
grep "def get_account_balance" backend/data/ibkr_connector_insync.py

# If ANY grep returns nothing → METHOD DOES NOT EXIST
# Read those files to find the actual method names
```

**STEP 2: Create risk_manager.py (30 min)**

```python
"""
Risk Manager - Component 8

Enforces capital protection limits:
- Daily loss limit: -1.5% of capital
- Emergency kill switch for immediate stops

Continuously monitors realized P&L and halts trading when limit breached.

Author: The Luggage Room Boys Fund
Date: November 2025
"""

from typing import Dict, Tuple, Optional, List
from datetime import datetime, date
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RiskStatus:
    """Current risk status of the trading system."""
    is_halted: bool = False
    halt_reason: Optional[str] = None
    halt_timestamp: Optional[datetime] = None
    daily_realized_pnl: float = 0.0
    daily_loss_limit: float = 0.0
    starting_capital: float = 0.0
    daily_loss_pct: float = 0.0


class RiskManager:
    """
    Monitors and enforces risk limits.
    
    Usage:
        risk_mgr = RiskManager(
            position_manager=pm,
            database=db,
            ibkr_connector=ibkr,
            starting_capital=50000.0
        )
        
        # After each fill
        if risk_mgr.check_daily_loss_limit():
            # Trading halted
            pass
        
        # Before opening new position
        if not risk_mgr.can_trade():
            # Reject trade - system halted
            pass
    """
    
    def __init__(
        self,
        position_manager,
        database,
        ibkr_connector,
        starting_capital: float = 50000.0,
        daily_loss_limit_pct: float = 1.5
    ):
        """
        Initialize risk manager.
        
        Args:
            position_manager: PositionManager instance
            database: TradingDatabase instance
            ibkr_connector: IBKRConnectorInsync instance
            starting_capital: Starting capital for the day
            daily_loss_limit_pct: Daily loss limit as % of capital (default 1.5%)
        """
        self.pm = position_manager
        self.db = database
        self.ibkr = ibkr_connector
        
        self.starting_capital = starting_capital
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.daily_loss_limit_dollars = starting_capital * (daily_loss_limit_pct / 100)
        
        # Risk status
        self.status = RiskStatus(
            starting_capital=starting_capital,
            daily_loss_limit=-self.daily_loss_limit_dollars
        )
        
        logger.info(
            f"RiskManager initialized - Capital: ${starting_capital:,.2f}, "
            f"Daily Loss Limit: -${self.daily_loss_limit_dollars:.2f} (-{daily_loss_limit_pct}%)"
        )
    
    def get_daily_realized_pnl(self) -> Tuple[float, List[Dict]]:
        """
        Calculate total realized P&L for today from database fills.
        
        CRITICAL: Uses REALIZED P&L (closed trades) not unrealized.
        CRITICAL: Includes commission in calculation.
        
        Returns:
            (total_pnl, fills_list)
        """
        try:
            # Get today's fills from database
            # NOTE: Verify actual method name exists in database.py
            today = date.today()
            fills = self.db.get_todays_fills()  # VERIFY THIS METHOD EXISTS
            
            if not fills:
                return 0.0, []
            
            # Calculate realized P&L including commission
            total_pnl = 0.0
            for fill in fills:
                pnl = fill.get('realized_pnl', 0.0)
                commission = fill.get('commission', 0.0)
                total_pnl += (pnl - commission)
            
            return total_pnl, fills
            
        except Exception as e:
            logger.error(f"Error calculating daily realized P&L: {e}")
            return 0.0, []
    
    def check_daily_loss_limit(self) -> bool:
        """
        Check if daily loss limit has been breached.
        
        This should be called after EVERY fill.
        
        Returns:
            True if system was halted (limit breached)
        """
        # Get current realized P&L
        daily_pnl, fills = self.get_daily_realized_pnl()
        
        # Update status
        self.status.daily_realized_pnl = daily_pnl
        self.status.daily_loss_pct = (daily_pnl / self.starting_capital) * 100
        
        # Check if limit breached
        if daily_pnl <= -self.daily_loss_limit_dollars and not self.status.is_halted:
            logger.critical(
                f"🛑 DAILY LOSS LIMIT BREACHED: ${daily_pnl:.2f} "
                f"({self.status.daily_loss_pct:.2f}%) ≤ -${self.daily_loss_limit_dollars:.2f} "
                f"(-{self.daily_loss_limit_pct}%)"
            )
            
            # Halt system
            self.halt_trading("daily_loss_limit_breached")
            return True
        
        return False
    
    def halt_trading(self, reason: str):
        """
        Halt all trading and close open positions.
        
        Args:
            reason: Reason for halt (e.g., 'daily_loss_limit_breached', 'kill_switch')
        """
        if self.status.is_halted:
            logger.warning(f"System already halted: {self.status.halt_reason}")
            return
        
        logger.critical(f"🛑 HALTING TRADING: {reason}")
        
        # Update status
        self.status.is_halted = True
        self.status.halt_reason = reason
        self.status.halt_timestamp = datetime.now()
        
        # Close all open positions
        results = self.pm.close_all_positions(reason=f"Emergency stop: {reason}")
        
        # Log results
        success_count = sum(1 for success, _ in results.values() if success)
        logger.critical(
            f"Emergency position closure: {success_count}/{len(results)} positions closed"
        )
        
        # Log to database
        self.db.log_event(
            event_type="CRITICAL",
            severity="HIGH",
            message=f"Trading halted: {reason}",
            ticker=None
        )
    
    def activate_kill_switch(self):
        """
        Manually activate emergency kill switch.
        
        Immediately halts trading and closes all positions.
        """
        logger.critical("🚨 KILL SWITCH ACTIVATED")
        self.halt_trading("kill_switch_manual")
    
    def can_trade(self) -> Tuple[bool, str]:
        """
        Check if system can accept new trades.
        
        Returns:
            (can_trade, reason)
        """
        if self.status.is_halted:
            return False, f"System halted: {self.status.halt_reason}"
        
        return True, "OK"
    
    def reset_halt(self, authorized: bool = False):
        """
        Reset halt status (use with EXTREME caution).
        
        Args:
            authorized: Must be True to reset (safety check)
        """
        if not authorized:
            logger.error("Cannot reset halt - authorization required")
            return
        
        logger.warning("⚠️ Resetting halt status - trading will resume")
        
        self.status.is_halted = False
        self.status.halt_reason = None
        self.status.halt_timestamp = None
        
        self.db.log_event(
            event_type="WARNING",
            severity="MEDIUM",
            message="Halt status reset - trading resumed",
            ticker=None
        )
    
    def get_risk_status(self) -> Dict:
        """
        Get current risk status.
        
        Returns:
            Dictionary with risk metrics
        """
        return {
            'is_halted': self.status.is_halted,
            'halt_reason': self.status.halt_reason,
            'halt_timestamp': self.status.halt_timestamp.isoformat() if self.status.halt_timestamp else None,
            'daily_realized_pnl': self.status.daily_realized_pnl,
            'daily_loss_pct': self.status.daily_loss_pct,
            'daily_loss_limit_dollars': -self.daily_loss_limit_dollars,
            'daily_loss_limit_pct': -self.daily_loss_limit_pct,
            'starting_capital': self.starting_capital,
            'loss_limit_remaining': self.daily_loss_limit_dollars + self.status.daily_realized_pnl
        }
```

**STEP 3: Test with 3 Scenarios (20 min)**

Create `tests/test_risk_manager.py`:

```python
# Test 1: Normal trading (below limit)
# - Multiple trades, cumulative loss at -0.8%
# - System should NOT halt
# - can_trade() should return True

# Test 2: Daily loss limit breach
# - Multiple trades, cumulative loss hits -1.5%
# - System SHOULD halt automatically
# - can_trade() should return False
# - All positions should be closed

# Test 3: Emergency kill switch
# - Manually activate kill switch
# - System should halt immediately
# - All positions should be closed
# - can_trade() should return False

# (Implementation details for each test)
```

**STEP 4: Integration Test (10 min)**

```python
# Test with Position Manager
# Test with Database fills
# Test with IBKR connector
# Test check_daily_loss_limit() after simulated fills
```

**STEP 5: Commit (5 min)**

```bash
git add backend/core/risk_manager.py
git add tests/test_risk_manager.py
git commit -m "Phase 0: Add risk management system with -1.5% daily loss limit

- Continuous monitoring of realized P&L from database fills
- Automatic halt when daily loss reaches -1.5% of capital
- Emergency kill switch for manual stops
- Closes all positions when limit breached
- Uses realized P&L (not unrealized) with commission
- Tested with 3 scenarios (normal, limit breach, kill switch)"
git push origin main
```

---

### ✅ Success Criteria (All Must Pass)

- [ ] Read trading_strategy_explainer.md (verified)
- [ ] Verified Position Manager methods exist (verified line numbers)
- [ ] Verified Database fill methods exist (verified line numbers)
- [ ] Verified IBKR connector methods exist (verified line numbers)
- [ ] Uses REALIZED P&L from database (not unrealized)
- [ ] Includes commission in loss calculation
- [ ] Continuous monitoring (not just once)
- [ ] Automatically halts at -1.5% limit
- [ ] Closes all positions when halted
- [ ] Rejects new trades when halted (can_trade() returns False)
- [ ] Kill switch works (manual emergency stop)
- [ ] Test 1 passes (normal trading below limit)
- [ ] Test 2 passes (auto-halt at -1.5%)
- [ ] Test 3 passes (kill switch)
- [ ] No phantom references (all methods verified)
- [ ] Integration test with Position Manager works
- [ ] Integration test with Database works
- [ ] Commit pushed to GitHub
- [ ] User confirmed commit visible in GitHub Desktop

---

### 🔍 Verification Steps (Do After Coding)

```bash
# 1. Check file exists
ls -la backend/core/risk_manager.py

# 2. Check for phantom references
python3 -c "
import sys
sys.path.append('.')
from backend.core.risk_manager import RiskManager
print('✅ No import errors')
"

# 3. Run tests
python3 tests/test_risk_manager.py

# 4. Check commit
git log -1 --oneline
```

---


## Components 9-19: TODO

*(To be detailed in subsequent updates)*
