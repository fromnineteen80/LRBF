# LRBF Complete Data Pipeline

This document explains the entire data flow from morning analysis through live trading to end-of-day reporting.

## Pipeline Overview

```
5:45 AM                    9:31 AM - 4:00 PM               4:00 PM
   ↓                              ↓                           ↓
Morning Report  ══════════▶  Railyard Trading  ══════════▶  EOD Analysis
   │                              │                           │
   │ • Scan 500 stocks           │ • Monitor patterns         │ • Load forecast
   │ • Detect patterns            │ • Execute trades           │ • Fetch fills
   │ • Score & rank               │ • Track P&L                │ • Calculate metrics
   │ • Generate 7 forecasts       │ • Compare vs forecast      │ • Store summary
   │ • Select 8/12/16/20 stocks   │ • Auto-pause if -1.5%      │ • Generate charts
   ↓                              ↓                           ↓
Store morning_forecasts      Store fills table          Store daily_summaries
```

## Phase 1: Morning Report (5:45 AM)

### Step 1.1: Stock Universe Scan

**Source:** IBKR Market Scanner API

**Process:**
```python
from backend.data.stock_universe import get_stock_universe

# Load curated list or scan top stocks
stocks = get_stock_universe()  # Returns ~500 tickers

# Criteria:
# - Volume > 5M shares/day
# - Price > $5
# - Primary exchanges only (NYSE, NASDAQ)
# - Exclude OTC, pink sheets
```

**Output:** List of 500 stock tickers

**Database:** None (in-memory)

---

### Step 1.2: Market Data Fetch

**Source:** IBKR Historical Data API via ib_insync

**Process:**
```python
from backend.data.ibkr_data_provider import IBKRDataProvider

provider = IBKRDataProvider()

for ticker in stocks:
    # Fetch 20 days of intraday data
    df = provider.fetch_intraminute_data(
        ticker=ticker,
        days=20,
        bar_size='5 secs'  # Or '1 min'
    )
    
    # Data includes:
    # - timestamp
    # - open, high, low, close
    # - volume
    # - VWAP (calculated)
    # - bid_ask_spread
```

**Volume:** 234 million data points
- 500 stocks × 20 days × 390 minutes × 60 ticks ≈ 234M points

**Output:** DataFrame per stock with OHLCV + VWAP

**Database:** None (processed in-memory for speed)

---

### Step 1.3: News Screening

**Source:** News API (configured in backend/data/news_providers.py)

**Process:**
```python
from backend.core.news_monitor import NewsMonitor

monitor = NewsMonitor()

excluded_stocks = []
for ticker in stocks:
    # Check for material news in last 24 hours
    has_news = monitor.check_material_news(
        ticker=ticker,
        lookback_hours=24,
        news_types=['earnings', 'fda', 'halts', 'lawsuits', 'exec_changes']
    )
    
    if has_news:
        excluded_stocks.append({
            'ticker': ticker,
            'reason': has_news['type'],
            'headline': has_news['headline']
        })
```

**Output:** List of excluded stocks with reasons (20-50 stocks typically)

**Database:** Stored in morning_forecasts.news_screening_json

---

### Step 1.4: Pattern Detection

**Source:** backend/core/pattern_detector.py + vwap_breakout_detector.py

**Process:**
```python
from backend.core.pattern_detector import PatternDetector
from backend.core.vwap_breakout_detector import VWAPBreakoutDetector

detector = PatternDetector()
vwap_detector = VWAPBreakoutDetector()

for ticker in stocks:
    if ticker not in excluded_stocks:
        # 3-Step VWAP Recovery Pattern
        three_step_patterns = detector.detect_patterns(
            df=stock_data[ticker],
            config=config
        )
        
        # VWAP Breakout Pattern
        vwap_patterns = vwap_detector.detect_breakouts(
            df=stock_data[ticker],
            config=config
        )
        
        # Each pattern includes:
        # - Timestamps (millisecond precision)
        # - Price levels (high, low, entry, exit)
        # - Entry confirmation (did it climb +0.5%?)
        # - Trade outcome (win/loss, P&L %, hold time)
        # - Exit reason (T1, CROSS, T2, dead zone, stop loss)
```

