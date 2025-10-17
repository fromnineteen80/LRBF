# Phase 2 & 3 Runtime Testing Guide

**Purpose:** Verify Phase 2 (Scheduler) and Phase 3 (Market Progress Bar) work correctly in live Flask environment  
**Estimated Time:** 30-45 minutes  
**Prerequisites:** Flask app running locally or on Railway

---

## TESTING ENVIRONMENT SETUP

### Option A: Local Testing

1. **Start Flask Application**
```bash
cd /path/to/LRBF
source venv/bin/activate  # or: venv\Scripts\activate on Windows
python app.py
```

2. **Expected Console Output**
Look for these messages:
```
✅ Morning report scheduler started - generates at 12:01 AM EST
 * Running on http://127.0.0.1:5000
```

3. **If Errors Occur**
- "Backend modules not fully loaded" → Install dependencies: `pip install -r requirements.txt`
- "Scheduler failed to start" → Check logs for specific error

### Option B: Railway Testing

1. **Access Railway Deployment**
- URL: https://your-app.railway.app
- Check deployment logs in Railway dashboard

2. **Expected Log Messages**
```
✅ Morning report scheduler started - generates at 12:01 AM EST
```

---

## PHASE 2: SCHEDULER TESTING

### Test 1: Verify Scheduler Started

**What to Check:** Scheduler initialized with Flask app

**Steps:**
1. Start Flask app
2. Look for console message: "Morning report scheduler started"
3. Check for any error messages

**Expected Result:**
```
✅ Morning report scheduler started - generates at 12:01 AM EST
```

**Pass/Fail:** [ ]

---

### Test 2: Check Scheduler Status API

**What to Check:** Status endpoint returns correct information

**Steps:**
1. Open browser or use curl:
```bash
curl http://localhost:5000/api/scheduler/status
```

2. Or visit in browser (requires login): http://localhost:5000/api/scheduler/status

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
  "is_trading_day": true,
  "next_trading_day": "2025-10-18"
}
```

**Verify:**
- [ ] is_running is true
- [ ] Job "morning_report_generation" exists
- [ ] next_run time is 12:01 AM Eastern
- [ ] market_status matches current time
- [ ] is_trading_day correct for today
- [ ] next_trading_day is reasonable

**Pass/Fail:** [ ]

---

### Test 3: Manual Trigger (Admin Only)

**What to Check:** Can manually trigger morning report generation

**Prerequisites:** 
- Logged in as admin user
- Test endpoint: POST /api/scheduler/trigger

**Steps:**
1. **Using curl (with session cookie):**
```bash
# First login to get session cookie
curl -c cookies.txt -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Then trigger report
curl -b cookies.txt -X POST http://localhost:5000/api/scheduler/trigger
```

2. **Using browser console:**
```javascript
fetch('/api/scheduler/trigger', { method: 'POST' })
  .then(r => r.json())
  .then(console.log);
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

**Verify:**
- [ ] success is true
- [ ] selected_stocks is 8
- [ ] backup_stocks is 4
- [ ] is_trading_day matches today
- [ ] No error message

**Check Database:**
```bash
sqlite3 data/luggage_room.db
SELECT date, selected_stocks_json FROM morning_forecasts ORDER BY date DESC LIMIT 1;
```

Should show today's date with JSON containing 8 selected stocks + 4 backup stocks.

**Pass/Fail:** [ ]

---

### Test 4: Trading Day Detection

**What to Check:** Correctly identifies trading vs non-trading days

**Steps:**
1. **Check today's status:**
```python
python3 -c "from modules.market_calendar import is_trading_day; print(is_trading_day())"
```

2. **Check a known holiday (e.g., Christmas):**
```python
python3 -c "from modules.market_calendar import is_trading_day; from datetime import date; print(is_trading_day(date(2025, 12, 25)))"
```

**Expected Results:**
- Weekday (non-holiday): True
- Weekend: False
- NYSE holiday: False

**Verify:**
- [ ] Weekday detection correct
- [ ] Weekend detection correct
- [ ] Holiday detection correct

**Pass/Fail:** [ ]

---

### Test 5: Automatic Generation (Wait for Midnight)

**What to Check:** Scheduler automatically triggers at 12:01 AM on trading days

**Prerequisites:** 
- Flask app running overnight
- Access to logs

**Steps:**
1. Leave Flask app running (or Railway deployment active)
2. Check logs after 12:01 AM Eastern next trading day
3. Look for log message: "Generating morning report..."

**Expected Log Output (around 12:01 AM):**
```
[2025-10-18 00:01:00] INFO - Generating morning report...
[2025-10-18 00:01:15] INFO - Morning report generated successfully
[2025-10-18 00:01:15] INFO -   Selected stocks: 8
[2025-10-18 00:01:15] INFO -   Backup stocks: 4
```

