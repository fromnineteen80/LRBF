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


## Component 9: Cooldown Manager

**File**: `backend/core/cooldown_manager.py`

---

### 🚨 MANDATORY PRE-WORK (DO THIS FIRST OR FAIL)

**BEFORE writing any code, you MUST:**

1. **Read the trading strategy explainer** (10 minutes):
   ```bash
   Read: docs/explainers/trading_strategy_explainer.md
   Focus on: "After entry (tiered exit system)" section
   Note: "Wait 1 minute - Cool down before scanning same stock again"
   Understand: Why cooldown exists (prevent overtrading same stock)
   ```

2. **Review existing components** (verify these files exist and study their APIs):
   ```bash
   View: backend/core/position_manager.py
   Check: How positions are tracked by ticker
   Note: We need to track tickers that recently exited
   
   View: backend/core/exit_logic_engine.py
   Check: How exits are signaled (exit_reason, exit_time)
   Note: Cooldown starts AFTER exit, not after entry
   ```

3. **Read common pitfalls** (avoid past mistakes):
   ```bash
   Read: /mnt/skills/user/lrbf-skill/references/common-pitfalls.md
   Focus on: "Complex Code Over Simple Solutions" section
   Focus on: "Phantom References" section
   ```

**⚠️ If you skip this pre-work, you'll create a cooldown system that doesn't actually prevent re-entry.**

---

### 🛑 CRITICAL CHECKPOINT (STOP HERE UNTIL COMPLETE)

**YOU CANNOT PROCEED TO CODING UNTIL YOU:**

1. ✅ **Read and confirmed understanding of:**
   - [ ] docs/explainers/trading_strategy_explainer.md (cooldown section)
   - [ ] /mnt/skills/user/lrbf-skill/references/common-pitfalls.md (ALL pitfall sections)
   - [ ] Understanding: Cooldown is PER TICKER, not global
   - [ ] Understanding: Cooldown starts AFTER exit, not after entry