**Detected:**
- 3-Step patterns: ~15-30 per stock × 500 stocks = 7,500-15,000 patterns
- VWAP Breakout patterns: ~8-15 per stock × 500 stocks = 4,000-7,500 patterns

**Output:** Array of pattern objects per stock

**Database:** None (used for scoring only)

---

### Step 1.5: Quality Scoring

**Source:** backend/core/category_scorer.py

**Process:**
```python
from backend.core.category_scorer import CategoryScorer

scorer = CategoryScorer()

for ticker in stocks:
    scores = scorer.score_stock(
        ticker=ticker,
        patterns=patterns[ticker],
        market_data=stock_data[ticker],
        config=config
    )
    
    # Calculates 16 category scores:
    # 1. Pattern Frequency (20% weight)
    # 2. Confirmation Rate (10% weight)
    # 3. Win Rate (8% weight)
    # 4. Expected Value (6% weight)
    # 5. Avg Win % (3% weight)
    # 6. Risk/Reward Ratio (3% weight)
    # 7. Liquidity Score (6% weight)
    # 8. Volatility Score (8% weight)
    # 9. Spread Quality (5% weight)
    # 10. VWAP Stability (8% weight)
    # 11. Trend Alignment (3% weight)
    # 12. Dead Zone Risk (5% weight)
    # 13. Halt Risk (5% weight)
    # 14. Execution Efficiency (5% weight)
    # 15. Backtest Consistency (3% weight)
    # 16. Composite Rank (2% weight)
    
    stock_scores[ticker] = {
        'scores': scores,
        'composite': weighted_average(scores),
        'category': classify_risk(scores)  # Conservative/Medium/Aggressive
    }
```

**Output:** Composite score (0-100) and risk category per stock

**Database:** None (used for ranking)

---

### Step 1.6: Stock Ranking & Selection

**Source:** backend/core/stock_ranker.py + stock_selector.py

**Process:**
```python
from backend.core.stock_ranker import StockRanker
from backend.core.stock_selector import StockSelector

ranker = StockRanker()
selector = StockSelector()

# Rank all stocks by composite score
ranked_stocks = ranker.rank(stock_scores)

# Select balanced portfolio (2 conservative, 4 medium, 2 aggressive)
selected = selector.select_portfolio(
    ranked_stocks=ranked_stocks,
    num_stocks=8,  # Or 12, 16, 20
    balance_ratio=(2, 4, 2)
)
```

**Output:** 
- Top N stocks (8/12/16/20)
- Backup stocks (N+4 for replacements)
- Risk distribution maintained

**Database:** Stored in morning_forecasts.selected_stocks_json

---

### Step 1.7: Generate 7 Forecasts

**Source:** backend/core/seven_forecast_generator.py

**Process:**
```python
from backend.core.seven_forecast_generator import SevenForecastGenerator

generator = SevenForecastGenerator()

forecasts = generator.generate_all_forecasts(
    ranked_stocks=ranked_stocks,
    account_balance=account_balance,
    config=config
)

# Generates 7 scenarios:
# 1. Default (3-Step, no filters)
# 2. Conservative (3-Step, all filters tight)
# 3. Aggressive (3-Step, minimal filters)
# 4. Choppy Market (3-Step, S/R focused)
# 5. Trending Market (3-Step, momentum focused)
# 6. AB Test (3-Step, experimental)
# 7. VWAP Breakout (different pattern)

# Each forecast includes:
# - Selected stocks (8/12/16/20)
# - Backup stocks (N+4)
# - Expected trades (low, high range)
# - Expected P&L (low, high range)
# - Win rate estimate
# - Risk metrics (Sharpe, Sortino, Calmar)
# - Dead zone probability
# - Filter configuration
```

