# Simulation Mode - Using Last Trading Day's Data

## Overview

Simulation Mode allows you to test the entire trading workflow (Morning → Live → EOD) using **real historical data from the last completed trading day**. This is perfect for:

- 🌙 **After-hours testing** (after 4:00 PM ET)
- 🎡 **Weekend testing** (Saturday/Sunday)
- 🎉 **Holiday testing** (market closed days)
- 🧪 **Strategy validation** without risking live trades

## How It Works

### 1. **Intelligent Date Detection**

The system automatically finds the last **completed** trading day:

```python
# Example scenarios:
Today: Saturday, Oct 14        → Last Trading Day: Friday, Oct 11
Today: Monday, Oct 16, 10 AM   → Last Trading Day: Friday, Oct 11 (Monday incomplete)
Today: Monday, Oct 16, 5 PM    → Last Trading Day: Monday, Oct 16 (now complete)
Today: Tuesday, Oct 15, 2 PM   → Last Trading Day: Monday, Oct 14 (Tuesday incomplete)
```

### 2. **Real Data, Full Workflow**

**Morning Report:**
- Analyzes 20 trading days **before** the last trading day
- Uses real 1-minute bars from yfinance
- Selects 8 stocks based on actual pattern detection
- Generates forecast using real win rates and P&L

**Live Monitor:**
- Replays the last trading day's actual price action
- Shows real fills, real P&L, real win rates
- Can speed up (10x) or slow down (0.1x) playback

**EOD Report:**
- Shows actual results from that historical day
- Real Sharpe ratio, Sortino ratio, max drawdown
- Actual comparison to forecast

### 3. **Toggle in Settings**

Navigate to **Settings** → **Trading Mode**:

**Option 1: Live Trading** 🔴
- Uses current market data
- Requires market hours (9:31 AM - 4:00 PM ET)
- Real-time execution

**Option 2: Simulation Mode** 🔵
- Uses last trading day's data
- Works anytime (24/7)
- Safe testing environment

## Technical Implementation

### Config Variables

```python
# modules/config.py
USE_SIMULATION = False              # Master toggle (False = production ready)
SIMULATION_MODE = "last_trading_day"  # Use real historical data
SIMULATION_STARTING_BALANCE = 30000.0
SIMULATION_SPEED = 1.0              # Playback speed (1.0 = real-time)
```

### User Preference Storage

```python
# Stored in session (per user)
session['trading_mode'] = 'live'  # or 'simulation'
```

### API Endpoints

**GET `/api/settings/trading-mode`**
- Returns current mode and simulation status
```json
{
  "mode": "simulation",
  "simulation_status": {
    "last_trading_day": "2025-10-14",
    "market_currently_open": false,
    "simulation_analysis_start": "2025-09-16",
    "simulation_analysis_end": "2025-10-13",
    "reason": "Market closed"
  }
}
```

**POST `/api/settings/trading-mode`**
- Sets trading mode preference
```json
{
  "mode": "simulation"  // or "live"
}
```

**GET `/api/settings/simulation-status`**
- Gets current simulation date information

### Simulation Helper Module

`modules/simulation_helper.py` provides:

```python
from modules.simulation_helper import (
    get_last_trading_day,       # Find last completed trading day
    get_simulation_date_range,   # Get 20-day analysis window
    is_market_open,              # Check if market is currently open
    get_simulation_status,       # Get full status info
    should_use_simulation        # Auto-detect if simulation needed
)

# Example usage:
last_day = get_last_trading_day()
# Returns: date(2025, 10, 14)

start, end = get_simulation_date_range(last_day, analysis_days=20)
# Returns: (date(2025, 9, 16), date(2025, 10, 13))
```

## Data Flow

### When Simulation Mode is ACTIVE:

```
1. User opens Morning Report page
   ↓
2. Frontend calls /api/morning/generate
   ↓
3. Backend checks session['trading_mode'] → 'simulation'
   ↓
4. simulation_helper.get_last_trading_day() → October 14, 2025
   ↓
5. Download data for Sept 16 - Oct 13 (20 days before)
   ↓
6. Run pattern detection on real historical data
   ↓
7. Select 8 stocks based on actual patterns found
   ↓
8. Generate forecast using real win rates
   ↓
9. User sees: "Simulation Mode - Using data from Oct 14, 2025"
```

