#!/usr/bin/env python3
"""
Comprehensive Backtesting Engine for Crypto Signal Bot

Tests full bot functionality including:
- Signal generation with different parameters
- Bookmap fusion simulation
- Risk management
- Performance optimization
- Parameter tuning
"""

import pandas as pd
import numpy as np
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import itertools

# Mock the app modules for standalone testing
import sys
import os
sys.path.append('./crypto-signal-bot')

@dataclass
class Trade:
    """Represents a completed trade."""
    symbol: str
    direction: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    leverage: int
    pnl_pct: float
    pnl_usd: float
    exit_reason: str
    duration_hours: float
    signal_strength: float
    confluence_points: int
    confidence_score: float

@dataclass
class BacktestConfig:
    """Backtesting configuration parameters."""
    # Signal generation parameters
    min_signal_strength: float = 2.0
    min_confluence_points: int = 1
    directional_bias_multiplier: float = 1.1
    
    # Technical indicator parameters
    rsi_range: Tuple[float, float] = (35, 85)
    volume_ratio_threshold: float = 1.1
    price_momentum_threshold: float = 0.005
    ema_slope_threshold: float = 0.0005
    
    # Risk management parameters
    max_leverage: int = 20
    stop_loss_pct: float = 2.0
    take_profit_1_pct: float = 1.5
    take_profit_2_pct: float = 3.0
    take_profit_3_pct: float = 5.0
    
    # Position management
    max_concurrent_positions: int = 3
    position_size_pct: float = 10.0  # % of portfolio per trade
    max_daily_trades: int = 10
    
    # Exit conditions
    max_hold_hours: int = 24
    trailing_stop_pct: float = 1.0

