"""
Time-of-Day Performance Profile Analyzer

Analyzes 20-day historical data to build stock-specific time profiles.
Each profile contains:
- Pattern frequency per time window
- Win rate per time window
- Average duration per time window
- Dead zone rate per time window
- Recommended adaptive timeouts
"""

from typing import Dict, List, Tuple
from datetime import time, datetime, timedelta
import pandas as pd
import numpy as np

# Time windows (Eastern Time)
TIME_WINDOWS = {
    'market_open': (time(9, 31), time(10, 0)),
    'mid_morning': (time(10, 0), time(11, 30)),
    'lunch': (time(11, 30), time(13, 30)),
    'afternoon': (time(13, 30), time(15, 30)),
    'market_close': (time(15, 30), time(16, 0))
}


def get_time_window(timestamp: datetime) -> str:
    """
    Classify timestamp into one of 5 time windows.
    
    Args:
        timestamp: datetime object (Eastern Time)
        
    Returns:
        Window name: 'market_open', 'mid_morning', 'lunch', 'afternoon', 'market_close'
    """
    t = timestamp.time()
    
    for window_name, (start, end) in TIME_WINDOWS.items():
        if start <= t < end:
            return window_name
    
    # Fallback (shouldn't happen during market hours)
    return 'afternoon'


def analyze_time_profiles(ticker: str, patterns: List[Dict]) -> Dict:
    """
    Build time-of-day performance profiles from historical patterns.
    
    Args:
        ticker: Stock symbol
        patterns: List of pattern dicts from pattern_detector.py
                 Each pattern must have 'timestamp', 'outcome', 'duration_minutes'
    
    Returns:
        {
            'market_open': {
                'pattern_count': 15,
                'win_rate': 0.73,
                'avg_duration_minutes': 6.2,
                'dead_zone_rate': 0.13,
                'recommended_timeout_minutes': 8.0
            },
            'mid_morning': {...},
            'lunch': {...},
            'afternoon': {...},
            'market_close': {...},
            'overall': {...}
        }
    """
    # Initialize profiles
    profiles = {window: {
        'pattern_count': 0,
        'wins': 0,
        'losses': 0,
        'dead_zones': 0,
        'durations': []
    } for window in TIME_WINDOWS.keys()}
    
    profiles['overall'] = {
        'pattern_count': 0,
        'wins': 0,
        'losses': 0,
        'dead_zones': 0,
        'durations': []
    }
    
    # Classify patterns by time window
    for pattern in patterns:
        # Determine time window
        window = get_time_window(pattern['timestamp'])
        
        # Update window stats
        profiles[window]['pattern_count'] += 1
        profiles['overall']['pattern_count'] += 1
        
        # Track outcome
        if pattern['outcome'] == 'WIN':
            profiles[window]['wins'] += 1
            profiles['overall']['wins'] += 1
        elif pattern['outcome'] == 'LOSS':
            profiles[window]['losses'] += 1
            profiles['overall']['losses'] += 1
        elif pattern['outcome'] == 'DEAD_ZONE':
            profiles[window]['dead_zones'] += 1
            profiles['overall']['dead_zones'] += 1
        
        # Track duration
        if 'duration_minutes' in pattern:
            profiles[window]['durations'].append(pattern['duration_minutes'])
            profiles['overall']['durations'].append(pattern['duration_minutes'])
    
    # Calculate metrics for each window
    for window_name, stats in profiles.items():
        total = stats['pattern_count']
        
        if total == 0:
            # No patterns in this window
            profiles[window_name] = {
                'pattern_count': 0,
                'win_rate': 0.0,
                'avg_duration_minutes': 0.0,
                'dead_zone_rate': 0.0,
                'recommended_timeout_minutes': 8.0,  # Default fallback
                'opportunity_score': 0.0
            }
            continue
        
        # Win rate
        win_rate = stats['wins'] / total if total > 0 else 0.0
        
        # Dead zone rate
        dead_zone_rate = stats['dead_zones'] / total if total > 0 else 0.0
        
        # Average duration
        avg_duration = np.mean(stats['durations']) if stats['durations'] else 8.0
        
        # Recommended timeout (adaptive)
        # Formula: avg_duration * (1 + dead_zone_rate) + 2 minutes buffer
        recommended_timeout = avg_duration * (1 + dead_zone_rate) + 2.0
        recommended_timeout = min(recommended_timeout, 15.0)  # Cap at 15 minutes
        
        # Opportunity score (higher = better window)
        # Formula: win_rate * (1 - dead_zone_rate) * pattern_frequency
        pattern_frequency = total / 20  # Patterns per day (20 days total)
        opportunity_score = win_rate * (1 - dead_zone_rate) * pattern_frequency
        
        profiles[window_name] = {
            'pattern_count': total,
            'win_rate': round(win_rate, 3),
            'avg_duration_minutes': round(avg_duration, 2),
            'dead_zone_rate': round(dead_zone_rate, 3),
            'recommended_timeout_minutes': round(recommended_timeout, 1),
            'opportunity_score': round(opportunity_score, 3)
        }
    
    return profiles