### When Live Mode is ACTIVE:

```
1. User opens Morning Report page
   ↓
2. Frontend calls /api/morning/generate
   ↓
3. Backend checks session['trading_mode'] → 'live'
   ↓
4. Download data for TODAY minus 20 days
   ↓
5. Run pattern detection on current data
   ↓
6. Select 8 stocks for TODAY's trading
   ↓
7. Generate forecast for TODAY
   ↓
8. User sees: "Live Mode - Today's trading day"
```

## Benefits

### ✅ For Development & Testing:
- Test anytime without waiting for market hours
- Validate full workflow with realistic data
- Demo the system to potential investors
- Practice with known outcomes (hindsight)

### ✅ For Production:
- Analyze historical performance
- Backtest strategy changes
- Compare different time periods
- Understand pattern frequency over time

## Example Scenarios

### Scenario 1: Weekend Demo

**Situation:** It's Saturday, you want to show the system to a co-founder

**Steps:**
1. Open Settings → Select "Simulation Mode"
2. System automatically uses Friday's data
3. Run Morning Report → See real stocks selected
4. View Live Monitor → See Friday's replay
5. Check EOD Report → See Friday's actual results

**Result:** Full demo with real data, no fake synthetic numbers!

### Scenario 2: After-Hours Analysis

**Situation:** It's 8 PM ET, market closed, you want to review today

**Steps:**
1. Open Settings → Select "Simulation Mode"
2. System uses today's data (now complete)
3. Morning Report shows what was selected
4. Live Monitor shows actual intraday performance
5. EOD Report shows final results

**Result:** Review today's trading with actual data!

### Scenario 3: Strategy Testing

**Situation:** You want to test a new entry threshold (1.5% vs 2.0%)

**Steps:**
1. Enable Simulation Mode
2. Adjust entry_threshold in Settings
3. Run Morning Report with new threshold
4. Compare results to baseline
5. Iterate and optimize

**Result:** Safe testing without risking capital!

## UI Indicators

When Simulation Mode is active, all pages show:

```
🔵 SIMULATION MODE
Using data from: Friday, October 11, 2025
Analysis period: Sept 1 - Oct 10, 2025
```

When Live Mode is active:

```
🔴 LIVE TRADING
Current session: Monday, October 14, 2025
Market hours: 9:31 AM - 4:00 PM ET
```

## Roadmap Enhancements

### Phase 1 (Current):
- ✅ Toggle between Live and Simulation
- ✅ Use last trading day's real data
- ✅ Full workflow simulation

### Phase 2 (Future):
- ⏭️ Select any historical date for simulation
- ⏭️ Speed controls (1x, 10x, 100x playback)
- ⏭️ Compare multiple historical days side-by-side
- ⏭️ Holiday calendar integration (detect market closures)

### Phase 3 (Advanced):
- ⏭️ Range simulation (test over multiple days)
- ⏭️ Monte Carlo simulation (random historical samples)
- ⏭️ Walk-forward optimization
- ⏭️ Export simulation results to CSV

## Testing

### Manual Test:

1. Open http://localhost:5000/settings
2. Select "Simulation Mode"
3. Click "Save Trading Mode"
4. Navigate to Morning Report
5. Generate report
6. Should see: "Last Trading Day: [date]"

### API Test:

```bash
# Get current mode
curl -X GET http://localhost:5000/api/settings/trading-mode \
  -H "Cookie: session=..."

# Set simulation mode
curl -X POST http://localhost:5000/api/settings/trading-mode \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"mode": "simulation"}'

# Get simulation status
curl -X GET http://localhost:5000/api/settings/simulation-status \
  -H "Cookie: session=..."
```

## Summary

Simulation Mode transforms your trading platform into a **time machine**:
- 🕐 Test any time (24/7)
- 📊 Real historical data (not fake)
- ✅ Full workflow validation
- 🔄 Repeatable testing
- 📈 Safe experimentation

**Perfect for development, testing, demos, and strategy optimization!** 🚀