**Output:** Array of 7 forecast objects

**Database:** Stored in morning_forecasts.all_forecasts_json

---

### Step 1.8: Time Profile Analysis

**Source:** backend/core/time_profile_analyzer.py

**Process:**
```python
from backend.core.time_profile_analyzer import TimeProfileAnalyzer

analyzer = TimeProfileAnalyzer()

for ticker in selected_stocks:
    profile = analyzer.analyze_timeouts(
        ticker=ticker,
        patterns=patterns[ticker],
        dead_zone_history=dead_zones[ticker]
    )
    
    # Calculates adaptive timeouts:
    # - Below T1: 3 min
    # - At T1: 4 min
    # - At CROSS: 4 min
    # - After momentum: 6 min
    
    # Based on stock's historical dead zone behavior
    time_profiles[ticker] = profile
```

**Output:** Adaptive timeout settings per stock

**Database:** Stored in morning_forecasts.time_profiles_json

---

### Step 1.9: Store Morning Forecast

**Source:** backend/models/database.py

**Process:**
```python
from backend.models.database import store_morning_forecast

forecast_data = {
    'date': today,
    'generated_at': datetime.now(),
    'selected_stocks_json': json.dumps(selected_stocks),
    'all_forecasts_json': json.dumps(forecasts),
    'time_profiles_json': json.dumps(time_profiles),
    'news_screening_json': json.dumps(excluded_stocks),
    'expected_trades_low': forecasts[selected_preset]['trades_low'],
    'expected_trades_high': forecasts[selected_preset]['trades_high'],
    'expected_pl_low': forecasts[selected_preset]['pl_low'],
    'expected_pl_high': forecasts[selected_preset]['pl_high'],
    'active_preset': selected_preset
}

store_morning_forecast(forecast_data)
```

**Database:** morning_forecasts table
```sql
INSERT INTO morning_forecasts (
    date, generated_at, selected_stocks_json, all_forecasts_json,
    time_profiles_json, news_screening_json, expected_trades_low,
    expected_trades_high, expected_pl_low, expected_pl_high, active_preset
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

**Output:** Database record with ID

---

## Phase 2: Railyard Trading (9:31 AM - 4:00 PM)

### Step 2.1: Load Morning Forecast

**Source:** backend/models/database.py

**Process:**
```python
from backend.models.database import get_todays_forecast

forecast = get_todays_forecast()

selected_stocks = json.loads(forecast['selected_stocks_json'])
time_profiles = json.loads(forecast['time_profiles_json'])
active_preset = forecast['active_preset']
```

**Database:** Query morning_forecasts table

---

### Step 2.2: Initialize IBKR Connection

**Source:** backend/data/ibkr_connector_insync.py

**Process:**
```python
from backend.data.ibkr_connector_insync import IBKRConnectorInsync

connector = IBKRConnectorInsync()
connector.connect(
    host='localhost',
    port=4002,  # Paper trading
    client_id=1
)

# Get account balance
balance = connector.get_account_balance()

# Calculate position sizes
deployed_capital = balance * config.DEPLOYMENT_RATIO
position_size = deployed_capital / len(selected_stocks)
```

**Connection:** IB Gateway on localhost:4002

---

### Step 2.3: Monitor Real-Time Patterns

**Source:** backend/core/railyard.py (NEEDS OVERHAUL)

**Process:**
```python
from backend.core.railyard import Railyard

railyard = Railyard(
    stocks=selected_stocks,
    connector=connector,
    config=config,
    time_profiles=time_profiles
)

