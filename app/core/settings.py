"""
Configuration settings for the crypto signal bot.

This module uses pydantic settings for type-safe configuration management
with environment variable support.
"""

from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr, field_validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "Crypto Signal Bot"
    app_version: str = "2.0.0"  # Updated version for short-term trading
    debug: bool = Field(default=False, description="Debug mode")
    
    # Bybit API
    bybit_api_key: SecretStr = Field(..., description="Bybit API key")
    bybit_api_secret: SecretStr = Field(..., description="Bybit API secret")
    bybit_testnet: bool = Field(default=False, description="Use Bybit testnet")
    
    # Telegram
    telegram_bot_token: SecretStr = Field(..., description="Telegram bot token")
    telegram_chat_ids: List[str] = Field(default=[], description="Allowed chat IDs")
    
    @field_validator('telegram_chat_ids', mode='before')
    @classmethod
    def validate_chat_ids(cls, v):
        """Convert chat IDs to strings if they're integers."""
        if isinstance(v, str):
            # Handle JSON string format like '["123", "456"]' or '[123, 456]'
            import json
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                # If not JSON, treat as single ID
                return [str(v)]
        
        if isinstance(v, list):
            # Convert all items to strings
            return [str(item) for item in v]
        
        # Single value
        return [str(v)]
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    redis_ttl: int = Field(default=300, description="Redis TTL in seconds (5 min for fast timeframes)")
    
    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/crypto_signals",
        description="PostgreSQL/TimescaleDB connection URL"
    )
    
    # Trading Configuration - Optimized for Short-Term High-Leverage Trading
    default_threshold_pct: float = Field(default=3.0, description="Short-term profit threshold % (3% for quick profits)")
    max_leverage: int = Field(default=20, description="Maximum leverage for high-volatility trades")
    min_leverage: int = Field(default=10, description="Minimum leverage for small coins")
    short_trade_duration_minutes: int = Field(default=15, description="Target position duration in minutes")
    
    # Time Frames - Focused on Short-Term (1m, 5m only)
    time_frames: List[str] = Field(
        default=["1m", "5m"],
        description="Ultra-short timeframes for scalping and quick profits"
    )
    
    # Signal Quality - Aggressive settings for short-term trading
    min_signal_strength: int = Field(default=1, description="Low threshold for more signals")
    require_volume_confirmation: bool = Field(default=True, description="Volume spike confirmation for breakouts")
    require_trend_alignment: bool = Field(default=False, description="Not required for scalping")
    
    # Market Scanner Configuration for Top Movers
    scanner_enabled: bool = Field(default=True, description="Enable automatic market scanner")
    scanner_interval_minutes: int = Field(default=5, description="Scanner interval in minutes")
    min_price_change_pct: float = Field(default=3.0, description="Minimum price change % to trigger analysis")
    top_movers_count: int = Field(default=20, description="Number of top movers to track")
    min_volume_usdt: float = Field(default=1000000, description="Minimum 24h volume in USDT (1M)")
    
    # Small Coins Configuration
    small_coin_max_market_cap: float = Field(default=500000000, description="Max market cap for small coins (500M)")
    volatility_threshold: float = Field(default=5.0, description="Minimum volatility % for trading")
    
    # Performance
    max_concurrent_jobs: int = Field(default=100, description="Higher concurrency for fast scanning")
    latency_threshold_ms: int = Field(default=500, description="Lower latency for scalping")
    
    # Monitoring
    prometheus_port: int = Field(default=8001, description="Prometheus metrics port")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json/text)")
    
    # Auto Trading Toggle
    enable_auto_trading: bool = Field(default=False, description="Enable Bybit automated trade execution")
    
    # ML Model
    model_path: str = Field(default="./models/confidence_model.pkl", description="ML model path")
    model_retrain_days: int = Field(default=7, description="Retrain model weekly for short-term patterns")
    
    # WebSocket
    ws_ping_interval: int = Field(default=10, description="Faster ping for real-time data")
    ws_ping_timeout: int = Field(default=5, description="Shorter timeout")
    ws_reconnect_attempts: int = Field(default=10, description="More reconnect attempts")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @property
    def bybit_base_url(self) -> str:
        """Get Bybit base URL based on testnet setting."""
        if self.bybit_testnet:
            return "https://api-testnet.bybit.com"
        return "https://api.bybit.com"
    
    @property
    def bybit_ws_url(self) -> str:
        """Get Bybit WebSocket URL based on testnet setting."""
        if self.bybit_testnet:
            return "wss://stream-testnet.bybit.com/v5/public/spot"
        return "wss://stream.bybit.com/v5/public/spot"


# Global settings instance
settings = Settings() 