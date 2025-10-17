# Phase 1 & 2 Testing Guide

**Date:** October 17, 2025  
**Version:** 1.0  
**Phases Tested:** Stock Selection with Backups + Automatic Morning Generation

---

## Overview

This guide helps you verify that Phase 1 and Phase 2 implementations work correctly.

**What We Built:**
- ✅ N+4 backup stock selection
- ✅ Backup stocks stored in database
- ✅ Backup stocks displayed on morning page
- ✅ Scheduler for 12:01 AM generation
- ✅ Trading day detection
- ✅ Manual trigger endpoints

---

## Test 1: Database Schema

**Goal:** Verify backup_stocks_json column exists

### Steps:

1. Open Python shell:
```bash
python3
```

2. Run:
```python
from modules.database import TradingDatabase
db = TradingDatabase()

# Check column exists
cursor = db.conn.cursor()
cursor.execute("PRAGMA table_info(morning_forecasts)")
columns = cursor.fetchall()

print("Morning Forecasts Columns:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

db.close()
```

### Expected Output:
```
id - INTEGER
date - DATE
generated_at - TIMESTAMP
selected_stocks_json - TEXT
backup_stocks_json - TEXT          <-- THIS ONE
expected_trades_low - INTEGER
...
```

### Result:
- [ ] ✅ PASS: backup_stocks_json column exists
- [ ] ❌ FAIL: Column missing

**If FAIL:** Run migration:
```python
from modules.database import TradingDatabase
db = TradingDatabase()
db.conn.execute("ALTER TABLE morning_forecasts ADD COLUMN backup_stocks_json TEXT")
db.conn.commit()
db.close()
print("Migration complete!")
```

---

## Test 2: Backend Stock Selection

**Goal:** Verify stock selector returns 4 backup stocks

### Steps:

1. In Python shell:
```python
from modules.stock_selector import select_balanced_portfolio
from modules.batch_analyzer import analyze_batch, calculate_quality_scores
from modules.stock_universe import get_sample_tickers

# Analyze sample stocks
print("Analyzing stocks...")
tickers = get_sample_tickers(20)
results = analyze_batch(tickers, use_simulation=True, verbose=False)
results = calculate_quality_scores(results)

# Select with backups
selection = select_balanced_portfolio(
    results, 
    n_conservative=2, 
    n_medium=4, 
    n_aggressive=2
)

# Display results
print(f"\nPrimary stocks: {len(selection['selected'])}")
print(f"Backup stocks: {len(selection['backup'])}")

print("\nPRIMARY STOCKS:")
for _, stock in selection['selected'].iterrows():
    print(f"  {stock['ticker']:6s} - {stock['category']}")

print("\nBACKUP STOCKS:")
for _, stock in selection['backup'].iterrows():
    print(f"  {stock['ticker']:6s} - Quality: {stock['quality_score']:.3f}")
```

### Expected Output:
```
Primary stocks: 8
Backup stocks: 4

PRIMARY STOCKS:
  AAPL   - Conservative
  MSFT   - Conservative
  ...

BACKUP STOCKS:
  TSLA   - Quality: 0.652
  AMD    - Quality: 0.648
  ...
```

### Result:
- [ ] ✅ PASS: Shows 8 primary + 4 backup
- [ ] ❌ FAIL: Wrong counts or error

---

## Test 3: API Endpoints

### Test 3A: Scheduler Status

1. Start Flask app:
```bash
python3 app.py
```

2. Login to app at http://localhost:5000

3. Open browser console (F12) and run:
```javascript
fetch("/api/scheduler/status", {
  credentials: "include"
}).then(r => r.json()).then(console.log)
```

**Expected Response:**
```json
{
  "is_running": true,
  "jobs": [
    {
      "id": "morning_report_generation",
      "name": "Generate Morning Report",
      "next_run": "2025-10-18T00:01:00-04:00"
    }
  ],
  "market_status": "closed",
  "is_trading_day": false,
  "next_trading_day": "2025-10-20"
}
```

### Result:
- [ ] ✅ PASS: Returns valid status
- [ ] ❌ FAIL: Error or scheduler not running

---

### Test 3B: Manual Trigger

**⚠️ ADMIN ONLY**

In browser console:
```javascript
fetch("/api/scheduler/trigger", {
  method: "POST",
  credentials: "include"
}).then(r => r.json()).then(console.log)
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Morning report generated successfully",
  "is_trading_day": true,
  "selected_stocks": 8,
  "backup_stocks": 4
}
```

### Result:
- [ ] ✅ PASS: Report generated
- [ ] ❌ FAIL: Error or 403 (need admin role)

---

### Test 3C: Morning Report API

In browser console:
```javascript
fetch("/api/morning/generate", {
  method: "POST",
  credentials: "include"
}).then(r => r.json()).then(data => {
  console.log("Selected stocks:", data.selected_stocks);
  console.log("Backup stocks:", data.backup_stocks);
  console.log("\nBackup details:");
  data.backup_stocks.forEach((stock, i) => {
    console.log(`  ${i+1}. ${stock.ticker} - ${stock.category}`);
  });
})
```

