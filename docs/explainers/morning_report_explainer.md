Morning Report: Pattern Detection & Delivery
Overview
The LRBFund Morning Report scans 500 stocks, detects patterns in 20 days of historical data, scores them across 16 categories, and generates 7 different forecasts. In under two minutes, our Morning Report python crunches +230 million points of data and ranks 24 optimized stocks at 5:45 AM. 

The report delivers this optimized list to the user with several choices to make before markets open for the day, including one of two trading strategies for the day and a number of variable options. 

As we move through the first few months of trading, we will include the ability to execute both strategies or mix strategies for high probability stocks on our optimized daily list. 
Step-by-Step Process
1. Universe Selection (5:45:00 AM)
What happens:
System calls IBKR Market Scanner API
Requests top 500 stocks by average daily volume
Filters: Volume > 5M shares/day, Price > $5, Primary exchanges only

Output: 500 tickers (dynamic, changes daily based on volume)

Why dynamic?
Yesterday's liquid stocks may not be today's
Captures emerging movers
Avoids stale lists
2. Market Data Fetch (5:45:15 AM)
What happens:
For each of 500 stocks, fetch last 20 days of tick data from IBKR
20 days × 390 minutes/day × 60 ticks/min = ~468,000 ticks per stock
Total: 234 million data points

Data includes:
Price (bid, ask, last)
Volume per tick
VWAP (calculated on-the-fly)
Spread (bid-ask)
Timestamps (millisecond precision)

Optimization:
Parallel processing (8 cores)
Uses IBKR's native binary protocol (ib_insync)
Compressed tick aggregation (5-second micro-bars for pattern scanning)

Output: 500 DataFrames with OHLCV + VWAP + Spread
3. News Screening (5:45:45 AM)
What happens:
Check each stock for news in last 24 hours
Filters: Earnings, FDA, halts, lawsuits, executive changes
Excludes any stock with fresh material news

Why?
Patterns break during news events
News creates unpredictable volatility
Conservative risk management

Output: ~450-480 stocks (20-50 excluded for news)

4. Pattern Detection (5:46:00 AM) - THE CORE
For each stock, detect TWO pattern types:
Pattern Type 1: 3-Step Geometric Reversal
Algorithm (per stock, per day):

For each 5-second micro-bar in the day:
  
  STEP 1: Scan for DECLINE
    - Look back 3 minutes
    - Find recent high
    - Check if price dropped ≥1.0% from that high
    - If yes → DECLINE DETECTED
  
  STEP 2: Scan for 50% RECOVERY
    - After decline, look forward up to 2 minutes
    - Target = decline_low + (50% × decline_amount)
    - Check if price climbs to target
    - If yes → RECOVERY DETECTED
  
  STEP 3: Scan for 50% RETRACEMENT
    - After recovery, look forward up to 2 minutes
    - Target = recovery_high - (50% × recovery_amount)
    - Check if price drops to target
    - If yes → PATTERN COMPLETE
  
  STEP 4: Check for ENTRY CONFIRMATION
    - After pattern complete, look forward up to 3 minutes
    - Check if price climbs +0.5% from pattern low
    - If yes → ENTRY CONFIRMED
  
  STEP 5: SIMULATE TRADE
    - Entry price = pattern_low + 0.5%
    - Track price tick-by-tick
    - Apply exit logic (T1, CROSS, momentum, T2, dead zone, stop loss)
    - Record: Win/Loss, P&L %, hold time, exit reason
  
  STEP 6: Apply FILTERS (if enhanced strategy)
    - VWAP proximity: Entry price within ±3% of VWAP?
    - Volume: Current volume ≥ 2x average?
    - Time-of-day: Not first or last hour?
    - Support/Resistance: Near pivot level?
    - Trend: Aligned with 20/50/200 MAs?
    - If ANY filter fails → Mark as "filtered_out"
  
  Record pattern with ALL metadata:
    - Timestamps (millisecond precision)
    - Price levels (high, decline_low, recovery_high, pattern_low, entry, exit)
    - Outcome (win/loss/filtered)
    - P&L %
    - Hold time (milliseconds)
    - Dead zone duration (if applicable)
    - Filter results (which passed/failed)
    - Exit reason (T1, CROSS, T2, dead zone, stop loss)

Per stock output:
~15-30 patterns detected per stock (across 20 days)
Each pattern records:
Detection time: 1,234 ms
Entry confirmation time: 567 ms
Hold time: 3,456 ms
Total cycle time: 5,257 ms
Outcome: Win +1.2% (T1 exit)
Pattern Type 2: VWAP Breakout
Algorithm (per stock, per day):