# For each stock, monitor tick-by-tick:
for ticker in selected_stocks:
    # Stream real-time tick data
    ticks = connector.stream_ticks(ticker)
    
    # Check for pattern completion
    pattern_complete = detector.check_pattern(
        recent_ticks=ticks,
        pattern_type=active_preset
    )
    
    if pattern_complete:
        # Wait for entry confirmation (+0.5% from pattern low)
        entry_confirmed = wait_for_entry_signal(
            ticks=ticks,
            pattern_low=pattern['low'],
            threshold=0.5,  # 0.5%
            timeout=3 * 60  # 3 minutes
        )
        
        if entry_confirmed:
            # EXECUTE BUY
            order = connector.place_market_order(
                ticker=ticker,
                action='BUY',
                quantity=position_size / current_price
            )
```

**Output:** Orders executed in IBKR account

---

### Step 2.4: Apply Exit Logic

**Source:** backend/core/railyard.py (NEEDS OVERHAUL)

**Process:**
```python
# After entering position:
position = {
    'ticker': ticker,
    'entry_price': entry_price,
    'entry_time': entry_time,
    'quantity': quantity,
    'status': 'active'
}

# Monitor tick-by-tick for exit signals:
while position['status'] == 'active':
    current_price = get_current_price(ticker)
    pl_pct = (current_price - entry_price) / entry_price * 100
    
    # Tiered Exit Logic:
    if pl_pct >= 0.75 and 'T1' not in position:
        position['T1_locked'] = True  # Lock in T1 (+0.75%)
        
    if pl_pct >= 1.00 and 'CROSS' not in position:
        position['CROSS_locked'] = True  # Lock in CROSS (+1.00%)
        
    if pl_pct >= 1.25 and position.get('CROSS_locked'):
        position['momentum_confirmed'] = True  # Going for T2
        
    if pl_pct >= 1.75 and position.get('momentum_confirmed'):
        # EXIT at T2 (+1.75%)
        exit_position(position, reason='T2', exit_price=current_price)
        break
        
    # Check if fell below locked floor:
    if position.get('momentum_confirmed') and pl_pct < 1.00:
        # EXIT at CROSS (fell from momentum pursuit)
        exit_position(position, reason='CROSS_FLOOR', exit_price=current_price)
        break
        
    if position.get('CROSS_locked') and not position.get('momentum_confirmed') and pl_pct < 0.75:
        # EXIT at T1 (CROSS didn't reach momentum)
        exit_position(position, reason='T1_FLOOR', exit_price=current_price)
        break
        
    # Dead Zone Detection:
    time_in_position = time.time() - position['entry_time']
    if time_in_position > get_timeout_for_pl(ticker, pl_pct, time_profiles):
        # EXIT at best available (dead zone timeout)
        exit_position(position, reason='DEAD_ZONE', exit_price=current_price)
        break
        
    # Stop Loss:
    if pl_pct <= -0.5:
        # EXIT at stop loss (-0.5%)
        exit_position(position, reason='STOP_LOSS', exit_price=current_price)
        break
```

**Output:** Exit orders executed, fills recorded

---

### Step 2.5: Store Fills

**Source:** backend/models/database.py

**Process:**
```python
from backend.models.database import store_fill

# After each execution (entry or exit):
fill_data = {
    'ibkr_execution_id': order.execution_id,
    'date': today,
    'timestamp': execution_time,
    'ticker': ticker,
    'action': 'BUY' or 'SELL',
    'quantity': quantity,
    'price': execution_price,
    'realized_pnl': realized_pnl,  # For SELLs only
    'commission': commission,
    'latency_ms': latency,
    'slippage_pct': slippage
}