def calculate_adaptive_timeout(
    stock_profile: Dict,
    milestone: str,
    current_time: datetime,
    pattern_strength: float = 1.0
) -> float:
    """
    Calculate adaptive timeout for current position.
    
    Args:
        stock_profile: Time profile dict from analyze_time_profiles()
        milestone: 'ENTRY', 'TARGET_1', 'TARGET_2'
        current_time: Current datetime (Eastern Time)
        pattern_strength: Quality multiplier (0.5-1.5)
                         Higher = stronger pattern = longer timeout allowed
    
    Returns:
        Timeout in minutes (adaptive based on time-of-day + pattern strength)
    """
    # Get current time window
    window = get_time_window(current_time)
    
    # Get base timeout for this window
    if window not in stock_profile or stock_profile[window]['pattern_count'] == 0:
        # No data for this window, use overall
        base_timeout = stock_profile.get('overall', {}).get('recommended_timeout_minutes', 8.0)
    else:
        base_timeout = stock_profile[window]['recommended_timeout_minutes']
    
    # Milestone multipliers
    milestone_multipliers = {
        'ENTRY': 1.0,      # Full timeout for initial entry
        'TARGET_1': 0.7,   # 70% of base timeout after hitting T1
        'TARGET_2': 0.5    # 50% of base timeout after hitting T2
    }
    
    milestone_mult = milestone_multipliers.get(milestone, 1.0)
    
    # Pattern strength adjustment
    # Strong patterns (1.2-1.5) get more time
    # Weak patterns (0.5-0.8) get less time
    strength_mult = pattern_strength
    
    # Calculate final adaptive timeout
    adaptive_timeout = base_timeout * milestone_mult * strength_mult
    
    # Safety bounds
    adaptive_timeout = max(3.0, min(adaptive_timeout, 15.0))
    
    return round(adaptive_timeout, 1)


def get_best_trading_windows(stock_profile: Dict, min_patterns: int = 5) -> List[str]:
    """
    Identify the best time windows for trading this stock.
    
    Args:
        stock_profile: Time profile dict from analyze_time_profiles()
        min_patterns: Minimum pattern count to consider window viable
    
    Returns:
        List of window names sorted by opportunity score (best first)
    """
    windows_with_scores = []
    
    for window_name in TIME_WINDOWS.keys():
        if window_name not in stock_profile:
            continue
        
        profile = stock_profile[window_name]
        
        # Skip windows with insufficient data
        if profile['pattern_count'] < min_patterns:
            continue
        
        windows_with_scores.append({
            'window': window_name,
            'score': profile['opportunity_score'],
            'win_rate': profile['win_rate'],
            'dead_zone_rate': profile['dead_zone_rate']
        })
    
    # Sort by opportunity score (descending)
    windows_with_scores.sort(key=lambda x: x['score'], reverse=True)
    
    return [w['window'] for w in windows_with_scores]


def calculate_time_based_position_size_multiplier(
    stock_profile: Dict,
    current_time: datetime,
    base_multiplier: float = 1.0
) -> float:
    """
    Adjust position size based on time-of-day performance.
    
    Args:
        stock_profile: Time profile dict from analyze_time_profiles()
        current_time: Current datetime (Eastern Time)
        base_multiplier: Starting multiplier (default 1.0)
    
    Returns:
        Position size multiplier (0.5-1.5)
        - 1.5x during best windows (high win rate, low dead zones)
        - 1.0x during average windows
        - 0.5x during poor windows (low win rate, high dead zones)
    """
    window = get_time_window(current_time)
    
    # Get window profile
    if window not in stock_profile or stock_profile[window]['pattern_count'] == 0:
        return base_multiplier
    
    profile = stock_profile[window]
    
    # Calculate quality multiplier
    # High win rate + low dead zone rate = higher multiplier
    win_rate = profile['win_rate']
    dead_zone_rate = profile['dead_zone_rate']
    
    # Quality score (0-1)
    quality = win_rate * (1 - dead_zone_rate)
    
    # Map quality to multiplier
    # quality > 0.6 → 1.5x
    # quality 0.4-0.6 → 1.0x
    # quality < 0.4 → 0.5x
    if quality > 0.6:
        multiplier = 1.5
    elif quality > 0.4:
        multiplier = 1.0
    else:
        multiplier = 0.5
    
    return multiplier * base_multiplier


def generate_time_profile_summary(stock_profile: Dict) -> str:
    """
    Generate human-readable summary of stock's time profiles.
    
    Args:
        stock_profile: Time profile dict from analyze_time_profiles()
    
    Returns:
        Formatted string summary
    """
    best_windows = get_best_trading_windows(stock_profile)
    
    summary_lines = [
        f"Overall: {stock_profile['overall']['pattern_count']} patterns, "
        f"{stock_profile['overall']['win_rate']:.1%} win rate, "
        f"{stock_profile['overall']['dead_zone_rate']:.1%} dead zones",
        "",
        "Best Trading Windows:"
    ]
    
    for window in best_windows[:3]:  # Top 3
        profile = stock_profile[window]
        summary_lines.append(
            f"  {window:15} - Win: {profile['win_rate']:.1%}, "
            f"Dead Zone: {profile['dead_zone_rate']:.1%}, "
            f"Avg Duration: {profile['avg_duration_minutes']:.1f}min"
        )
    
    return "\n".join(summary_lines)


# Example usage
if __name__ == "__main__":
    # Mock pattern data for testing
    mock_patterns = [
        {
            'timestamp': datetime(2025, 10, 1, 9, 45),
            'outcome': 'WIN',
            'duration_minutes': 5.2
        },
        {
            'timestamp': datetime(2025, 10, 1, 10, 30),
            'outcome': 'WIN',
            'duration_minutes': 7.1
        },
        {
            'timestamp': datetime(2025, 10, 1, 14, 15),
            'outcome': 'DEAD_ZONE',
            'duration_minutes': 11.3
        },
    ]
    
    # Analyze
    profiles = analyze_time_profiles('AAPL', mock_patterns)
    
    # Print summary
    print(generate_time_profile_summary(profiles))
    
    # Test adaptive timeout
    timeout = calculate_adaptive_timeout(
        stock_profile=profiles,
        milestone='ENTRY',
        current_time=datetime(2025, 10, 27, 10, 30),
        pattern_strength=1.2
    )
    print(f"\nAdaptive timeout at 10:30 AM: {timeout} minutes")
