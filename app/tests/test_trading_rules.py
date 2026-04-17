"""
Tests for trading rules module.

Tests the core trading logic and signal generation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.logic.rules import TradingRules
from app.indicators.technical import TechnicalIndicators


class TestTradingRules:
    """Test trading rules functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(end=datetime.now(), periods=200, freq='15min')
        
        # Create trending data
        trend = np.linspace(40000, 42000, 200)
        noise = np.random.normal(0, 100, 200)
        prices = trend + noise
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices - 50,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': np.random.uniform(1000, 5000, 200)
        })
        
        return df
    
    @pytest.fixture
    def multi_timeframe_data(self, sample_data):
        """Create multi-timeframe data dictionary."""
        return {
            "1m": sample_data.copy(),
            "5m": sample_data.copy(),
            "15m": sample_data.copy(),
            "1h": sample_data.copy(),
            "4h": sample_data.copy()
        }
    
    def test_analyze_symbol_with_valid_data(self, multi_timeframe_data):
        """Test symbol analysis with valid data."""
        result = TradingRules.analyze_symbol(multi_timeframe_data)
        
        assert "timestamp" in result
        assert "direction" in result
        assert result["direction"] in ["LONG", "SHORT", "NEUTRAL"]
        assert "leverage" in result
        assert 10 <= result["leverage"] <= 50
        assert "entry_price" in result
        assert "stop_loss" in result
        assert "take_profit_1" in result
        assert "take_profit_2" in result
        assert "take_profit_3" in result
        assert "rationale" in result
        assert isinstance(result["rationale"], list)
    
    def test_analyze_symbol_with_empty_data(self):
        """Test symbol analysis with empty data."""
        result = TradingRules.analyze_symbol({})
        
        assert result["direction"] == "NEUTRAL"
        assert "error" in result
    
    def test_get_dominant_timeframe(self, multi_timeframe_data):
        """Test dominant timeframe selection."""
        # Add indicators to data
        for tf, df in multi_timeframe_data.items():
            multi_timeframe_data[tf] = TechnicalIndicators.calculate_all(df)
        
        dominant_tf = TradingRules._get_dominant_timeframe(multi_timeframe_data)
        
        assert dominant_tf in ["1m", "5m", "15m", "1h", "4h"]
    
    def test_determine_trade_direction_bullish(self, sample_data):
        """Test trade direction determination for bullish trend."""
        # Create bullish setup
        df = TechnicalIndicators.calculate_all(sample_data)
        data = {"15m": df}
        
        signal = TradingRules._determine_trade_direction(data, "bullish", 75)
        
        assert signal["direction"] in ["LONG", "NEUTRAL"]
        assert signal["strength"] >= 0
    
    def test_calculate_leverage(self):
        """Test leverage calculation based on volatility."""
        # Low volatility
        leverage = TradingRules._calculate_leverage(10)
        assert leverage == 14  # 10 + (10 * 0.4) = 14
        
        # Medium volatility
        leverage = TradingRules._calculate_leverage(50)
        assert leverage == 30  # 10 + (50 * 0.4) = 30
        
        # High volatility
        leverage = TradingRules._calculate_leverage(100)
        assert leverage == 50  # Capped at 50
    
    def test_calculate_trade_levels_long(self, sample_data):
        """Test trade level calculation for long positions."""
        df = TechnicalIndicators.calculate_all(sample_data)
        current_price = 42000
        
        levels = TradingRules._calculate_trade_levels(
            df, current_price, "LONG", 20.0
        )
        
        assert levels["entry"] > current_price
        assert levels["stop_loss"] < levels["entry"]
        assert levels["tp1"] > levels["entry"]
        assert levels["tp2"] > levels["tp1"]
        assert levels["tp3"] > levels["tp2"]
        
        # Check profit targets are approximately correct
        tp2_profit = ((levels["tp2"] - levels["entry"]) / levels["entry"]) * 100
        assert 19 < tp2_profit < 21  # Should be around 20%
    
    def test_calculate_trade_levels_short(self, sample_data):
        """Test trade level calculation for short positions."""
        df = TechnicalIndicators.calculate_all(sample_data)
        current_price = 42000
        
        levels = TradingRules._calculate_trade_levels(
            df, current_price, "SHORT", 20.0
        )
        
        assert levels["entry"] < current_price
        assert levels["stop_loss"] > levels["entry"]
        assert levels["tp1"] < levels["entry"]
        assert levels["tp2"] < levels["tp1"]
        assert levels["tp3"] < levels["tp2"]
    
    def test_generate_rationale(self, multi_timeframe_data):
        """Test rationale generation."""
        trade_signal = {"direction": "LONG", "strength": 5}
        volatility_score = 45
        trend_strength = 70
        
        rationale = TradingRules._generate_rationale(
            multi_timeframe_data,
            trade_signal,
            volatility_score,
            trend_strength
        )
        
        assert isinstance(rationale, list)
        assert len(rationale) <= 5
        assert all(isinstance(r, str) for r in rationale)
    
    def test_extract_features(self, multi_timeframe_data):
        """Test feature extraction for ML model."""
        # Add indicators
        for tf, df in multi_timeframe_data.items():
            multi_timeframe_data[tf] = TechnicalIndicators.calculate_all(df)
        
        trade_signal = {"direction": "LONG", "strength": 5}
        
        features = TradingRules._extract_features(
            multi_timeframe_data,
            50.0,
            75.0,
            trade_signal
        )
        
        assert "volatility_score" in features
        assert "trend_strength" in features
        assert "signal_strength" in features
        assert features["volatility_score"] == 50.0
        assert features["trend_strength"] == 75.0
        assert features["signal_strength"] == 5.0
    
    def test_integration_full_analysis(self, multi_timeframe_data):
        """Test full integration of analysis pipeline."""
        result = TradingRules.analyze_symbol(multi_timeframe_data, 25.0)
        
        if result["direction"] != "NEUTRAL":
            # Verify all required fields
            required_fields = [
                "timestamp", "dominant_timeframe", "direction",
                "leverage", "entry_price", "stop_loss",
                "take_profit_1", "take_profit_2", "take_profit_3",
                "volatility_score", "trend_strength", "rationale",
                "features", "current_price"
            ]
            
            for field in required_fields:
                assert field in result, f"Missing field: {field}"
            
            # Verify data types
            assert isinstance(result["timestamp"], datetime)
            assert isinstance(result["leverage"], int)
            assert isinstance(result["rationale"], list)
            assert isinstance(result["features"], dict)
            
            # Verify logical consistency
            if result["direction"] == "LONG":
                assert result["stop_loss"] < result["entry_price"]
                assert result["take_profit_1"] > result["entry_price"]
            else:
                assert result["stop_loss"] > result["entry_price"]
                assert result["take_profit_1"] < result["entry_price"] 