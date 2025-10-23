#!/usr/bin/env python3
"""Morning Report Test Script"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_morning_report():
    print("=" * 70)
    print("MORNING REPORT GENERATION TEST")
    print("=" * 70)
    print(f"Test run at: {datetime.now()}")
    print("Mode: SIMULATION")
    print()
    
    try:
        from modules.morning_report import MorningReport
        from modules.database import Database
        print("[OK] Imports successful\n")
        
        print("=" * 70)
        print("STEP 1: Generating Morning Report")
        print("=" * 70)
        morning = MorningReport(use_simulation=True)
        print("[OK] MorningReport instance created\n")
        
        print("Generating report...")
        report = morning.generate_report()
        
        if not report.get("success"):
            print("[FAIL] Report generation failed!")
            print(f"Error: {report.get('error')}")
            return False
        print("[OK] Report generated successfully\n")
        
        print("=" * 70)
        print("STEP 2: Report Results")
        print("=" * 70)
        print(f"Forecast ID: {report.get('forecast_id')}")
        print(f"Date: {report.get('date')}")
        print(f"Generated: {report.get('generated_at')}\n")
        
        selected = report.get("selected_stocks", [])
        print(f"Selected Stocks: {len(selected)}")
        for stock in selected:
            print(f"  {stock['ticker']:6} | {stock['category']:12} | Score: {stock['quality_score']:.2f}")
        
        backup = report.get("backup_stocks", [])
        print(f"\nBackup Stocks: {len(backup)}")
        for stock in backup:
            print(f"  {stock['ticker']:6} | {stock['category']:12} | Score: {stock['quality_score']:.2f}")
        
        forecast = report.get("forecast", {})
        print(f"\nForecast:")
        print(f"  Trades: {forecast.get('expected_trades_low')} - {forecast.get('expected_trades_high')}")
        print(f"  P&L: ${forecast.get('expected_pl_low'):.2f} - ${forecast.get('expected_pl_high'):.2f}")
        
        print("\n" + "=" * 70)
        print("STEP 3: Verifying Database")
        print("=" * 70)
        
        db = Database()
        today_forecast = db.get_todays_forecast()
        
        if today_forecast:
            print("\n[OK] Forecast found in database")
            print(f"   ID: {today_forecast['id']}")
            print(f"   Selected: {len(today_forecast['selected_stocks'])}")
            print(f"   Backup: {len(today_forecast['backup_stocks'])}")
        
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM morning_forecasts")
        count = cursor.fetchone()[0]
        print(f"\n   Total forecasts: {count}")
        
        db.close()
        
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print("\n[SUCCESS] All tests passed!")
        print(f"[SUCCESS] Generated {len(selected)} primary + {len(backup)} backup")
        print("[SUCCESS] Pipeline working correctly\n")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_morning_report()
    sys.exit(0 if success else 1)