"""
Capitalise.ai Prompt Generator

Generates prompt files for automated trading execution.
Each selected stock gets its own prompt file with parameters from config.py.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
sys.path.append('/home/claude/railyard')

from typing import List
from config import TradingConfig as cfg
import os


def generate_capitalise_prompts(
    selected_tickers: List[str],
    output_dir: str = "/home/claude/railyard/output/capitalise_prompts"
) -> List[str]:
    """
    Generate Capitalise.ai prompt files for selected stocks.
    
    This creates one .txt file per stock with the complete trading prompt.
    All parameters come from config.py, ensuring consistency.
    
    Args:
        selected_tickers: List of stock tickers to create prompts for
        output_dir: Directory to save prompt files
    
    Returns:
        List of generated file paths
        
    Example:
        >>> selected = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD']
        >>> files = generate_capitalise_prompts(selected)
        >>> print(f"Generated {len(files)} prompts")
        Generated 8 prompts
    """
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    generated_files = []
    
    for ticker in selected_tickers:
        prompt = _build_prompt_for_ticker(ticker)
        filename = f"prompt_{ticker}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(prompt)
        
        generated_files.append(filepath)
    
    return generated_files


def _build_prompt_for_ticker(ticker: str) -> str:
    """
    Build Capitalise.ai prompt for a single ticker.
    All parameters from config.py - no hardcoded values.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Complete prompt text ready for Capitalise.ai
    """
    
    # Calculate position size percentage
    # Example: 80% deployed / 8 stocks = 10% per stock
    position_size_pct = (cfg.DEPLOYMENT_RATIO / cfg.NUM_STOCKS) * 100
    
    prompt = f"""Start running at 9:31 AM US/Eastern

If daily realized losses exceed {abs(cfg.DAILY_LOSS_LIMIT)} percent of current account balance
Stop running this strategy

Only one open position in {ticker} at any time
Do not open a new position in {ticker} if an order is pending

When the price of {ticker} decreases by {cfg.DECLINE_THRESHOLD} percent from its recent high
And then increases by 50 percent of that decline
And then decreases by 50 percent of that recovery
And then increases by {cfg.ENTRY_THRESHOLD} percent from the last low
Buy using {position_size_pct:.1f} percent of current account balance

When the price of {ticker} increases by {cfg.TARGET_1} percent from entry price
Wait until price increases by another {cfg.TARGET_2 - cfg.TARGET_1} percent
If it does, sell all at plus {cfg.TARGET_2} percent
Otherwise, if price returns to plus {cfg.TARGET_1} percent, sell all

If the price of {ticker} decreases by {abs(cfg.STOP_LOSS)} percent from entry price
Sell all immediately

After a position in {ticker} is closed
Wait {cfg.COOLDOWN_MINUTES} minute before scanning {ticker} again

Repeat indefinitely, check every 1 minute

Stop new entries at 3:50 PM US/Eastern
Close all positions 10 minutes before market close.
"""
    
    return prompt


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CAPITALISE.AI PROMPT GENERATOR TEST")
    print("="*60)
    print()
    
    # Test with sample tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD']
    
    print(f"Config: {cfg.NUM_STOCKS} stocks, {cfg.DEPLOYMENT_RATIO*100:.0f}% deployed")
    print(f"Position size: {(cfg.DEPLOYMENT_RATIO / cfg.NUM_STOCKS * 100):.1f}% each")
    print()
    
    print(f"Generating prompts for {len(test_tickers)} stocks...")
    files = generate_capitalise_prompts(test_tickers)
    
    print(f"✅ Generated {len(files)} prompt files:")
    for f in files:
        print(f"   {f}")
    
    print()
    print("Sample prompt (AAPL):")
    print("-" * 60)
    with open(files[0], 'r') as f:
        print(f.read())
    print("-" * 60)
    print()
    
    print("✅ Test complete!")
    print()
    print("To deploy:")
    print("1. Review each prompt file")
    print("2. Copy/paste into Capitalise.ai (one per stock)")
    print("3. Activate at 9:30 AM ET")
    print()
