#!/usr/bin/env python3
"""
Relaxed Scaling Configuration for Signal Generation

Configuration optimized for generating more signals while maintaining quality:
- More relaxed filtering thresholds
- Improved technical indicator handling
- Better signal passage rates
"""

import os
from typing import Dict, List, Any

class RelaxedScalingConfig:
    """
    Relaxed configuration for better signal generation.
    Balances signal quantity with quality control.
    """
    
    # ==========================================
    # CORE SCALING PARAMETERS (RELAXED)
    # ==========================================
    
    # Smart Filtering Thresholds - More Permissive
    MIN_VOLATILITY_THRESHOLD: float = 5.0      # 5%+ 24h change (was 8%)
    MIN_VOLUME_THRESHOLD: int = 1500000         # $1.5M+ volume (was $3M)
    MAX_PAIRS_FOR_ANALYSIS: int = 25            # Top 25 pairs (was 20)
    
    # Staged Analysis Configuration - More Candidates
    STAGE1_MAX_PAIRS: int = 60                  # Quick scan up to 60 pairs (was 50)
    STAGE2_MAX_PAIRS: int = 20                  # Detailed analysis for 20 pairs (was 15)
    STAGE3_MAX_PAIRS: int = 8                   # Full signals for 8 pairs (was 5)
    
    # ==========================================
    # SIGNAL QUALITY THRESHOLDS (RELAXED)
    # ==========================================
    
    # Quick Scan Thresholds (Stage 1) - More Permissive
    QUICK_SCAN_MIN_SCORE: float = 0.2           # Lower minimum score (was 0.3)
    QUICK_SCAN_MIN_RSI_DIVERGENCE: int = 7      # 7 point RSI move (was 10)
    QUICK_SCAN_MIN_VOLUME_SPIKE: float = 1.2    # 1.2x volume spike (was 1.5x)
    QUICK_SCAN_MIN_MOMENTUM: float = 0.002      # 0.2% price momentum (was 0.3%)
    
    # Detailed Analysis Thresholds (Stage 2) - Much More Relaxed
    DETAILED_MIN_SIGNAL_STRENGTH: float = 1.2   # Lower signal strength (was 1.8)
    DETAILED_MIN_CONFLUENCE_POINTS: int = 1     # Only 1 confluence point (was 2)
    DETAILED_MIN_TREND_ALIGNMENT: float = 0.4   # Lower trend alignment (was 0.6)
    
    # Final Signal Thresholds (Stage 3) - Relaxed but Safe
    FINAL_MIN_CONFIDENCE: float = 0.45          # Lower confidence threshold (was 0.65)
    FINAL_MIN_QUALITY_SCORE: int = 55           # Lower quality score (was 70)
    
    # ==========================================
    # API RATE LIMITING
    # ==========================================
    
    # Request Rate Limiting
    MAX_CONCURRENT_API_CALLS: int = 12          # Slightly more concurrent requests
    API_REQUEST_DELAY_MS: int = 80              # Slightly faster requests
    BATCH_SIZE: int = 25                        # Larger batches
    API_TIMEOUT_SECONDS: int = 20               # Longer timeout
    
    # Circuit Breaker Settings
    API_FAILURE_THRESHOLD: int = 8              # More tolerance for failures
    CIRCUIT_BREAKER_TIMEOUT: int = 45           # Shorter cooldown
    
    # ==========================================
    # CACHING STRATEGY
    # ==========================================
    
    # Cache TTL (Time To Live) in seconds
    CACHE_TTL_TICKER: int = 25                  # Slightly shorter for fresher data
    CACHE_TTL_KLINES_SHORT: int = 45            # Shorter cache for active timeframes
    CACHE_TTL_KLINES_MEDIUM: int = 90           # 
    CACHE_TTL_KLINES_LONG: int = 240            # 
    CACHE_TTL_ANALYSIS: int = 180               # Shorter analysis cache
    
    # ==========================================
    # MARKET CONDITIONS ADAPTATION (RELAXED)
    # ==========================================
    
    # High Volatility Market Adjustments
    HIGH_VOLATILITY_THRESHOLD: float = 12.0     # Higher threshold before restrictions
    HIGH_VOL_VOLATILITY_MULTIPLIER: float = 1.1 # Less restrictive multiplier
    HIGH_VOL_VOLUME_MULTIPLIER: float = 1.3     # Lower volume requirements
    HIGH_VOL_PAIRS_REDUCTION: int = -3          # Smaller reduction
    
    # Low Volatility Market Adjustments
    LOW_VOLATILITY_THRESHOLD: float = 2.5       # Lower threshold for relaxation
    LOW_VOL_VOLATILITY_MULTIPLIER: float = 0.7  # More relaxed in quiet markets
    LOW_VOL_VOLUME_MULTIPLIER: float = 0.6      # Much lower volume requirements
    LOW_VOL_PAIRS_INCREASE: int = 8             # More pairs in quiet markets
    
    # ==========================================
    # ENHANCED TECHNICAL INDICATOR SETTINGS
    # ==========================================
    
    # RSI Settings
    RSI_OVERSOLD_LEVEL: int = 35               # More relaxed oversold (was 30)
    RSI_OVERBOUGHT_LEVEL: int = 65             # More relaxed overbought (was 70)
    RSI_DIVERGENCE_MIN_BARS: int = 5           # Shorter divergence period
    
    # MACD Settings
    MACD_SIGNAL_SENSITIVITY: float = 0.8       # More sensitive signal detection
    MACD_HISTOGRAM_THRESHOLD: float = 0.1      # Lower threshold for histogram
    
    # Volume Analysis
    VOLUME_SPIKE_THRESHOLD: float = 1.3         # Lower volume spike threshold
    VOLUME_TREND_PERIODS: int = 10              # Shorter volume trend analysis
    
    # ==========================================
    # POSITION MANAGEMENT (RELAXED)
    # ==========================================
    
    # Position Limits
    MAX_CONCURRENT_POSITIONS: int = 4           # Allow one more position
    MAX_DAILY_TRADES: int = 8                   # More trades allowed
    POSITION_SIZE_PCT: float = 2.5              # Slightly larger positions
    MAX_PORTFOLIO_HEAT: float = 10.0            # More total risk allowed
    
    # Risk Management
    MAX_LEVERAGE: int = 15                      # Higher leverage allowed
    DEFAULT_STOP_LOSS_PCT: float = 1.8          # Wider stop loss
    CORRELATION_LIMIT_ENABLED: bool = True      # Keep correlation limits
    
    # ==========================================
    # DEPLOYMENT MODES (RELAXED VERSIONS)
    # ==========================================
    
    @classmethod
    def get_signal_friendly_mode(cls) -> Dict[str, Any]:
        """Configuration optimized for signal generation."""
        return {
            "max_pairs_for_analysis": 30,
            "stage1_max_pairs": 70,
            "stage2_max_pairs": 25,
            "stage3_max_pairs": 10,
            "min_volatility_threshold": 4.0,
            "min_volume_threshold": 1000000,
            "detailed_min_signal_strength": 1.0,
            "detailed_min_confluence_points": 1,
            "final_min_confidence": 0.35,
            "final_min_quality_score": 45,
            "description": "Signal-friendly mode for maximum opportunity discovery"
        }
    
    @classmethod
    def get_balanced_relaxed_mode(cls) -> Dict[str, Any]:
        """Balanced relaxed configuration (recommended)."""
        return {
            "max_pairs_for_analysis": cls.MAX_PAIRS_FOR_ANALYSIS,
            "stage1_max_pairs": cls.STAGE1_MAX_PAIRS,
            "stage2_max_pairs": cls.STAGE2_MAX_PAIRS,
            "stage3_max_pairs": cls.STAGE3_MAX_PAIRS,
            "min_volatility_threshold": cls.MIN_VOLATILITY_THRESHOLD,
            "min_volume_threshold": cls.MIN_VOLUME_THRESHOLD,
            "detailed_min_signal_strength": cls.DETAILED_MIN_SIGNAL_STRENGTH,
            "detailed_min_confluence_points": cls.DETAILED_MIN_CONFLUENCE_POINTS,
            "final_min_confidence": cls.FINAL_MIN_CONFIDENCE,
            "final_min_quality_score": cls.FINAL_MIN_QUALITY_SCORE,
            "description": "Balanced relaxed mode for optimal signal generation"
        }
    
    @classmethod
    def get_quality_focused_mode(cls) -> Dict[str, Any]:
        """Higher quality but still more relaxed than original strict mode."""
        return {
            "max_pairs_for_analysis": 20,
            "stage1_max_pairs": 45,
            "stage2_max_pairs": 15,
            "stage3_max_pairs": 6,
            "min_volatility_threshold": 6.0,
            "min_volume_threshold": 2000000,
            "detailed_min_signal_strength": 1.4,
            "detailed_min_confluence_points": 2,
            "final_min_confidence": 0.55,
            "final_min_quality_score": 60,
            "description": "Quality-focused mode with relaxed thresholds"
        }
    
    # ==========================================
    # PRIORITY PAIRS (EXPANDED LIST)
    # ==========================================
    
    PRIORITY_PAIRS: List[str] = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
        "SOLUSDT", "LUNAUSDT", "AVAXUSDT", "DOGEUSDT", "MATICUSDT", 
        "DOTUSDT", "LTCUSDT", "LINKUSDT", "BCHUSD", "UNIUSDT",
        "ATOMUSDT", "FTMUSDT", "MANAUSDT", "SANDUSDT", "AXSUSDT"
    ]
    
    # ==========================================
    # VALIDATION AND MONITORING
    # ==========================================
    
    @classmethod
    def validate_relaxed_config(cls) -> Dict[str, bool]:
        """Validate the relaxed configuration."""
        checks = {
            "reasonable_thresholds": cls.MIN_VOLATILITY_THRESHOLD > 0,
            "progressive_stages": cls.STAGE1_MAX_PAIRS > cls.STAGE2_MAX_PAIRS > cls.STAGE3_MAX_PAIRS,
            "api_limits_safe": cls.MAX_CONCURRENT_API_CALLS <= 20,
            "signal_thresholds_relaxed": cls.DETAILED_MIN_SIGNAL_STRENGTH < 1.8,
            "confidence_reasonable": 0.3 <= cls.FINAL_MIN_CONFIDENCE <= 0.7
        }
        return checks
    
    @classmethod
    def get_optimization_summary(cls) -> Dict[str, Any]:
        """Get summary of relaxed optimizations."""
        return {
            "configuration_type": "relaxed_scaling",
            "optimizations": {
                "volatility_threshold": f"Reduced to {cls.MIN_VOLATILITY_THRESHOLD}% (from 8%)",
                "volume_threshold": f"Reduced to ${cls.MIN_VOLUME_THRESHOLD/1000000:.1f}M (from $3M)",
                "signal_strength": f"Reduced to {cls.DETAILED_MIN_SIGNAL_STRENGTH} (from 1.8)",
                "confluence_points": f"Reduced to {cls.DETAILED_MIN_CONFLUENCE_POINTS} (from 2)",
                "confidence_threshold": f"Reduced to {cls.FINAL_MIN_CONFIDENCE} (from 0.65)",
                "quality_score": f"Reduced to {cls.FINAL_MIN_QUALITY_SCORE} (from 70)"
            },
            "expected_improvements": {
                "signal_generation": "3-5x more signals",
                "market_coverage": "25% more pairs analyzed",
                "opportunity_detection": "Significantly improved",
                "false_positive_risk": "Controlled through staged filtering"
            }
        } 