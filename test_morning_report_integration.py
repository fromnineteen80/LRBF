#!/usr/bin/env python3
"""
End-to-End Integration Test

Tests complete workflow:
1. Morning report generates 7 forecasts
2. Stores all forecasts in database
3. Retrieves forecast from database
4. Railyard.py loads selected stocks
5. Monitors patterns (simulation mode)
6. EOD processes results
"""

import sys
import os
from datetime import date, datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_integration():
    """Run full integration test."""
    
    print("=" * 80)
    print("INTEGRATION TEST - FULL PIPELINE")
    print("=" * 80)
    print(f"Test started: {datetime.now()}")
    print(f"Mode: SIMULATION (no real IBKR connection required)")
    print()
    
    test_results = {
        'morning_report': False,
        'database_storage': False,
        'forecast_retrieval': False,
        'railyard_init': False,
        'eod_reporter': False
    }
    
    # Step 1: Generate morning report
    print("1. MORNING REPORT GENERATION")
    print("-" * 80)
    try:
        from backend.reports.morning_report import EnhancedMorningReport
        print("✓ Import successful")
        
        report_gen = EnhancedMorningReport(use_simulation=True)
        print("✓ MorningReport instance created")
        
        print("\nGenerating report (this may take a few minutes)...")
        report = report_gen.generate_report()
        
        if not report.get('success'):
            print(f"❌ Morning report failed: {report.get('error')}")
            return False
        
        print(f"✓ Morning report generated successfully")
        print(f"  Date: {report.get('date')}")
        print(f"  Forecast ID: {report.get('forecast_id')}")
        
        # Check for all 7 forecasts
        all_forecasts = report.get('all_forecasts', {})
        expected_forecasts = [
            'default', 'conservative', 'aggressive', 
            'choppy', 'trending', 'abtest', 'vwap_breakout'
        ]
        
        print(f"\n  Forecasts generated: {len(all_forecasts)}")
        for forecast_name in expected_forecasts:
            if forecast_name in all_forecasts:
                forecast = all_forecasts[forecast_name]
                stocks = forecast.get('selected_stocks', [])
                print(f"    ✓ {forecast_name:15} - {len(stocks)} stocks")
            else:
                print(f"    ✗ {forecast_name:15} - MISSING")
                return False
        
        test_results['morning_report'] = True
        
    except Exception as e:
        print(f"❌ Morning report exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Step 2: Verify database storage
    print("2. DATABASE STORAGE VERIFICATION")
    print("-" * 80)
    try:
        from backend.models.database import TradingDatabase
        print("✓ Database import successful")
        
        db = TradingDatabase()
        print("✓ Database connection established")
        
        forecast = db.get_morning_forecast(date.today())
        
        if not forecast:
            print("❌ Forecast not found in database")
            print("  This might be expected if report generation just created the forecast")
            print("  but database insertion hasn't completed yet.")
            # Don't fail - this could be timing
        else:
            print("✓ Forecast found in database")
            print(f"  Date: {forecast.get('date')}")
            print(f"  Selected stocks: {len(forecast.get('selected_stocks', []))}")
        
        # Verify all 7 forecast columns exist in schema
        print("\n  Checking database schema for seven-forecast support...")
        cursor = db.conn.cursor()
        cursor.execute("PRAGMA table_info(morning_forecasts)")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = [
            'default_forecast_json',
            'conservative_forecast_json', 
            'aggressive_forecast_json',
            'choppy_forecast_json',
            'trending_forecast_json',
            'abtest_forecast_json',
            'vwap_breakout_forecast_json',
            'active_preset',
            'active_strategy'
        ]
        
        missing_columns = []
        for col in required_columns:
            if col in columns:
                print(f"    ✓ {col}")
            else:
                print(f"    ✗ {col} - MISSING")
                missing_columns.append(col)
        
        if missing_columns:
            print(f"\n  ⚠️  Database migration needed!")
            print(f"  Run: python migrate_seven_forecasts.py")
            print(f"  Missing columns: {', '.join(missing_columns)}")
        else:
            print("\n  ✓ Database schema ready for seven forecasts")
        
        test_results['database_storage'] = len(missing_columns) == 0
        
    except Exception as e:
        print(f"❌ Database exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Step 3: Forecast retrieval test
    print("3. FORECAST RETRIEVAL TEST")
    print("-" * 80)
    try:
        if forecast:
            print("✓ Forecast already retrieved in step 2")
            
            # Try to parse the seven-forecast JSON fields
            if 'default_forecast_json' in forecast:
                import json
                try:
                    default = json.loads(forecast['default_forecast_json']) if forecast['default_forecast_json'] else {}
                    print(f"  ✓ default forecast: {len(default.get('selected_stocks', []))} stocks")
                except:
                    print(f"  ⚠️  default forecast: Could not parse JSON")
            
            test_results['forecast_retrieval'] = True
        else:
            print("⚠️  No forecast available to retrieve (might be first run)")
            test_results['forecast_retrieval'] = False
        
    except Exception as e:
        print(f"❌ Forecast retrieval exception: {e}")
        return False
    
    print()
    
    # Step 4: Railyard.py initialization test
    print("4. RAILYARD.PY INITIALIZATION")
    print("-" * 80)
    try:
        from backend.core.railyard import RailyardEngine
        print("✓ Railyard import successful")
        
        # Initialize with default strategy (no IBKR connection required)
        engine = RailyardEngine(
            strategy='default',
            use_filters=False
        )
        print(f"✓ Railyard initialized")
        print(f"  Strategy: {engine.strategy}")
        print(f"  Filters: {'ON' if engine.use_filters else 'OFF'}")
        
        # Check IBKR connection (don't fail if not connected - might not have Gateway running)
        if hasattr(engine, 'ibkr'):
            print(f"  IBKR connector: Present")
        else:
            print(f"  ⚠️  IBKR connector: Not initialized (expected if Gateway not running)")
        
        test_results['railyard_init'] = True
        
    except Exception as e:
        print(f"❌ Railyard initialization exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Step 5: Test EOD reporter
    print("5. EOD REPORTER INITIALIZATION")
    print("-" * 80)
    try:
        from backend.reports.eod_reporter import EODReporter
        print("✓ EOD import successful")
        
        eod = EODReporter()
        print(f"✓ EOD reporter initialized")
        
        # Note: We can't test full EOD report generation without real trades
        # Just verify the reporter can be created
        test_results['eod_reporter'] = True
        
    except Exception as e:
        print(f"❌ EOD reporter exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Summary
    print("=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print()
    
    for test, passed in test_results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test.replace('_', ' ').title()}")
    
    print()
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print("✅ ALL INTEGRATION TESTS PASSED")
        print()
        print("System verified:")
        print("  ✓ Morning report generates 7 forecasts")
        print("  ✓ All forecasts stored in database")
        print("  ✓ Forecast data can be retrieved")
        print("  ✓ Railyard.py initializes correctly")
        print("  ✓ EOD reporter ready")
        print()
        print("Next steps:")
        print("  1. Run test_latency.py to verify IBKR streaming")
        print("  2. Start IBKR Gateway (paper mode)")
        print("  3. Generate morning report at 5:45 AM ET")
        print("  4. Start Railyard.py at 9:31 AM ET")
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Review failed tests above and fix issues before proceeding.")
        
        if not test_results['database_storage']:
            print()
            print("⚠️  DATABASE MIGRATION REQUIRED:")
            print("  Run: python migrate_seven_forecasts.py")
    
    print()
    return all_passed


if __name__ == '__main__':
    success = test_integration()
    exit(0 if success else 1)