store_fill(fill_data)
```

**Database:** fills table
```sql
INSERT INTO fills (
    ibkr_execution_id, date, timestamp, ticker, action,
    quantity, price, realized_pnl, commission, latency_ms, slippage_pct
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

---

### Step 2.6: Track vs Forecast

**Source:** backend/reports/live_monitor.py

**Process:**
```python
from backend.reports.live_monitor import LiveMonitor

monitor = LiveMonitor()

while market_open:
    # Get current state
    live_data = monitor.get_live_data(
        date=today,
        config=config
    )
    
    # Compare actual vs forecast:
    comparison = {
        'expected_trades': forecast['expected_trades_low', 'expected_trades_high'],
        'actual_trades': len(fills),
        'expected_pl': forecast['expected_pl_low', 'expected_pl_high'],
        'actual_pl': sum(fill['realized_pnl'] for fill in fills),
        'win_rate': calculate_win_rate(fills),
        'positions': get_active_positions()
    }
    
    # Check daily loss limit:
    if comparison['actual_pl'] <= -balance * 0.015:  # -1.5%
        auto_pause_trading()
```

**Output:** Real-time monitoring data

**Database:** None (live data only)

**API Endpoint:** /api/railyard-data

---

## Phase 3: EOD Analysis (4:00 PM)

### Step 3.1: Load Forecast & Fills

**Source:** backend/models/database.py

**Process:**
```python
from backend.models.database import get_todays_forecast, get_todays_fills

forecast = get_todays_forecast()
fills = get_todays_fills()

# Filter fills to selected stocks only
selected_stocks = json.loads(forecast['selected_stocks_json'])
relevant_fills = [f for f in fills if f['ticker'] in selected_stocks]
```

**Database:** Query morning_forecasts + fills tables

---

### Step 3.2: Calculate Metrics

**Source:** backend/core/metrics_calculator.py

**Process:**
```python
from backend.core.metrics_calculator import MetricsCalculator

calculator = MetricsCalculator()

metrics = calculator.calculate_all_metrics(
    fills=relevant_fills,
    opening_balance=opening_balance,
    closing_balance=closing_balance
)

# Metrics include:
# - Win rate, loss rate
# - Average win %, average loss %
# - Sharpe ratio
# - Sortino ratio
# - Calmar ratio
# - Max drawdown %
# - Average latency ms
# - Average slippage %
```

**Output:** Dictionary of calculated metrics

---

### Step 3.3: Per-Stock Breakdown

**Source:** backend/reports/eod_reporter.py

**Process:**
```python
from backend.reports.eod_reporter import EODReporter

reporter = EODReporter()

stock_breakdown = []
for ticker in selected_stocks:
    ticker_fills = [f for f in relevant_fills if f['ticker'] == ticker]
    
    breakdown = {
        'ticker': ticker,
        'trade_count': len([f for f in ticker_fills if f['action'] == 'SELL']),
        'realized_pl': sum(f['realized_pnl'] for f in ticker_fills if f['action'] == 'SELL'),
        'win_rate': calculate_win_rate(ticker_fills),
        'avg_win': calculate_avg_win(ticker_fills),
        'avg_loss': calculate_avg_loss(ticker_fills)
    }
    
    stock_breakdown.append(breakdown)
```

**Output:** Per-stock performance array

---

### Step 3.4: Forecast Accuracy

**Source:** backend/reports/eod_reporter.py

**Process:**
```python
# Compare actual vs forecast:
accuracy = {
    'trade_count_forecast': [forecast['expected_trades_low'], forecast['expected_trades_high']],
    'trade_count_actual': len([f for f in relevant_fills if f['action'] == 'SELL']),
    'trade_count_accuracy': calculate_accuracy(expected, actual),
    
    'pl_forecast': [forecast['expected_pl_low'], forecast['expected_pl_high']],
    'pl_actual': sum(f['realized_pnl'] for f in relevant_fills if f['action'] == 'SELL'),
    'pl_accuracy': calculate_accuracy(expected, actual)
}
```

**Output:** Forecast vs actual comparison

---

### Step 3.5: Store Daily Summary

**Source:** backend/models/database.py

**Process:**
```python
from backend.models.database import store_daily_summary

summary_data = {
    'date': today,
    'opening_balance': opening_balance,
    'closing_balance': closing_balance,
    'realized_pl': total_realized_pl,
    'roi_pct': (closing_balance - opening_balance) / opening_balance * 100,
    'trade_count': total_trades,
    'win_count': win_count,
    'loss_count': loss_count,
    'win_rate': win_rate,
    'sharpe_ratio': metrics['sharpe'],
    'sortino_ratio': metrics['sortino'],
    'max_drawdown_pct': metrics['max_drawdown'],
    'avg_latency_ms': metrics['avg_latency'],
    'avg_slippage_pct': metrics['avg_slippage'],
    'stock_performance_json': json.dumps(stock_breakdown)
}

store_daily_summary(summary_data)
```

**Database:** daily_summaries table
```sql
INSERT INTO daily_summaries (
    date, opening_balance, closing_balance, realized_pl, roi_pct,
    trade_count, win_count, loss_count, win_rate, sharpe_ratio,
    sortino_ratio, max_drawdown_pct, avg_latency_ms, avg_slippage_pct,
    stock_performance_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

---

### Step 3.6: Generate Charts

**Source:** frontend (Chart.js in eod.html)

**Process:**
```javascript
// Equity Curve Chart
fetch('/api/equity-curve')
  .then(r => r.json())
  .then(data => {
    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.dates,
        datasets: [{
          label: 'Account Balance',
          data: data.balances
        }]
      }
    });
  });