2. ✅ **Verified these concepts:**
   - [ ] Cooldown is 60 seconds (1 minute) per trading strategy
   - [ ] Cooldown prevents ENTRY only (doesn't affect exits)
   - [ ] Each ticker has independent cooldown timer
   - [ ] Cooldown starts when position EXITS (not when it enters)

3. ✅ **Aware of ALL critical pitfalls:**
   - [ ] Making cooldown global instead of per-ticker
   - [ ] Starting cooldown at entry instead of exit
   - [ ] Not actually blocking entry attempts during cooldown
   - [ ] Using complex timer logic instead of simple timestamp check
   - [ ] Not cleaning up old cooldown records (memory leak)
   - [ ] Blocking exits during cooldown (should only block entries)

**WHEN COMMITTING THIS COMPONENT, YOU MUST REPORT:**

```
Component 9 Complete - Pre-Commit Verification Report:

✅ Read trading_strategy_explainer.md - understood 1-minute cooldown
✅ Read common-pitfalls.md - aware of all 6 critical pitfalls
✅ Cooldown is per-ticker (not global)
✅ Cooldown starts after EXIT (not entry)
✅ Cooldown duration: 60 seconds
✅ Only blocks ENTRIES (not exits)
✅ Cleans up expired cooldowns (no memory leak)
✅ Test scenario 1 passes (blocks re-entry during cooldown)
✅ Test scenario 2 passes (allows re-entry after cooldown)
✅ Test scenario 3 passes (multiple tickers independent)
✅ Test scenario 4 passes (doesn't block exits)
✅ Integration test passes
✅ No phantom references found

Commit: [hash]
Ready for user confirmation.
```

**If you cannot check ALL boxes above, DO NOT COMMIT. Ask user for guidance.**

---

### 🎯 Purpose

Prevent overtrading the same stock by enforcing a 1-minute cooldown after each exit.

**From trading_strategy_explainer.md:**
> "Wait 1 minute - Cool down before scanning same stock again"

**Why this matters:**
- Prevents emotional re-entry (chasing the same stock)
- Allows price action to settle after our exit
- Reduces transaction costs from excessive trading
- Enforces discipline in pattern recognition

**NOT a global pause**. This is **per-ticker cooldown** - other stocks can still be traded.

---

### 📊 Cooldown Logic (CRITICAL - Study This)

```
AAPL Position Lifecycle:
    ↓
Entry @ 9:31:00 AM
    ↓
Hold for 3 minutes
    ↓
Exit @ 9:34:00 AM ← COOLDOWN STARTS HERE
    ↓
Cooldown until 9:35:00 AM (60 seconds)
    ↓
    ├─ 9:34:30 AM: New AAPL entry signal → ❌ BLOCKED (in cooldown)
    ├─ 9:34:50 AM: New AAPL entry signal → ❌ BLOCKED (in cooldown)
    └─ 9:35:01 AM: New AAPL entry signal → ✅ ALLOWED (cooldown expired)

Meanwhile:
MSFT can be traded normally (independent cooldown)
NVDA can be traded normally (independent cooldown)
```

**Example from trading strategy:**
1. AAPL exits at 10:15:00 AM
2. New AAPL pattern detected at 10:15:30 AM
3. Cooldown manager checks: (10:15:30 - 10:15:00) = 30 seconds < 60 seconds
4. **Entry BLOCKED** - still in cooldown
5. New AAPL pattern detected at 10:16:05 AM
6. Cooldown manager checks: (10:16:05 - 10:15:00) = 65 seconds > 60 seconds
7. **Entry ALLOWED** - cooldown expired

---

### 🚨 CRITICAL PITFALLS (Read Before Coding)

**From common-pitfalls.md and past failures:**

| ❌ WRONG | ✅ RIGHT |
|----------|----------|
| Global cooldown (all stocks) | Per-ticker cooldown (independent) |
| Start cooldown at entry | Start cooldown at EXIT |
| Warn but allow entry | Actually BLOCK entry attempt |
| Complex state machine | Simple timestamp comparison |
| Keep all cooldowns forever | Clean up expired cooldowns |
| Block exits during cooldown | Only block ENTRIES |
| Fixed cooldown dict | Auto-cleanup old entries |

**Reality Check Questions** (ask yourself these):
- ❓ Is cooldown per-ticker or global? (should be per-ticker)
- ❓ When does cooldown start - entry or exit? (should be exit)
- ❓ Does it actually BLOCK entry or just warn? (must block)
- ❓ Can we still EXIT a stock during its cooldown? (yes - only entries blocked)
- ❓ Are expired cooldowns cleaned up? (yes - prevent memory leak)
- ❓ Did I test multiple independent ticker cooldowns?

---

### 📋 Step-by-Step Implementation

**STEP 1: Verify Dependencies (5 min)**

```bash
# Check if we need any external methods
# Cooldown manager is mostly self-contained
# Just needs to track ticker + timestamp pairs

# No external method dependencies to verify
echo "✅ Cooldown manager is self-contained"
```

**STEP 2: Create cooldown_manager.py (20 min)**

```python
"""
Cooldown Manager - Component 9

Enforces 1-minute cooldown per ticker after position exit.

From trading_strategy_explainer.md:
"Wait 1 minute - Cool down before scanning same stock again"

Prevents overtrading the same stock immediately after exit.

Author: The Luggage Room Boys Fund
Date: November 2025
"""

from typing import Dict, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CooldownManager:
    """
    Manages per-ticker cooldown periods after position exits.
    
    Simple rule: After exiting a position, wait 60 seconds before
    entering the same ticker again.
    
    Usage:
        cooldown = CooldownManager(cooldown_seconds=60)
        
        # After exiting AAPL
        cooldown.start_cooldown('AAPL')
        
        # Before entering AAPL again
        can_enter, reason = cooldown.can_enter('AAPL')
        if not can_enter:
            # Block entry - still in cooldown
            pass
    """
    
    def __init__(self, cooldown_seconds: int = 60):
        """
        Initialize cooldown manager.
        
        Args:
            cooldown_seconds: Cooldown duration in seconds (default 60)
        """
        self.cooldown_duration = timedelta(seconds=cooldown_seconds)
        
        # Track cooldown end time for each ticker
        # {ticker: cooldown_end_time}
        self.cooldowns: Dict[str, datetime] = {}
        
        logger.info(f"CooldownManager initialized - Duration: {cooldown_seconds}s")
    
    def start_cooldown(self, ticker: str, exit_time: datetime = None):
        """
        Start cooldown for a ticker after position exit.
        
        Args:
            ticker: Stock symbol
            exit_time: Exit timestamp (uses now() if None)
        """
        if exit_time is None:
            exit_time = datetime.now()
        
        cooldown_end = exit_time + self.cooldown_duration
        self.cooldowns[ticker] = cooldown_end
        
        logger.info(
            f"Cooldown started: {ticker} - "
            f"Exit: {exit_time.strftime('%H:%M:%S')}, "
            f"Available: {cooldown_end.strftime('%H:%M:%S')}"
        )
    
    def can_enter(self, ticker: str, current_time: datetime = None) -> Tuple[bool, str]:
        """
        Check if ticker can be entered (not in cooldown).
        
        Args:
            ticker: Stock symbol
            current_time: Current timestamp (uses now() if None)
        
        Returns:
            (can_enter, reason)
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Check if ticker is in cooldown
        if ticker not in self.cooldowns:
            return True, "No cooldown active"
        
        cooldown_end = self.cooldowns[ticker]
        
        # Check if cooldown expired
        if current_time >= cooldown_end:
            # Cooldown expired - clean up and allow
            del self.cooldowns[ticker]
            return True, "Cooldown expired"
        
        # Still in cooldown
        remaining_seconds = (cooldown_end - current_time).total_seconds()
        return False, f"In cooldown - {remaining_seconds:.0f}s remaining"
    
    def get_cooldown_status(self, ticker: str, current_time: datetime = None) -> Dict:
        """
        Get cooldown status for a ticker.
        
        Args:
            ticker: Stock symbol
            current_time: Current timestamp (uses now() if None)
        
        Returns:
            Dictionary with cooldown info
        """
        if current_time is None:
            current_time = datetime.now()
        
        if ticker not in self.cooldowns:
            return {
                'ticker': ticker,
                'in_cooldown': False,
                'can_enter': True,
                'cooldown_end': None,
                'remaining_seconds': 0
            }
        
        cooldown_end = self.cooldowns[ticker]
        remaining = (cooldown_end - current_time).total_seconds()
        
        return {
            'ticker': ticker,
            'in_cooldown': remaining > 0,
            'can_enter': remaining <= 0,
            'cooldown_end': cooldown_end.isoformat(),
            'remaining_seconds': max(0, remaining)
        }
    
    def cleanup_expired_cooldowns(self, current_time: datetime = None):
        """
        Remove expired cooldowns to prevent memory leak.
        
        This should be called periodically (e.g., every minute).
        
        Args:
            current_time: Current timestamp (uses now() if None)
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Find expired cooldowns
        expired = [
            ticker for ticker, cooldown_end in self.cooldowns.items()
            if current_time >= cooldown_end
        ]
        
        # Remove them
        for ticker in expired:
            del self.cooldowns[ticker]
        
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired cooldowns: {expired}")
    
    def get_all_cooldowns(self, current_time: datetime = None) -> Dict[str, Dict]:
        """
        Get status of all active cooldowns.
        
        Args:
            current_time: Current timestamp (uses now() if None)
        
        Returns:
            Dictionary mapping ticker to cooldown status
        """
        if current_time is None:
            current_time = datetime.now()
        
        return {
            ticker: self.get_cooldown_status(ticker, current_time)
            for ticker in self.cooldowns.keys()
        }
    
    def reset_cooldown(self, ticker: str):
        """
        Manually reset cooldown for a ticker (emergency use only).
        
        Args:
            ticker: Stock symbol
        """
        if ticker in self.cooldowns:
            del self.cooldowns[ticker]
            logger.warning(f"⚠️ Cooldown manually reset for {ticker}")
    
    def reset_all_cooldowns(self):
        """
        Reset all cooldowns (emergency use only).
        """
        count = len(self.cooldowns)
        self.cooldowns.clear()
        logger.warning(f"⚠️ All cooldowns reset ({count} tickers)")
```

**STEP 3: Test with 4 Scenarios (20 min)**

Create `tests/test_cooldown_manager.py`:

```python
"""Test cooldown manager."""

from backend.core.cooldown_manager import CooldownManager
from datetime import datetime, timedelta


def test_scenario_1_blocks_reentry_during_cooldown():
    """Test that entry is blocked during cooldown period."""
    cooldown = CooldownManager(cooldown_seconds=60)
    
    # Exit AAPL at 10:00:00
    exit_time = datetime(2025, 11, 1, 10, 0, 0)
    cooldown.start_cooldown('AAPL', exit_time)
    
    # Try to enter at 10:00:30 (30 seconds later)
    current_time = datetime(2025, 11, 1, 10, 0, 30)
    can_enter, reason = cooldown.can_enter('AAPL', current_time)
    
    assert can_enter == False, "Should block entry during cooldown"
    assert "30s remaining" in reason
    print("✅ Test 1 passed: Blocks re-entry during cooldown")


def test_scenario_2_allows_reentry_after_cooldown():
    """Test that entry is allowed after cooldown expires."""
    cooldown = CooldownManager(cooldown_seconds=60)
    
    # Exit AAPL at 10:00:00
    exit_time = datetime(2025, 11, 1, 10, 0, 0)
    cooldown.start_cooldown('AAPL', exit_time)
    
    # Try to enter at 10:01:05 (65 seconds later)
    current_time = datetime(2025, 11, 1, 10, 1, 5)
    can_enter, reason = cooldown.can_enter('AAPL', current_time)
    
    assert can_enter == True, "Should allow entry after cooldown"
    assert "expired" in reason.lower()
    print("✅ Test 2 passed: Allows re-entry after cooldown")


def test_scenario_3_multiple_tickers_independent():
    """Test that multiple tickers have independent cooldowns."""
    cooldown = CooldownManager(cooldown_seconds=60)
    
    base_time = datetime(2025, 11, 1, 10, 0, 0)
    
    # Exit AAPL at 10:00:00
    cooldown.start_cooldown('AAPL', base_time)
    
    # Exit MSFT at 10:00:30
    cooldown.start_cooldown('MSFT', base_time + timedelta(seconds=30))
    
    # At 10:00:45
    check_time = base_time + timedelta(seconds=45)
    
    # AAPL cooldown should be almost expired (45s elapsed)
    can_enter_aapl, _ = cooldown.can_enter('AAPL', check_time)
    
    # MSFT cooldown should still be active (15s elapsed)
    can_enter_msft, _ = cooldown.can_enter('MSFT', check_time)
    
    assert can_enter_aapl == False, "AAPL still in cooldown"
    assert can_enter_msft == False, "MSFT still in cooldown"
    
    # At 10:01:05 (65s after AAPL exit, 35s after MSFT exit)
    check_time2 = base_time + timedelta(seconds=65)
    
    can_enter_aapl2, _ = cooldown.can_enter('AAPL', check_time2)
    can_enter_msft2, _ = cooldown.can_enter('MSFT', check_time2)
    
    assert can_enter_aapl2 == True, "AAPL cooldown expired"
    assert can_enter_msft2 == False, "MSFT still in cooldown"
    
    print("✅ Test 3 passed: Multiple tickers have independent cooldowns")


def test_scenario_4_doesnt_block_exits():
    """Test that cooldown doesn't affect exits (only entries)."""
    cooldown = CooldownManager(cooldown_seconds=60)
    
    # Exit AAPL at 10:00:00
    exit_time = datetime(2025, 11, 1, 10, 0, 0)
    cooldown.start_cooldown('AAPL', exit_time)
    
    # Cooldown manager doesn't control exits
    # This test just verifies the logic is entry-only
    # (In real system, Position Manager handles exits independently)
    
    can_enter, _ = cooldown.can_enter('AAPL', exit_time + timedelta(seconds=30))
    assert can_enter == False, "Entry blocked during cooldown"
    
    # But we could still call start_cooldown again if we exited another position
    # (This would reset the cooldown timer)
    cooldown.start_cooldown('AAPL', exit_time + timedelta(seconds=30))
    
    print("✅ Test 4 passed: Cooldown only affects entries")


if __name__ == "__main__":
    test_scenario_1_blocks_reentry_during_cooldown()
    test_scenario_2_allows_reentry_after_cooldown()
    test_scenario_3_multiple_tickers_independent()
    test_scenario_4_doesnt_block_exits()
    print("
" + "="*60)
    print("✅ All cooldown manager tests passed!")
```

**STEP 4: Integration Test (10 min)**

```python
# Test cleanup_expired_cooldowns()
# Test get_all_cooldowns()
# Test integration with Position Manager workflow
```

**STEP 5: Commit (5 min)**

```bash
git add backend/core/cooldown_manager.py
git add tests/test_cooldown_manager.py
git commit -m "Phase 0: Add cooldown manager with 1-minute per-ticker cooldown

- Per-ticker cooldown (60 seconds) after position exit
- Blocks re-entry during cooldown period
- Independent cooldowns for multiple tickers
- Auto-cleanup of expired cooldowns (no memory leak)
- Only blocks entries (exits not affected)
- Tested with 4 scenarios (block/allow/multi-ticker/exit-check)"
git push origin main
```

---

### ✅ Success Criteria (All Must Pass)

- [ ] Read trading_strategy_explainer.md (verified)
- [ ] Understood cooldown is per-ticker, not global (verified)
- [ ] Understood cooldown starts after EXIT, not entry (verified)
- [ ] Cooldown duration is 60 seconds (verified)
- [ ] Only blocks ENTRIES, not exits (verified)
- [ ] Test 1 passes (blocks re-entry during cooldown)
- [ ] Test 2 passes (allows re-entry after cooldown)
- [ ] Test 3 passes (multiple tickers independent)
- [ ] Test 4 passes (doesn't block exits)
- [ ] Cleanup removes expired cooldowns (no memory leak)
- [ ] No phantom references (all self-contained)
- [ ] Integration test passes
- [ ] Commit pushed to GitHub
- [ ] User confirmed commit visible in GitHub Desktop

---

### 🔍 Verification Steps (Do After Coding)

```bash
# 1. Check file exists
ls -la backend/core/cooldown_manager.py

# 2. Check for phantom references (should be none - self-contained)
python3 -c "
import sys
sys.path.append('.')
from backend.core.cooldown_manager import CooldownManager
print('✅ No import errors')
"

# 3. Run tests
python3 tests/test_cooldown_manager.py

# 4. Check commit
git log -1 --oneline
```

---


## Component 10: Metrics Calculator

**File**: `backend/core/metrics_calculator.py`

---

### 🚨 MANDATORY PRE-WORK (DO THIS FIRST OR FAIL)

**BEFORE writing any code, you MUST:**

1. **Read the trading strategy explainer** (15 minutes):
   ```bash
   Read: docs/explainers/trading_strategy_explainer.md
   Focus on: Performance metrics mentioned throughout
   Note: Win rate, P&L, trade counts
   
   Read: docs/explainers/morning_report_explainer.md
   Focus on: "Quality Scoring (5:47:00 AM)" section
   Note: All 16 scoring categories - these are the metrics we calculate
   ```

2. **Review existing components** (verify these files exist and study their APIs):
   ```bash
   View: backend/models/database.py
   Check methods: get_todays_fills(), get_daily_summary()
   Note: How fills are stored (realized_pnl, commission, etc.)
   
   View: backend/core/position_manager.py
   Check methods: get_all_positions(), get_total_unrealized_pnl()
   Note: How positions track entry_price, current_price, unrealized_pnl
   ```

3. **Read common pitfalls** (avoid past mistakes):
   ```bash
   Read: /mnt/skills/user/lrbf-skill/references/common-pitfalls.md
   Focus on: "Phantom References" section
   Focus on: "Assumption-Based Development" section
   Focus on: "Complex Code Over Simple Solutions" section
   ```

**⚠️ If you skip this pre-work, you'll calculate metrics incorrectly and provide misleading performance data.**

---

### 🛑 CRITICAL CHECKPOINT (STOP HERE UNTIL COMPLETE)

**YOU CANNOT PROCEED TO CODING UNTIL YOU:**

1. ✅ **Read and confirmed understanding of:**
   - [ ] docs/explainers/morning_report_explainer.md (16 scoring categories)
   - [ ] docs/explainers/trading_strategy_explainer.md (performance metrics)
   - [ ] /mnt/skills/user/lrbf-skill/references/common-pitfalls.md (ALL pitfall sections)
   - [ ] backend/models/database.py (fill data structure)

2. ✅ **Verified these methods exist (grep each one):**
   - [ ] database.get_todays_fills() OR similar method (find actual name)
   - [ ] position_manager.get_all_positions()
   - [ ] position_manager.get_total_unrealized_pnl()

3. ✅ **Aware of ALL critical pitfalls:**
   - [ ] Mixing realized and unrealized P&L (must separate)
   - [ ] Not including commission in calculations
   - [ ] Dividing by zero when no trades (edge case handling)
   - [ ] Using float for money calculations (precision errors)
   - [ ] Calculating Sharpe ratio incorrectly (needs returns series, not single value)
   - [ ] Not handling empty fills list (no trades today)
   - [ ] Complex nested calculations instead of simple formulas

**WHEN COMMITTING THIS COMPONENT, YOU MUST REPORT:**

```
Component 10 Complete - Pre-Commit Verification Report:

✅ Read morning_report_explainer.md - understood 16 scoring categories
✅ Read trading_strategy_explainer.md - understood performance metrics
✅ Read common-pitfalls.md - aware of all 7 critical pitfalls
✅ Verified database.get_todays_fills() exists (line X) OR actual method name
✅ Verified position_manager.get_all_positions() exists (line Y)
✅ Separates realized vs unrealized P&L
✅ Includes commission in all calculations
✅ Handles zero-trade edge case (no division by zero)
✅ Handles empty fills list gracefully
✅ Test scenario 1 passes (normal trading day)
✅ Test scenario 2 passes (no trades today)
✅ Test scenario 3 passes (all losses)
✅ Test scenario 4 passes (mixed wins/losses)
✅ Integration test passes
✅ No phantom references found

Commit: [hash]
Ready for user confirmation.
```

**If you cannot check ALL boxes above, DO NOT COMMIT. Ask user for guidance.**

---

### 🎯 Purpose

Calculate real-time performance metrics from trading activity for:
- Live monitoring (Railyard dashboard)
- EOD analysis (daily summary)
- Forecast accuracy validation
- Risk management decisions

**From morning_report_explainer.md, we need to track:**
- Win rate (Category #3: 8% weight)
- Expected Value (Category #4: 6% weight)
- Average Win % (Category #5: 3% weight)
- Risk/Reward Ratio (Category #6: 3% weight)
- And many more...

---

### 📊 Metrics to Calculate (CRITICAL - Study This)

**Basic Trading Metrics:**
```python
# From fills (realized trades)
total_trades = len(fills)
winning_trades = len([f for f in fills if f['realized_pnl'] > 0])
losing_trades = len([f for f in fills if f['realized_pnl'] < 0])
win_rate = winning_trades / total_trades  # Category #3

# P&L calculations
total_realized_pnl = sum(f['realized_pnl'] - f['commission'] for f in fills)
avg_win = average of winning trade P&Ls
avg_loss = average of losing trade P&Ls
expected_value = (win_rate × avg_win) - ((1 - win_rate) × avg_loss)  # Category #4

# Risk metrics
risk_reward_ratio = avg_win / abs(avg_loss)  # Category #6
```

**Position Metrics:**
```python
# From open positions (unrealized)
open_position_count = len(positions)
total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
```

**Time-Based Metrics:**
```python
# From fills
avg_hold_time = average of (exit_time - entry_time)
fastest_trade = min hold time
slowest_trade = max hold time
```

**Advanced Metrics (if data available):**
```python
# Sharpe ratio (needs daily returns series)
# Sortino ratio (needs downside deviation)
# Max drawdown
```

---

### 🚨 CRITICAL PITFALLS (Read Before Coding)

**From common-pitfalls.md and quantitative finance best practices:**

| ❌ WRONG | ✅ RIGHT |
|----------|----------|
| Mix realized & unrealized P&L | Separate: realized (closed), unrealized (open) |
| Ignore commission | Always subtract commission from P&L |
| wins / 0 if no trades | Check if total_trades > 0 first |
| Use float for money | Use Decimal or round to 2 places consistently |
| Sharpe = pnl / std | Sharpe = mean(returns) / std(returns) × sqrt(periods) |
| Crash on empty fills | Return zero/None gracefully |
| Nested complex logic | Simple formulas, one metric at a time |

**Reality Check Questions** (ask yourself these):
- ❓ Did I separate realized P&L (closed trades) from unrealized (open positions)?
- ❓ Did I subtract commission from every P&L calculation?
- ❓ Did I check for division by zero (no trades, no losses, etc.)?
- ❓ Does it handle the case where fills list is empty?
- ❓ Are all money values rounded to 2 decimal places?
- ❓ Did I test with a day that has zero trades?

---

### 📋 Step-by-Step Implementation

**STEP 1: Verify Dependencies (5 min)**

```bash
# Check database methods exist
grep "def get.*fill" backend/models/database.py
# Find the actual method name for getting today's fills

# Check position manager methods
grep "def get_all_positions" backend/core/position_manager.py
grep "def get_total_unrealized_pnl" backend/core/position_manager.py

# If ANY grep returns nothing → METHOD DOES NOT EXIST
# Read those files to find actual method names
```

**STEP 2: Create metrics_calculator.py (40 min)**

```python
"""
Metrics Calculator - Component 10

Calculates real-time performance metrics from trading activity.

Metrics include:
- Win rate, expected value, risk/reward ratio
- Realized P&L (closed trades)
- Unrealized P&L (open positions)
- Trade counts, hold times
- Advanced metrics (Sharpe, etc.) if data available

Author: The Luggage Room Boys Fund
Date: November 2025
"""

from typing import Dict, List, Optional
from datetime import datetime, date
from dataclasses import dataclass
import logging
import statistics

logger = logging.getLogger(__name__)


@dataclass
class TradingMetrics:
    """Container for calculated trading metrics."""
    
    # Date
    date: str
    
    # Trade counts
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # Win/Loss rates
    win_rate: float = 0.0
    loss_rate: float = 0.0
    
    # P&L (realized - from closed trades)
    total_realized_pnl: float = 0.0
    total_commission: float = 0.0
    net_realized_pnl: float = 0.0
    
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    # Risk metrics
    expected_value: float = 0.0
    risk_reward_ratio: float = 0.0
    
    # Position metrics (unrealized - from open positions)
    open_positions: int = 0
    total_unrealized_pnl: float = 0.0
    
    # Combined
    total_pnl: float = 0.0  # realized + unrealized
    
    # Time metrics
    avg_hold_time_seconds: float = 0.0
    avg_hold_time_minutes: float = 0.0
    
    # Advanced metrics (optional)
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown_pct: Optional[float] = None


class MetricsCalculator:
    """
    Calculates performance metrics from trading data.
    
    Usage:
        calculator = MetricsCalculator(database, position_manager)
        metrics = calculator.calculate_daily_metrics()
        
        print(f"Win Rate: {metrics.win_rate:.1%}")
        print(f"Total P&L: ${metrics.total_pnl:.2f}")
    """
    
    def __init__(self, database, position_manager):
        """
        Initialize metrics calculator.
        
        Args:
            database: TradingDatabase instance
            position_manager: PositionManager instance
        """
        self.db = database
        self.pm = position_manager
        
        logger.info("MetricsCalculator initialized")
    
    def calculate_daily_metrics(
        self,
        target_date: Optional[date] = None
    ) -> TradingMetrics:
        """
        Calculate all metrics for a trading day.
        
        Args:
            target_date: Date to calculate (uses today if None)
        
        Returns:
            TradingMetrics object with all calculated metrics
        """
        if target_date is None:
            target_date = date.today()
        
        # Get fills (closed trades)
        fills = self._get_fills_for_date(target_date)
        
        # Get open positions
        positions = self.pm.get_all_positions()
        
        # Calculate metrics
        metrics = TradingMetrics(date=target_date.isoformat())
        
        # Trade counts
        metrics.total_trades = len(fills)
        
        if metrics.total_trades == 0:
            # No trades today - return zeros
            logger.info(f"No trades on {target_date} - returning zero metrics")
            return metrics
        
        # Separate wins and losses
        wins = [f for f in fills if f.get('realized_pnl', 0) > 0]
        losses = [f for f in fills if f.get('realized_pnl', 0) < 0]
        
        metrics.winning_trades = len(wins)
        metrics.losing_trades = len(losses)
        
        # Win/Loss rates
        metrics.win_rate = metrics.winning_trades / metrics.total_trades
        metrics.loss_rate = metrics.losing_trades / metrics.total_trades
        
        # P&L calculations (REALIZED - from closed trades)
        metrics.total_commission = sum(f.get('commission', 0) for f in fills)
        
        gross_pnl = sum(f.get('realized_pnl', 0) for f in fills)
        metrics.total_realized_pnl = gross_pnl
        metrics.net_realized_pnl = gross_pnl - metrics.total_commission
        
        # Average win/loss (NET of commission)
        if wins:
            win_pnls = [f['realized_pnl'] - f.get('commission', 0) for f in wins]
            metrics.avg_win = statistics.mean(win_pnls)
            metrics.largest_win = max(win_pnls)
        
        if losses:
            loss_pnls = [f['realized_pnl'] - f.get('commission', 0) for f in losses]
            metrics.avg_loss = statistics.mean(loss_pnls)
            metrics.largest_loss = min(loss_pnls)  # Most negative
        
        # Expected Value (EV)
        if metrics.total_trades > 0:
            metrics.expected_value = (
                (metrics.win_rate * metrics.avg_win) -
                (metrics.loss_rate * abs(metrics.avg_loss))
            )
        
        # Risk/Reward Ratio
        if metrics.avg_loss != 0:
            metrics.risk_reward_ratio = metrics.avg_win / abs(metrics.avg_loss)
        
        # Position metrics (UNREALIZED - from open positions)
        metrics.open_positions = len(positions)
        metrics.total_unrealized_pnl = self.pm.get_total_unrealized_pnl()
        
        # Combined P&L
        metrics.total_pnl = metrics.net_realized_pnl + metrics.total_unrealized_pnl
        
        # Time metrics
        hold_times = self._calculate_hold_times(fills)
        if hold_times:
            metrics.avg_hold_time_seconds = statistics.mean(hold_times)
            metrics.avg_hold_time_minutes = metrics.avg_hold_time_seconds / 60
        
        return metrics
    
    def _get_fills_for_date(self, target_date: date) -> List[Dict]:
        """
        Get fills for a specific date from database.
        
        Args:
            target_date: Date to query
        
        Returns:
            List of fill dictionaries
        """
        try:
            # VERIFY THIS METHOD EXISTS IN database.py
            fills = self.db.get_todays_fills()  # or get_fills_by_date(target_date)
            
            # Filter to target date if method returns multiple days
            # (Adjust based on actual database method behavior)
            
            return fills if fills else []
            
        except Exception as e:
            logger.error(f"Error getting fills for {target_date}: {e}")
            return []
    
    def _calculate_hold_times(self, fills: List[Dict]) -> List[float]:
        """
        Calculate hold times in seconds for each fill.
        
        Args:
            fills: List of fill dictionaries
        
        Returns:
            List of hold times in seconds
        """
        hold_times = []
        
        for fill in fills:
            entry_time = fill.get('entry_time')
            exit_time = fill.get('exit_time')
            
            if entry_time and exit_time:
                # Parse timestamps if they're strings
                if isinstance(entry_time, str):
                    entry_time = datetime.fromisoformat(entry_time)
                if isinstance(exit_time, str):
                    exit_time = datetime.fromisoformat(exit_time)
                
                hold_time = (exit_time - entry_time).total_seconds()
                hold_times.append(hold_time)
        
        return hold_times
    
    def get_metrics_summary(self, metrics: TradingMetrics) -> str:
        """
        Get human-readable summary of metrics.
        
        Args:
            metrics: TradingMetrics object
        
        Returns:
            Formatted string summary
        """
        return f"""
Trading Metrics for {metrics.date}
{"="*50}
Trades: {metrics.total_trades} (W: {metrics.winning_trades}, L: {metrics.losing_trades})
Win Rate: {metrics.win_rate:.1%}
Expected Value: ${metrics.expected_value:.2f}
Risk/Reward: {metrics.risk_reward_ratio:.2f}

Realized P&L: ${metrics.net_realized_pnl:.2f}
Unrealized P&L: ${metrics.total_unrealized_pnl:.2f}
Total P&L: ${metrics.total_pnl:.2f}

Avg Win: ${metrics.avg_win:.2f}
Avg Loss: ${metrics.avg_loss:.2f}
Largest Win: ${metrics.largest_win:.2f}
Largest Loss: ${metrics.largest_loss:.2f}

Avg Hold Time: {metrics.avg_hold_time_minutes:.1f} min
Open Positions: {metrics.open_positions}
"""
```

**STEP 3: Test with 4 Scenarios (20 min)**

Create `tests/test_metrics_calculator.py`:

```python
# Test 1: Normal trading day (mix of wins and losses)
# Test 2: No trades today (edge case)
# Test 3: All losses (edge case)
# Test 4: All wins (edge case)

# Each test verifies:
# - No division by zero errors
# - Realized/unrealized separated correctly
# - Commission included in calculations
# - Metrics make mathematical sense
```

**STEP 4: Integration Test (10 min)**

```python
# Test with real Position Manager
# Test with real Database
# Test metric calculations match manual calculations
```

**STEP 5: Commit (5 min)**

```bash
git add backend/core/metrics_calculator.py
git add tests/test_metrics_calculator.py
git commit -m "Phase 0: Add metrics calculator for real-time performance tracking

- Calculate win rate, expected value, risk/reward ratio
- Separate realized P&L (closed) from unrealized (open)
- Include commission in all calculations
- Handle edge cases (zero trades, all wins/losses)
- Time-based metrics (avg hold time)
- Tested with 4 scenarios (normal/no-trades/all-loss/all-win)"
git push origin main
```

---

### ✅ Success Criteria (All Must Pass)

- [ ] Read morning_report_explainer.md (verified 16 categories)
- [ ] Read trading_strategy_explainer.md (verified)
- [ ] Verified database fill methods exist (line numbers)
- [ ] Verified position_manager methods exist (line numbers)
- [ ] Separates realized vs unrealized P&L correctly
- [ ] Includes commission in all P&L calculations
- [ ] Handles zero trades gracefully (no division by zero)
- [ ] Handles all-wins edge case (no losses to divide)
- [ ] Handles all-losses edge case (no wins to divide)
- [ ] Test 1 passes (normal trading day)
- [ ] Test 2 passes (no trades)
- [ ] Test 3 passes (all losses)
- [ ] Test 4 passes (all wins)
- [ ] Win rate calculation correct (wins/total)
- [ ] Expected value calculation correct (formula verified)
- [ ] Risk/reward ratio calculation correct (avg_win/avg_loss)
- [ ] No phantom references (all methods verified)
- [ ] Integration test passes
- [ ] Commit pushed to GitHub
- [ ] User confirmed commit visible in GitHub Desktop

---

### 🔍 Verification Steps (Do After Coding)

```bash
# 1. Check file exists
ls -la backend/core/metrics_calculator.py

# 2. Check for phantom references
python3 -c "
import sys
sys.path.append('.')
from backend.core.metrics_calculator import MetricsCalculator
print('✅ No import errors')
"

# 3. Run tests
python3 tests/test_metrics_calculator.py

# 4. Test edge case manually
python3 -c "
from backend.core.metrics_calculator import TradingMetrics
m = TradingMetrics(date='2025-11-01')
print('Zero trades:', m.win_rate)  # Should be 0.0, not error
"

# 5. Check commit
git log -1 --oneline
```

---


## Components 11-19: TODO

*(To be detailed in subsequent updates)*
