# LRBFund Trading Strategy Walkthrough

## 5:45 AM \- Morning Report (Automated)

* **Scan 500 stocks** \- Pull top stocks by volume from Interactive Brokers’ Trading API  
* **Detect patterns** \- Find 3-Step Geometric and VWAP Breakout patterns in last 20 days  
* **Score each stock** \- Rate on 16 metrics:  
  * **Pattern Performance (50% weight):** Pattern Frequency (20%), Confirmation Rate (10%), Win Rate (8%), Expected Value (6%), Avg Win % (3%), Risk/Reward Ratio (3%)  
  * **Market Quality (30% weight):** Liquidity Score (6%), Volatility Score (8%), Spread Quality (5%), VWAP Stability (8%), Trend Alignment (3%)  
  * **Risk Factors (15% weight):** Dead Zone Risk (5%), Halt Risk (5%), Execution Efficiency (5%)  
  * **Consistency (5% weight):** Backtest Consistency (3%), Composite Rank (2%)  
* **Rank stocks** \- Sort by composite score  
* **Generate 7 forecasts** \- One for each strategy/preset combination:  
  * **Default (3-Step):** No filters, baseline performance.   
    * **Why:** Establishes pure pattern win rate without optimization. Benchmark for measuring filter impact.  
  * **Conservative (3-Step):** All filters ON, tight thresholds.   
    * **Why:** Maximize win rate when you want safety over frequency. Best for volatile/uncertain days.  
  * **Aggressive (3-Step):** Minimal filters, loose thresholds.   
    * **Why:** Maximize trade count when the market is stable. Best for high-volume capture.  
  * **Choppy Market (3-Step):** S/R focused, neutral trend.   
    * **Why:** Optimized for range-bound markets where price bounces between levels. Use when the market lacks direction.  
  * **Trending Market (3-Step):** Momentum focused, trend-aligned.   
    * **Why:** Optimized for directional markets with clear momentum. Use when the market has conviction.  
  * **AB Test (3-Step):** Experimental filter combinations.   
    * **Why:** Test new ideas without risking main strategies. Learn what works, iterate configurations.  
  * **VWAP Breakout:** Different pattern entirely.   
    * **Why:** Completely separate opportunity set. Captures institutional rebalancing that 3-Step misses. Diversification.  
* **Present options** \- Show you top stocks and expected performance for each approach

## 9:00 AM \- You Choose

* Pick strategy (3-Step or VWAP Breakout)  
* Pick preset (Default, Conservative, Aggressive, etc.)  
* Pick portfolio size (8, 12, 16, or 20 stocks)  
* System loads your selections into trading engine

## 9:31 AM \- Trading Starts (Automated)

**For each stock in your portfolio:**

* **Watch for pattern** \- Monitor price movement tick-by-tick  
* **Pattern completes?** Two different approaches:  
  * **3-Step Geometric:** Decline 1% → Recover 50% → Retrace 50%. Creates a W-bottom.   
    * **Advantage:** More opportunities (15-25/day), works in all market conditions, ignores VWAP position.   
    * **Use when:** You want higher trade frequency.  
  * **VWAP Breakout:** Drop below VWAP → Stabilize near VWAP → Break back above VWAP. Captures institutional rebalancing.   
    * **Advantage:** Higher win rate (81-83%), fewer but cleaner setups.   
    * **Use when:** You want quality over quantity.  
* **Entry signal triggers?** \- After pattern completes, wait for price to climb \+0.5% from the low point. This confirms buyers are in control.  
* **Filters pass?** \- Check VWAP proximity, volume, time-of-day, support/resistance, trend (if filters enabled)  
* **BUY** \- Enter position only when: Pattern complete \+ Entry signal confirmed \+ Filters pass

**After entry (tiered exit system):**

* **Hit T1 (+0.75%)?** → Lock it, wait for CROSS (+1.00%)  
* **Hit CROSS (+1.00%)?** → Lock it, wait for momentum confirmation (+1.25% total)  
* **Momentum confirmed?** → Hold for T2 (+1.75%), OR exit at CROSS if falls back  
* **Falls below the locked floor?** → Exit at previous milestone (T1 or CROSS)  
* **Dead zone detected?** → Tiered timeouts based on profit level:  
  * Below T1: 3 min → exit if any positive  
  * At T1: 4 min → exit at T1  
  * At CROSS: 4 min → exit at CROSS  
  * After momentum: 6 min → exit at best available  
* **Immediate crash?** → Stop loss at \-0.5%  
* **Wait 1 minute** \- Cool down before scanning same stock again

## Throughout Day

* **Live monitoring** \- Dashboard shows actual vs forecast (trades, P\&L, win rate)  
* **Guardrails active** \- If daily loss hits \-1.5%, stop all trading  
* **You can switch** \- Change strategy/preset mid-day if market conditions shift

## 4:00 PM \- Market Close

* **Final reconciliation** \- Pull all fills from IBKR  
* **Calculate metrics** \- Win rate, Sharpe ratio, actual vs forecast  
* **Store results** \- Save to database for tomorrow's morning report  
* **Update forecasts** \- Newest data feeds into next day's predictions

## Key Point

**You don't manually trade.** You pick the strategy in the morning, and the system executes hundreds of micro-trades automatically based on the math. You just monitor and can override if needed.

## Exit Logic Example (Real Trade)

**Entry:** Buy AAPL at $150.00

**Timeline:**

* **T+30s:** Price hits $150.75 (+0.50%) → Nothing happens yet  
* **T+1m:** Price hits $151.13 (+0.75%) → **T1 HIT, LOCKED IN**  
* **T+2m:** Price climbs to $151.50 (+1.00%) → **CROSS HIT, LOCKED IN**  
* **T+3m:** Price climbs to $151.88 (+1.25%) → **MOMENTUM CONFIRMED, GOING FOR T2**  
* **T+4m:** Price hits $152.63 (+1.75%) → **T2 HIT, EXIT** ✅

**Alternate scenario 1:**

* **T+3m:** Price at $151.80 (+1.20%) → Momentum NOT confirmed  
* **T+7m:** Still between $151.00-$151.80 → **DEAD ZONE at CROSS (4 min timeout)** → Exit at \+1.00% ✅

**Alternate scenario 2:**

* **T+2m:** Price only reaches $151.00 (+0.67%) → CROSS never hit  
* **T+3m:** Price falls to $150.60 (+0.40%) → Falls below T1  
* **EXIT at T1 (+0.75%)** ✅

**Alternate scenario 3:**

* **T+1m:** Price only reaches $150.60 (+0.40%) → T1 never hit  
* **T+4m:** Still at $150.30-$150.60 → **DEAD ZONE below T1 (3 min timeout)** → Exit at \+0.40% ✅

**Worst case:**

* **T+10s:** Price crashes to $149.25 (-0.50%) → **STOP LOSS, EXIT** ❌