class BacktestEngine:
    """Main backtesting engine."""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades: List[Trade] = []
        self.active_positions: Dict[str, Dict] = {}
        self.daily_stats: Dict[str, Dict] = {}
        
    def create_test_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Create realistic test data for backtesting."""
        periods = days * 24  # Hourly data
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=days), 
            periods=periods, 
            freq='h'
        )
        
        # Create realistic price movements
        np.random.seed(42)
        base_price = 50000.0 if symbol.startswith('BTC') else 3000.0
        
        # Generate realistic price series with trends and volatility
        returns = []
        trend_strength = np.random.choice([-0.001, 0.0, 0.001], p=[0.3, 0.4, 0.3])
        
        for i in range(periods):
            # Add trend changes every few days
            if i % (24 * 3) == 0:  # Change trend every 3 days
                trend_strength = np.random.choice([-0.002, -0.001, 0.0, 0.001, 0.002], 
                                                p=[0.2, 0.2, 0.2, 0.2, 0.2])
            
            # Generate return with trend and volatility
            daily_vol = np.random.uniform(0.01, 0.04)  # 1-4% daily volatility
            hourly_vol = daily_vol / np.sqrt(24)
            
            return_val = np.random.normal(trend_strength, hourly_vol)
            returns.append(return_val)
        
        # Convert returns to prices
        prices = [base_price]
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        
        prices = prices[1:]  # Remove initial price
        
        # Create OHLCV data
        data = []
        for i, price in enumerate(prices):
            high = price * (1 + abs(np.random.normal(0, 0.005)))
            low = price * (1 - abs(np.random.normal(0, 0.005)))
            volume = np.random.uniform(1000000, 5000000)
            
            # Add some volume spikes
            if np.random.random() < 0.1:  # 10% chance of volume spike
                volume *= np.random.uniform(2, 5)
            
            data.append({
                'timestamp': dates[i],
                'open': price,
                'high': high,
                'low': low,
                'close': price,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        
        # Add technical indicators
        df = self.add_technical_indicators(df)
        
        return df
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the dataframe."""
        # EMAs
        df['EMA_20'] = df['close'].ewm(span=20).mean()
        df['EMA_50'] = df['close'].ewm(span=50).mean()
        df['EMA_200'] = df['close'].ewm(span=200).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_hist'] = df['MACD'] - df['MACD_signal']
        
        # Volume indicators
        df['Volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        
        # Bollinger Bands
        bb_period = 20
        df['BB_middle'] = df['close'].rolling(bb_period).mean()
        bb_std = df['close'].rolling(bb_period).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        
        return df
    
    def generate_signal(self, data: pd.DataFrame, config: BacktestConfig, 
                       current_idx: int) -> Optional[Dict[str, Any]]:
        """Generate trading signal using the bot's logic with given config."""
        if current_idx < 200:  # Need enough history
            return None
        
        # Get current data slice
        df = data.iloc[:current_idx + 1].copy()
        
        if len(df) < 200:
            return None
        
        # Simulate multi-timeframe analysis (use same data for simplicity)
        timeframes = {
            "5m": df.copy(),
            "15m": df.copy(), 
            "1h": df.copy()
        }
        
        # Check signal conditions with current config
        signal_strength = 0
        confluence_factors = []
        direction = "NEUTRAL"
        
        # Get latest values
        close = df['close'].iloc[-1]
        ema20 = df['EMA_20'].iloc[-1]
        ema50 = df['EMA_50'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        volume_ratio = df['Volume_ratio'].iloc[-1]
        macd_hist = df['MACD_hist'].iloc[-1]
        
        # 1. Trend structure analysis
        ema_slope_20 = (ema20 - df['EMA_20'].iloc[-5]) / df['EMA_20'].iloc[-5]
        momentum_10 = (close - df['close'].iloc[-10]) / df['close'].iloc[-10]
        
        if (close > ema20 and ema20 > ema50 and
            ema_slope_20 > config.ema_slope_threshold and
            rsi > config.rsi_range[0] and rsi < config.rsi_range[1] and
            momentum_10 > config.price_momentum_threshold):
            
            signal_strength += 3
            confluence_factors.append("trend_structure")
            direction = "LONG"
        
        elif (close < ema20 and ema20 < ema50 and
              ema_slope_20 < -config.ema_slope_threshold and
              rsi < (100 - config.rsi_range[0]) and rsi > (100 - config.rsi_range[1]) and
              momentum_10 < -config.price_momentum_threshold):
            
            signal_strength += 3
            confluence_factors.append("trend_structure")
            direction = "SHORT"
        
        # 2. Volume confirmation
        price_change_5 = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]
        price_change_1 = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]
        avg_volume = df['volume'].rolling(20).mean().iloc[-1]
        current_volume = df['volume'].iloc[-1]
        
        if direction == "LONG":
            if (volume_ratio > config.volume_ratio_threshold and
                current_volume > avg_volume and
                price_change_5 > config.price_momentum_threshold and
                price_change_1 > 0.001):
                
                signal_strength += 2
                confluence_factors.append("volume_confirmation")
        
        elif direction == "SHORT":
            if (volume_ratio > config.volume_ratio_threshold and
                current_volume > avg_volume and
                price_change_5 < -config.price_momentum_threshold and
                price_change_1 < -0.001):
                
                signal_strength += 2
                confluence_factors.append("volume_confirmation")
        
        # 3. Momentum confirmation
        macd_hist_prev = df['MACD_hist'].iloc[-2]
        rsi_prev = df['RSI'].iloc[-5]
        macd_acceleration = macd_hist - macd_hist_prev
        
        if direction == "LONG":
            if (macd_hist > 0 and macd_acceleration > 0 and
                rsi > rsi_prev and rsi > 50):
                
                signal_strength += 1.5
                confluence_factors.append("momentum")
        
        elif direction == "SHORT":
            if (macd_hist < 0 and macd_acceleration < 0 and
                rsi < rsi_prev and rsi < 50):
                
                signal_strength += 1.5
                confluence_factors.append("momentum")
        
        # 4. Fallback conditions
        price_change_3 = (df['close'].iloc[-1] - df['close'].iloc[-3]) / df['close'].iloc[-3]
        price_trend = df['close'].iloc[-1] > df['close'].iloc[-5]
        
        if direction == "LONG" and price_change_3 > 0.003 and price_trend:
            signal_strength += 0.5
            confluence_factors.append("basic_momentum")
        elif direction == "SHORT" and price_change_3 < -0.003 and not price_trend:
            signal_strength += 0.5
            confluence_factors.append("basic_momentum")
        
        # Check if signal meets requirements
        if (signal_strength >= config.min_signal_strength and
            len(confluence_factors) >= config.min_confluence_points and
            direction != "NEUTRAL"):
            
            # Calculate entry and exit levels
            entry_price = close
            
            if direction == "LONG":
                stop_loss = entry_price * (1 - config.stop_loss_pct / 100)
                take_profit_1 = entry_price * (1 + config.take_profit_1_pct / 100)
                take_profit_2 = entry_price * (1 + config.take_profit_2_pct / 100)
                take_profit_3 = entry_price * (1 + config.take_profit_3_pct / 100)
            else:
                stop_loss = entry_price * (1 + config.stop_loss_pct / 100)
                take_profit_1 = entry_price * (1 - config.take_profit_1_pct / 100)
                take_profit_2 = entry_price * (1 - config.take_profit_2_pct / 100)
                take_profit_3 = entry_price * (1 - config.take_profit_3_pct / 100)
            
            # Calculate confidence score (simplified)
            confidence_score = min(10.0, signal_strength + len(confluence_factors))
            
            # Determine leverage based on confidence and volatility
            volatility = df['close'].pct_change().rolling(24).std().iloc[-1] * 100
            base_leverage = min(config.max_leverage, int(confidence_score * 2))
            
            if volatility > 5:  # High volatility
                leverage = max(1, base_leverage // 2)
            else:
                leverage = base_leverage
            
            return {
                "timestamp": df['timestamp'].iloc[-1],
                "direction": direction,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit_1": take_profit_1,
                "take_profit_2": take_profit_2,
                "take_profit_3": take_profit_3,
                "leverage": leverage,
                "signal_strength": signal_strength,
                "confluence_points": len(confluence_factors),
                "confluence_factors": confluence_factors,
                "confidence_score": confidence_score,
                "rsi": rsi,
                "volume_ratio": volume_ratio
            }
        
        return None
    
    def simulate_trade(self, signal: Dict[str, Any], data: pd.DataFrame, 
                      start_idx: int, config: BacktestConfig) -> Optional[Trade]:
        """Simulate a trade from signal to exit."""
        if len(self.active_positions) >= config.max_concurrent_positions:
            return None
        
        symbol = "BTCUSDT"  # For simulation
        entry_time = signal["timestamp"]
        direction = signal["direction"]
        entry_price = signal["entry_price"]
        leverage = signal["leverage"]
        
        # Position size based on configuration
        position_size_usd = self.current_capital * (config.position_size_pct / 100)
        position_size_base = position_size_usd / entry_price
        
        # Track position
        position_id = f"{symbol}_{entry_time}"
        self.active_positions[position_id] = {
            "symbol": symbol,
            "direction": direction,
            "entry_time": entry_time,
            "entry_price": entry_price,
            "position_size_usd": position_size_usd,
            "position_size_base": position_size_base,
            "leverage": leverage,
            "signal": signal,
            "highest_price": entry_price if direction == "LONG" else None,
            "lowest_price": entry_price if direction == "SHORT" else None
        }
        
        # Simulate price movement and exit conditions
        exit_price = None
        exit_reason = None
        exit_time = None
        
        for i in range(start_idx + 1, len(data)):
            current_time = data.iloc[i]['timestamp']
            current_price = data.iloc[i]['close']
            high_price = data.iloc[i]['high']
            low_price = data.iloc[i]['low']
            
            # Update tracking prices
            if direction == "LONG":
                if self.active_positions[position_id]["highest_price"] is None:
                    self.active_positions[position_id]["highest_price"] = high_price
                else:
                    self.active_positions[position_id]["highest_price"] = max(
                        self.active_positions[position_id]["highest_price"], high_price
                    )
            else:
                if self.active_positions[position_id]["lowest_price"] is None:
                    self.active_positions[position_id]["lowest_price"] = low_price
                else:
                    self.active_positions[position_id]["lowest_price"] = min(
                        self.active_positions[position_id]["lowest_price"], low_price
                    )
            
            # Check exit conditions
            if direction == "LONG":
                # Stop loss
                if low_price <= signal["stop_loss"]:
                    exit_price = signal["stop_loss"]
                    exit_reason = "stop_loss"
                    exit_time = current_time
                    break
                
                # Take profits
                elif high_price >= signal["take_profit_3"]:
                    exit_price = signal["take_profit_3"]
                    exit_reason = "take_profit_3"
                    exit_time = current_time
                    break
                elif high_price >= signal["take_profit_2"]:
                    exit_price = signal["take_profit_2"]
                    exit_reason = "take_profit_2"
                    exit_time = current_time
                    break
                elif high_price >= signal["take_profit_1"]:
                    exit_price = signal["take_profit_1"]
                    exit_reason = "take_profit_1"
                    exit_time = current_time
                    break
                
                # Trailing stop
                highest = self.active_positions[position_id]["highest_price"]
                trailing_stop = highest * (1 - config.trailing_stop_pct / 100)
                if current_price <= trailing_stop and highest > entry_price * 1.01:
                    exit_price = trailing_stop
                    exit_reason = "trailing_stop"
                    exit_time = current_time
                    break
            
            else:  # SHORT
                # Stop loss
                if high_price >= signal["stop_loss"]:
                    exit_price = signal["stop_loss"]
                    exit_reason = "stop_loss"
                    exit_time = current_time
                    break
                
                # Take profits
                elif low_price <= signal["take_profit_3"]:
                    exit_price = signal["take_profit_3"]
                    exit_reason = "take_profit_3"
                    exit_time = current_time
                    break
                elif low_price <= signal["take_profit_2"]:
                    exit_price = signal["take_profit_2"]
                    exit_reason = "take_profit_2"
                    exit_time = current_time
                    break
                elif low_price <= signal["take_profit_1"]:
                    exit_price = signal["take_profit_1"]
                    exit_reason = "take_profit_1"
                    exit_time = current_time
                    break
                
                # Trailing stop
                lowest = self.active_positions[position_id]["lowest_price"]
                trailing_stop = lowest * (1 + config.trailing_stop_pct / 100)
                if current_price >= trailing_stop and lowest < entry_price * 0.99:
                    exit_price = trailing_stop
                    exit_reason = "trailing_stop"
                    exit_time = current_time
                    break
            
            # Time-based exit
            hours_held = (current_time - entry_time).total_seconds() / 3600
            if hours_held >= config.max_hold_hours:
                exit_price = current_price
                exit_reason = "time_limit"
                exit_time = current_time
                break
        
        # If no exit found, close at end of data
        if exit_price is None:
            exit_price = data.iloc[-1]['close']
            exit_reason = "end_of_data"
            exit_time = data.iloc[-1]['timestamp']
        
        # Calculate P&L
        if direction == "LONG":
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100 * leverage
        else:
            pnl_pct = ((entry_price - exit_price) / entry_price) * 100 * leverage
        
        pnl_usd = position_size_usd * (pnl_pct / 100)
        
        # Update capital
        self.current_capital += pnl_usd
        
        # Remove from active positions
        del self.active_positions[position_id]
        
        # Create trade record
        duration_hours = (exit_time - entry_time).total_seconds() / 3600
        
        trade = Trade(
            symbol=symbol,
            direction=direction,
            entry_time=entry_time,
            exit_time=exit_time,
            entry_price=entry_price,
            exit_price=exit_price,
            leverage=leverage,
            pnl_pct=pnl_pct,
            pnl_usd=pnl_usd,
            exit_reason=exit_reason,
            duration_hours=duration_hours,
            signal_strength=signal["signal_strength"],
            confluence_points=signal["confluence_points"],
            confidence_score=signal["confidence_score"]
        )
        
        self.trades.append(trade)
        return trade
    
    def run_backtest(self, symbols: List[str], config: BacktestConfig, 
                    days: int = 30) -> Dict[str, Any]:
        """Run full backtest with given configuration."""
        print(f"🚀 Running backtest with config: {config}")
        
        self.trades = []
        self.active_positions = {}
        self.current_capital = self.initial_capital
        
        all_signals = []
        
        for symbol in symbols:
            print(f"  📊 Testing {symbol}...")
            
            # Create test data
            data = self.create_test_data(symbol, days)
            
            # Generate signals
            for i in range(200, len(data) - 24):  # Leave room for trade execution
                signal = self.generate_signal(data, config, i)
                
                if signal:
                    all_signals.append((signal, data, i, symbol))
                    
                    # Simulate trade
                    trade = self.simulate_trade(signal, data, i, config)
                    
                    if trade:
                        print(f"    💰 Trade: {trade.direction} {trade.pnl_pct:+.2f}% ({trade.exit_reason})")
        
        # Calculate performance metrics
        return self.calculate_performance_metrics(config, all_signals)
    
    def calculate_performance_metrics(self, config: BacktestConfig, 
                                    all_signals: List) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        if not self.trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_return": 0,
                "config": config,
                "score": 0
            }
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl_pct > 0]
        losing_trades = [t for t in self.trades if t.pnl_pct <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital * 100
        
        # P&L metrics
        avg_win = np.mean([t.pnl_pct for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl_pct for t in losing_trades]) if losing_trades else 0
        largest_win = max([t.pnl_pct for t in self.trades])
        largest_loss = min([t.pnl_pct for t in self.trades])
        
        # Risk metrics
        pnl_series = [t.pnl_pct for t in self.trades]
        volatility = np.std(pnl_series)
        sharpe_ratio = (np.mean(pnl_series) / volatility) if volatility > 0 else 0
        
        # Drawdown calculation
        cumulative_returns = np.cumsum([t.pnl_usd for t in self.trades])
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / self.initial_capital * 100
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        # Exit reason analysis
        exit_reasons = {}
        for trade in self.trades:
            exit_reasons[trade.exit_reason] = exit_reasons.get(trade.exit_reason, 0) + 1
        
        # Signal quality metrics
        avg_signal_strength = np.mean([t.signal_strength for t in self.trades])
        avg_confluence = np.mean([t.confluence_points for t in self.trades])
        avg_confidence = np.mean([t.confidence_score for t in self.trades])
        
        # Calculate composite score for optimization
        score = self.calculate_optimization_score({
            "win_rate": win_rate,
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "total_trades": total_trades
        })
        
        return {
            "config": config,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "total_return": total_return,
            "final_capital": self.current_capital,
            
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            
            "exit_reasons": exit_reasons,
            
            "avg_signal_strength": avg_signal_strength,
            "avg_confluence": avg_confluence,
            "avg_confidence": avg_confidence,
            
            "score": score,
            "profit_factor": abs(avg_win * len(winning_trades) / (avg_loss * len(losing_trades))) if losing_trades else float('inf')
        }
    
    def calculate_optimization_score(self, metrics: Dict[str, float]) -> float:
        """Calculate composite optimization score."""
        # Weighted scoring system
        weights = {
            "win_rate": 0.25,
            "total_return": 0.30,
            "sharpe_ratio": 0.20,
            "max_drawdown": 0.15,  # Negative impact
            "total_trades": 0.10
        }
        
        # Normalize metrics to 0-100 scale
        normalized = {
            "win_rate": min(100, max(0, metrics["win_rate"])),
            "total_return": min(100, max(-50, metrics["total_return"] + 50)),  # Shift to positive
            "sharpe_ratio": min(100, max(0, (metrics["sharpe_ratio"] + 2) * 25)),  # Scale
            "max_drawdown": min(100, max(0, 100 + metrics["max_drawdown"])),  # Invert (less drawdown = better)
            "total_trades": min(100, metrics["total_trades"] * 2)  # More trades = better (to a point)
        }
        
        score = sum(normalized[key] * weights[key] for key in weights.keys())
        return score

def optimize_parameters() -> Tuple[BacktestConfig, Dict[str, Any]]:
    """Optimize bot parameters using grid search."""
    print("🔧 Starting parameter optimization...")
    
    # Define parameter ranges for optimization
    param_ranges = {
        "min_signal_strength": [1.5, 2.0, 2.5, 3.0],
        "min_confluence_points": [1, 2],
        "directional_bias_multiplier": [1.05, 1.1, 1.15, 1.2],
        "rsi_range": [(30, 80), (35, 85), (25, 90)],
        "volume_ratio_threshold": [1.0, 1.1, 1.2, 1.3],
        "price_momentum_threshold": [0.003, 0.005, 0.007, 0.010],
        "stop_loss_pct": [1.5, 2.0, 2.5, 3.0],
        "take_profit_1_pct": [1.0, 1.5, 2.0],
        "take_profit_2_pct": [2.5, 3.0, 3.5],
        "max_leverage": [10, 15, 20, 25]
    }
    
    # Generate parameter combinations (sample due to computational constraints)
    print("  📋 Generating parameter combinations...")
    
    # Use random sampling for efficiency
    num_tests = 50  # Limit to manageable number
    best_config = None
    best_score = -float('inf')
    best_results = None
    
    results = []
    
    for test_num in range(num_tests):
        print(f"  🧪 Test {test_num + 1}/{num_tests}")
        
        # Generate random configuration
        config = BacktestConfig(
            min_signal_strength=np.random.choice(param_ranges["min_signal_strength"]),
            min_confluence_points=np.random.choice(param_ranges["min_confluence_points"]),
            directional_bias_multiplier=np.random.choice(param_ranges["directional_bias_multiplier"]),
            rsi_range=np.random.choice(param_ranges["rsi_range"]),
            volume_ratio_threshold=np.random.choice(param_ranges["volume_ratio_threshold"]),
            price_momentum_threshold=np.random.choice(param_ranges["price_momentum_threshold"]),
            stop_loss_pct=np.random.choice(param_ranges["stop_loss_pct"]),
            take_profit_1_pct=np.random.choice(param_ranges["take_profit_1_pct"]),
            take_profit_2_pct=np.random.choice(param_ranges["take_profit_2_pct"]),
            max_leverage=np.random.choice(param_ranges["max_leverage"])
        )
        
        # Run backtest
        engine = BacktestEngine(initial_capital=10000)
        result = engine.run_backtest(["BTCUSDT", "ETHUSDT"], config, days=14)
        
        results.append(result)
        
        if result["score"] > best_score:
            best_score = result["score"]
            best_config = config
            best_results = result
            
        print(f"    📈 Score: {result['score']:.1f}, Return: {result['total_return']:+.1f}%")
    
    print(f"\n🏆 Optimization complete!")
    print(f"   Best Score: {best_score:.1f}")
    print(f"   Best Return: {best_results['total_return']:+.1f}%")
    
    return best_config, best_results, results

def run_comprehensive_backtest():
    """Run comprehensive backtest and optimization."""
    print("🚀 CRYPTO SIGNAL BOT - COMPREHENSIVE BACKTEST")
    print("=" * 60)
    
    # Test with current (relaxed) parameters
    print("\n📊 Testing current relaxed parameters...")
    current_config = BacktestConfig()
    
    engine = BacktestEngine(initial_capital=10000)
    current_results = engine.run_backtest(["BTCUSDT", "ETHUSDT", "ADAUSDT"], current_config, days=21)
    
    print(f"\n📈 CURRENT CONFIG RESULTS:")
    print(f"   Total Trades: {current_results['total_trades']}")
    print(f"   Win Rate: {current_results['win_rate']:.1f}%")
    print(f"   Total Return: {current_results['total_return']:+.1f}%")
    print(f"   Final Capital: ${current_results['final_capital']:,.2f}")
    print(f"   Max Drawdown: {current_results['max_drawdown']:.1f}%")
    print(f"   Sharpe Ratio: {current_results['sharpe_ratio']:.2f}")
    print(f"   Score: {current_results['score']:.1f}")
    
    # Run optimization
    print(f"\n🔧 Running parameter optimization...")
    best_config, best_results, all_results = optimize_parameters()
    
    print(f"\n🎯 OPTIMIZATION RESULTS:")
    print(f"   Best Score: {best_results['score']:.1f}")
    print(f"   Best Return: {best_results['total_return']:+.1f}%")
    print(f"   Best Win Rate: {best_results['win_rate']:.1f}%")
    print(f"   Max Drawdown: {best_results['max_drawdown']:.1f}%")
    
    print(f"\n🏆 OPTIMAL CONFIGURATION:")
    print(f"   Signal Strength: {best_config.min_signal_strength}")
    print(f"   Confluence Points: {best_config.min_confluence_points}")
    print(f"   RSI Range: {best_config.rsi_range}")
    print(f"   Volume Threshold: {best_config.volume_ratio_threshold}")
    print(f"   Stop Loss: {best_config.stop_loss_pct}%")
    print(f"   Max Leverage: {best_config.max_leverage}x")
    
    # Performance comparison
    improvement = best_results['score'] - current_results['score']
    return_improvement = best_results['total_return'] - current_results['total_return']
    
    print(f"\n📊 IMPROVEMENT ANALYSIS:")
    print(f"   Score Improvement: {improvement:+.1f} points")
    print(f"   Return Improvement: {return_improvement:+.1f}%")
    
    if improvement > 10:
        print(f"   ✅ SIGNIFICANT IMPROVEMENT FOUND!")
        print(f"   💡 Recommend updating bot parameters")
    elif improvement > 5:
        print(f"   ⚠️  MODERATE IMPROVEMENT FOUND")
        print(f"   💭 Consider testing optimal config in paper trading")
    else:
        print(f"   ℹ️  CURRENT CONFIG IS REASONABLY OPTIMAL")
        print(f"   👍 No major changes needed")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"backtest_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "current_results": current_results,
            "best_results": best_results,
            "best_config": best_config.__dict__,
            "all_results": [r for r in all_results][:10]  # Top 10 results
        }, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    print(f"\n✅ Backtest complete!")
    
    return best_config, best_results

if __name__ == "__main__":
    best_config, best_results = run_comprehensive_backtest() 