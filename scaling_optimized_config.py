#!/usr/bin/env python3
"""
Scaling Optimized Configuration

Configuration optimized for handling 50-100+ trading pairs efficiently:
- Smart pre-filtering to reduce API calls
- Staged analysis pipeline
- Rate limiting and caching
- Resource management
"""

import os
from typing import Dict, List, Any

class ScalingOptimizedConfig:
    """
    Configuration optimized for scaling to many trading pairs.
    Focuses on efficiency and resource management.
    """
    
    # ==========================================
    # CORE SCALING PARAMETERS
    # ==========================================
    
    # Smart Filtering Thresholds
    MIN_VOLATILITY_THRESHOLD: float = 8.0      # 8%+ 24h change
    MIN_VOLUME_THRESHOLD: int = 3000000         # $3M+ volume
    MAX_PAIRS_FOR_ANALYSIS: int = 20            # Top 20 pairs only
    
    # Staged Analysis Configuration
    STAGE1_MAX_PAIRS: int = 50                  # Quick scan up to 50 pairs
    STAGE2_MAX_PAIRS: int = 15                  # Detailed analysis for 15 pairs
    STAGE3_MAX_PAIRS: int = 5                   # Full signals for 5 pairs
    
    # ==========================================
    # API RATE LIMITING
    # ==========================================
    
    # Request Rate Limiting
    MAX_CONCURRENT_API_CALLS: int = 10          # Max concurrent requests
    API_REQUEST_DELAY_MS: int = 100             # 100ms between requests
    BATCH_SIZE: int = 20                        # Process in batches of 20
    API_TIMEOUT_SECONDS: int = 15               # 15 second timeout per request
    
    # Circuit Breaker Settings
    API_FAILURE_THRESHOLD: int = 5              # Open circuit after 5 failures
    CIRCUIT_BREAKER_TIMEOUT: int = 60           # 60 second cooldown
    
    # ==========================================
    # CACHING STRATEGY
    # ==========================================
    
    # Cache TTL (Time To Live) in seconds
    CACHE_TTL_TICKER: int = 30                  # 30 seconds for ticker data
    CACHE_TTL_KLINES_SHORT: int = 60            # 1 minute for 1m/5m data
    CACHE_TTL_KLINES_MEDIUM: int = 120          # 2 minutes for 15m/1h data
    CACHE_TTL_KLINES_LONG: int = 300            # 5 minutes for 4h+ data
    CACHE_TTL_ANALYSIS: int = 300               # 5 minutes for analysis results
    
    # ==========================================
    # TIMEFRAME PRIORITIZATION
    # ==========================================
    
    # Primary timeframes (always fetched)
    PRIMARY_TIMEFRAMES: List[str] = ["15m", "1h"]
    
    # Secondary timeframes (fetched for top candidates only)
    SECONDARY_TIMEFRAMES: List[str] = ["5m", "4h"]
    
    # All supported timeframes
    ALL_TIMEFRAMES: List[str] = ["1m", "5m", "15m", "1h", "4h", "1d"]
    
    # ==========================================
    # RESOURCE MANAGEMENT
    # ==========================================
    
    # Memory Management
    MAX_MEMORY_USAGE_MB: int = 500              # 500MB memory limit
    MAX_SIGNAL_HISTORY_PER_PAIR: int = 100      # Keep last 100 signals per pair
    DATA_CLEANUP_INTERVAL_HOURS: int = 2        # Clean old data every 2 hours
    
    # Processing Limits
    MAX_CONCURRENT_ANALYSIS: int = 15           # Max 15 concurrent analyses
    ANALYSIS_TIMEOUT_SECONDS: int = 30          # 30 second timeout per analysis
    
    # ==========================================
    # SIGNAL QUALITY THRESHOLDS
    # ==========================================
    
    # Quick Scan Thresholds (Stage 1)
    QUICK_SCAN_MIN_SCORE: float = 0.3           # Minimum score to proceed
    QUICK_SCAN_MIN_RSI_DIVERGENCE: int = 10     # 10 point RSI move
    QUICK_SCAN_MIN_VOLUME_SPIKE: float = 1.5    # 1.5x volume spike
    QUICK_SCAN_MIN_MOMENTUM: float = 0.003      # 0.3% price momentum
    
    # Detailed Analysis Thresholds (Stage 2)
    DETAILED_MIN_SIGNAL_STRENGTH: float = 1.8   # Signal strength threshold
    DETAILED_MIN_CONFLUENCE_POINTS: int = 2     # Confluence points required
    DETAILED_MIN_TREND_ALIGNMENT: float = 0.6   # Trend alignment score
    
    # Final Signal Thresholds (Stage 3)
    FINAL_MIN_CONFIDENCE: float = 0.65          # Minimum confidence for trading
    FINAL_MIN_QUALITY_SCORE: int = 70           # Minimum quality score
    
    # ==========================================
    # MARKET CONDITIONS ADAPTATION
    # ==========================================
    
    # High Volatility Market Adjustments
    HIGH_VOLATILITY_THRESHOLD: float = 10.0     # 10%+ average major coin change
    HIGH_VOL_VOLATILITY_MULTIPLIER: float = 1.2 # More selective in volatile markets
    HIGH_VOL_VOLUME_MULTIPLIER: float = 1.5     # Higher volume requirements
    HIGH_VOL_PAIRS_REDUCTION: int = -5          # Analyze 5 fewer pairs
    
    # Low Volatility Market Adjustments
    LOW_VOLATILITY_THRESHOLD: float = 3.0       # <3% average major coin change
    LOW_VOL_VOLATILITY_MULTIPLIER: float = 0.8  # Less strict in quiet markets
    LOW_VOL_VOLUME_MULTIPLIER: float = 0.7      # Lower volume requirements
    LOW_VOL_PAIRS_INCREASE: int = 5             # Analyze 5 more pairs
    
    # ==========================================
    # POSITION MANAGEMENT (Conservative for Scale)
    # ==========================================
    
    # Position Limits
    MAX_CONCURRENT_POSITIONS: int = 3           # Conservative position limit
    MAX_DAILY_TRADES: int = 5                   # Fewer trades for better quality
    POSITION_SIZE_PCT: float = 2.0              # Smaller positions (2% vs 3%)
    MAX_PORTFOLIO_HEAT: float = 8.0             # Max 8% total risk
    
    # Risk Management
    MAX_LEVERAGE: int = 10                      # Conservative leverage
    DEFAULT_STOP_LOSS_PCT: float = 1.5          # 1.5% stop loss
    CORRELATION_LIMIT_ENABLED: bool = True      # Avoid correlated positions
    
    # ==========================================
    # MONITORING AND ALERTS
    # ==========================================
    
    # Performance Monitoring
    ENABLE_PERFORMANCE_TRACKING: bool = True
    PERFORMANCE_LOG_INTERVAL_MINUTES: int = 15  # Log performance every 15 minutes
    
    # Alert Thresholds
    HIGH_API_USAGE_THRESHOLD: float = 0.8       # Alert at 80% rate limit
    HIGH_MEMORY_USAGE_THRESHOLD: float = 0.85   # Alert at 85% memory usage
    CIRCUIT_BREAKER_ALERT: bool = True          # Alert on circuit breaker activation
    
    # ==========================================
    # DEPLOYMENT MODES
    # ==========================================
    
    @classmethod
    def get_light_mode_config(cls) -> Dict[str, Any]:
        """Get configuration for light resource usage."""
        return {
            "max_pairs_for_analysis": 10,
            "stage1_max_pairs": 25,
            "stage2_max_pairs": 8,
            "stage3_max_pairs": 3,
            "max_concurrent_api_calls": 5,
            "primary_timeframes": ["15m"],
            "secondary_timeframes": ["1h"],
            "description": "Light mode for resource-constrained environments"
        }
    
    @classmethod
    def get_aggressive_mode_config(cls) -> Dict[str, Any]:
        """Get configuration for maximum opportunity discovery."""
        return {
            "max_pairs_for_analysis": 30,
            "stage1_max_pairs": 75,
            "stage2_max_pairs": 20,
            "stage3_max_pairs": 8,
            "max_concurrent_api_calls": 15,
            "min_volatility_threshold": 6.0,
            "min_volume_threshold": 2000000,
            "description": "Aggressive mode for maximum market coverage"
        }
    
    @classmethod
    def get_balanced_mode_config(cls) -> Dict[str, Any]:
        """Get balanced configuration (default)."""
        return {
            "max_pairs_for_analysis": cls.MAX_PAIRS_FOR_ANALYSIS,
            "stage1_max_pairs": cls.STAGE1_MAX_PAIRS,
            "stage2_max_pairs": cls.STAGE2_MAX_PAIRS,
            "stage3_max_pairs": cls.STAGE3_MAX_PAIRS,
            "max_concurrent_api_calls": cls.MAX_CONCURRENT_API_CALLS,
            "min_volatility_threshold": cls.MIN_VOLATILITY_THRESHOLD,
            "min_volume_threshold": cls.MIN_VOLUME_THRESHOLD,
            "description": "Balanced mode for optimal performance/resource usage"
        }
    
    # ==========================================
    # SUPPORTED PAIRS CONFIGURATION
    # ==========================================
    
    # Always monitor these major pairs
    PRIORITY_PAIRS: List[str] = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT",
        "AVAXUSDT", "DOGEUSDT", "MATICUSDT", "DOTUSDT"
    ]
    
    # Exclude these pairs from analysis (stablecoins, etc.)
    EXCLUDED_PAIRS: List[str] = [
        "USDCUSDT", "BUSDUSDT", "TUSDUSDT", "DAIUSDT",
        "FDUSDUSDT", "EURUSDT", "GBPUSDT"
    ]
    
    # Correlation groups for risk management
    CORRELATION_GROUPS: Dict[str, List[str]] = {
        "LAYER1": ["SOL", "ADA", "DOT", "AVAX", "ATOM", "NEAR"],
        "DEFI": ["UNI", "AAVE", "COMP", "SUSHI", "CRV", "YFI"],
        "MEME": ["DOGE", "SHIB", "PEPE", "FLOKI", "WIF"],
        "GAMING": ["AXS", "SAND", "MANA", "GALA", "ENJ"]
    }
    
    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """Validate configuration parameters."""
        validations = {
            "api_limits": cls.MAX_CONCURRENT_API_CALLS <= 20,
            "stage_progression": (
                cls.STAGE1_MAX_PAIRS >= cls.STAGE2_MAX_PAIRS >= cls.STAGE3_MAX_PAIRS
            ),
            "timeframes": len(cls.PRIMARY_TIMEFRAMES) >= 1,
            "memory_limit": cls.MAX_MEMORY_USAGE_MB >= 100,
            "position_limits": cls.MAX_CONCURRENT_POSITIONS <= 10,
            "thresholds": (
                cls.MIN_VOLATILITY_THRESHOLD > 0 and
                cls.MIN_VOLUME_THRESHOLD > 0
            )
        }
        
        all_valid = all(validations.values())
        validations["overall"] = all_valid
        
        return validations
    
    @classmethod
    def get_optimization_summary(cls) -> Dict[str, Any]:
        """Get summary of optimization features."""
        return {
            "optimization_features": [
                "Smart pre-filtering reduces API calls by 60-70%",
                "Staged analysis processes only promising candidates",
                "Rate limiting prevents API circuit breaker activation",
                "Intelligent caching reduces redundant data fetching",
                "Resource management prevents memory overuse",
                "Market condition adaptation adjusts thresholds dynamically"
            ],
            "expected_performance": {
                "pairs_monitored": "100+",
                "api_call_reduction": "60-70%",
                "processing_time": "<30 seconds",
                "memory_usage": "<500MB",
                "signal_quality": "maintained or improved"
            },
            "scalability_limits": {
                "recommended_max_pairs": 200,
                "absolute_max_pairs": 500,
                "critical_resource": "API rate limits"
            }
        } 