For each 5-second micro-bar in the day:
  
  STEP 1: Scan for DROP BELOW VWAP
    - Check if price < VWAP
    - If yes → BELOW VWAP STATE
  
  STEP 2: Scan for STABILIZATION
    - After drop, look forward
    - Check if price stays within VWAP ±0.2% for ≥60 seconds
    - If yes → STABILIZATION DETECTED
  
  STEP 3: Scan for BREAKOUT
    - Check if price crosses back ABOVE VWAP
    - Confirm price stays ≥+0.2% above VWAP
    - If yes → BREAKOUT DETECTED
  
  STEP 4: Check for ENTRY CONFIRMATION
    - After breakout, check for +0.5% climb
    - Confirm volume spike (≥2x average)
    - If yes → ENTRY CONFIRMED
  
  STEP 5: SIMULATE TRADE
    - Entry price = breakout_price + 0.5%
    - Track price tick-by-tick
    - Apply same exit logic as 3-Step
    - Record: Win/Loss, P&L %, hold time, exit reason
  
  STEP 6: Apply FILTERS (if enhanced)
    - Same filter checks as 3-Step
  
  Record pattern with ALL metadata

Per stock output:
~8-15 VWAP Breakout patterns per stock (across 20 days)
Typically fewer than 3-Step but higher win rate

Parallelization:
500 stocks analyzed in parallel (8 cores)
Each core processes ~62 stocks
Total time: ~60 seconds

5. Quality Scoring (5:47:00 AM)
For each stock, calculate 16 scores:
Category 1: Pattern Frequency (20% weight)
Total patterns found across 20 days / 20 = patterns per day
Score = normalize(patterns_per_day, target=3-5)
Category 2: Confirmation Rate (10% weight)
Entry-confirmed patterns / Total patterns detected
Score = confirmation_rate × 100
Category 3: Win Rate (8% weight)
Winning trades / Total confirmed trades
Score = win_rate × 100
Category 4: Expected Value (6% weight)
EV = (win_rate × avg_win) - (loss_rate × avg_loss) - costs
Score = normalize(EV, target=0.5-1.5%)
Category 5: Avg Win % (3% weight)
Average P&L of winning trades
Score = normalize(avg_win, target=1.0-1.5%)
Category 6: Risk/Reward Ratio (3% weight)
RR = avg_win / avg_loss
Score = normalize(RR, target=2.5-3.5)
Category 7: Liquidity Score (6% weight) [UPDATED]
Components:
- Average volume (40%)
- Bid-ask spread (30%)
- Order book depth (30%)
Score = weighted average
Category 8: Volatility Score (8% weight)
ATR as % of price
Target range: 1.5%-3.5% (sweet spot)
Too low = no movement, too high = unpredictable
Category 9: Spread Quality (5% weight)
Average bid-ask spread in basis points
Lower = better
Score = 100 - (spread_bps × 10)
Category 10: VWAP Stability (8% weight) [UPDATED]
Measures how "clean" the VWAP curve is
Calculation:
- Measure VWAP deviation from smooth curve
- Lower deviation = more stable = higher score
Score = 100 - (deviation_pct × 10)
Category 11: Trend Alignment (3% weight)
Price vs moving averages (20/50/200 day)
Uptrend = 100
Neutral = 50
Downtrend = 0
Category 12: Dead Zone Risk (5% weight)
% of trades that got stuck >3 minutes
Average dead zone duration
Score = 100 - (dead_zone_pct × 2)
Category 13: Halt Risk (5% weight)
Days to next earnings
Recent halt history
News volatility
Score = 100 if >30 days to earnings, lower if closer
Category 14: Execution Efficiency (5% weight)
Average cycle time (detection → exit)
Target: 3-5 minutes
Slippage: <0.05%
Score = efficiency composite
Category 15: Backtest Consistency (3% weight)
Standard deviation of daily win rates across 20 days
Lower variance = more consistent = higher score
Category 16: Composite Rank (2% weight)
Weighted average of categories 1-15
Used to break ties

Output per stock:
16 individual scores (0-100 scale)
1 composite score (weighted average)
Risk classification: Conservative / Medium / Aggressive

Example:

AAPL:
  Pattern Frequency: 85 (4.2 patterns/day)
  Confirmation Rate: 78 (42% confirmed)
  Win Rate: 88 (72% wins)
  Expected Value: 92 (1.2% EV)
  Avg Win %: 85 (1.3% avg)
  Risk/Reward: 90 (2.8 RR)
  Liquidity: 95 (excellent)
  Volatility: 88 (2.1% ATR)
  Spread Quality: 92 (tight)
  VWAP Stability: 94 (clean curve)
  Trend Alignment: 100 (uptrend)
  Dead Zone Risk: 80 (15% stuck)
  Halt Risk: 100 (no earnings)
  Execution Efficiency: 87 (4.2min avg)
  Backtest Consistency: 82 (stable)
  Composite Rank: 89
  
  → Classification: MEDIUM RISK


