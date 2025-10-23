"""
Stock Universe Loader

Loads a curated list of liquid stocks suitable for VWAP Recovery trading.

Criteria for inclusion:
- Average daily volume > 5M shares
- Market cap > $5B (stability)
- Tight spreads (< $0.10 typical)
- Traded on major exchanges (NYSE, NASDAQ)
- Excludes: penny stocks, ETFs, ADRs with low liquidity

Author: The Luggage Room Boys Fund
Date: October 2025
"""

from typing import List, Dict, Set
import pandas as pd


# Core liquid stock universe (manually curated for quality)
# These are the most liquid, actively traded stocks suitable for scalping

MEGA_CAP = [
    # Tech Giants
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD',
    'NFLX', 'ADBE', 'CRM', 'ORCL', 'INTC', 'CSCO', 'AVGO', 'QCOM',
    
    # Finance
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW',
    
    # Healthcare
    'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'MRK', 'ABT', 'LLY',
    
    # Consumer
    'WMT', 'HD', 'NKE', 'MCD', 'DIS', 'SBUX', 'TGT', 'LOW',
    
    # Industrial
    'BA', 'CAT', 'GE', 'UPS', 'HON', 'MMM', 'RTX',
    
    # Energy
    'XOM', 'CVX', 'COP', 'SLB', 'EOG',
]

LARGE_CAP_TECH = [
    'UBER', 'ABNB', 'SNOW', 'PLTR', 'COIN', 'RBLX', 'U', 'DDOG',
    'NET', 'CRWD', 'ZS', 'OKTA', 'MDB', 'SHOP', 'SQ', 'PYPL',
    'ROKU', 'TWLO', 'ZM', 'DOCU', 'SNAP', 'PINS', 'LYFT', 'DASH',
    'SE', 'MELI', 'BKNG', 'TCOM', 'BABA', 'JD', 'PDD', 'NIO',
]

LARGE_CAP_FINANCE = [
    'V', 'MA', 'AXP', 'SPGI', 'BLK', 'ICE', 'CME', 'MCO',
    'BX', 'KKR', 'APO', 'COIN', 'SOFI', 'AFRM', 'HOOD',
]

LARGE_CAP_HEALTHCARE = [
    'ISRG', 'VRTX', 'GILD', 'REGN', 'BIIB', 'MRNA', 'AMGN',
    'CVS', 'CI', 'HUM', 'ELV', 'ANTM',
]

LARGE_CAP_CONSUMER = [
    'TSLA', 'COST', 'TGT', 'TJX', 'ROST', 'ULTA', 'DG', 'DLTR',
    'LULU', 'DECK', 'TPR', 'RL', 'PVH', 'VFC',
]

LARGE_CAP_INDUSTRIAL = [
    'UNP', 'CSX', 'NSC', 'FDX', 'JBHT', 'ODFL', 'XPO',
    'DE', 'EMR', 'ETN', 'PH', 'ROK', 'DOV',
]

LARGE_CAP_ENERGY = [
    'OXY', 'HAL', 'MPC', 'PSX', 'VLO', 'FANG', 'DVN', 'HES',
]

MID_CAP_HIGH_VOLUME = [
    # Software/Cloud
    'BILL', 'HUBS', 'ESTC', 'DDOG', 'FROG', 'S', 'GTLB',
    
    # Semiconductors
    'MRVL', 'AMAT', 'LRCX', 'KLAC', 'SNPS', 'CDNS', 'ON', 'MPWR',
    
    # Biotech
    'ILMN', 'ALNY', 'BMRN', 'SRPT', 'TECH', 'ARWR', 'IONS',
    
    # Retail/Consumer
    'ETSY', 'W', 'CHWY', 'CVNA', 'FL', 'FIVE', 'OLLI', 'ANF',
    
    # Industrial
    'CARR', 'OTIS', 'GNRC', 'IR', 'FAST', 'SNA', 'TT',
    
    # Financial
    'ALLY', 'SYF', 'COF', 'DFS', 'FITB', 'HBAN', 'KEY', 'RF',
]

GROWTH_STOCKS = [
    # High-growth tech
    'PANW', 'WDAY', 'NOW', 'TEAM', 'DDOG', 'SNOW', 'MDB', 'NET',
    'CRWD', 'ZS', 'S', 'BILL', 'HUBS', 'GTLB', 'FROG',
    
    # EVs and Clean Energy
    'RIVN', 'LCID', 'CHPT', 'BLNK', 'ENPH', 'SEDG', 'RUN',
    
    # Genomics
    'PACB', 'CRSP', 'NTLA', 'BEAM', 'EDIT', 'RXRX',
]

# Excluded categories (informational only - not included in universe)
EXCLUDED_TYPES = {
    'ETFs': ['SPY', 'QQQ', 'IWM', 'DIA', 'VOO', 'VTI'],  # Too stable, not enough patterns
    'Penny Stocks': [],  # Market cap < $1B
    'Low Volume': [],  # ADV < 1M shares
    'Wide Spreads': [],  # Spread > $0.20 typical
}


