"""
Morning Report Scheduler

Automatically generates morning report at 12:01 AM on trading days.
Uses APScheduler for background task execution.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MorningReportScheduler:
    """Scheduler for automatic morning report generation."""
    
    def __init__(self, app=None):
        """
        Initialize scheduler.
        
        Args:
            app: Flask application instance (optional)
        """
        self.app = app
        self.scheduler = BackgroundScheduler(timezone='US/Eastern')
        self.is_running = False
        
    def init_app(self, app):
        """
        Initialize with Flask app context.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
    def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        # Schedule morning report generation at 12:01 AM Eastern
        self.scheduler.add_job(
            func=self._generate_morning_report_task,
            trigger=CronTrigger(
                hour=0,
                minute=1,
                timezone='US/Eastern'
            ),
            id='morning_report_generation',
            name='Generate Morning Report',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("Scheduler started - Morning report will generate at 12:01 AM EST on trading days")
        
    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Scheduler stopped")
        
    def _generate_morning_report_task(self):
        """
        Background task to generate morning report.
        Only runs on trading days.
        """
        try:
            # Import here to avoid circular imports
            from modules.market_calendar import is_trading_day
            from modules.morning_report import MorningReport
            
            # Check if today is a trading day
            if not is_trading_day():
                logger.info("Skipping morning report - not a trading day")
                return
            
            logger.info("Generating morning report...")
            
            # Create app context if Flask app provided
            if self.app:
                with self.app.app_context():
                    morning = MorningReport()
                    report = morning.generate_report()
                    logger.info(f"Morning report generated successfully")
                    logger.info(f"  Selected stocks: {len(report.get('selected_stocks', []))}")
                    logger.info(f"  Backup stocks: {len(report.get('backup_stocks', []))}")
            else:
                # No Flask app context needed
                morning = MorningReport()
                report = morning.generate_report()
                logger.info("Morning report generated successfully")
                
        except Exception as e:
            logger.error(f"Failed to generate morning report: {e}")
            
    def trigger_manual_generation(self):
        """
        Manually trigger morning report generation.
        Useful for testing.
        
        Returns:
            Dictionary with generation result
        """
        try:
            logger.info("Manual trigger - generating morning report...")
            
            from modules.market_calendar import is_trading_day
            from modules.morning_report import MorningReport
            
            # Check if today is a trading day
            today_is_trading = is_trading_day()
            
            if self.app:
                with self.app.app_context():
                    morning = MorningReport()
                    report = morning.generate_report()
            else:
                morning = MorningReport()
                report = morning.generate_report()
            
            return {
                'success': True,
                'message': 'Morning report generated successfully',
                'is_trading_day': today_is_trading,
                'selected_stocks': len(report.get('selected_stocks', [])),
                'backup_stocks': len(report.get('backup_stocks', []))
            }
            
        except Exception as e:
            logger.error(f"Manual generation failed: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_status(self) -> dict:
        """
        Get scheduler status.
        
        Returns:
            Dictionary with scheduler info
        """
        from modules.market_calendar import get_market_status
        
        market_status = get_market_status()
        
        jobs = []
        if self.is_running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                })
        
        return {
            'is_running': self.is_running,
            'jobs': jobs,
            'market_status': market_status['status'],
            'is_trading_day': market_status['is_trading_day'],
            'next_trading_day': market_status['next_trading_day'].isoformat() if market_status['next_trading_day'] else None
        }


# Global scheduler instance
scheduler = MorningReportScheduler()


if __name__ == "__main__":
    print("=" * 80)
    print("SCHEDULER TEST")
    print("=" * 80)
    
    # Create scheduler
    test_scheduler = MorningReportScheduler()
    
    # Get status
    status = test_scheduler.get_status()
    print(f"Scheduler running: {status['is_running']}")
    print(f"Market status: {status['market_status']}")
    print(f"Is trading day: {status['is_trading_day']}")
    print(f"Next trading day: {status['next_trading_day']}")
    
    print("=" * 80)
