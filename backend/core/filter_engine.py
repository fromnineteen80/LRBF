"""
Filter System - 7 Strategy Presets for Phase 0

Each preset represents a different trading approach with specific filter configurations.
Used by Morning Report to generate 7 forecast scenarios.

Author: The Luggage Room Boys Fund  
Date: October 2025 - Phase 0
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class FilterPreset:
    """Configuration for a trading strategy preset."""
    name: str
    description: str
    
    # Pattern selection filters
    min_decline_pct: float = 1.0  # Minimum decline to trigger pattern
    
    # Entry filters
    entry_threshold_pct: float = 0.5  # Entry confirmation threshold
    require_volume_confirmation: bool = False  # Require volume spike
    volume_multiplier: float = 1.5  # Volume must be Nx average
    
    # Quality filters
    check_vwap_proximity: bool = False  # Pattern must be near VWAP
    vwap_proximity_pct: float = 2.0  # Within X% of VWAP
    
    # Timing filters
    avoid_first_30min: bool = False  # Skip first 30 min of trading
    avoid_last_30min: bool = False  # Skip last 30 min of trading
    
    # Exit parameters (same for all presets per explainer)
    target_1_pct: float = 0.75  # T1 target
    target_2_pct: float = 1.75  # T2 target
    stop_loss_pct: float = 0.5  # Stop loss
    cross_threshold_pct: float = 1.0  # CROSS threshold


# =============================================================================
# 7 PRESETS FOR MORNING REPORT
# =============================================================================

PRESETS = {
    'default': FilterPreset(
        name='Default (3-Step)',
        description='No filters, baseline performance. Pure pattern win rate.',
        min_decline_pct=1.0,
        entry_threshold_pct=0.5,
        require_volume_confirmation=False,
        check_vwap_proximity=False,
        avoid_first_30min=False,
        avoid_last_30min=False
    ),
    
    'conservative': FilterPreset(
        name='Conservative (3-Step)',
        description='All filters ON, tight thresholds. Maximize win rate, lower frequency.',
        min_decline_pct=1.2,  # Higher decline threshold
        entry_threshold_pct=0.5,
        require_volume_confirmation=True,
        volume_multiplier=2.0,  # Stronger volume required
        check_vwap_proximity=True,
        vwap_proximity_pct=1.5,  # Must be within 1.5% of VWAP
        avoid_first_30min=True,
        avoid_last_30min=True
    ),
    
    'aggressive': FilterPreset(
        name='Aggressive (3-Step)',
        description='Minimal filters, loose thresholds. Maximize trade count.',
        min_decline_pct=0.8,  # Lower decline threshold
        entry_threshold_pct=0.5,
        require_volume_confirmation=False,
        check_vwap_proximity=False,
        avoid_first_30min=False,
        avoid_last_30min=False
    ),
    
    'choppy': FilterPreset(
        name='Choppy Market (3-Step)',
        description='S/R focused, neutral trend. Optimized for range-bound markets.',
        min_decline_pct=1.0,
        entry_threshold_pct=0.5,
        require_volume_confirmation=True,
        volume_multiplier=1.5,
        check_vwap_proximity=True,
        vwap_proximity_pct=2.5,  # Allow wider VWAP range
        avoid_first_30min=True,  # Avoid opening volatility
        avoid_last_30min=False
    ),
    
    'trending': FilterPreset(
        name='Trending Market (3-Step)',
        description='Momentum focused, trend-aligned. Optimized for directional markets.',
        min_decline_pct=1.0,
        entry_threshold_pct=0.5,
        require_volume_confirmation=True,
        volume_multiplier=1.8,  # Higher volume for momentum confirmation
        check_vwap_proximity=False,  # Don't restrict VWAP proximity in trends
        avoid_first_30min=True,
        avoid_last_30min=False
    ),
    
    'abtest': FilterPreset(
        name='AB Test (3-Step)',
        description='Experimental filter combinations. Test new ideas.',
        min_decline_pct=1.0,
        entry_threshold_pct=0.5,
        require_volume_confirmation=True,
        volume_multiplier=1.5,
        check_vwap_proximity=True,
        vwap_proximity_pct=2.0,
        avoid_first_30min=False,
        avoid_last_30min=False
    ),
    
    'vwap_breakout': FilterPreset(
        name='VWAP Breakout',
        description='Different pattern entirely. Captures institutional rebalancing.',
        min_decline_pct=1.0,  # Not used for VWAP breakout
        entry_threshold_pct=0.5,  # 0.5% above VWAP
        require_volume_confirmation=True,  # Always required for VWAP breakout
        volume_multiplier=1.5,
        check_vwap_proximity=False,  # N/A - pattern IS the VWAP proximity
        avoid_first_30min=True,
        avoid_last_30min=True
    )
}


class FilterEngine:
    """
    Filter engine for evaluating patterns based on preset configurations.
    
    Usage:
        engine = FilterEngine(preset='conservative')
        passed, reason = engine.should_trade(pattern_data, market_data)
    """
    
    def __init__(self, preset_name: str = 'default'):
        """
        Initialize filter engine with a preset.
        
        Args:
            preset_name: One of: default, conservative, aggressive, 
                        choppy, trending, abtest, vwap_breakout
        """
        if preset_name not in PRESETS:
            raise ValueError(f"Unknown preset: {preset_name}. Must be one of {list(PRESETS.keys())}")
        
        self.preset_name = preset_name
        self.preset = PRESETS[preset_name]
    
    def should_trade_pattern(
        self,
        pattern_data: Dict,
        market_data: Optional[Dict] = None,
        current_time = None
    ) -> tuple[bool, str]:
        """
        Determine if pattern should be traded based on preset filters.
        
        Args:
            pattern_data: Pattern information (price, volume, vwap, etc.)
            market_data: Market context (optional)
            current_time: Current market time (optional)
        
        Returns:
            (should_trade: bool, reason: str)
        """
        # Default preset - no filters, always trade
        if self.preset_name == 'default':
            return True, "Default preset - no filters"
        
        # Check volume confirmation if required
        if self.preset.require_volume_confirmation:
            volume_ratio = pattern_data.get('volume_ratio', 0)
            if volume_ratio < self.preset.volume_multiplier:
                return False, f"Volume too low: {volume_ratio:.1f}x < {self.preset.volume_multiplier}x required"
        
        # Check VWAP proximity if required
        if self.preset.check_vwap_proximity:
            entry_price = pattern_data.get('entry_price', 0)
            vwap = pattern_data.get('vwap', 0)
            
            if vwap > 0:
                vwap_distance_pct = abs((entry_price - vwap) / vwap) * 100
                if vwap_distance_pct > self.preset.vwap_proximity_pct:
                    return False, f"Too far from VWAP: {vwap_distance_pct:.1f}% > {self.preset.vwap_proximity_pct}%"
        
        # Check timing filters
        if current_time:
            from datetime import time as time_class
            
            market_time = current_time.time()
            market_open = time_class(9, 30)
            first_30min_end = time_class(10, 0)
            last_30min_start = time_class(15, 30)
            market_close = time_class(16, 0)
            
            # Check first 30 minutes
            if self.preset.avoid_first_30min:
                if market_open <= market_time < first_30min_end:
                    return False, "Within first 30 minutes - preset avoids opening volatility"
            
            # Check last 30 minutes
            if self.preset.avoid_last_30min:
                if last_30min_start <= market_time < market_close:
                    return False, "Within last 30 minutes - preset avoids closing volatility"
        
        return True, f"All {self.preset_name} filters passed"
    
    def get_preset_info(self) -> Dict:
        """Get information about current preset."""
        return {
            'name': self.preset.name,
            'preset_key': self.preset_name,
            'description': self.preset.description,
            'min_decline_pct': self.preset.min_decline_pct,
            'entry_threshold_pct': self.preset.entry_threshold_pct,
            'require_volume': self.preset.require_volume_confirmation,
            'volume_multiplier': self.preset.volume_multiplier,
            'check_vwap': self.preset.check_vwap_proximity,
            'vwap_proximity_pct': self.preset.vwap_proximity_pct,
            'avoid_first_30min': self.preset.avoid_first_30min,
            'avoid_last_30min': self.preset.avoid_last_30min,
            'target_1_pct': self.preset.target_1_pct,
            'target_2_pct': self.preset.target_2_pct,
            'stop_loss_pct': self.preset.stop_loss_pct
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_preset(preset_name: str) -> FilterPreset:
    """Get a preset configuration by name."""
    if preset_name not in PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}")
    return PRESETS[preset_name]


def list_presets() -> list[str]:
    """List all available preset names."""
    return list(PRESETS.keys())


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("Testing Filter Engine with 7 Presets...")
    print("=" * 60)
    
    # List all presets
    print("\nAvailable Presets:")
    for preset_name in list_presets():
        preset = get_preset(preset_name)
        print(f"  • {preset.name}")
        print(f"    {preset.description}")
    
    # Test each preset
    print("\n" + "=" * 60)
    print("Testing Pattern Evaluation:")
    
    pattern_data = {
        'entry_price': 150.50,
        'vwap': 150.00,
        'volume_ratio': 2.0
    }
    
    for preset_name in list_presets():
        engine = FilterEngine(preset_name)
        should_trade, reason = engine.should_trade_pattern(pattern_data)
        
        status = "✅ TRADE" if should_trade else "❌ SKIP"
        print(f"\n{engine.preset.name}:")
        print(f"  {status} - {reason}")
    
    print("\n" + "=" * 60)
    print("✅ Filter Engine test complete")