**If Non-Trading Day (Weekend/Holiday):**
```
[2025-10-19 00:01:00] INFO - Skipping morning report - not a trading day
```

**Verify:**
- [ ] Scheduler triggered at 12:01 AM
- [ ] Generated report on trading day
- [ ] Skipped on non-trading day
- [ ] No errors in logs

**Pass/Fail:** [ ]

---

## PHASE 3: MARKET PROGRESS BAR TESTING

### Test 6: Visual Display Check

**What to Check:** Market progress bar visible in header/sidebar

**Steps:**
1. Login to application
2. Navigate to any page (dashboard, live, EOD)
3. Look for "Denver to DC" railroad track in header

**Expected Display:**
- Railroad track with train icon
- Time remaining or status text
- Smooth animation (if market open)

**Verify:**
- [ ] Progress bar visible
- [ ] Train icon displayed (Material Icon: train)
- [ ] Track styling correct
- [ ] Time remaining shows (if market open)
- [ ] Status text shows (if market closed)

**Pass/Fail:** [ ]

---

### Test 7: API Response Check

**What to Check:** /api/market-status returns correct data

**Steps:**
1. **During market hours (9:30 AM - 4:00 PM ET):**
```bash
curl http://localhost:5000/api/market-status
```

**Expected Response (Market Open):**
```json
{
  "status": "open",
  "is_trading_day": true,
  "progress_pct": 38.46,
  "time_remaining": "3:45:12",
  "time_remaining_seconds": 13512,
  "current_time": "2025-10-17T12:00:00-04:00",
  "market_open": "2025-10-17T09:30:00-04:00",
  "market_close": "2025-10-17T16:00:00-04:00",
  "next_trading_day": "2025-10-18"
}
```

2. **Before 9:30 AM ET:**
```json
{
  "status": "pre_market",
  "time_remaining": "Pre-Market"
}
```

3. **After 4:00 PM ET:**
```json
{
  "status": "after_hours",
  "time_remaining": "After Hours"
}
```

4. **Weekend/Holiday:**
```json
{
  "status": "closed",
  "is_trading_day": false,
  "time_remaining": "Market Closed"
}
```

**Verify:**
- [ ] Status matches current time
- [ ] progress_pct between 0-100 (if open)
- [ ] time_remaining formatted correctly
- [ ] Timezone correct (Eastern Time)

**Pass/Fail:** [ ]

---

### Test 8: Progress Bar Animation (Market Hours Only)

**What to Check:** Progress bar updates every 30 seconds during market hours

**Prerequisites:** Test during market hours (9:30 AM - 4:00 PM ET)

**Steps:**
1. Open dashboard page
2. Open browser DevTools (F12) → Console
3. Watch for console messages: "[MarketStatus] Initialized - updating every 30 seconds"
4. Observe progress bar for 2 minutes

**Expected Behavior:**
- Progress bar position updates smoothly
- Train icon moves along track
- Time remaining counts down
- Updates occur every 30 seconds

**Verify:**
- [ ] Progress bar animates
- [ ] Train icon moves
- [ ] Time remaining updates
- [ ] No JavaScript errors in console
- [ ] Smooth CSS transitions

**Pass/Fail:** [ ]

---

### Test 9: Time Remaining Accuracy

**What to Check:** Time remaining calculation is accurate

**Steps:**
1. During market hours, note the displayed time remaining
2. Calculate expected time:
   - Market close: 4:00 PM Eastern
   - Current time: [your current time]
   - Expected remaining: [market close - current time]
3. Compare displayed time to calculated time

**Example:**
- Current: 2:30:00 PM ET
- Close: 4:00:00 PM ET
- Expected: 1:30:00
- Displayed: Should match within a few seconds

**Verify:**
- [ ] Hours correct
- [ ] Minutes correct
- [ ] Seconds updating in real-time
- [ ] Format is H:MM:SS

**Pass/Fail:** [ ]

---

### Test 10: Mobile Responsiveness

**What to Check:** Progress bar displays correctly on mobile devices

**Steps:**
1. **Desktop Browser:**
   - Open DevTools (F12)
   - Toggle device toolbar (mobile simulation)
   - Test iPhone SE (375px width)
   - Test iPad (768px width)

2. **Real Mobile Device:**
   - Access app from phone
   - Check header/sidebar

**Expected Behavior:**
- Progress bar visible on all screen sizes
- Text readable (not cut off)
- Touch-friendly (if interactive)
- No horizontal scroll

**Verify:**
- [ ] Visible on mobile (375px)
- [ ] Visible on tablet (768px)
- [ ] Visible on desktop (1920px)
- [ ] Text not truncated
- [ ] Layout not broken

**Pass/Fail:** [ ]

---

### Test 11: Page Load Performance

**What to Check:** Market status loads quickly without blocking page render