// Win Rate Chart
// Stock Breakdown Pie Chart
// Risk Metrics Gauges
```

**Output:** Charts rendered in browser

---

## Critical Data Flow Points

### Database Schema Dependencies

```
morning_forecasts (PRIMARY)
    ↓ (provides selected stocks)
fills (FILTERED by selected_stocks_json)
    ↓ (provides actual trades)
daily_summaries (AGGREGATED from fills)
```

**CRITICAL:** Fills must be filtered to selected stocks only, not all stocks traded.

### API Endpoint Data Flow

```
/api/morning-data
    ↓ Reads: morning_forecasts
    ↓ Returns: selected_stocks, all_forecasts, time_profiles

/api/railyard-data
    ↓ Reads: morning_forecasts, fills
    ↓ Filters: fills to selected stocks only
    ↓ Returns: positions, fills, metrics, forecast_comparison

/api/eod-data
    ↓ Reads: morning_forecasts, fills, daily_summaries
    ↓ Filters: fills to selected stocks only
    ↓ Returns: summary, forecast_accuracy, stock_breakdown, risk_metrics
```

### IBKR Data Flow

```
IB Gateway (localhost:4002)
    ↓ via ib_insync library
backend/data/ibkr_connector_insync.py
    ↓ provides methods
backend/core/railyard.py
    ↓ executes trades
backend/models/database.py (fills table)
```

## Data Validation Checklist

Before marking pipeline complete:

### Morning Report
- [ ] 500 stocks scanned
- [ ] 20-day data fetched for each
- [ ] News screening excludes material events
- [ ] 7 forecasts generated
- [ ] Selected stocks stored (8/12/16/20)
- [ ] Time profiles calculated
- [ ] Stored in morning_forecasts table

### Railyard
- [ ] Forecast loaded from database
- [ ] IBKR connection established
- [ ] Real-time tick streaming works
- [ ] Pattern detection functional
- [ ] Entry confirmation (+0.5%) works
- [ ] Tiered exit logic (T1/CROSS/momentum/T2) works
- [ ] Dead zone timeout adaptive
- [ ] Stop loss triggers (-0.5%)
- [ ] Daily loss limit auto-pauses (-1.5%)
- [ ] Fills stored after each execution
- [ ] Fills filtered to selected stocks only

### EOD Analysis
- [ ] Forecast loaded from database
- [ ] Fills loaded and filtered correctly
- [ ] Metrics calculated (Sharpe, Sortino, etc.)
- [ ] Per-stock breakdown generated
- [ ] Forecast accuracy measured
- [ ] Summary stored in daily_summaries table
- [ ] Charts render correctly

## End of Data Pipeline

For other topics:
- Development workflow → `references/development-workflow.md`
- Common pitfalls → `references/common-pitfalls.md`
- Integration testing → `references/integration-testing.md`
- Phase execution → `references/phase-execution.md`
