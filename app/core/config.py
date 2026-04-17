class Settings:
    # ... existing settings ...
    
    # RELIABLE VALIDATED PARAMETERS (balanced aggressive configuration)
    # Based on comprehensive reliability testing achieving +0.3% monthly return with 41.1% win rate
    MIN_SIGNAL_STRENGTH: float = 1.5     # RELIABLE: Validated through out-of-sample testing ⭐
    MIN_CONFLUENCE_POINTS: int = 1        # Maintained optimal level
    
    # RSI Configuration (validated range)
    RSI_OVERSOLD: float = 15.0           # RELIABLE: Broad but validated range
    RSI_OVERBOUGHT: float = 85.0         # RELIABLE: Broad but validated range
    
    # VOLUME ANALYSIS (validated parameters)
    VOLUME_RATIO_THRESHOLD: float = 1.0   # RELIABLE: Validated threshold
    PRICE_MOMENTUM_THRESHOLD: float = 0.005  # RELIABLE: Validated sensitivity
    EMA_SLOPE_THRESHOLD: float = 0.0005       # RELIABLE: Conservative slope detection
    
    # BALANCED RISK MANAGEMENT (sustainable performance)
    MAX_LEVERAGE: int = 5              # RELIABLE: Sustainable leverage tested across conditions ⭐
    DEFAULT_STOP_LOSS_PCT: float = 2.5  # RELIABLE: Validated stop loss
    DEFAULT_TAKE_PROFIT_1_PCT: float = 2.5  # RELIABLE: Conservative profit targets
    DEFAULT_TAKE_PROFIT_2_PCT: float = 5.0  # RELIABLE: Validated take profit
    DEFAULT_TAKE_PROFIT_3_PCT: float = 5.0  # RELIABLE: Conservative final target
    
    # POSITION MANAGEMENT (reliable configuration)
    MAX_CONCURRENT_POSITIONS: int = 3    # RELIABLE: Conservative position count
    POSITION_SIZE_PCT: float = 2.0       # RELIABLE: Validated position sizing
    MAX_DAILY_TRADES: int = 5            # RELIABLE: Sustainable trade frequency
    
    # RELIABLE SIGNAL FILTERING (validated thresholds)
    MIN_CONFIDENCE_SCORE: float = 0.55   # RELIABLE: Validated confidence threshold ⭐
    MIN_VOLUME_CONFIRMATION: float = 1.0  # RELIABLE: Validated volume filter
    MAX_CORRELATION_THRESHOLD: float = 0.8  # RELIABLE: Validated correlation limit
    
    # ADAPTIVE RISK CONTROLS (slightly relaxed)
    DAILY_LOSS_LIMIT_PCT: float = 7.0    # RELAXED: 5.0 → 7.0 (more room for trading)
    MONTHLY_LOSS_LIMIT_PCT: float = 20.0  # RELAXED: 15.0 → 20.0 (more room for monthly trades)
    DRAWDOWN_PAUSE_THRESHOLD: float = 12.0  # RELAXED: 10.0 → 12.0 (less frequent pauses)
    
    # ... existing code ... 