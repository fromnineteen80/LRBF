NEXT SESSION PLAN - Morning Report Completion
==============================================

SESSION GOAL: Complete morning report with correct IBKR integration

==============================================
DECISION POINT (Choose before starting)
==============================================

Option A: Use ib_insync (RECOMMENDED)
- Rebuild 3 files: ibkr_connector.py, ibkr_data_provider.py, delete ibkr_websocket.py
- 5 commits, ~15k tokens, 30 minutes
- Institutional-grade: 1-10ms latency, tick data, native scanner
- Rest of repo unchanged

Option B: Keep Client Portal Web API
- Test current implementation with test_ibkr_connector.py
- Fix any broken endpoints based on test results
- ~5k tokens for fixes
- May need rebuild later for production

==============================================
IF OPTION A (ib_insync) - 5 Steps
==============================================

1. Install ib_insync
   - Add to requirements.txt
   - Commit

2. Rewrite backend/data/ibkr_connector.py
   - Use ib_insync.IB() instead of requests
   - Keep same method signatures (get_historical_data, etc.)
   - Add native scanner support
   - Commit

3. Update backend/data/ibkr_data_provider.py
   - Change imports to use new connector
   - Test fetch_market_data() works
   - Commit

4. Delete backend/data/ibkr_websocket.py
   - ib_insync has streaming built-in
   - Commit

5. Test end-to-end
   - Run morning_report.py
   - Verify 7 forecasts generated
   - Commit fixes if needed

==============================================
IF OPTION B (Client Portal) - 3 Steps
==============================================

1. Run validation test
   - python test_ibkr_connector.py
   - Note which tests fail

2. Fix failed endpoints
   - Update URLs/parameters based on errors
   - Add VWAP calculation if not in response
   - Add scanner fallback if endpoint doesn't exist
   - Commit fixes

3. Test morning report
   - Run morning_report.py
   - Verify 7 forecasts generated
   - Commit fixes if needed

==============================================
MORNING REPORT INTEGRATION (Both Options)
==============================================

1. Verify morning_report.py flow
   - Loads top 500 from IBKR scanner ✅ (commit 710456f)
   - Fetches 20-day data for each ✅
   - Runs pattern detection ✅
   - Generates 7 forecasts ✅
   - Stores in database ✅

2. Test database storage
   - Check morning_forecasts table has all_forecasts_json
   - Check users table has fund_contribution, ownership_pct
   - Run migrations if needed

3. Run full morning report
   - python backend/reports/morning_report.py
   - Should generate JSON output with 7 forecasts
   - Store in database
   - Print summary

4. Verify output
   - Selected stocks (8-20)
   - Backup stocks (4)
   - 7 forecast scenarios
   - Expected trades/P&L ranges
   - Quality scores

==============================================
REMAINING GAPS (If Time Permits)
==============================================

1. VWAP calculation
   - If not in historical data response
   - Add manual calculation: VWAP = sum(price*volume) / sum(volume)

2. Rate limiting
   - 500 stocks × 20 days = potential rate limit issue
   - Add retry logic for 429 status codes
   - Add delays between requests

3. Error handling
   - Add try/catch for failed stock data
   - Continue if 1 stock fails (don't break entire scan)

4. Logging
   - Add detailed logs for debugging
   - Track timing per stock
   - Identify slow stocks

==============================================
SUCCESS CRITERIA
==============================================

Morning report should:
✅ Scan 500 stocks from IBKR
✅ Fetch 20-day historical data
✅ Generate 7 forecasts:
   1. Default (no filters)
   2. Conservative
   3. Aggressive
   4. Choppy Market
   5. Trending Market
   6. AB Test
   7. VWAP Breakout
✅ Store in database
✅ Return JSON output
✅ Complete in <5 minutes

==============================================
CURRENT STATUS
==============================================

✅ COMPLETED (15 commits this session):
- Fixed IBKR gateway URLs
- Replaced RapidAPI with IBKR
- Added market scanner
- Created VWAP Breakout detector
- Generated 7 forecasts
- Added WebSocket streaming
- Added database migrations
- Morning report uses IBKR scanner

⚠️ NOT TESTED:
- IBKR endpoints (may be wrong)
- Morning report end-to-end
- Database storage
- 7-forecast generation

==============================================
RECOMMENDED APPROACH
==============================================

START NEXT SESSION:
1. User decides: ib_insync (Option A) or Client Portal (Option B)
2. Execute chosen option (5 or 3 steps)
3. Test morning report end-to-end
4. Fix any issues
5. Verify 7 forecasts stored in database

ESTIMATED TIME:
- Option A: 30-45 minutes (rebuild + test)
- Option B: 15-30 minutes (test + fix)

ESTIMATED TOKENS:
- Option A: ~15-20k tokens
- Option B: ~5-10k tokens

==============================================
FILES TO REFERENCE NEXT SESSION
==============================================

✅ Keep open:
- project_handoff.md (context)
- TECHNICAL_SPECS.md (reference)
- morning_report_assessment.md (requirements)
- IBKR_API_VERIFICATION.md (API notes)
- test_ibkr_connector.py (validation script)

❌ Don't read:
- Building Railyard Markets.docx (not needed)
- Full IBKR API docs (too large)

==============================================
END OF PLAN
==============================================

Token Status: 88k remaining
Next Session: Choose Option A or B, execute, test, verify