6. Dead Zone Analysis (5:47:30 AM)
For each stock:

Analyze all patterns that entered dead zone:
  
  1. Dead Zone Probability
     = (trades stuck >3min) / total_trades × 100
  2. Average Dead Zone Duration
     = mean(duration for stuck trades) in minutes
  3. Opportunity Cost
     = (capital tied up) × (duration) × (expected_return_rate)
  4. Recovery Rate
     = (trades that escaped dead zone with profit) / total_stuck_trades
  5. Time-of-Day Pattern
     = when do dead zones occur most? (first hour, lunch, close)
  6. Adaptive Timeout
     = recommended timeout based on stock's history

Output:
Dead zone probability: 18%
Avg duration: 4.2 minutes
Opportunity cost: $0.42 per $100 deployed
Recovery rate: 67%
High-risk windows: 9:31-10:00 AM, 3:30-4:00 PM
Recommended timeout: 5.5 minutes

7. Generate ALL 7 Forecasts (5:47:45 AM)
For each of 7 scenarios, system:

Applies scenario-specific filters (or none for Default)
Re-ranks stocks based on filtered results
Selects portfolio (8, 12, 16, or 20 stocks)
Calculates forecast (expected trades, P&L range)
Scenario 1: Default (No Filters)
Filter configuration: ALL OFF
Stock selection: Pure composite score ranking
  
Top 8 stocks (example):
  1. AAPL (score: 89, medium)
  2. MSFT (score: 87, medium)
  3. NVDA (score: 85, aggressive)
  4. META (score: 84, medium)
  5. GOOGL (score: 83, conservative)
  6. AMZN (score: 82, medium)
  7. TSLA (score: 81, aggressive)
  8. AMD (score: 79, conservative)

Forecast:
  Expected trades: 15-25 per day
  Expected P&L: +2.8% to +4.5%
  Win rate: 68%
  Dead zone probability: 22%
Scenario 2: Conservative (All Filters Tight)
Filter configuration:
  VWAP proximity: ±2%
  Volume: 2.5x average
  Time-of-day: Exclude first/last hour
  Support/Resistance: Required
  Trend: Uptrend only

Effect: Filters out 65% of patterns

Re-ranked top 8:
  1. GOOGL (score: 95, conservative)
  2. AAPL (score: 92, medium → conservative after filters)
  3. MSFT (score: 91, medium → conservative)
  4. JPM (score: 89, conservative)
  5. UNH (score: 87, conservative)
  6. JNJ (score: 85, conservative)
  7. V (score: 84, medium → conservative)
  8. MA (score: 83, medium → conservative)

Forecast:
  Expected trades: 8-15 per day
  Expected P&L: +3.2% to +4.8%
  Win rate: 81%
  Dead zone probability: 12%
Scenario 3: Aggressive (Minimal Filters)
Filter configuration:
  VWAP proximity: ±10%
  Volume: 1.5x average
  Time-of-day: All hours
  Support/Resistance: Not required
  Trend: Any

Effect: Filters out only 20% of patterns

Re-ranked top 8:
  1. NVDA (score: 88, aggressive)
  2. TSLA (score: 86, aggressive)
  3. AMD (score: 84, aggressive)
  4. AAPL (score: 83, medium → aggressive after filters)
  5. SMCI (score: 81, aggressive)
  6. MARA (score: 79, aggressive)
  7. COIN (score: 77, aggressive)
  8. RIOT (score: 75, aggressive)

Forecast:
  Expected trades: 20-30 per day
  Expected P&L: +3.5% to +5.2%
  Win rate: 66%
  Dead zone probability: 28%
Scenario 4: Choppy Market (S/R Focused)
Filter configuration:
  VWAP proximity: ±3%
  Volume: 2.5x average
  Time-of-day: All hours
  Support/Resistance: REQUIRED (critical)
  Trend: Neutral or ranging

Effect: Finds stocks bouncing between S/R levels

Top 8: Mix of large-caps in consolidation zones
Forecast: 10-18 trades/day, 75% win rate
Scenario 5: Trending Market (Momentum Focused)
Filter configuration:
  VWAP proximity: ±5%
  Volume: 1.5x average
  Time-of-day: All hours
  Support/Resistance: Not required
  Trend: UPTREND REQUIRED (critical)

Effect: Finds stocks with strong directional momentum