**Steps:**
1. Open DevTools → Network tab
2. Refresh page
3. Look for /api/market-status request
4. Check timing

**Expected Performance:**
- Request completes in < 500ms
- Page fully interactive before market status loads
- No JavaScript errors

**Verify:**
- [ ] API request < 500ms
- [ ] Page not blocked waiting for status
- [ ] No console errors

**Pass/Fail:** [ ]

---

### Test 12: Error Handling

**What to Check:** Graceful degradation if API fails

**Steps:**
1. **Simulate API failure:**
   - Temporarily stop Flask app
   - Or modify /api/market-status to return 500 error

2. **Check frontend behavior:**
   - Page should still load
   - Progress bar should show "Error" or remain hidden
   - No JavaScript crashes

**Expected Behavior:**
- Page loads successfully
- Error logged to console
- User sees "Error" text or progress bar hidden
- Page remains functional

**Verify:**
- [ ] Page doesn't crash
- [ ] Error logged to console
- [ ] Error displayed to user (or hidden)
- [ ] No repeated failed requests (backoff)

**Pass/Fail:** [ ]

---

## TESTING RESULTS SUMMARY

### Phase 2: Scheduler (5 tests)

- [ ] Test 1: Scheduler Started
- [ ] Test 2: Status API
- [ ] Test 3: Manual Trigger
- [ ] Test 4: Trading Day Detection
- [ ] Test 5: Automatic Generation

**Phase 2 Score:** ___/5

---

### Phase 3: Market Progress Bar (7 tests)

- [ ] Test 6: Visual Display
- [ ] Test 7: API Response
- [ ] Test 8: Progress Animation
- [ ] Test 9: Time Accuracy
- [ ] Test 10: Mobile Responsive
- [ ] Test 11: Performance
- [ ] Test 12: Error Handling

**Phase 3 Score:** ___/7

---

### Overall Testing Result

**Total Score:** ___/12  
**Pass Threshold:** 10/12 (83%)

**Verdict:**
- [ ] PASS - Proceed to Phase 4
- [ ] FAIL - Review failed tests and fix issues

---

## TROUBLESHOOTING GUIDE

### Issue: Scheduler Not Starting

**Symptoms:** No "scheduler started" message in logs

**Possible Causes:**
1. Missing dependencies (APScheduler, pandas-market-calendars, pytz)
2. Import error in modules
3. BACKEND_AVAILABLE flag is False

**Solutions:**
```bash
# Install dependencies
pip install APScheduler>=3.10.4 pandas-market-calendars>=4.3.0 pytz>=2024.1

# Check imports manually
python3 -c "from modules.scheduler import scheduler; print('OK')"

# Check BACKEND_AVAILABLE flag in app.py logs
```

---

### Issue: Market Progress Bar Not Visible

**Symptoms:** No railroad track in header

**Possible Causes:**
1. JavaScript not loaded (check browser console)
2. CSS not applied
3. DOM elements missing IDs
4. market-status.js failed to initialize

**Solutions:**
1. Check browser console for errors
2. Verify script tag in base.html: `<script src="/static/js/market-status.js"></script>`
3. Check element IDs exist: marketProgressContainer, marketProgressBar, etc.
4. Look for "[MarketStatus] Initialized" in console

---

### Issue: Progress Bar Not Updating

**Symptoms:** Bar displays but doesn't move

**Possible Causes:**
1. API endpoint returning error
2. JavaScript interval not running
3. Not during market hours

**Solutions:**
1. Check /api/market-status in browser: http://localhost:5000/api/market-status
2. Open console, look for fetch errors
3. Verify current time is during market hours (9:30 AM - 4:00 PM ET)

---

### Issue: Time Remaining Incorrect

**Symptoms:** Displayed time doesn't match expected

**Possible Causes:**
1. Timezone issue (server vs. Eastern Time)
2. Calculation error in backend
3. Clock drift

**Solutions:**
1. Verify server timezone: `python3 -c "import datetime; print(datetime.datetime.now().astimezone())"`
2. Check market_calendar.py uses pytz correctly
3. Sync server clock with NTP

---

## NEXT STEPS AFTER TESTING

### If All Tests Pass (10+ / 12):
1. Document any minor issues in GitHub Issues
2. Update WHATS_NEXT.md with "Phase 2 & 3: VERIFIED"
3. Create READY_FOR_PHASE_4.md
4. Proceed to Phase 4: MD3 Stock Components

### If Tests Fail (< 10 / 12):
1. Document all failed tests
2. Create bug fix issues in GitHub
3. Fix issues before proceeding
4. Re-run failed tests
5. Only proceed when 10/12 tests pass

---

## TESTING COMPLETED BY

**Tester Name:** _______________  
**Date:** _______________  
**Environment:** [ ] Local [ ] Railway  
**Overall Result:** [ ] PASS [ ] FAIL  

**Notes:**
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
