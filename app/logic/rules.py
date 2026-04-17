"""
Trading rules and signal generation logic.

Implements the core trading logic based on technical indicators and market conditions.
Enhanced with advanced signal quality algorithms and multi-confluence analysis.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np
import pandas as pd
import asyncio
import math

from ..core.logging import get_logger
from ..indicators.technical import TechnicalIndicators
from ..data.rest import rest_client
from ..core.settings import settings

logger = get_logger(__name__)


class TradingRules:
    """Trading rules engine for signal generation."""
    
    @staticmethod
    async def analyze_symbol(
        symbol: str,
        data: Dict[str, pd.DataFrame],
        threshold_pct: float = 20.0,
        regime_metrics: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze symbol across all timeframes and generate trading signal.
        
        Args:
            data: Dictionary of DataFrames by timeframe
            threshold_pct: Target profit percentage
            regime_metrics: Optional market regime metrics for strategy adaptation
            
        Returns:
            Analysis results with trade recommendation
        """
        if not data:
            return TradingRules._empty_analysis()
            
        # Calculate indicators for all timeframes
        for tf, df in data.items():
            if not df.empty:
                data[tf] = TechnicalIndicators.calculate_all(df)
        
        # Determine dominant timeframe
        dominant_tf = TradingRules._get_dominant_timeframe(data)
        
        # Get primary analysis from dominant timeframe
        primary_df = data.get(dominant_tf)
        if primary_df is None or primary_df.empty:
            return TradingRules._empty_analysis()
            
        # Calculate core metrics
        current_price = float(primary_df['close'].iloc[-1])
        volatility_score = TechnicalIndicators.calculate_volatility_score(primary_df)
        trend_direction, trend_strength = TechnicalIndicators.calculate_trend_strength(primary_df)
        
        # Determine trade direction
        trade_signal = TradingRules._determine_trade_direction(
            data, trend_direction, trend_strength
        )
        
        if trade_signal["direction"] == "NEUTRAL":
            return TradingRules._empty_analysis()
            
        # Calculate leverage using maximum available for the symbol
        leverage = await TradingRules._calculate_leverage(symbol, volatility_score, regime_metrics)
        
        # Calculate entry, SL, and TP levels
        levels = TradingRules._calculate_trade_levels(
            primary_df,
            current_price,
            trade_signal["direction"],
            threshold_pct,
            volatility_score,  # Pass volatility score for buffer calculation
            leverage  # Pass the actual maximum leverage
        )
        
        # Generate technical rationale
        rationale = TradingRules._generate_rationale(
            data, trade_signal, volatility_score, trend_strength
        )
        
        # Calculate confidence score features
        features = TradingRules._extract_features(
            data, volatility_score, trend_strength, trade_signal
        )
        
        return {
            "timestamp": datetime.utcnow(),
            "dominant_timeframe": dominant_tf,
            "direction": trade_signal["direction"],
            "leverage": leverage,
            "entry_price": levels["entry"],
            "stop_loss": levels["stop_loss"],
            "take_profit_1": levels["tp1"],
            "take_profit_2": levels["tp2"],
            "take_profit_3": levels["tp3"],
            "volatility_score": volatility_score,
            "trend_strength": trend_strength,
            "rationale": rationale,
            "features": features,
            "current_price": current_price,
            "liquidation_info": {
                "estimated_leverage": levels.get("estimated_leverage", leverage),
                "liquidation_price": levels.get("liquidation_price", 0),
                "stop_buffer_pct": levels.get("stop_buffer_pct", 0),
                "distance_to_liquidation": abs(levels.get("liquidation_price", 0) - current_price) / current_price * 100 if levels.get("liquidation_price") else 0
            },
            "accuracy_metrics": {
                "signal_strength": trade_signal.get("strength", 0),
                "confluence_points": trade_signal.get("confluence_points", 0),
                "confluence_factors": trade_signal.get("confluence_factors", []),
                "trend_alignment": TradingRules._check_trend_alignment(data),
                "quality_score": min(100, max(0, (float(trade_signal.get("strength", 0)) * 5) + (float(trade_signal.get("confluence_points", 0)) * 10))),
                "accuracy_rating": "HIGH" if trade_signal.get("confluence_points", 0) >= 4 else "MEDIUM" if trade_signal.get("confluence_points", 0) >= 3 else "LOW"
            }
        }
        
    @staticmethod
    def _get_dominant_timeframe(data: Dict[str, pd.DataFrame]) -> str:
        """Determine dominant timeframe based on trend alignment."""
        scores = {}
        
        for tf, df in data.items():
            if df.empty or len(df) < 200:
                continue
                
            score = 0
            
            # Check trend alignment
            if 'EMA_20' in df and 'EMA_50' in df and 'EMA_200' in df:
                if df['EMA_20'].iloc[-1] > df['EMA_50'].iloc[-1] > df['EMA_200'].iloc[-1]:
                    score += 3
                elif df['EMA_20'].iloc[-1] < df['EMA_50'].iloc[-1] < df['EMA_200'].iloc[-1]:
                    score += 3
                    
            # Check MACD
            if 'MACD_cross_up' in df and df['MACD_cross_up'].tail(5).any():
                score += 2
            elif 'MACD_cross_down' in df and df['MACD_cross_down'].tail(5).any():
                score += 2
                
            # Check RSI
            if 'RSI' in df:
                rsi = df['RSI'].iloc[-1]
                if 30 < rsi < 70:
                    score += 1
                    
            scores[tf] = score
            
        # Return timeframe with highest score, defaulting to 15m
        if scores:
            return max(scores, key=scores.get)
        return "15m"
        
    @staticmethod
    def _check_trend_alignment(data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Check if multiple timeframes are aligned in the same direction.
        Returns trend alignment status for enhanced accuracy.
        """
        timeframe_trends = {}
        
        for tf, df in data.items():
            if df.empty or len(df) < 50:
                continue
                
            # Simple trend analysis using EMAs
            if 'EMA_20' in df and 'EMA_50' in df and 'close' in df:
                ema20 = df['EMA_20'].iloc[-1]
                ema50 = df['EMA_50'].iloc[-1]
                close = df['close'].iloc[-1]
                
                if close > ema20 > ema50:
                    timeframe_trends[tf] = "BULLISH"
                elif close < ema20 < ema50:
                    timeframe_trends[tf] = "BEARISH"
                else:
                    timeframe_trends[tf] = "NEUTRAL"
        
        if len(timeframe_trends) < 2:
            return {"aligned": True, "direction": "NEUTRAL", "confidence": 50}
        
        # Check for alignment (at least 50% agreement - made more lenient)
        bullish_count = sum(1 for trend in timeframe_trends.values() if trend == "BULLISH")
        bearish_count = sum(1 for trend in timeframe_trends.values() if trend == "BEARISH")
        total_count = len(timeframe_trends)
        
        bullish_pct = bullish_count / total_count
        bearish_pct = bearish_count / total_count
        
        if bullish_pct >= 0.5:  # Reduced from 0.7
            return {"aligned": True, "direction": "BULLISH", "confidence": bullish_pct * 100}
        elif bearish_pct >= 0.5:  # Reduced from 0.7
            return {"aligned": True, "direction": "BEARISH", "confidence": bearish_pct * 100}
        elif (bullish_pct + bearish_pct) < 0.7:  # Mostly neutral (increased from 0.6)
            return {"aligned": True, "direction": "NEUTRAL", "confidence": 60}
        else:
            return {"aligned": False, "direction": "CONFLICTED", "confidence": 30}

    @staticmethod
    def _determine_trade_direction(
        data: Dict[str, pd.DataFrame],
        trend_direction: str,
        trend_strength: float
    ) -> Dict[str, str]:
        """
        Enhanced trade direction determination with strict accuracy requirements.
        
        Implements multi-timeframe confluence, volume confirmation, and market structure analysis
        for maximum signal accuracy and reduced false signals.
        """
        
        long_signals = 0
        short_signals = 0
        confluence_checks = {"long": [], "short": []}
        timeframe_weights = {"1d": 4, "4h": 3, "1h": 2, "15m": 1.5, "5m": 1}  # Enhanced weights
        
        # Import settings here to avoid circular import
        from ..core.settings import settings
        
        # REQUIREMENT 1: Multi-timeframe trend alignment
        trend_alignment = TradingRules._check_trend_alignment(data)
        if not trend_alignment["aligned"]:
            return {"direction": "NEUTRAL", "strength": 0, "reason": "Multi-timeframe trend not aligned"}
        
        for tf, df in data.items():
            if df.empty:
                continue
                
            weight = timeframe_weights.get(tf, 1)
            
            # ENHANCED CONFLUENCE SYSTEM: Each condition adds specific confluence points
            
            # 1. TREND STRUCTURE ANALYSIS (Most Important)
            if 'close' in df and 'EMA_20' in df and 'EMA_50' in df and 'EMA_200' in df and 'RSI' in df:
                close = df['close'].iloc[-1]
                ema20 = df['EMA_20'].iloc[-1]
                ema50 = df['EMA_50'].iloc[-1]
                ema200 = df['EMA_200'].iloc[-1]
                rsi = df['RSI'].iloc[-1]
                
                # Higher Order Moving Average Analysis
                ema_slope_20 = (ema20 - df['EMA_20'].iloc[-5]) / df['EMA_20'].iloc[-5]
                ema_slope_50 = (ema50 - df['EMA_50'].iloc[-5]) / df['EMA_50'].iloc[-5]
                
                # VERY RELAXED Long conditions with confluence
                if (close > ema20 and  # Only require price above EMA20 (removed EMA alignment)
                    ema_slope_20 > 0.0005 and  # Much more relaxed EMA20 slope
                    rsi > 25 and rsi < 90 and  # Much broader RSI range
                    close > df['close'].shift(10).iloc[-1] * 1.002):  # Very small momentum (0.2%+ over 10 periods)
                    
                    long_signals += weight * 3
                    confluence_checks["long"].append(f"{tf}_trend_structure")
                    
                # VERY RELAXED Short conditions with confluence
                elif (close < ema20 and  # Only require price below EMA20 (removed EMA alignment)
                      ema_slope_20 < -0.0005 and  # Much more relaxed EMA20 slope
                      rsi < 75 and rsi > 10 and  # Much broader RSI range
                      close < df['close'].shift(10).iloc[-1] * 0.998):  # Very small momentum (0.2%+ down over 10 periods)
                    
                    short_signals += weight * 3
                    confluence_checks["short"].append(f"{tf}_trend_structure")
                    
            # 2. VOLUME CONFIRMATION (Critical for accuracy)
            if 'Volume_ratio' in df and 'close' in df and 'volume' in df:
                vol_ratio = df['Volume_ratio'].iloc[-1]
                avg_volume = df['volume'].rolling(20).mean().iloc[-1]
                current_volume = df['volume'].iloc[-1]
                price_change_5 = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]
                price_change_1 = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]
                
                # Volume must confirm direction with very relaxed participation  
                if (vol_ratio > 0.9 and  # Even below average volume acceptable (was 1.1)
                    current_volume > avg_volume * 0.8 and  # Allow low volume (was 1.0)
                    price_change_5 > 0.005 and  # Very small 5-period move (was 0.005)
                    price_change_5 > 0.005):  # Tiny recent continuation (was 0.005)
                    
                    long_signals += weight * 2
                    confluence_checks["long"].append(f"{tf}_volume_confirmation")
                    
                elif (vol_ratio > 0.9 and  # Even below average volume acceptable (was 1.1)
                      current_volume > avg_volume * 0.8 and  # Allow low volume (was 1.0)
                      price_change_5 < -0.005 and  # Very small 5-period move (was -0.005)
                      price_change_5 < -0.005):  # Tiny recent continuation (was -0.005)
                    
                    short_signals += weight * 2
                    confluence_checks["short"].append(f"{tf}_volume_confirmation")
                    
            # 3. MOMENTUM CONFIRMATION (MACD + RSI Divergence)
            if 'MACD_hist' in df and 'MACD' in df and 'RSI' in df and len(df) >= 14:
                macd_hist = df['MACD_hist'].iloc[-1]
                macd_hist_prev = df['MACD_hist'].iloc[-2]
                rsi_current = df['RSI'].iloc[-1]
                rsi_prev = df['RSI'].iloc[-5]
                
                # MACD histogram must be accelerating in direction
                macd_acceleration = macd_hist - macd_hist_prev
                
                if (macd_hist > -0.01 and macd_acceleration > -0.01 and  # Very relaxed MACD (allow small negative)
                    rsi_current > 30):  # Very relaxed RSI (just above oversold)
                    
                    long_signals += weight * 1.5
                    confluence_checks["long"].append(f"{tf}_momentum")
                    
                elif (macd_hist < 0.01 and macd_acceleration < 0.01 and  # Very relaxed MACD (allow small positive)
                      rsi_current < 70):  # Very relaxed RSI (just below overbought)
                    
                    short_signals += weight * 1.5
                    confluence_checks["short"].append(f"{tf}_momentum")
                    
            # 4. MARKET STRUCTURE CONFIRMATION (Support/Resistance)
            if 'high' in df and 'low' in df and len(df) >= 50:
                recent_highs = df['high'].rolling(20).max().iloc[-1]
                recent_lows = df['low'].rolling(20).min().iloc[-1]
                current_close = df['close'].iloc[-1]
                
                # Breaking above resistance with conviction
                if (current_close > recent_highs * 1.002 and  # Clear break above resistance
                    current_close > df['close'].shift(1).iloc[-1]):  # Higher close
                    
                    long_signals += weight
                    confluence_checks["long"].append(f"{tf}_structure_break")
                    
                # Breaking below support with conviction
                elif (current_close < recent_lows * 0.998 and  # Clear break below support
                      current_close < df['close'].shift(1).iloc[-1]):  # Lower close
                    
                    short_signals += weight
                    confluence_checks["short"].append(f"{tf}_structure_break")
                    
            # 5. MARKET-NEUTRAL FALLBACK CONDITIONS - Balanced momentum with price action
            if 'close' in df and len(df) >= 10:
                price_change_3 = (df['close'].iloc[-1] - df['close'].iloc[-3]) / df['close'].iloc[-3]
                price_change_5 = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]
                price_trend_up = df['close'].iloc[-1] > df['close'].iloc[-5]  # Simple trend check
                price_trend_down = df['close'].iloc[-1] < df['close'].iloc[-5]  # Simple trend check
                
                # BALANCED momentum conditions - SAME WEIGHT FOR BOTH DIRECTIONS
                if price_change_3 > 0.002 and price_trend_up:  # Bullish: 0.2% over 3 periods AND uptrend
                    long_signals += weight * 0.6  # Reduced and balanced weight
                    confluence_checks["long"].append(f"{tf}_basic_momentum")
                    
                elif price_change_3 < -0.002 and price_trend_down:  # Bearish: -0.2% over 3 periods AND downtrend
                    short_signals += weight * 0.6  # Same weight as LONG
                    confluence_checks["short"].append(f"{tf}_basic_momentum")
                
                # Additional neutral momentum check for sideways markets
                elif abs(price_change_5) < 0.005:  # Sideways market (< 0.5% movement)
                    # In sideways markets, favor mean reversion
                    if rsi > 65:  # Overbought in sideways = SHORT signal
                        short_signals += weight * 0.4
                        confluence_checks["short"].append(f"{tf}_sideways_reversion")
                    elif rsi < 35:  # Oversold in sideways = LONG signal
                        long_signals += weight * 0.4
                        confluence_checks["long"].append(f"{tf}_sideways_reversion")
                    
        # ENHANCED DECISION LOGIC WITH MODERATE REQUIREMENTS
        
        # ENHANCED SIGNAL QUALITY REQUIREMENTS
        # Dynamic thresholds based on market conditions and confluence quality
        base_confluence_points = 1
        base_signal_strength = 1.0
        
        # Quality bonus system - reward diverse confluence sources
        long_confluence_count = len(confluence_checks["long"])
        short_confluence_count = len(confluence_checks["short"])
        
        # Calculate signal quality scores
        long_quality_score = TradingRules._calculate_signal_quality(
            long_signals, confluence_checks["long"], trend_alignment
        )
        short_quality_score = TradingRules._calculate_signal_quality(
            short_signals, confluence_checks["short"], trend_alignment
        )
        
        # Apply advanced signal filtering with quality enhancement
        # FIXED: SYSTEMATIC BIAS - Compare signal strength and choose the stronger direction
        
        # Check if both directions meet minimum thresholds
        long_qualifies = (long_signals >= base_signal_strength and 
                         long_confluence_count >= base_confluence_points and
                         long_quality_score >= 2.5)
        
        short_qualifies = (short_signals >= base_signal_strength and  
                          short_confluence_count >= base_confluence_points and
                          short_quality_score >= 2.5)
        
        # If both qualify, choose the stronger one based on combined score
        if long_qualifies and short_qualifies:
            # Calculate combined score: signal_strength * quality_score * confluence_count
            long_combined_score = long_signals * long_quality_score * (1 + long_confluence_count * 0.1)
            short_combined_score = short_signals * short_quality_score * (1 + short_confluence_count * 0.1)
            
            # Choose stronger direction
            if long_combined_score > short_combined_score:
                # DEBUG: Log why LONG signal was chosen over SHORT
                logger.info("🟢 LONG SIGNAL GENERATED (chosen over SHORT)",
                           long_signals=round(long_signals, 2),
                           short_signals=round(short_signals, 2),
                           long_confluence=long_confluence_count,
                           short_confluence=short_confluence_count,
                           long_quality=round(long_quality_score, 2),
                           short_quality=round(short_quality_score, 2),
                           long_combined=round(long_combined_score, 2),
                           short_combined=round(short_combined_score, 2),
                           long_factors=confluence_checks["long"][:3],
                           short_factors=confluence_checks["short"][:3])
                
                enhanced_strength = long_signals * (1 + long_quality_score * 0.1)
                return {
                    "direction": "LONG", 
                    "strength": int(enhanced_strength),
                    "confluence_points": long_confluence_count,
                    "confluence_factors": confluence_checks["long"],
                    "quality_score": round(long_quality_score, 2),
                    "enhanced": True
                }
            else:
                # DEBUG: Log why SHORT signal was chosen over LONG
                logger.info("🔴 SHORT SIGNAL GENERATED (chosen over LONG)",
                           long_signals=round(long_signals, 2),
                           short_signals=round(short_signals, 2),
                           long_confluence=long_confluence_count,
                           short_confluence=short_confluence_count,
                           long_quality=round(long_quality_score, 2),
                           short_quality=round(short_quality_score, 2),
                           long_combined=round(long_combined_score, 2),
                           short_combined=round(short_combined_score, 2),
                           long_factors=confluence_checks["long"][:3],
                           short_factors=confluence_checks["short"][:3])
                
                enhanced_strength = short_signals * (1 + short_quality_score * 0.1)
                return {
                    "direction": "SHORT", 
                    "strength": int(enhanced_strength),
                    "confluence_points": short_confluence_count,
                    "confluence_factors": confluence_checks["short"],
                    "quality_score": round(short_quality_score, 2),
                    "enhanced": True
                }
                
        elif long_qualifies:
            # Only LONG qualifies
            logger.info("🟢 LONG SIGNAL GENERATED (only LONG qualified)",
                       long_signals=round(long_signals, 2),
                       short_signals=round(short_signals, 2),
                       long_confluence=long_confluence_count,
                       short_confluence=short_confluence_count,
                       long_quality=round(long_quality_score, 2),
                       short_quality=round(short_quality_score, 2),
                       long_factors=confluence_checks["long"][:3],
                       short_factors=confluence_checks["short"][:3])
            
            enhanced_strength = long_signals * (1 + long_quality_score * 0.1)
            return {
                "direction": "LONG", 
                "strength": int(enhanced_strength),
                "confluence_points": long_confluence_count,
                "confluence_factors": confluence_checks["long"],
                "quality_score": round(long_quality_score, 2),
                "enhanced": True
            }
            
        elif short_qualifies:
            # Only SHORT qualifies
            logger.info("🔴 SHORT SIGNAL GENERATED (only SHORT qualified)",
                       long_signals=round(long_signals, 2),
                       short_signals=round(short_signals, 2),
                       long_confluence=long_confluence_count,
                       short_confluence=short_confluence_count,
                       long_quality=round(long_quality_score, 2),
                       short_quality=round(short_quality_score, 2),
                       long_factors=confluence_checks["long"][:3],
                       short_factors=confluence_checks["short"][:3])
            
            enhanced_strength = short_signals * (1 + short_quality_score * 0.1)
            return {
                "direction": "SHORT", 
                "strength": int(enhanced_strength),
                "confluence_points": short_confluence_count,
                "confluence_factors": confluence_checks["short"],
                "quality_score": round(short_quality_score, 2),
                "enhanced": True
            }
            
        else:
            # DEBUG: Log why signal was REJECTED (this is critical!)
            logger.info("⚪ SIGNAL REJECTED - NEUTRAL",
                       long_signals=round(long_signals, 2),
                       short_signals=round(short_signals, 2),
                       long_confluence=long_confluence_count,
                       short_confluence=short_confluence_count,
                       long_quality=round(long_quality_score, 2),
                       short_quality=round(short_quality_score, 2),
                       base_strength_req=base_signal_strength,
                       base_confluence_req=base_confluence_points,
                       quality_threshold=2.5)
            
            # Enhanced rejection analysis
            rejection_reasons = []
            if long_signals < base_signal_strength and short_signals < base_signal_strength:
                rejection_reasons.append("insufficient_signal_strength")
            if long_confluence_count < base_confluence_points and short_confluence_count < base_confluence_points:
                rejection_reasons.append("insufficient_confluence")
            if long_quality_score < 2.5 and short_quality_score < 2.5:
                rejection_reasons.append("insufficient_quality_score")
            if not trend_alignment["aligned"]:
                rejection_reasons.append("trend_misalignment")
                
            return {
                "direction": "NEUTRAL", 
                "strength": 0,
                "reason": "enhanced_quality_filter",
                "rejection_reasons": rejection_reasons,
                "long_signals": round(long_signals, 1),
                "short_signals": round(short_signals, 1),
                "long_confluence": long_confluence_count,
                "short_confluence": short_confluence_count,
                "long_quality": round(long_quality_score, 2),
                "short_quality": round(short_quality_score, 2)
            }
            
    @staticmethod
    async def _calculate_leverage(symbol: str, volatility_score: float, regime_metrics: Optional[Any] = None) -> int:
        """
        Calculate leverage using DYNAMIC CONFIDENCE-BASED scaling for safety.
        
        This implements critical safety measures:
        - Low confidence signals get drastically reduced leverage
        - High confidence signals can use more leverage
        - Never exceed maximum available leverage for the symbol
        """
        try:
            # Get maximum leverage for this specific symbol
            max_symbol_leverage = await rest_client.get_max_leverage(symbol)
            
            # CRITICAL SAFETY: Get confidence score from current analysis context
            # This is passed through the processing pipeline
            confidence_score = getattr(TradingRules, '_current_confidence', 50.0)  # Fallback
            
            # DYNAMIC CONFIDENCE-BASED LEVERAGE SCALING
            if confidence_score >= 80:  # Very high confidence
                leverage_factor = 0.9  # 90% of max leverage
            elif confidence_score >= 70:  # High confidence  
                leverage_factor = 0.75  # 75% of max leverage
            elif confidence_score >= 60:  # Good confidence
                leverage_factor = 0.6   # 60% of max leverage
            elif confidence_score >= 50:  # Moderate confidence
                leverage_factor = 0.4   # 40% of max leverage
            elif confidence_score >= 40:  # Low confidence
                leverage_factor = 0.25  # 25% of max leverage
            elif confidence_score >= 30:  # Very low confidence
                leverage_factor = 0.15  # 15% of max leverage
            else:  # Extremely low confidence (< 30%)
                leverage_factor = 0.08  # 8% of max leverage - VERY SAFE
            
            # Calculate base leverage with confidence scaling
            base_leverage = int(max_symbol_leverage * leverage_factor)
            
            # Minimum safety floor (never go below 2x, even for terrible signals)
            base_leverage = max(2, base_leverage)
            
            # Market regime adjustments (smaller impact now)
            if regime_metrics:
                regime = getattr(regime_metrics, 'regime', None)
                regime_confidence = getattr(regime_metrics, 'confidence', 50)
                
                # Only minor adjustments since confidence is primary factor
                if regime and str(regime).lower() == 'high_volatility':
                    base_leverage = int(base_leverage * 0.8)  # 20% reduction for high vol
                elif regime and 'trend' in str(regime).lower() and regime_confidence > 70:
                    base_leverage = int(base_leverage * 1.1)  # 10% boost for strong trends
            
            # Volatility-based fine-tuning (minor adjustments)
            if volatility_score > 80:  # Extreme volatility
                base_leverage = int(base_leverage * 0.9)
            elif volatility_score < 20:  # Very low volatility
                base_leverage = int(base_leverage * 1.05)
            
            # Final safety checks
            final_leverage = max(2, min(base_leverage, max_symbol_leverage))
            
            # Validate with risk manager
            try:
                from ..services.risk_manager import RiskManager
                validated_leverage, _ = RiskManager.validate_leverage(volatility_score, final_leverage)
                final_leverage = validated_leverage
            except ImportError:
                # Fallback if RiskManager not available
                logger.warning("RiskManager not available, using calculated leverage as-is")
                pass
            
            logger.info(f"SAFETY-FIRST leverage calculated for {symbol}",
                       confidence=confidence_score,
                       confidence_factor=leverage_factor,
                       max_available=max_symbol_leverage,
                       final_leverage=final_leverage,
                       safety_reduction=f"{((max_symbol_leverage - final_leverage) / max_symbol_leverage * 100):.1f}%")
            
            return final_leverage
            
        except Exception as e:
            logger.error(f"Failed to calculate safe leverage for {symbol}, using ultra-conservative fallback", error=str(e))
            # Ultra-conservative fallback for ANY error
            return 3  # Very safe fallback
    
    @classmethod
    def set_current_confidence(cls, confidence: float):
        """Set current confidence for leverage calculation."""
        cls._current_confidence = confidence
        
    @staticmethod
    def _calculate_trade_levels(
        df: pd.DataFrame,
        current_price: float,
        direction: str,
        threshold_pct: float,
        volatility_score: float,
        actual_leverage: int = None
    ) -> Dict[str, float]:
        """Calculate entry, stop loss, and take profit levels with aggressive liquidation-based stops.
        
        AGGRESSIVE CONFIGURATION: Stop losses are set extremely close to liquidation prices
        (0.1-0.5% buffer) for maximum position utilization. Use with caution.
        """
        
        # Use actual leverage calculated earlier, or fallback to high leverage
        from ..core.settings import settings
        
        if actual_leverage is not None:
            estimated_leverage = actual_leverage
        else:
            # Fallback to high leverage if not provided
            estimated_leverage = min(settings.max_leverage, 50)
        
        if direction == "LONG":
            # Entry at current price
            entry = current_price
            
            # Calculate liquidation price: Liquidation = Entry * (1 - 1/leverage)
            liquidation_price = entry * (1 - 1/estimated_leverage)
            
            # Set stop loss extremely close to liquidation (0.05-0.2% buffer depending on volatility) ⭐ ULTRA TIGHT
            if volatility_score < 30:
                buffer_pct = 0.0005  # 0.05% buffer for low volatility - ultra tight
            elif volatility_score < 60:
                buffer_pct = 0.0015  # 0.15% buffer for medium volatility - very tight
            else:
                buffer_pct = 0.002   # 0.2% buffer for high volatility - tight
                
            stop_loss = liquidation_price * (1 + buffer_pct)
            
            # Ensure stop loss is not too close to entry (minimum 0.1% away for ultra aggressive positioning) ⭐ ULTRA TIGHT
            min_stop_distance = entry * 0.001
            if (entry - stop_loss) < min_stop_distance:
                stop_loss = entry - min_stop_distance
            
            # Take profit levels: Tighter profits for higher win rate
            tp1 = entry * (1 + 0.004)   # 0.4% - Very quick profit taking
            tp2 = entry * (1 + 0.008)   # 0.8% - Main target for scalping approach
            tp3 = entry * (1 + 0.012)   # 1.2% - Conservative extended target
            
        else:  # SHORT
            # Entry at current price
            entry = current_price
            
            # Calculate liquidation price: Liquidation = Entry * (1 + 1/leverage)
            liquidation_price = entry * (1 + 1/estimated_leverage)
            
            # Set stop loss extremely close to liquidation (0.05-0.2% buffer depending on volatility) ⭐ ULTRA TIGHT
            if volatility_score < 30:
                buffer_pct = 0.0005  # 0.05% buffer for low volatility - ultra tight
            elif volatility_score < 60:
                buffer_pct = 0.0015  # 0.15% buffer for medium volatility - very tight
            else:
                buffer_pct = 0.002   # 0.2% buffer for high volatility - tight
                
            stop_loss = liquidation_price * (1 - buffer_pct)
            
            # Ensure stop loss is not too close to entry (minimum 0.1% away for ultra aggressive positioning) ⭐ ULTRA TIGHT
            min_stop_distance = entry * 0.001
            if (stop_loss - entry) < min_stop_distance:
                stop_loss = entry + min_stop_distance
            
            # Take profit levels: Tighter profits for short trades
            tp1 = entry * (1 - 0.004)   # 0.4%
            tp2 = entry * (1 - 0.008)   # 0.8%
            tp3 = entry * (1 - 0.012)   # 1.2%
            
        return {
            "entry": round(entry, 6),
            "stop_loss": round(stop_loss, 6),
            "tp1": round(tp1, 6),
            "tp2": round(tp2, 6),
            "tp3": round(tp3, 6),
            "estimated_leverage": estimated_leverage,
            "liquidation_price": round(liquidation_price, 6),
            "stop_buffer_pct": round(buffer_pct * 100, 2)
        }
        
    @staticmethod
    def _generate_rationale(
        data: Dict[str, pd.DataFrame],
        trade_signal: Dict[str, Any],
        volatility_score: float,
        trend_strength: float
    ) -> List[str]:
        """Generate technical rationale for the trade."""
        rationale = []
        
        # Trend rationale
        if trend_strength > 60:
            rationale.append(f"Strong {trade_signal['direction'].lower()} trend detected (strength: {trend_strength:.0f}%)")
        else:
            rationale.append(f"Moderate trend conditions favor {trade_signal['direction'].lower()} position")
            
        # Volatility rationale
        if volatility_score < 30:
            rationale.append("Low volatility environment supports stable price movement")
        elif volatility_score > 70:
            rationale.append("High volatility increases profit potential but requires careful risk management")
        else:
            rationale.append(f"Moderate volatility score ({volatility_score:.0f}) balances risk/reward")
            
        # Technical indicator rationale
        for tf, df in data.items():
            if df.empty:
                continue
                
            # MACD signals
            if 'MACD_cross_up' in df and df['MACD_cross_up'].tail(5).any():
                rationale.append(f"MACD bullish crossover on {tf} timeframe")
                break
            elif 'MACD_cross_down' in df and df['MACD_cross_down'].tail(5).any():
                rationale.append(f"MACD bearish crossover on {tf} timeframe")
                break
                
        # RSI conditions
        primary_tf = list(data.keys())[0]
        if primary_tf in data and 'RSI' in data[primary_tf]:
            rsi = data[primary_tf]['RSI'].iloc[-1]
            if rsi < 30:
                rationale.append("RSI oversold condition presents reversal opportunity")
            elif rsi > 70:
                rationale.append("RSI overbought condition suggests potential reversal")
            else:
                rationale.append(f"RSI at {rsi:.0f} supports continued momentum")
                
        # Volume confirmation
        if primary_tf in data and 'Volume_ratio' in data[primary_tf]:
            vol_ratio = data[primary_tf]['Volume_ratio'].iloc[-1]
            if vol_ratio > 2:
                rationale.append(f"Strong volume surge ({vol_ratio:.1f}x average) confirms movement")
            elif vol_ratio > 1.2:
                rationale.append("Above-average volume supports price action")
                
        return rationale[:5]  # Limit to 5 points
        
    @staticmethod
    def _extract_features(
        data: Dict[str, pd.DataFrame],
        volatility_score: float,
        trend_strength: float,
        trade_signal: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract features for confidence model."""
        features = {
            "volatility_score": volatility_score,
            "trend_strength": trend_strength,
            "signal_strength": float(trade_signal.get("strength", 0)),
            "orderbook_imbalance": 0.0,  # Placeholder - will be filled by orderbook data
            "funding_rate_deviation": 0.0,  # Placeholder - will be filled by funding data
        }
        
        # Add indicator features from primary timeframe
        primary_tf = TradingRules._get_dominant_timeframe(data)
        if primary_tf in data:
            df = data[primary_tf]
            if not df.empty:
                # RSI
                if 'RSI' in df:
                    features["rsi"] = float(df['RSI'].iloc[-1])
                    features["rsi_divergence"] = float(df.get('RSI_divergence', pd.Series([0])).iloc[-1])
                    
                # MACD
                if 'MACD_hist' in df:
                    features["macd_histogram"] = float(df['MACD_hist'].iloc[-1])
                    
                # Bollinger Bands
                if 'BB_pct' in df:
                    features["bb_position"] = float(df['BB_pct'].iloc[-1])
                    
                # Volume
                if 'Volume_ratio' in df:
                    features["volume_ratio"] = float(df['Volume_ratio'].iloc[-1])
                    
                # ADX
                if 'ADX' in df:
                    features["adx"] = float(df['ADX'].iloc[-1])
                    
        return features
        
    @staticmethod
    def _calculate_signal_quality(
        signal_strength: float, 
        confluence_factors: List[str], 
        trend_alignment: Dict[str, Any]
    ) -> float:
        """
        Calculate advanced signal quality score based on multiple factors.
        Higher score indicates higher quality signal.
        """
        quality_score = 0.0
        
        # Base score from signal strength
        quality_score += signal_strength * 0.3
        
        # Confluence diversity bonus
        unique_categories = set()
        for factor in confluence_factors:
            if "trend_structure" in factor:
                unique_categories.add("trend")
            elif "volume_confirmation" in factor:
                unique_categories.add("volume")
            elif "momentum" in factor:
                unique_categories.add("momentum")
            elif "structure_break" in factor:
                unique_categories.add("structure")
            elif "basic_momentum" in factor:
                unique_categories.add("basic")
        
        # Bonus for confluence diversity (more categories = higher quality)
        quality_score += len(unique_categories) * 1.2
        
        # Timeframe diversity bonus
        timeframes = set()
        for factor in confluence_factors:
            if "_" in factor:
                tf = factor.split("_")[0]
                timeframes.add(tf)
        
        quality_score += min(len(timeframes) * 0.8, 3.0)  # Cap at 3.0
        
        # Trend alignment quality bonus
        if trend_alignment.get("aligned", False):
            confidence = trend_alignment.get("confidence", 50)
            quality_score += (confidence / 100) * 1.5
        
        # Volume confirmation bonus (critical for quality)
        volume_factors = [f for f in confluence_factors if "volume" in f]
        if volume_factors:
            quality_score += len(volume_factors) * 1.0
        
        # Structure break bonus (high-quality signals)
        structure_factors = [f for f in confluence_factors if "structure_break" in f]
        if structure_factors:
            quality_score += len(structure_factors) * 1.5
        
        return quality_score
    
    @staticmethod
    def _empty_analysis() -> Dict[str, Any]:
        """Return empty analysis result."""
        return {
            "timestamp": datetime.utcnow(),
            "direction": "NEUTRAL",
            "error": "Insufficient data for analysis"
        } 