Top 8: Mix of trending names
Forecast: 12-20 trades/day, 72% win rate
Scenario 6: AB Test (Experimental)
Filter configuration: User-defined experimental combos
Current test: Volume OFF, S/R ON, Time=mid-day only

Effect: Testing new filter combinations

Top 8: TBD based on experiment
Forecast: TBD, will be measured
Scenario 7: VWAP Breakout (Different Pattern)
Pattern type: VWAP Breakout (not 3-Step)
Filter configuration: Default (can add presets later)

Effect: Completely different opportunity set

Top 8: Stocks with clean VWAP behavior
  1. AAPL (score: 93)
  2. MSFT (score: 91)
  3. GOOGL (score: 89)
  4. V (score: 87)
  5. MA (score: 85)
  6. JNJ (score: 83)
  7. PG (score: 81)
  8. KO (score: 79)

Forecast:
  Expected trades: 8-12 per day
  Expected P&L: +2.9% to +4.2%
  Win rate: 83%
  Dead zone probability: 10%

Critical insight: Different scenarios select DIFFERENT stocks because filters change what patterns qualify. Conservative finds fewer, cleaner patterns. Aggressive finds more, noisier patterns.

8. Risk Metrics Calculation (5:48:15 AM)
For each forecast, calculate:
Sharpe Ratio
Sharpe = (Expected_ROI - Risk_Free_Rate) / Std_Dev_ROI
Target: >2.0
Sortino Ratio
Sortino = (Expected_ROI - Risk_Free_Rate) / Downside_Std_Dev
Target: >3.0
Calmar Ratio
Calmar = Annual_Return / Max_Drawdown
Target: >2.5
Max Drawdown
Worst peak-to-trough decline in equity curve
Target: <2.0%
Value at Risk (VaR)
99% confidence loss threshold
Based on 20-day distribution


9. Store in Database (5:48:30 AM)
Stored data structure:

morning_forecasts table:
  - date
  - generated_at (5:48:30 AM)
  - selected_stocks_json (default selection)
  - all_forecasts_json (all 7 scenarios)
  - time_profiles_json (adaptive timeouts)
  - news_screening_json (excluded stocks)
  
For each forecast:
  - strategy (3-Step or VWAP Breakout)
  - preset (Default, Conservative, etc.)
  - stocks (list of tickers)
  - backup_stocks (N+4)
  - expected_trades_low
  - expected_trades_high
  - expected_pl_low
  - expected_pl_high
  - win_rate_estimate
  - risk_metrics (Sharpe, Sortino, Calmar)
  - dead_zone_probability
  - filter_configuration


10. Present to User (5:48:45 AM) (beta version)
Frontend displays:
Dashboard View
7 Strategy Cards:

┌─────────────────────────────────┐
│ Default (3-Step)                │
│ 18-25 trades  |  +2.8% to +4.5% │
│ Win rate: 68% |  Sharpe: 2.3    │
│ 8 stocks selected               │
│ [View Details] [Select]         │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Conservative (3-Step)           │
│ 8-15 trades   |  +3.2% to +4.8% │
│ Win rate: 81% |  Sharpe: 3.1    │
│ 8 stocks selected               │
│ [View Details] [Select] ⭐      │
└─────────────────────────────────┘

[... 5 more cards ...]
Stock Detail View (Per Forecast)
Conservative Forecast - Selected Stocks:

┌──────┬───────┬──────────┬──────────┬──────────┬──────────┐
│Rank  │Ticker │Category  │Win Rate  │Exp Trades│Exp P&L   │
├──────┼───────┼──────────┼──────────┼──────────┼──────────┤
│  1   │GOOGL  │Conserv   │  84%     │  1.2/day │ +0.42%   │
│  2   │AAPL   │Conserv   │  82%     │  1.5/day │ +0.48%   │
│  3   │MSFT   │Conserv   │  80%     │  1.3/day │ +0.44%   │
│  4   │JPM    │Conserv   │  79%     │  1.1/day │ +0.38%   │
│  5   │UNH    │Conserv   │  78%     │  1.4/day │ +0.46%   │
│  6   │JNJ    │Conserv   │  77%     │  0.9/day │ +0.32%   │
│  7   │V      │Medium    │  76%     │  1.6/day │ +0.51%   │
│  8   │MA     │Medium    │  75%     │  1.7/day │ +0.54%   │
└──────┴───────┴──────────┴──────────┴──────────┴──────────┘

Backups: PG, KO, WMT, HD

