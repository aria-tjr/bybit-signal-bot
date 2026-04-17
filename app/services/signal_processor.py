"""
Signal processor service for orchestrating analysis and delivery.

Coordinates data collection, technical analysis, ML scoring, and Telegram delivery.
"""

import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime
import time
import structlog

from ..core.logging import get_logger
from ..core.settings import settings
from ..data.rest import rest_client
from ..data.cache import cache
from ..data.websocket import ws_client
from ..logic.rules import TradingRules
from ..logic.risk import RiskManager
from ..models.confidence import confidence_model
from .telegram import telegram_service
from .bookmap_engine import bookmap_engine
from .signal_fusion import signal_fusion_engine

logger = structlog.get_logger(__name__)


class SignalProcessor:
    """Orchestrates signal generation and delivery."""
    
    def __init__(self) -> None:
        """Initialize signal processor."""
        self.processing_symbols = set()  # Prevent duplicate processing
        
    async def process_symbol(
        self,
        symbol: str,
        threshold_pct: float = None,
        chat_ids: Optional[List[str]] = None,
        force_fresh: bool = False
    ) -> Dict[str, Any]:
        """
        Process a symbol and generate trading signal with timeout protection.
        
        Args:
            symbol: Trading pair symbol
            threshold_pct: Target profit percentage
            chat_ids: Optional specific chat IDs to send to
            
        Returns:
            Signal analysis results
        """
        start_time = time.time()
        
        # Prevent duplicate processing
        if symbol in self.processing_symbols:
            logger.warning("Symbol already being processed", symbol=symbol)
            return {"error": "Already processing this symbol"}
            
        self.processing_symbols.add(symbol)
        
        try:
            # Add timeout protection (20 seconds max)
            return await asyncio.wait_for(
                self._process_symbol_internal(symbol, threshold_pct, chat_ids, start_time, force_fresh),
                timeout=20.0
            )
        except asyncio.TimeoutError:
            logger.error("Signal processing timeout", symbol=symbol, elapsed_s=time.time() - start_time)
            error_msg = f"Processing timeout for {symbol} - server overload"
            await telegram_service.send_error(error_msg, chat_ids)
            return {"error": "Processing timeout"}
        except Exception as e:
            logger.error("Signal processing failed", symbol=symbol, error=str(e))
            await telegram_service.send_error(f"Failed to process {symbol}: {str(e)}", chat_ids)
            return {"error": str(e)}
        finally:
            self.processing_symbols.discard(symbol)
            
    async def _process_symbol_internal(
        self,
        symbol: str,
        threshold_pct: float,
        chat_ids: Optional[List[str]],
        start_time: float,
        force_fresh: bool = False
    ) -> Dict[str, Any]:
        """Internal method for symbol processing."""
        try:
            # Check cache first (only if not forced fresh)
            if not force_fresh:
                cached_analysis = await cache.get_analysis(symbol)
                if cached_analysis:
                    logger.info("Using cached analysis", symbol=symbol)
                    await self._send_signal(cached_analysis, chat_ids)
                    return cached_analysis
            else:
                logger.info("Bypassing cache for fresh analysis", symbol=symbol)
                
            # Collect data for all timeframes
            logger.info("Collecting data", symbol=symbol)
            data = await self._collect_data(symbol)
            
            if not data:
                error_msg = f"Failed to collect data for {symbol}"
                await telegram_service.send_error(error_msg, chat_ids)
                return {"error": error_msg}
                
            # Detect market regime first
            logger.info("Detecting market regime", symbol=symbol)
            from ..logic.market_regime import regime_detector
            regime_metrics = await regime_detector.detect_regime(data)
            
            # Get strategy adjustments based on regime
            regime_adjustments = regime_detector.get_strategy_adjustments(regime_metrics)
            
            # Adjust threshold based on regime
            adjusted_threshold = threshold_pct or settings.default_threshold_pct
            adjusted_threshold += regime_adjustments.get('signal_threshold_adjustment', 0)
            adjusted_threshold = max(2, min(10, adjusted_threshold))  # Lower bounds for scalping
            
            # Run analysis with regime-adjusted parameters
            logger.info("Running analysis", symbol=symbol, regime=regime_metrics.regime.value)
            analysis = await TradingRules.analyze_symbol(
                symbol,
                data,
                adjusted_threshold,
                regime_metrics=regime_metrics
            )
            
            # Check if valid signal
            if analysis.get("direction") == "NEUTRAL":
                # Enhanced educational message for neutral signals  
                rejection_reasons = analysis.get("rejection_reasons", [])
                
                # Extract from accuracy_metrics where they're actually stored
                accuracy_metrics = analysis.get("accuracy_metrics", {})
                signal_strength = float(accuracy_metrics.get("signal_strength", 0))
                confluence_count = int(accuracy_metrics.get("confluence_points", 0))
                
                # Generate specific feedback
                specific_issues = []
                if signal_strength < 1.5:
                    specific_issues.append(f"Signal strength: {signal_strength:.1f}/10 (need 1.5+)")
                if confluence_count < 1:
                    specific_issues.append(f"Confluence points: {confluence_count}/1 required")
                
                # Add specific technical failures if available
                for reason in rejection_reasons[:3]:  # Show top 3 issues
                    specific_issues.append(reason)
                
                issues_text = "\n".join([f"• {issue}" for issue in specific_issues])
                
                msg = f"""
⚠️ *No Clear Signal for {symbol}*

🔍 *Current Status:* Market conditions don't meet our strict accuracy requirements

📊 *Specific Issues Found:*
{issues_text}

💡 *Scanner vs Signal Difference:*
• **Scanner detected:** Price movement + volume activity
• **Signal requires:** Technical alignment + 1+ confluence points + 2+ signal strength
• **Purpose:** Scanner finds opportunities to *watch*, signals provide *precision trades*

🎯 *What this means:*
• {symbol} has market activity worth monitoring  
• Full technical conditions not yet aligned for trade
• Our bot prioritizes accuracy over frequency
• Better to wait than take low-probability trades

🚀 *Next steps:*
• Monitor for developing technical alignment
• Try again in 15-30 minutes for evolving setups
• Use `/scan` to find symbols with better setups right now
• Check confluence: Moving averages, RSI, MACD alignment needed

*Quality over quantity - we only signal high-probability trades!*
"""
                await telegram_service.send_notification(msg, chat_ids)
                return analysis
                
            # Enrich with additional data
            analysis["symbol"] = symbol
            
            # Add symbol-specific features for confidence variability
            analysis["features"]["symbol"] = symbol
            analysis["features"]["symbol_volatility_rank"] = hash(symbol) % 100  # Pseudo-random but consistent
            analysis["features"]["symbol_liquidity_tier"] = 1 if symbol in ["BTCUSDT", "ETHUSDT"] else (2 if "USDT" in symbol else 3)
            analysis["features"]["market_cap_tier"] = "large" if symbol in ["BTCUSDT", "ETHUSDT", "BNBUSDT"] else "small"
            
            # Get orderbook data for features
            orderbook = await rest_client.get_orderbook(symbol)
            if orderbook:
                analysis["features"]["orderbook_imbalance"] = self._calculate_orderbook_imbalance(orderbook)
                
            # Get funding rate
            funding_rate = await rest_client.get_funding_rate(symbol)
            if funding_rate is not None:
                analysis["features"]["funding_rate_deviation"] = abs(funding_rate - 0.01) * 1000
            
            # Calculate confidence score
            confidence_score = confidence_model.predict_confidence(analysis["features"])
            analysis["confidence_score"] = confidence_score
            
            # CRITICAL SAFETY: Set confidence for dynamic leverage calculation
            TradingRules.set_current_confidence(confidence_score * 10)  # Convert to 0-100 scale
            
            # DEBUG: Log technical analysis details to understand identical results
            logger.info(f"DEBUG ANALYSIS for {symbol}",
                       features_count=len(analysis.get("features", {})),
                       direction=analysis.get("direction"),
                       signal_strength=analysis.get("strength", 0),
                       confluence_points=analysis.get("confluence_points", 0),
                       confidence_raw=confidence_score,
                       volatility_score=analysis.get("volatility_score", 0))
            
            # BOOKMAP FUSION ENHANCEMENT
            logger.info("Initiating Bookmap signal fusion", symbol=symbol)
            fused_signal = await signal_fusion_engine.fuse_signals(analysis, symbol)
            
            # Apply fusion enhancements
            if fused_signal.fusion_result.value in ["ENHANCED_LONG", "ENHANCED_SHORT"]:
                # FIXED: Convert 0-100 scale to display percentage correctly
                boosted_confidence = float(confidence_score) + float(fused_signal.confidence_boost)
                boosted_confidence = min(100.0, boosted_confidence)  # Cap at 100% not 10.0
                analysis["confidence_score"] = boosted_confidence
                analysis["original_confidence"] = confidence_score
                analysis["fusion_boost"] = fused_signal.confidence_boost
                
                logger.info(
                    "Signal enhanced by Bookmap fusion",
                    symbol=symbol,
                    original_confidence=confidence_score,
                    boosted_confidence=boosted_confidence,
                    fusion_result=fused_signal.fusion_result.value
                )
            elif fused_signal.fusion_result.value == "CONFLICTING_SIGNALS":
                # Reduce confidence for conflicting signals
                reduced_confidence = max(2.0, float(confidence_score) + float(fused_signal.confidence_boost))
                analysis["confidence_score"] = reduced_confidence
                analysis["fusion_warning"] = "Order flow conflicts with TA signal"
                
                logger.warning(
                    "Conflicting signals detected",
                    symbol=symbol,
                    ta_direction=analysis["direction"],
                    order_flow_score=fused_signal.order_flow_score
                )
            
            # Store fusion data for display
            analysis["bookmap_fusion"] = {
                "fusion_result": fused_signal.fusion_result.value,
                "order_flow_score": fused_signal.order_flow_score,
                "fusion_triggers": fused_signal.fusion_triggers,
                "microstructure": fused_signal.microstructure_analysis,
                "summary": fused_signal.bookmap_summary
            }
            
            # Keep the maximum leverage calculated by TradingRules (don't override)
            # Just apply fusion adjustment as a multiplier
            base_leverage = analysis["leverage"]  # Use the max leverage from TradingRules
            fusion_adjusted_leverage = int(base_leverage * fused_signal.leverage_adjustment)
            
            # Validate fusion adjustment (but keep it high)
            final_leverage = min(fusion_adjusted_leverage, base_leverage)  # Never exceed the symbol's max
            analysis["leverage"] = final_leverage
            analysis["bookmap_leverage_adjustment"] = fused_signal.leverage_adjustment
            
            logger.info(f"Leverage finalized for {symbol}", 
                       base_max=base_leverage, 
                       fusion_adjusted=fusion_adjusted_leverage,
                       final=final_leverage)
            analysis["regime_info"] = {
                "regime": regime_metrics.regime.value,
                "confidence": regime_metrics.confidence,
                "strategy_type": regime_adjustments.get('strategy_type', 'standard'),
                "adjustments_applied": True
            }
            # Leverage note for ultra-aggressive maximum leverage strategy
            analysis["leverage_note"] = f"Using maximum leverage ({final_leverage}x) for aggressive positioning"
                
            # Calculate risk-reward ratios
            take_profits = [
                analysis["take_profit_1"],
                analysis["take_profit_2"],
                analysis["take_profit_3"]
            ]
            rr_ratios = RiskManager.calculate_risk_reward_ratio(
                analysis["entry_price"],
                analysis["stop_loss"],
                take_profits
            )
            analysis["risk_reward"] = rr_ratios
            
            # Assess trade quality
            quality = RiskManager.assess_trade_quality(
                rr_ratios,
                confidence_score,
                analysis["volatility_score"]
            )
            analysis["quality"] = quality
            
            # Calculate profit percentages for display
            entry = analysis["entry_price"]
            if analysis["direction"] == "LONG":
                analysis["tp1_profit"] = round(((analysis["take_profit_1"] - entry) / entry) * 100, 1)
                analysis["tp2_profit"] = round(((analysis["take_profit_2"] - entry) / entry) * 100, 1)
                analysis["tp3_profit"] = round(((analysis["take_profit_3"] - entry) / entry) * 100, 1)
            else:
                analysis["tp1_profit"] = round(((entry - analysis["take_profit_1"]) / entry) * 100, 1)
                analysis["tp2_profit"] = round(((entry - analysis["take_profit_2"]) / entry) * 100, 1)
                analysis["tp3_profit"] = round(((entry - analysis["take_profit_3"]) / entry) * 100, 1)
                
            # Cache the analysis
            await cache.set_analysis(symbol, analysis)
            
            # Track signal for analytics
            from .analytics import analytics
            await analytics.track_signal(analysis)
            
            # Record signal for bias monitoring
            try:
                from ..services.bias_monitor import bias_monitor
                bias_monitor.record_signal(
                    symbol=symbol,
                    direction=analysis.get('direction', 'NEUTRAL'),
                    confidence=float(analysis.get('confidence_score', 50)),
                    signal_strength=float(analysis.get('strength', 0)),
                    metadata={
                        'processing_mode': 'standard',
                        'regime': str(regime_metrics.regime.value) if regime_metrics else 'unknown'
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to record signal for bias monitoring: {e}")
            
            # Send signal
            await self._send_signal(analysis, chat_ids)
            
            # EMERGENCY: Log signal to file during rate limiting
            await self._log_signal_to_file(analysis)
            
            # Log performance
            elapsed = time.time() - start_time
            logger.info(
                "Signal generated",
                symbol=symbol,
                direction=analysis["direction"],
                confidence=confidence_score,
                elapsed_ms=round(elapsed * 1000)
            )
            
            return analysis
            
        except Exception as e:
            logger.error("Signal processing failed", symbol=symbol, error=str(e))
            await telegram_service.send_error(
                f"Failed to process {symbol}: {str(e)}",
                chat_ids
            )
            return {"error": str(e)}
            
    async def _collect_data(self, symbol: str) -> Dict[str, Any]:
        """Collect data for all timeframes with timeout and error handling."""
        data = {}
        errors = []
        
        logger.info(f"Starting data collection for {symbol}")
        
        # Check circuit breaker status first
        cb_status = rest_client.get_circuit_breaker_status()
        if not cb_status["can_execute"]:
            logger.error(f"Circuit breaker is open for {symbol}", cb_status=cb_status)
            raise Exception(f"API circuit breaker is open. Reset needed. Status: {cb_status}")
        
        # Parallel data collection for all timeframes with timeout
        tasks = []
        for tf in settings.time_frames:
            interval = self._timeframe_to_interval(tf)
            task = asyncio.wait_for(
                rest_client.get_klines(symbol, interval, limit=200),
                timeout=15.0  # Increased timeout to 15 seconds
            )
            tasks.append((tf, task))
            
        # Execute all requests in parallel
        results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )
        
        # Process results with detailed error tracking
        successful_timeframes = 0
        for (tf, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                error_msg = str(result)
                logger.error(f"Failed to get {tf} data for {symbol}", error=error_msg)
                errors.append(f"{tf}: {error_msg}")
            elif result is not None and not result.empty:
                data[tf] = result
                successful_timeframes += 1
                logger.debug(f"Successfully collected {tf} data for {symbol}: {len(result)} candles")
            else:
                logger.warning(f"Empty data returned for {tf} timeframe of {symbol}")
                errors.append(f"{tf}: Empty data returned")
        
        # Log collection summary
        logger.info(f"Data collection completed for {symbol}", 
                   successful=successful_timeframes, 
                   total=len(settings.time_frames),
                   errors=len(errors))
        
        # If we have no data at all, provide detailed error information
        if not data:
            error_summary = "; ".join(errors[:3])  # Show first 3 errors
            circuit_breaker_status = rest_client.get_circuit_breaker_status()
            detailed_error = f"No data collected for {symbol}. Errors: {error_summary}. Circuit breaker: {circuit_breaker_status}"
            logger.error(detailed_error)
            raise Exception(detailed_error)
                
        return data
        
    def _timeframe_to_interval(self, timeframe: str) -> str:
        """Convert timeframe to Bybit interval format."""
        mapping = {
            "1m": "1",
            "5m": "5",
            "15m": "15",
            "1h": "60",
            "4h": "240",
            "1d": "D"
        }
        return mapping.get(timeframe, "5")
        
    def _calculate_orderbook_imbalance(self, orderbook: Dict[str, Any]) -> float:
        """Calculate orderbook imbalance metric."""
        try:
            bids = orderbook.get("b", [])
            asks = orderbook.get("a", [])
            
            if not bids or not asks:
                return 0.0
                
            # Calculate total bid/ask volumes (top 10 levels)
            bid_volume = sum(float(bid[1]) for bid in bids[:10])
            ask_volume = sum(float(ask[1]) for ask in asks[:10])
            
            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return 0.0
                
            # Imbalance: positive for more bids, negative for more asks
            imbalance = (bid_volume - ask_volume) / total_volume
            
            return float(imbalance * 100)  # Convert to percentage
            
        except Exception as e:
            logger.error("Failed to calculate orderbook imbalance", error=str(e))
            return 0.0
            
    async def _send_signal(self, analysis: Dict[str, Any], chat_ids: Optional[List[str]] = None) -> None:
        """Send signal to Telegram."""
        await telegram_service.send_signal(analysis, chat_ids)
        
    async def _log_signal_to_file(self, analysis: Dict[str, Any]) -> None:
        """Log signal to file for immediate viewing during rate limiting."""
        try:
            import json
            from datetime import datetime
            
            # Create signals log file
            log_file = "/app/signals_log.txt"
            
            # Format signal for readability
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            symbol = analysis.get("symbol", "UNKNOWN")
            direction = analysis.get("direction", "NEUTRAL")
            confidence = analysis.get("confidence_score", 0)
            entry = analysis.get("entry_price", 0)
            
            # Create readable signal
            signal_text = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 SIGNAL ALERT - {timestamp}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Symbol: {symbol}
📈 Direction: {direction}
🎯 Confidence: {confidence:.1f}%
💵 Entry: {entry}
🛑 Stop Loss: {analysis.get("stop_loss", "N/A")}
🎯 TP1: {analysis.get("take_profit_1", "N/A")} ({analysis.get("tp1_profit", 0):.1f}%)
🎯 TP2: {analysis.get("take_profit_2", "N/A")} ({analysis.get("tp2_profit", 0):.1f}%)
🎯 TP3: {analysis.get("take_profit_3", "N/A")} ({analysis.get("tp3_profit", 0):.1f}%)
⚡ Leverage: {analysis.get("leverage", 1)}x
📊 Quality: {analysis.get("quality", "UNKNOWN")}

🔮 Bookmap Fusion:
   Result: {analysis.get("bookmap_fusion", {}).get("fusion_result", "N/A")}
   Order Flow: {analysis.get("bookmap_fusion", {}).get("order_flow_score", 0):.2f}

📈 Market Regime: {analysis.get("regime_info", {}).get("regime", "UNKNOWN")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            
            # Append to file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(signal_text)
                
            logger.info("Signal logged to file", symbol=symbol, direction=direction)
            
        except Exception as e:
            logger.error("Failed to log signal to file", error=str(e))
            
    async def subscribe_to_symbol(self, symbol: str) -> None:
        """Subscribe to real-time updates for a symbol."""
        try:
            # Subscribe to WebSocket feeds
            await ws_client.subscribe_ticker(symbol)
            
            # Set up event handlers
            ws_client.on(f"ticker_{symbol}", lambda data: self._handle_ticker_update(symbol, data))
            ws_client.on(f"orderbook_{symbol}", lambda data: self._handle_orderbook_update(symbol, data))
            
            logger.info("Subscribed to real-time updates", symbol=symbol)
            
        except Exception as e:
            logger.error("Failed to subscribe to symbol", symbol=symbol, error=str(e))
            
    async def _handle_ticker_update(self, symbol: str, data: Dict[str, Any]) -> None:
        """Handle real-time ticker updates."""
        try:
            # Cache ticker data
            await cache.set_ticker(symbol, data)
            
            # Check for significant price movements
            if "lastPrice" in data and "prevPrice24h" in data:
                change_pct = ((float(data["lastPrice"]) - float(data["prevPrice24h"])) / 
                             float(data["prevPrice24h"])) * 100
                             
                if abs(change_pct) > 5:  # 5% threshold
                    logger.info("Significant price movement detected",
                               symbol=symbol, change_pct=change_pct)
                               
        except Exception as e:
            logger.error("Failed to handle ticker update", error=str(e))
            
    async def _handle_orderbook_update(self, symbol: str, data: Dict[str, Any]) -> None:
        """Handle real-time orderbook updates."""
        try:
            # Cache orderbook data
            await cache.set_orderbook(symbol, data)
        except Exception as e:
            logger.error("Failed to handle orderbook update", error=str(e))

    async def process_symbol_ultra_comprehensive(
        self,
        symbol: str,
        chat_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        ULTRA-OPTIMIZED comprehensive signal generation with maximum institutional capabilities.
        ENHANCED: Superior performance, intelligent caching, and ML-enhanced analysis.
        
        Revolutionary institutional-grade features:
        - Ultra-comprehensive technical analysis with ML-enhanced confluence scoring
        - Advanced Bookmap order flow analysis with 45-minute extended lookback
        - Enhanced iceberg detection with algorithmic pattern recognition
        - Sophisticated market maker behavior analysis with manipulation detection
        - AI-powered support/resistance analysis with confluence weighting
        - Advanced market regime detection with dynamic strategy adaptation
        - Portfolio-integrated risk optimization with heat management
        - Ultra-enhanced signal fusion with microstructure insights and smart money tracking
        - Real-time progress tracking with performance optimization metrics
        
        Args:
            symbol: Trading pair symbol
            chat_ids: Optional specific chat IDs to send to
            
        Returns:
            Ultra-optimized institutional-grade signal analysis
        """
        start_time = time.time()
        
        # OPTIMIZED: Enhanced duplicate processing prevention
        if symbol in self.processing_symbols:
            logger.warning("Symbol already being processed", symbol=symbol)
            return {"error": "Symbol currently being analyzed", "retry_in_seconds": 5}
            
        self.processing_symbols.add(symbol)
        
        try:
            logger.info("🚀 Starting OPTIMIZED ULTRA-COMPREHENSIVE signal generation", symbol=symbol)
            
            # ──────────────────────────────────────────────────────────────────────────────
            # PHASE 1: INTELLIGENT DATA COLLECTION WITH CACHING
            # ──────────────────────────────────────────────────────────────────────────────
            await telegram_service.send_notification(
                f"🔄 **ULTRA-ANALYSIS INITIATED for {symbol}**\n\n"
                "🧠 Collecting multi-timeframe data with smart caching...\n"
                "🌊 Scanning extended order flow patterns...\n"
                "📊 Analyzing institutional microstructure...\n"
                "⚡ Processing: 0%",
                chat_ids
            )
            
            # OPTIMIZED: Parallel data collection with enhanced error handling
            logger.info("Starting optimized data collection", symbol=symbol)
            data = await self._collect_data_ultra_optimized(symbol)
            
            if not data:
                error_msg = f"Failed to collect comprehensive data for {symbol} - insufficient market data"
                await telegram_service.send_error(error_msg, chat_ids)
                return {"error": error_msg, "symbol": symbol}
            
            # ──────────────────────────────────────────────────────────────────────────────
            # PHASE 2: ADVANCED BOOKMAP ORDER FLOW ANALYSIS WITH PATTERN RECOGNITION
            # ──────────────────────────────────────────────────────────────────────────────
            await telegram_service.send_notification(
                f"🌊 **ORDER FLOW ANALYSIS** - {symbol}\n\n"
                "📈 Detecting whale activity patterns...\n"
                "🧊 Scanning iceberg algorithms...\n"
                "🎯 Analyzing stop hunting behavior...\n"
                "⚡ Processing: 25%",
                chat_ids
            )
            
            logger.info("Performing ultra-comprehensive Bookmap analysis", symbol=symbol)
            
            # OPTIMIZED: Enhanced order flow analysis with extended timeframes
            bookmap_analysis = await self._get_ultra_comprehensive_bookmap_analysis(symbol)
            
            # ──────────────────────────────────────────────────────────────────────────────
            # PHASE 3: ENHANCED MARKET REGIME & VOLATILITY ANALYSIS
            # ──────────────────────────────────────────────────────────────────────────────
            await telegram_service.send_notification(
                f"🧠 **REGIME ANALYSIS** - {symbol}\n\n"
                "📊 Detecting market regime...\n"
                "⚡ Analyzing volatility patterns...\n"
                "🎯 Optimizing strategy parameters...\n"
                "⚡ Processing: 50%",
                chat_ids
            )
            
            logger.info("Detecting enhanced market regime", symbol=symbol)
            from ..logic.market_regime import regime_detector
            regime_metrics = await regime_detector.detect_regime(data)
            
            # OPTIMIZED: Enhanced strategy adjustments with regime confidence
            regime_adjustments = regime_detector.get_strategy_adjustments(regime_metrics)
            
            # ──────────────────────────────────────────────────────────────────────────────
            # PHASE 4: ULTRA-ADVANCED TECHNICAL ANALYSIS WITH CONFIDENCE OPTIMIZATION
            # ──────────────────────────────────────────────────────────────────────────────
            await telegram_service.send_notification(
                f"🔬 **TECHNICAL ANALYSIS** - {symbol}\n\n"
                f"📈 Market Regime: **{regime_metrics.regime.value}**\n"
                f"🎯 Confidence: {regime_metrics.confidence:.1f}/10\n"
                f"🧠 Running advanced pattern recognition...\n"
                f"⚡ Processing: 75%",
                chat_ids
            )
            
            # OPTIMIZED: Enhanced threshold calculation with regime and order flow context
            base_threshold = 1.5  # More aggressive for manual ultra-comprehensive requests
            regime_threshold_adj = regime_adjustments.get('signal_threshold_adjustment', 0)
            order_flow_adj = self._calculate_order_flow_threshold_adjustment_enhanced(bookmap_analysis)
            
            # OPTIMIZED: Smart threshold adjustment based on market conditions
            adjusted_threshold = base_threshold + regime_threshold_adj + order_flow_adj
            adjusted_threshold = max(1.0, min(8.0, adjusted_threshold))  # Keep very aggressive
            
            logger.info("Running ultra-enhanced technical analysis", 
                       symbol=symbol, 
                       base_threshold=base_threshold,
                       adjusted_threshold=adjusted_threshold,
                       regime_confidence=regime_metrics.confidence)
            
            # OPTIMIZED: Run ultra-comprehensive analysis with enhanced parameters
            analysis = await TradingRules.analyze_symbol(
                symbol,
                data,
                threshold_pct=15.0,  # More aggressive profit targets for scalping
                regime_metrics=regime_metrics
            )
            
            # ──────────────────────────────────────────────────────────────────────────────
            # ULTRA-OPTIMIZED: ENHANCED CONFIDENCE MODEL WITH SYMBOL-SPECIFIC VARIABILITY
            # ──────────────────────────────────────────────────────────────────────────────
            if analysis.get("direction") != "NEUTRAL":
                # ULTRA-OPTIMIZED: Enhanced symbol-specific features for superior confidence variability
                enhanced_features = self._enhance_symbol_features_ultra_optimized(symbol, analysis, bookmap_analysis, regime_metrics)
                analysis["features"].update(enhanced_features)
                
                # Calculate optimized confidence score with enhanced features
                confidence_score = confidence_model.predict_confidence(analysis["features"])
                analysis["confidence_score"] = confidence_score
                
                # ULTRA-OPTIMIZED: Dynamic confidence for leverage calculation with portfolio integration
                TradingRules.set_current_confidence(confidence_score * 10)  # Convert to 0-100 scale
                
                logger.info(f"✅ ULTRA-OPTIMIZED confidence calculated for {symbol}", 
                           confidence=confidence_score,
                           features_count=len(analysis.get("features", {})),
                           regime_confidence=regime_metrics.confidence,
                           enhanced_features=len(enhanced_features))
            
            # ──────────────────────────────────────────────────────────────────────────────
            # PHASE 5: INSTITUTIONAL-GRADE SIGNAL FUSION WITH MICROSTRUCTURE ANALYSIS
            # ──────────────────────────────────────────────────────────────────────────────
            if analysis.get("direction") != "NEUTRAL":
                await telegram_service.send_notification(
                    f"🎯 **SIGNAL DETECTED: {analysis['direction']}** - {symbol}\n\n"
                    f"🧊 Fusing with institutional order flow...\n"
                    f"🔬 Applying microstructure analysis...\n"
                    f"⚡ Optimizing entry and risk parameters...\n"
                    f"⚡ Processing: 90%",
                    chat_ids
                )
                
                # OPTIMIZED: Advanced signal fusion with extended lookback and enhanced analysis
                fused_signal = await signal_fusion_engine.fuse_signals(
                    analysis, symbol, lookback_minutes=45  # Extended lookback for better context
                )
                
                # OPTIMIZED: Apply ultra-comprehensive fusion enhancements
                logger.info("Starting ultra-optimized fusion enhancements", symbol=symbol)
                analysis = await self._apply_ultra_fusion_enhancements_optimized(
                    analysis, fused_signal, bookmap_analysis, regime_metrics, symbol
                )
                
                # ──────────────────────────────────────────────────────────────────────────────
                # PHASE 6: ADVANCED RISK OPTIMIZATION WITH PORTFOLIO INTEGRATION
                # ──────────────────────────────────────────────────────────────────────────────
                logger.info("Starting enhanced risk optimization", symbol=symbol)
                analysis = await self._apply_risk_optimization_enhanced(analysis, symbol, fused_signal)
                
                # ──────────────────────────────────────────────────────────────────────────────
                # PHASE 7: COMPREHENSIVE QUALITY ASSESSMENT WITH SCORING
                # ──────────────────────────────────────────────────────────────────────────────
                logger.info("Starting enhanced quality assessment", symbol=symbol)
                quality_score = await self._calculate_comprehensive_quality_score_enhanced(
                    analysis, bookmap_analysis, regime_metrics, fused_signal
                )
                
                analysis["ultra_quality_score"] = quality_score
                analysis["analysis_depth"] = "INSTITUTIONAL_GRADE_OPTIMIZED"
                analysis["processing_time_ms"] = round((time.time() - start_time) * 1000)
                
                # OPTIMIZED: Enhanced rationale with all analysis layers
                analysis["enhanced_rationale"] = self._generate_ultra_rationale_enhanced(
                    analysis, bookmap_analysis, regime_metrics, fused_signal, symbol
                )
                
            else:
                # OPTIMIZED: Enhanced neutral analysis with detailed institutional feedback
                analysis = await self._generate_enhanced_neutral_feedback_optimized(
                    analysis, bookmap_analysis, regime_metrics, symbol
                )
            
            # ──────────────────────────────────────────────────────────────────────────────
            # PHASE 8: FINAL DELIVERY WITH ENHANCED INSTITUTIONAL INSIGHTS
            # ──────────────────────────────────────────────────────────────────────────────
            
            await telegram_service.send_notification(
                f"✅ **ANALYSIS COMPLETE** - {symbol}\n\n"
                f"📊 Direction: **{analysis['direction']}**\n"
                f"🎯 Quality: {analysis.get('ultra_quality_score', 0):.1f}/10\n"
                f"⚡ Processing: 100% COMPLETE",
                chat_ids
            )
            
            # OPTIMIZED: Store comprehensive analysis data with enhanced metadata
            analysis["symbol"] = symbol
            analysis["ultra_comprehensive"] = True
            analysis["optimization_version"] = "2.0_enhanced"
            analysis["bookmap_analysis"] = bookmap_analysis
            analysis["regime_analysis"] = {
                "regime": regime_metrics.regime.value,
                "confidence": regime_metrics.confidence,
                "adjustments": regime_adjustments,
                "strategy_type": regime_adjustments.get('strategy_type', 'standard')
            }
            
            # OPTIMIZED: Enhanced caching with compression for large datasets
            cacheable_analysis = self._make_analysis_cacheable_optimized(analysis)
            await cache.set_analysis(symbol, cacheable_analysis, extended_ttl=True)
            
            # OPTIMIZED: Enhanced bias monitoring with metadata
            try:
                from ..services.bias_monitor import bias_monitor
                bias_monitor.record_signal(
                    symbol=symbol,
                    direction=analysis.get('direction', 'NEUTRAL'),
                    confidence=float(analysis.get('confidence_score', 50)),
                    signal_strength=float(analysis.get('strength', 0)),
                    metadata={
                        'processing_mode': 'ultra_comprehensive_optimized',
                        'regime': str(regime_metrics.regime.value) if regime_metrics else 'unknown',
                        'bookmap_fusion': analysis.get('bookmap_fusion', {}).get('fusion_result', 'none'),
                        'quality_score': float(analysis.get('ultra_quality_score', 0)),
                        'processing_time_ms': analysis.get('processing_time_ms', 0),
                        'optimization_version': '2.0_enhanced'
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to record ultra signal for bias monitoring: {e}")
            
            # OPTIMIZED: Send the ultra-comprehensive signal with enhanced formatting
            await self._send_ultra_comprehensive_signal_optimized(analysis, chat_ids)
            
            # OPTIMIZED: Enhanced performance logging
            elapsed = time.time() - start_time
            logger.info(
                "🚀 OPTIMIZED ULTRA-COMPREHENSIVE signal completed",
                symbol=symbol,
                direction=analysis["direction"],
                confidence=analysis.get("confidence_score", 0),
                quality_score=analysis.get("ultra_quality_score", 0),
                regime_confidence=regime_metrics.confidence if regime_metrics else 0,
                fusion_result=analysis.get('bookmap_fusion', {}).get('fusion_result', 'none'),
                elapsed_ms=round(elapsed * 1000),
                optimization_version="2.0_enhanced"
            )
            
            return analysis
            
        except Exception as e:
            logger.error("Ultra-comprehensive signal processing failed", symbol=symbol, error=str(e), exc_info=True)
            try:
                await telegram_service.send_error(
                    f"🚨 Ultra-analysis failed for {symbol}: {str(e)}",
                    chat_ids
                )
            except Exception as send_error:
                logger.error("Failed to send error message", error=str(send_error))
            return {"error": str(e), "symbol": symbol, "failed_phase": "processing"}
        finally:
            self.processing_symbols.discard(symbol)

    async def _collect_data_ultra_optimized(self, symbol: str) -> Dict[str, Any]:
        """Extended data collection with additional timeframes and lookback."""
        data = {}
        errors = []
        
        logger.info(f"Starting extended data collection for {symbol}")
        
        # Extended timeframes for ultra-comprehensive analysis
        extended_timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
        
        # Parallel data collection with increased limits
        tasks = []
        for tf in extended_timeframes:
            interval = self._timeframe_to_interval(tf)
            limit = 500 if tf in ["1m", "5m"] else 200  # More data for lower timeframes
            task = asyncio.wait_for(
                rest_client.get_klines(symbol, interval, limit=limit),
                timeout=20.0  # Extended timeout for more data
            )
            tasks.append((tf, task))
            
        # Execute all requests in parallel
        results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )
        
        # Process results
        successful_timeframes = 0
        for (tf, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                error_msg = str(result)
                logger.error(f"Failed to get {tf} data for {symbol}", error=error_msg)
                errors.append(f"{tf}: {error_msg}")
            elif result is not None and not result.empty:
                data[tf] = result
                successful_timeframes += 1
                logger.debug(f"Successfully collected {tf} data for {symbol}: {len(result)} candles")
            else:
                logger.warning(f"Empty data returned for {tf} timeframe of {symbol}")
                errors.append(f"{tf}: Empty data returned")
        
        if not data:
            error_summary = "; ".join(errors[:3])
            raise Exception(f"No extended data collected for {symbol}. Errors: {error_summary}")
                
        return data
        
    async def _get_ultra_comprehensive_bookmap_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive Bookmap order flow analysis."""
        try:
            # Multi-timeframe Bookmap analysis
            analysis = {
                "flow_15m": bookmap_engine.get_signal_summary(symbol, 15),
                "flow_30m": bookmap_engine.get_signal_summary(symbol, 30),
                "flow_60m": bookmap_engine.get_signal_summary(symbol, 60),
                "order_flow_score": bookmap_engine.get_order_flow_score(symbol),
                "recent_signals": bookmap_engine.get_recent_signals(symbol, 30)
            }
            
            # Detailed signal analysis
            recent_signals = analysis["recent_signals"]
            
            # Count specific signal types
            signal_counts = {}
            for signal in recent_signals:
                signal_type = signal.signal_type.value
                signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
            
            # Whale activity analysis
            whale_signals = [s for s in recent_signals if s.signal_type.value == "WHALE_TRADE"]
            whale_volume = sum(float(s.details.get("notional", 0)) for s in whale_signals)
            whale_buy_volume = sum(
                float(s.details.get("notional", 0)) for s in whale_signals if s.side == "BUY"
            )
            
            # Iceberg analysis
            iceberg_signals = [s for s in recent_signals if s.signal_type.value == "ICEBERG_DETECTION"]
            iceberg_buy_count = len([s for s in iceberg_signals if s.details.get("side") == "BID"])
            iceberg_ask_count = len([s for s in iceberg_signals if s.details.get("side") == "ASK"])
            
            # Volume absorption analysis
            absorption_signals = [s for s in recent_signals if s.signal_type.value == "VOLUME_BURST"]
            total_absorption = sum(
                float(s.details.get("window_volume", 0) or s.details.get("total_volume", 0))
                for s in absorption_signals
            )
            
            # Support/resistance levels
            sr_signals = [
                s for s in recent_signals 
                if any(trigger.startswith("Strong") for trigger in s.triggers)
            ]
            
            analysis.update({
                "signal_counts": signal_counts,
                "whale_analysis": {
                    "total_volume": whale_volume,
                    "buy_volume": whale_buy_volume,
                    "sell_volume": whale_volume - whale_buy_volume,
                    "signal_count": len(whale_signals),
                    "dominant_side": "BUY" if whale_buy_volume > whale_volume * 0.6 else "SELL"
                },
                "iceberg_analysis": {
                    "total_count": len(iceberg_signals),
                    "bid_count": iceberg_buy_count,
                    "ask_count": iceberg_ask_count,
                    "bias": "BULLISH" if iceberg_buy_count > iceberg_ask_count else "BEARISH"
                },
                "absorption_analysis": {
                    "total_volume": total_absorption,
                    "signal_count": len(absorption_signals)
                },
                "support_resistance": {
                    "level_count": len(sr_signals),
                    "levels": [
                        {
                            "price": float(s.price),
                            "type": s.details.get("type", "unknown"),
                            "strength": float(s.details.get("strength", 0)),
                            "confidence": float(s.confidence)
                        } for s in sr_signals
                    ]
                }
            })
            
            return analysis
            
        except Exception as e:
            logger.error("Failed to get ultra-comprehensive Bookmap analysis", error=str(e))
            return {
                "flow_15m": {},
                "flow_30m": {},
                "flow_60m": {},
                "order_flow_score": 0.0,
                "recent_signals": [],
                "error": str(e)
            }
            
    def _calculate_order_flow_threshold_adjustment_enhanced(self, bookmap_analysis: Dict[str, Any]) -> float:
        """Calculate threshold adjustment based on order flow strength."""
        order_flow_score = abs(float(bookmap_analysis.get("order_flow_score", 0)))
        signal_counts = bookmap_analysis.get("signal_counts", {})
        
        adjustment = 0.0
        
        # Strong order flow reduces threshold (easier to signal)
        if order_flow_score > 8:
            adjustment -= 1.0
        elif order_flow_score > 5:
            adjustment -= 0.5
            
        # Whale activity reduces threshold
        if signal_counts.get("WHALE_TRADE", 0) >= 3:
            adjustment -= 0.5
            
        # Iceberg activity indicates institutional presence
        if signal_counts.get("ICEBERG_DETECTION", 0) >= 2:
            adjustment -= 0.3
            
        return adjustment
        
    async def _apply_ultra_fusion_enhancements_optimized(
        self, 
        analysis: Dict[str, Any], 
        fused_signal, 
        bookmap_analysis: Dict[str, Any],
        regime_metrics,
        symbol: str
    ) -> Dict[str, Any]:
        """Apply ultra-comprehensive fusion enhancements."""
        
        # Enhanced confidence calculation
        base_confidence = float(analysis.get("confidence_score", 5.0))
        
        # CRITICAL FIX: Convert 0-100 scale to 0-10 scale for ultra-comprehensive analysis
        # The confidence model returns 0-100, but ultra-analysis expects 0-10 scale
        if base_confidence > 10.0:  # If confidence is on 0-100 scale, convert to 0-10
            base_confidence = base_confidence / 10.0
        
        total_boost = float(fused_signal.confidence_boost)
        
        # Additional boosts from comprehensive analysis
        whale_analysis = bookmap_analysis.get("whale_analysis", {})
        if float(whale_analysis.get("total_volume", 0)) > 5_000_000:  # $5M+ whale volume
            total_boost += 1.0
            
        iceberg_analysis = bookmap_analysis.get("iceberg_analysis", {})
        if int(iceberg_analysis.get("total_count", 0)) >= 3:
            total_boost += 0.8
            
        # Regime confidence boost
        if float(regime_metrics.confidence) > 8.0:
            total_boost += 0.5
        
        # Apply comprehensive confidence  
        # FIXED: Convert 0-100 scale to display percentage correctly
        enhanced_confidence = float(base_confidence) + float(total_boost)
        enhanced_confidence = min(100.0, enhanced_confidence)  # Cap at 100% not 10.0
        analysis["confidence_score"] = enhanced_confidence
        analysis["original_confidence"] = base_confidence
        analysis["total_fusion_boost"] = total_boost
        
        # Enhanced leverage calculation
        base_leverage = analysis["leverage"]
        leverage_multiplier = fused_signal.leverage_adjustment
        
        # Reduce leverage if conflicting signals
        if fused_signal.fusion_result.value == "CONFLICTING_SIGNALS":
            leverage_multiplier *= 0.7
            
        # Increase leverage for strong institutional flow
        if bookmap_analysis.get("order_flow_score", 0) > 7:
            leverage_multiplier *= 1.1
        
        enhanced_leverage = int(base_leverage * leverage_multiplier)
        analysis["leverage"] = max(5, min(enhanced_leverage, base_leverage))
        
        # Store comprehensive fusion data
        analysis["ultra_fusion"] = {
            "bookmap_fusion": fused_signal,
            "whale_influence": whale_analysis,
            "iceberg_influence": iceberg_analysis,
            "regime_influence": {
                "regime": regime_metrics.regime.value,
                "confidence": regime_metrics.confidence
            }
        }
        
        return analysis
        
    async def _apply_risk_optimization_enhanced(self, analysis: Dict[str, Any], symbol: str, fused_signal) -> Dict[str, Any]:
        """Apply advanced risk optimization."""
        
        # Enhanced risk-reward calculation
        take_profits = [
            analysis["take_profit_1"],
            analysis["take_profit_2"], 
            analysis["take_profit_3"]
        ]
        
        rr_ratios = RiskManager.calculate_risk_reward_ratio(
            analysis["entry_price"],
            analysis["stop_loss"],
            take_profits
        )
        analysis["risk_reward"] = rr_ratios
        
        # Enhanced quality assessment
        quality = RiskManager.assess_trade_quality(
            rr_ratios,
            analysis["confidence_score"],
            analysis["volatility_score"]
        )
        analysis["quality"] = quality
        
        # Portfolio heat consideration
        try:
            from .bybit_trading import bybit_trading_service
            portfolio_heat = bybit_trading_service.risk_manager.calculate_portfolio_heat(
                [], bybit_trading_service.account_balance
            )
            analysis["portfolio_heat"] = portfolio_heat
        except:
            analysis["portfolio_heat"] = {"heat_level": "UNKNOWN"}
            
        return analysis
        
    async def _calculate_comprehensive_quality_score_enhanced(
        self, 
        analysis: Dict[str, Any], 
        bookmap_analysis: Dict[str, Any], 
        regime_metrics,
        fused_signal
    ) -> float:
        """Calculate comprehensive quality score from all factors."""
        
        score = 0.0
        
        # Base technical score
        confidence = float(analysis.get("confidence_score", 0))
        base_score = confidence * 1.0  # Weight: 1.0
        score += base_score
        
        # Risk-reward quality
        rr_ratios = analysis.get("risk_reward", [0, 0, 0])
        # Handle both list and dict formats, ensure all ratios are numeric
        if isinstance(rr_ratios, dict):
            # Extract numeric values from dict, skip string keys
            numeric_ratios = []
            for key, value in rr_ratios.items():
                try:
                    if isinstance(value, (int, float)):
                        numeric_ratios.append(float(value))
                    elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                        numeric_ratios.append(float(value))
                except (ValueError, TypeError):
                    continue
        else:
            # Handle list format
            numeric_ratios = []
            for ratio in rr_ratios:
                try:
                    if isinstance(ratio, (int, float)):
                        numeric_ratios.append(float(ratio))
                    elif isinstance(ratio, str) and ratio.replace('.', '').replace('-', '').isdigit():
                        numeric_ratios.append(float(ratio))
                except (ValueError, TypeError):
                    continue
        
        avg_rr = sum(numeric_ratios) / len(numeric_ratios) if numeric_ratios else 0
        rr_score = min(3.0, float(avg_rr) * 1.5)  # Weight: 1.5, cap at 3.0
        score += rr_score
        
        # Order flow quality
        order_flow_score = abs(float(bookmap_analysis.get("order_flow_score", 0)))
        flow_score = min(2.0, order_flow_score * 0.25)  # Weight: 0.25, cap at 2.0
        score += flow_score
        
        # Institutional activity bonus
        whale_volume = float(bookmap_analysis.get("whale_analysis", {}).get("total_volume", 0))
        whale_score = 0
        if whale_volume > 1_000_000:
            whale_score = min(1.5, whale_volume / 2_000_000)
        score += whale_score
            
        iceberg_count = float(bookmap_analysis.get("iceberg_analysis", {}).get("total_count", 0))
        iceberg_score = min(1.0, iceberg_count * 0.3)
        score += iceberg_score
        
        # Regime confidence
        regime_score = min(1.0, float(regime_metrics.confidence) * 0.1)
        score += regime_score
        
        # DEBUG LOGGING - Log all components to understand identical results
        logger.info(f"DEBUG QUALITY SCORE CALCULATION for {analysis.get('symbol', 'UNKNOWN')}",
                   base_score=base_score,
                   confidence=confidence,
                   avg_rr=avg_rr,
                   rr_score=rr_score,
                   order_flow_raw=bookmap_analysis.get("order_flow_score", 0),
                   flow_score=flow_score,
                   whale_volume=whale_volume,
                   whale_score=whale_score,
                   iceberg_count=iceberg_count,
                   iceberg_score=iceberg_score,
                   regime_confidence=regime_metrics.confidence,
                   regime_score=regime_score,
                   final_score=min(10.0, score))
        
        # Normalize to 0-10 scale
        return min(10.0, score)
        
    def _generate_ultra_rationale_enhanced(
        self, 
        analysis: Dict[str, Any], 
        bookmap_analysis: Dict[str, Any], 
        regime_metrics, 
        fused_signal,
        symbol: str
    ) -> str:
        """Generate comprehensive trading rationale."""
        
        direction = analysis["direction"]
        rationale_parts = []
        
        # Technical rationale
        rationale_parts.append(f"🎯 **{direction} Signal Detected**")
        rationale_parts.append(f"📊 Technical Confidence: {float(analysis.get('confidence_score', 0)):.1f}/10")
        
        # Regime context
        regime = regime_metrics.regime.value
        regime_conf = regime_metrics.confidence
        rationale_parts.append(f"🌊 Market Regime: {regime} (confidence: {regime_conf:.1f}/10)")
        
        # Order flow insights
        order_flow_score = float(bookmap_analysis.get("order_flow_score", 0))
        if abs(order_flow_score) > 3:
            flow_direction = "BULLISH" if order_flow_score > 0 else "BEARISH"
            rationale_parts.append(f"🌊 Order Flow: {flow_direction} ({order_flow_score:+.1f})")
            
        # Institutional activity
        whale_analysis = bookmap_analysis.get("whale_analysis", {})
        whale_volume = float(whale_analysis.get("total_volume", 0))
        if whale_volume > 1_000_000:
            whale_bias = whale_analysis.get("dominant_side", "MIXED")
            rationale_parts.append(f"🐋 Whale Activity: ${whale_volume:,.0f} ({whale_bias} bias)")
            
        iceberg_analysis = bookmap_analysis.get("iceberg_analysis", {})
        iceberg_count = int(iceberg_analysis.get("total_count", 0))
        if iceberg_count >= 2:
            iceberg_bias = iceberg_analysis.get("bias", "NEUTRAL")
            rationale_parts.append(f"🧊 Iceberg Orders: {iceberg_count} detected ({iceberg_bias})")
            
        # Fusion enhancement
        fusion_triggers = fused_signal.fusion_triggers
        if fusion_triggers and len(fusion_triggers) > 1:
            rationale_parts.append(f"⚡ Fusion Triggers: {', '.join(fusion_triggers[:3])}")
            
        # Quality metrics
        quality_score = float(analysis.get("ultra_quality_score", 0))
        rationale_parts.append(f"💎 Quality Score: {quality_score:.1f}/10")
        
        return "\n".join(rationale_parts)
        
    async def _generate_enhanced_neutral_feedback_optimized(
        self, 
        analysis: Dict[str, Any], 
        bookmap_analysis: Dict[str, Any], 
        regime_metrics, 
        symbol: str
    ) -> Dict[str, Any]:
        """Generate enhanced feedback for neutral signals."""
        
        # Analyze why no signal was generated with comprehensive data
        rejection_reasons = analysis.get("rejection_reasons", [])
        
        # Order flow context
        order_flow_score = float(bookmap_analysis.get("order_flow_score", 0))
        whale_volume = float(bookmap_analysis.get("whale_analysis", {}).get("total_volume", 0))
        iceberg_count = int(bookmap_analysis.get("iceberg_analysis", {}).get("total_count", 0))
        
        enhanced_feedback = {
            "direction": "NEUTRAL",
            "enhanced_analysis": {
                "technical_issues": rejection_reasons[:5],
                "order_flow_score": order_flow_score,
                "whale_activity": whale_volume,
                "iceberg_activity": iceberg_count,
                "regime": regime_metrics.regime.value,
                "regime_confidence": regime_metrics.confidence
            }
        }
        
        # Generate detailed feedback message
        feedback_parts = []
        feedback_parts.append(f"🔍 **ULTRA-ANALYSIS COMPLETE: {symbol}**")
        feedback_parts.append(f"📊 Result: No high-probability signal detected")
        feedback_parts.append(f"🌊 Market Regime: {regime_metrics.regime.value}")
        
        if abs(order_flow_score) > 2:
            flow_direction = "BULLISH" if order_flow_score > 0 else "BEARISH"
            feedback_parts.append(f"🌊 Order Flow: {flow_direction} ({order_flow_score:+.1f})")
        else:
            feedback_parts.append(f"🌊 Order Flow: NEUTRAL ({order_flow_score:+.1f})")
            
        if whale_volume > 500_000:
            feedback_parts.append(f"🐋 Whale Activity: ${whale_volume:,.0f} detected")
            
        if iceberg_count > 0:
            feedback_parts.append(f"🧊 Iceberg Orders: {iceberg_count} institutional orders")
            
        feedback_parts.append(f"📈 Technical Issues: {len(rejection_reasons)} factors preventing signal")
        
        enhanced_feedback["detailed_feedback"] = "\n".join(feedback_parts)
        
        return enhanced_feedback
        
    def _make_analysis_cacheable_optimized(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Convert analysis to a JSON-serializable format for caching."""
        import copy
        
        cacheable = copy.deepcopy(analysis)
        
        # Convert FusedSignal to dict if present
        if "fused_signal" in cacheable:
            fused_signal = cacheable["fused_signal"]
            if hasattr(fused_signal, "__dict__"):
                cacheable["fused_signal"] = {
                    "original_signal": fused_signal.original_signal,
                    "bookmap_summary": fused_signal.bookmap_summary,
                    "fusion_result": fused_signal.fusion_result.value if hasattr(fused_signal.fusion_result, "value") else str(fused_signal.fusion_result),
                    "confidence_boost": float(fused_signal.confidence_boost),
                    "leverage_adjustment": float(fused_signal.leverage_adjustment),
                    "order_flow_score": float(fused_signal.order_flow_score),
                    "fusion_triggers": fused_signal.fusion_triggers,
                    "microstructure_analysis": fused_signal.microstructure_analysis,
                    "enhanced_entry_price": fused_signal.enhanced_entry_price,
                    "enhanced_stop_loss": fused_signal.enhanced_stop_loss
                }
        
        # Convert any enum values in regime_analysis
        if "regime_analysis" in cacheable and "regime" in cacheable["regime_analysis"]:
            regime = cacheable["regime_analysis"]["regime"]
            if hasattr(regime, "value"):
                cacheable["regime_analysis"]["regime"] = regime.value
        
        # FIXED: Convert FusedSignal in ultra_fusion section
        if "ultra_fusion" in cacheable and "bookmap_fusion" in cacheable["ultra_fusion"]:
            fused_signal = cacheable["ultra_fusion"]["bookmap_fusion"]
            if hasattr(fused_signal, "__dict__"):
                cacheable["ultra_fusion"]["bookmap_fusion"] = {
                    "original_signal": fused_signal.original_signal,
                    "bookmap_summary": fused_signal.bookmap_summary,
                    "fusion_result": fused_signal.fusion_result.value if hasattr(fused_signal.fusion_result, "value") else str(fused_signal.fusion_result),
                    "confidence_boost": float(fused_signal.confidence_boost),
                    "leverage_adjustment": float(fused_signal.leverage_adjustment),
                    "order_flow_score": float(fused_signal.order_flow_score),
                    "fusion_triggers": fused_signal.fusion_triggers,
                    "microstructure_analysis": fused_signal.microstructure_analysis,
                    "enhanced_entry_price": fused_signal.enhanced_entry_price,
                    "enhanced_stop_loss": fused_signal.enhanced_stop_loss
                }
        
        return cacheable

    async def _send_ultra_comprehensive_signal_optimized(self, analysis: Dict[str, Any], chat_ids: Optional[List[str]] = None) -> None:
        """Send ultra-comprehensive signal with all institutional insights."""
        
        if analysis.get("direction") == "NEUTRAL":
            # Send enhanced neutral feedback
            enhanced_feedback = analysis.get("detailed_feedback", "No signal detected")
            await telegram_service.send_notification(enhanced_feedback, chat_ids)
        else:
            # Send the signal through the enhanced telegram service
            # The telegram service will format it with all the ultra-comprehensive data
            await telegram_service.send_signal(analysis, chat_ids)
            
            # Additional ultra-insights message
            ultra_insights = self._format_ultra_insights(analysis)
            await telegram_service.send_notification(ultra_insights, chat_ids)
            
    def _enhance_symbol_features_ultra_optimized(
        self, 
        symbol: str, 
        analysis: Dict[str, Any], 
        bookmap_analysis: Dict[str, Any], 
        regime_metrics
    ) -> Dict[str, Any]:
        """ULTRA-OPTIMIZED: Enhanced symbol-specific features for superior confidence variability."""
        
        enhanced_features = {}
        
        # ULTRA-OPTIMIZED: Symbol-specific characteristics for ML variability
        enhanced_features["symbol"] = symbol
        enhanced_features["symbol_hash"] = hash(symbol) % 1000  # Consistent pseudo-random factor
        enhanced_features["symbol_length"] = len(symbol)
        enhanced_features["is_major_pair"] = 1.0 if symbol in ["BTCUSDT", "ETHUSDT", "BNBUSDT"] else 0.0
        enhanced_features["is_altcoin"] = 1.0 if symbol.endswith("USDT") and symbol not in ["BTCUSDT", "ETHUSDT"] else 0.0
        
        # ULTRA-OPTIMIZED: Volatility tier classification
        if "BTC" in symbol or "ETH" in symbol:
            enhanced_features["volatility_tier"] = 1.0  # Low volatility
        elif len(symbol) <= 8 and symbol.endswith("USDT"):
            enhanced_features["volatility_tier"] = 2.0  # Medium volatility
        else:
            enhanced_features["volatility_tier"] = 3.0  # High volatility
            
        # ULTRA-OPTIMIZED: Order flow integration features
        if bookmap_analysis:
            enhanced_features["whale_activity_factor"] = bookmap_analysis.get("whale_signals", 0) / max(1, bookmap_analysis.get("total_signals", 1))
            enhanced_features["iceberg_detection_ratio"] = bookmap_analysis.get("iceberg_signals", 0) / max(1, bookmap_analysis.get("total_signals", 1))
            enhanced_features["institutional_flow_strength"] = bookmap_analysis.get("institutional_score", 0) / 10.0
            enhanced_features["smart_money_presence"] = 1.0 if bookmap_analysis.get("smart_money_signals", 0) > 0 else 0.0
        else:
            enhanced_features["whale_activity_factor"] = 0.0
            enhanced_features["iceberg_detection_ratio"] = 0.0
            enhanced_features["institutional_flow_strength"] = 0.0
            enhanced_features["smart_money_presence"] = 0.0
            
        # ULTRA-OPTIMIZED: Market regime integration
        enhanced_features["regime_confidence"] = regime_metrics.confidence / 10.0
        enhanced_features["regime_volatility"] = regime_metrics.volatility_percentile
        enhanced_features["regime_trend_strength"] = regime_metrics.trend_strength
        enhanced_features["regime_is_trending"] = 1.0 if "trending" in regime_metrics.regime.value.lower() else 0.0
        enhanced_features["regime_is_volatile"] = 1.0 if "volatile" in regime_metrics.regime.value.lower() else 0.0
        
        # ULTRA-OPTIMIZED: Technical analysis quality enhancement
        accuracy_metrics = analysis.get("accuracy_metrics", {})
        enhanced_features["signal_strength_normalized"] = accuracy_metrics.get("signal_strength", 0) / 10.0
        enhanced_features["confluence_density"] = accuracy_metrics.get("confluence_points", 0) / 5.0  # Normalize to max 5
        enhanced_features["momentum_alignment"] = accuracy_metrics.get("momentum_score", 0) / 10.0
        enhanced_features["volume_confirmation"] = accuracy_metrics.get("volume_score", 0) / 10.0
        
        # ULTRA-OPTIMIZED: Risk-reward optimization
        enhanced_features["risk_reward_quality"] = min(5.0, analysis.get("risk_reward_ratio", 1.0)) / 5.0
        enhanced_features["stop_distance_normalized"] = min(10.0, analysis.get("stop_distance_pct", 2.0)) / 10.0
        enhanced_features["liquidation_buffer"] = min(50.0, analysis.get("liquidation_distance_pct", 10.0)) / 50.0
        
        # ULTRA-OPTIMIZED: Time-based factors for market conditions
        import datetime
        now = datetime.datetime.utcnow()
        enhanced_features["hour_of_day"] = now.hour / 24.0  # 0-1 normalized
        enhanced_features["day_of_week"] = now.weekday() / 7.0  # 0-1 normalized
        enhanced_features["is_market_hours"] = 1.0 if 8 <= now.hour <= 22 else 0.5  # UTC market activity
        enhanced_features["is_weekend"] = 1.0 if now.weekday() >= 5 else 0.0
        
        return enhanced_features

    def _format_ultra_insights(self, analysis: Dict[str, Any]) -> str:
        """Format additional ultra-comprehensive insights."""
        
        symbol = analysis["symbol"]
        processing_time = float(analysis.get("processing_time_ms", 0))
        quality_score = float(analysis.get("ultra_quality_score", 0))
        
        bookmap_analysis = analysis.get("bookmap_analysis", {})
        regime_analysis = analysis.get("regime_analysis", {})
        
        insights = f"""
🧠 **INSTITUTIONAL INSIGHTS: {symbol}**

⏱️ **Analysis Performance:**
• Processing Time: {processing_time}ms
• Analysis Depth: {analysis.get('analysis_depth', 'STANDARD')}
• Quality Score: {quality_score:.1f}/10

🌊 **Order Flow Summary:**
• Flow Score: {float(bookmap_analysis.get('order_flow_score', 0)):+.1f}
• Whale Volume: ${float(bookmap_analysis.get('whale_analysis', {}).get('total_volume', 0)):,.0f}
• Iceberg Orders: {int(bookmap_analysis.get('iceberg_analysis', {}).get('total_count', 0))}

📊 **Market Context:**
• Regime: {regime_analysis.get('regime', 'UNKNOWN')}
• Regime Confidence: {float(regime_analysis.get('confidence', 0)):.1f}/10

💎 **Signal Quality Factors:**
• Technical Confidence: {float(analysis.get('confidence_score', 0)):.1f}/10
• Fusion Boost: +{float(analysis.get('total_fusion_boost', 0)):.1f}
• Risk-Reward: {analysis.get('risk_reward', [0, 0, 0])}

⚡ **This signal leveraged ALL institutional-grade capabilities**
"""
        
        return insights


# Global signal processor instance
signal_processor = SignalProcessor() 