def get_stock_universe(
    min_market_cap_b: float = 5.0,
    min_avg_volume_m: float = 5.0,
    include_growth: bool = True,
    include_mid_cap: bool = True
) -> List[str]:
    """
    Get the curated stock universe for VWAP Recovery trading.
    
    Args:
        min_market_cap_b: Minimum market cap in billions (default: $5B)
        min_avg_volume_m: Minimum average daily volume in millions (default: 5M)
        include_growth: Include high-growth stocks (default: True)
        include_mid_cap: Include mid-cap stocks (default: True)
    
    Returns:
        List of ticker symbols
        
    Example:
        >>> universe = get_stock_universe()
        >>> print(f"Loaded {len(universe)} stocks")
        >>> print(universe[:10])  # First 10 tickers
    """
    
    # Start with mega caps (always included)
    universe = set(MEGA_CAP)
    
    # Add large caps by category
    universe.update(LARGE_CAP_TECH)
    universe.update(LARGE_CAP_FINANCE)
    universe.update(LARGE_CAP_HEALTHCARE)
    universe.update(LARGE_CAP_CONSUMER)
    universe.update(LARGE_CAP_INDUSTRIAL)
    universe.update(LARGE_CAP_ENERGY)
    
    # Optionally add mid caps
    if include_mid_cap:
        universe.update(MID_CAP_HIGH_VOLUME)
    
    # Optionally add growth stocks
    if include_growth:
        universe.update(GROWTH_STOCKS)
    
    # Convert to sorted list
    universe_list = sorted(list(universe))
    
    return universe_list


def get_universe_by_category() -> Dict[str, List[str]]:
    """
    Get stock universe organized by category for balanced selection.
    
    Returns:
        Dictionary with categories as keys and stock lists as values
        
    Example:
        >>> categories = get_universe_by_category()
        >>> print(f"Tech stocks: {len(categories['tech'])}")
        >>> print(f"Finance stocks: {len(categories['finance'])}")
    """
    
    return {
        'mega_cap': MEGA_CAP,
        'tech': LARGE_CAP_TECH,
        'finance': LARGE_CAP_FINANCE,
        'healthcare': LARGE_CAP_HEALTHCARE,
        'consumer': LARGE_CAP_CONSUMER,
        'industrial': LARGE_CAP_INDUSTRIAL,
        'energy': LARGE_CAP_ENERGY,
        'mid_cap': MID_CAP_HIGH_VOLUME,
        'growth': GROWTH_STOCKS,
    }


def get_conservative_stocks() -> List[str]:
    """
    Get list of conservative, ultra-reliable stocks.
    
    These are mega-cap stocks with:
    - Very high liquidity
    - Low volatility
    - Consistent patterns
    
    Returns:
        List of conservative ticker symbols
    """
    
    conservative = [
        # Ultra-stable tech
        'AAPL', 'MSFT', 'GOOGL', 'JPM', 'JNJ', 'WMT', 'PG',
        
        # Ultra-stable finance
        'V', 'MA', 'BAC', 'WFC',
        
        # Ultra-stable consumer
        'KO', 'PEP', 'MCD', 'NKE',
    ]
    
    return conservative


def get_aggressive_stocks() -> List[str]:
    """
    Get list of aggressive, high-frequency trading candidates.
    
    These stocks have:
    - Very high intraday volatility
    - Many VWAP patterns per day
    - Higher risk but more opportunities
    
    Returns:
        List of aggressive ticker symbols
    """
    
    aggressive = [
        # High volatility tech
        'TSLA', 'NVDA', 'AMD', 'COIN', 'RBLX', 'PLTR',
        
        # Volatile growth
        'RIVN', 'LCID', 'SNOW', 'NET', 'CRWD',
        
        # Meme/momentum stocks
        'GME', 'AMC',  # Only if volume criteria met
    ]
    
    return aggressive


def validate_universe(tickers: List[str]) -> Dict[str, any]:
    """
    Validate the stock universe and provide statistics.
    
    Args:
        tickers: List of ticker symbols to validate
    
    Returns:
        Dictionary with validation stats
    """
    
    stats = {
        'total_tickers': len(tickers),
        'unique_tickers': len(set(tickers)),
        'duplicates': len(tickers) - len(set(tickers)),
        'categories': {},
    }
    
    # Count by category
    categories = get_universe_by_category()
    for category, stocks in categories.items():
        in_category = [t for t in tickers if t in stocks]
        stats['categories'][category] = len(in_category)
    
    return stats


def get_sample_tickers(n: int = 10) -> List[str]:
    """
    Get a small sample of tickers for testing.
    
    Args:
        n: Number of tickers to return (default: 10)
    
    Returns:
        List of n ticker symbols
    """
    
    # Return a diverse sample
    sample = [
        'AAPL',   # Mega cap tech
        'MSFT',   # Mega cap tech
        'TSLA',   # High volatility
        'JPM',    # Finance
        'NVDA',   # Semiconductors
        'AMD',    # Semiconductors
        'META',   # Social media
        'NFLX',   # Streaming
        'BA',     # Industrial
        'XOM',    # Energy
    ]
    
    return sample[:n]


if __name__ == "__main__":
    print("Stock Universe Loader")
    print("=" * 60)
    print()
    
    # Get full universe
    universe = get_stock_universe()
    print(f"📊 Full Universe: {len(universe)} stocks")
    print()
    
    # Get validation stats
    stats = validate_universe(universe)
    print(f"✅ Validation:")
    print(f"   Total tickers: {stats['total_tickers']}")
    print(f"   Unique tickers: {stats['unique_tickers']}")
    print(f"   Duplicates: {stats['duplicates']}")
    print()
    
    # Show breakdown by category
    print(f"📈 Breakdown by Category:")
    for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"   {category}: {count}")
    print()
    
    # Show samples
    print(f"🎯 Conservative Stocks ({len(get_conservative_stocks())}):")
    print(f"   {', '.join(get_conservative_stocks()[:10])}")
    print()
    
    print(f"⚡ Aggressive Stocks ({len(get_aggressive_stocks())}):")
    print(f"   {', '.join(get_aggressive_stocks()[:10])}")
    print()
    
    print(f"🧪 Sample for Testing:")
    print(f"   {', '.join(get_sample_tickers(10))}")
    print()