Total Forecast: 10.7 trades/day, +3.55% daily ROI
User Actions
Review all 7 forecasts (takes 2-3 minutes)
Select strategy + preset based on:
Market conditions (choppy vs trending)
Risk tolerance (conservative vs aggressive)
Time availability (want to monitor 25 trades or 10?)
Adjust portfolio size (8, 12, 16, or 20 stocks)
Click "Start Trading"
System loads selected config into Railyard.py


Performance Benchmarks
Total Processing Time
Universe scan: 15 seconds
Data fetch: 30 seconds
News screen: 15 seconds
Pattern detection: 60 seconds (parallel)
Scoring: 15 seconds
Forecasts: 15 seconds
Storage: 5 seconds
Total: ~2.5 minutes
Data Volume
234 million tick data points analyzed
7,500-15,000 patterns detected (15-30 per stock × 500 stocks)
3,500 forecasts generated (7 scenarios × 500 stocks)
56,000 scores calculated (16 categories × 7 scenarios × 500 stocks)
Accuracy (Backtested)
Trade count forecast: ±15% accuracy
P&L forecast: ±20% accuracy
Win rate forecast: ±5% accuracy
Stock selection: Top 8 outperform bottom 8 by 2x


Key Innovations
1. Dual Pattern Detection
3-Step finds geometric reversals (ignores VWAP)
VWAP Breakout finds institutional rebalancing
Different patterns = different opportunities = diversification
2. Millisecond Precision
Tick-level analysis (not 1-minute bars)
Captures intraminute patterns
Precise timing for entry/exit
Realistic latency simulation
3. Seven Scenarios
One morning scan → seven trading plans
User chooses best fit for market conditions
Can switch mid-day without re-running
A/B test different approaches
4. Adaptive Timeouts
Dead zone timeout varies by stock
Learned from 20-day history
More patience for slow movers
Faster exits for volatile stocks
5. Filter Impact Tracking
Every filtered pattern recorded
Can measure: "Did filter help or hurt?"
Iterative improvement
Data-driven optimization
Example Complete Output
Morning Report - October 27, 2025
Generated: 5:48:45 AM

Stocks Analyzed: 487 (500 scanned, 13 excluded for news)
Patterns Detected: 9,214 (3-Step) + 4,103 (VWAP Breakout)
Processing Time: 2m 38s

═══════════════════════════════════════════════════════
SCENARIO FORECASTS
═══════════════════════════════════════════════════════

1. Default (3-Step, No Filters)
   Stocks: AAPL, MSFT, NVDA, META, GOOGL, AMZN, TSLA, AMD
   Trades: 18-25/day  |  P&L: +2.8% to +4.5%
   Win Rate: 68%  |  Sharpe: 2.3  |  Dead Zone: 22%

2. Conservative (3-Step, All Filters)
   Stocks: GOOGL, AAPL, MSFT, JPM, UNH, JNJ, V, MA
   Trades: 8-15/day  |  P&L: +3.2% to +4.8%
   Win Rate: 81%  |  Sharpe: 3.1  |  Dead Zone: 12%  ⭐ RECOMMENDED

3. Aggressive (3-Step, Minimal Filters)
   Stocks: NVDA, TSLA, AMD, AAPL, SMCI, MARA, COIN, RIOT
   Trades: 20-30/day  |  P&L: +3.5% to +5.2%
   Win Rate: 66%  |  Sharpe: 2.1  |  Dead Zone: 28%

4. Choppy Market (3-Step, S/R Focus)
   Stocks: GOOGL, JPM, WMT, KO, PG, JNJ, HD, LOW
   Trades: 10-18/day  |  P&L: +2.9% to +4.3%
   Win Rate: 75%  |  Sharpe: 2.7  |  Dead Zone: 16%

5. Trending Market (3-Step, Momentum)
   Stocks: NVDA, AAPL, MSFT, META, AMD, AVGO, QCOM, TSM
   Trades: 12-20/day  |  P&L: +3.8% to +5.5%
   Win Rate: 72%  |  Sharpe: 2.5  |  Dead Zone: 19%

6. AB Test (3-Step, Experimental)
   Stocks: AAPL, GOOGL, META, V, NVDA, JPM, UNH, PG
   Trades: 12-18/day  |  P&L: +3.0% to +4.6%
   Win Rate: 74%  |  Sharpe: 2.6  |  Dead Zone: 17%

7. VWAP Breakout (Different Pattern)
   Stocks: AAPL, MSFT, GOOGL, V, MA, JNJ, PG, KO
   Trades: 8-12/day  |  P&L: +2.9% to +4.2%
   Win Rate: 83%  |  Sharpe: 3.3  |  Dead Zone: 10%

═══════════════════════════════════════════════════════

Choose your strategy and click "Start Trading" at 9:00 AM