### Result:
- [ ] ✅ PASS: Both arrays present
- [ ] ❌ FAIL: backup_stocks missing/undefined

---

## Test 4: Frontend Display

### Steps:

1. Navigate to http://localhost:5000/morning
2. Click "Generate Report" button
3. Wait for report to load (may take 10-30 seconds)
4. Verify display

### Checklist:

**Primary Stocks Section:**
- [ ] Shows 8 selected stocks
- [ ] Each stock shows ticker, category, metrics
- [ ] Uses primary/secondary colors

**Backup Stocks Section:**
- [ ] Section appears below primary stocks
- [ ] Title: "Backup Stocks (N+4)"
- [ ] Shows 4 backup stocks
- [ ] Each backup shows: index, ticker, category, quality score
- [ ] Uses tertiary color scheme
- [ ] Info text: "Reserve stocks ranked by quality..."

**Responsive Design:**
- [ ] Looks good on desktop (1920px wide)
- [ ] Looks good on tablet (768px wide)
- [ ] Looks good on mobile (375px wide)

**Browser Console:**
- [ ] No JavaScript errors
- [ ] No 404 errors

### Result:
- [ ] ✅ PASS: All elements display correctly
- [ ] ❌ FAIL: Missing backup section or errors

---

## Test 5: Scheduler

### Test 5A: Startup Check

1. Restart Flask app:
```bash
python3 app.py
```

2. Look for startup messages:
```
✓ Morning report scheduler started - generates at 12:01 AM EST
```

### Result:
- [ ] ✅ PASS: Scheduler starts
- [ ] ❌ FAIL: Import errors or no message

---

### Test 5B: Trading Day Detection

In Python shell:
```python
from modules.market_calendar import MarketCalendar
from datetime import datetime

cal = MarketCalendar()

# Check today
today = datetime.now(cal.eastern).date()
print(f"Today: {today}")
print(f"Is trading day: {cal.is_trading_day(today)}")

# Next 5 trading days
print("\nNext 5 trading days:")
next_day = today
for i in range(5):
    next_day = cal.next_trading_day(next_day)
    print(f"  {i+1}. {next_day}")

# Market status
status = cal.get_market_status()
print(f"\nCurrent status: {status['status']}")
```

**Verify:**
- [ ] Correctly identifies weekends as non-trading
- [ ] Correctly identifies holidays as non-trading
- [ ] Returns proper next trading day

### Result:
- [ ] ✅ PASS: Trading days correct
- [ ] ❌ FAIL: Wrong dates

---

### Test 5C: 12:01 AM Generation (Production)

**⚠️ This requires overnight testing**

1. Keep Flask app running overnight
2. Check logs at 12:01 AM next trading day
3. Expected log entries:
```
[2025-10-20 00:01:00] Generating morning report...
[2025-10-20 00:01:15] Morning report generated successfully
  Selected stocks: 8
  Backup stocks: 4
```

4. Verify in database:
```python
from modules.database import TradingDatabase
from datetime import date

db = TradingDatabase()
forecast = db.get_morning_forecast(date.today())
print(f"Date: {forecast['date']}")
print(f"Selected: {len(forecast['selected_stocks'])}")
print(f"Backup: {len(forecast['backup_stocks'])}")
db.close()
```

### Result:
- [ ] ✅ PASS: Auto-generated at 12:01 AM
- [ ] ❌ FAIL: No generation or errors

---

## Common Issues & Fixes

### Issue 1: backup_stocks_json missing
**Symptom:** Database error when storing forecast  
**Fix:** Run ALTER TABLE migration (see Test 1)

### Issue 2: Scheduler not starting
**Symptom:** No startup message  
**Fix:** Install dependencies
```bash
pip install APScheduler pandas_market_calendars pytz
```

### Issue 3: backup_stocks undefined
**Symptom:** JavaScript error on morning page  
**Fix:** Check forecast_generator.py includes backup_stocks in dict

### Issue 4: JavaScript errors
**Symptom:** Console errors on morning page  
**Fix:** Clear cache (Ctrl+Shift+R) and refresh

### Issue 5: 403 Forbidden on /api/scheduler/trigger
**Symptom:** Manual trigger fails  
**Fix:** Login as admin user (admin/admin123)

---

## Testing Summary

Complete all tests and check off results above.

**Overall Status:**
- [ ] ✅ ALL TESTS PASSED - Ready for Phase 3
- [ ] ⚠️ SOME ISSUES - Fix and retest
- [ ] ❌ MAJOR PROBLEMS - Review implementation

**Report Issues:**
- List any failing tests
- Include error messages
- Attach screenshots if helpful

---

## Next Steps

After all tests pass:

**Option A:** Phase 3 - Market Progress Bar
- Real-time market status in header
- Progress bar showing % through day
- Updates every 30 seconds

**Option B:** Phase 4 - MD3 Stock Components  
- Reusable stock list items
- Stock cards and tables
- UI consistency improvements

**Option C:** Phase 5 - Live Monitor Enhancement
- RapidAPI fallback for prices
- Data source indicators
- Enhanced error handling

---

**Testing Guide Version:** 1.0  
**Last Updated:** October 17, 2025  
**Author:** The Luggage Room Boys Fund Development Team
