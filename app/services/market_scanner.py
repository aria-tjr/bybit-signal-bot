"""
Market scanner service for identifying high-volatility trading opportunities.

Automatically scans for top movers and small-cap coins suitable for short-term 
high-leverage trading with 1m and 5m timeframes.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time

from ..core.logging import get_logger
from ..core.settings import settings
from ..data.rest import rest_client
from ..data.cache import cache
from .signal_processor import signal_processor
from .telegram import telegram_service

logger = get_logger(__name__)


class MarketScanner:
    """
    Automated market scanner for short-term trading opportunities.
    
    Focuses on:
    - Top gainers/losers (red/green coins)
    - Small-cap high-volatility coins
    - Volume breakouts
    - Quick profit opportunities with 20x leverage
    """
    
    def __init__(self) -> None:
        """Initialize market scanner."""
        self.is_running = False
        self.last_scan_time = None
        self.processed_symbols = set()  # Avoid duplicate processing
        self.scan_results_cache = {}
        
    async def start_scanning(self) -> None:
        """Start the automated market scanning loop."""
        if not settings.scanner_enabled:
            logger.info("Market scanner is disabled in settings")
            return
            
        logger.info("Starting market scanner for short-term opportunities")
        self.is_running = True
        
        # Send startup notification
        await telegram_service.send_notification(
            "🔍 *Market Scanner Started*\n"
            f"• Scanning every {settings.scanner_interval_minutes} minutes\n"
            f"• Looking for {settings.min_price_change_pct}%+ moves\n"
            f"• Focus: 1m/5m timeframes with 20x leverage\n"
            "• Target: Top gainers/losers & small caps"
        )
        
        while self.is_running:
            try:
                await self._scan_cycle()
                await asyncio.sleep(settings.scanner_interval_minutes * 60)
                
            except Exception as e:
                logger.error("Scanner cycle failed", error=str(e))
                await asyncio.sleep(30)  # Short retry delay
                
    async def stop_scanning(self) -> None:
        """Stop the market scanner."""
        logger.info("Stopping market scanner")
        self.is_running = False
        
        await telegram_service.send_notification(
            "🛑 *Market Scanner Stopped*"
        )
        
    async def _scan_cycle(self) -> None:
        """Execute one complete scanning cycle."""
        scan_start = time.time()
        logger.info("Starting market scan cycle")
        
        try:
            # Parallel scanning for different categories
            tasks = [
                self._scan_top_movers(),
                self._scan_small_cap_movers(),
                self._scan_volume_breakouts()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            total_opportunities = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Scan task {i} failed", error=str(result))
                else:
                    total_opportunities += len(result) if result else 0
                    
            scan_duration = time.time() - scan_start
            logger.info(
                "Scan cycle completed",
                opportunities=total_opportunities,
                duration_ms=round(scan_duration * 1000)
            )
            
            # Clean processed symbols cache (keep only last hour)
            current_time = datetime.utcnow()
            cutoff_time = current_time - timedelta(hours=1)
            self.processed_symbols = {
                symbol for symbol in self.processed_symbols
                if current_time.timestamp() - hash(symbol) % 3600 < 3600
            }
            
        except Exception as e:
            logger.error("Scan cycle error", error=str(e))
            
    async def _scan_top_movers(self) -> List[str]:
        """Scan for top gaining and losing coins."""
        try:
            movers = await rest_client.get_top_movers(
                count=settings.top_movers_count,
                min_volume_usdt=settings.min_volume_usdt,
                min_change_pct=settings.min_price_change_pct
            )
            
            opportunities = []
            
            # Process gainers (green coins)
            for gainer in movers["gainers"]:
                symbol = gainer["symbol"]
                if await self._should_analyze_symbol(symbol, gainer):
                    opportunities.append(symbol)
                    await self._analyze_opportunity(symbol, "GAINER", gainer)
                    
            # Process losers (red coins)  
            for loser in movers["losers"]:
                symbol = loser["symbol"]
                if await self._should_analyze_symbol(symbol, loser):
                    opportunities.append(symbol)
                    await self._analyze_opportunity(symbol, "LOSER", loser)
                    
            logger.info(
                "Top movers scan completed",
                gainers=len(movers["gainers"]),
                losers=len(movers["losers"]),
                analyzed=len(opportunities)
            )
            
            return opportunities
            
        except Exception as e:
            logger.error("Top movers scan failed", error=str(e))
            return []
            
    async def _scan_small_cap_movers(self) -> List[str]:
        """Scan for small-cap high-volatility coins."""
        try:
            small_caps = await rest_client.get_small_cap_movers(
                count=10,
                min_change_pct=5.0
            )
            
            opportunities = []
            
            for coin in small_caps:
                symbol = coin["symbol"]
                if coin["leverage_suitable"] and await self._should_analyze_symbol(symbol, coin):
                    opportunities.append(symbol)
                    await self._analyze_opportunity(symbol, "SMALL_CAP", coin)
                    
            logger.info(
                "Small cap scan completed",
                found=len(small_caps),
                analyzed=len(opportunities)
            )
            
            return opportunities
            
        except Exception as e:
            logger.error("Small cap scan failed", error=str(e))
            return []
            
    async def _scan_volume_breakouts(self) -> List[str]:
        """Scan for unusual volume spikes indicating breakouts."""
        try:
            # This would require historical volume comparison
            # For now, we'll implement a basic version
            tickers = await rest_client.get_all_tickers()
            
            opportunities = []
            for ticker in tickers[:50]:  # Check top 50 by volume
                try:
                    symbol = ticker.get("symbol", "")
                    volume_24h = float(ticker.get("turnover24h", 0))
                    price_change = abs(float(ticker.get("price24hPcnt", 0)) * 100)
                    
                    # Look for high volume with moderate price change (breakout pattern)
                    if (
                        volume_24h > 5000000 and  # High volume
                        price_change >= 2.0 and  # Some movement
                        price_change <= 8.0 and  # Not too extreme
                        symbol.endswith("USDT")
                    ):
                        if await self._should_analyze_symbol(symbol, ticker):
                            opportunities.append(symbol)
                            await self._analyze_opportunity(symbol, "VOLUME_BREAKOUT", ticker)
                            
                except (ValueError, TypeError):
                    continue
                    
            logger.info("Volume breakout scan completed", analyzed=len(opportunities))
            return opportunities
            
        except Exception as e:
            logger.error("Volume breakout scan failed", error=str(e))
            return []
            
    async def _should_analyze_symbol(self, symbol: str, ticker_data: Dict[str, Any]) -> bool:
        """Determine if a symbol should be analyzed."""
        # Skip if recently processed
        if symbol in self.processed_symbols:
            return False
            
        # Check cache for recent analysis
        cached_analysis = await cache.get_analysis(symbol)
        if cached_analysis:
            try:
                timestamp = float(cached_analysis.get("timestamp", 0))
                cache_age = time.time() - timestamp
                if cache_age < 300:  # 5 minutes
                    return False
            except (ValueError, TypeError):
                # Invalid timestamp, ignore cache
                pass
                
        # Basic filters
        try:
            price_change = abs(float(ticker_data.get("price_change_pct", 0)))
            volume = float(ticker_data.get("volume_24h", 0))
            
            return (
                price_change >= settings.min_price_change_pct and
                volume >= 500000  # Minimum liquidity
            )
            
        except (ValueError, TypeError):
            return False
            
    async def _analyze_opportunity(
        self, 
        symbol: str, 
        category: str, 
        ticker_data: Dict[str, Any]
    ) -> None:
        """Analyze a trading opportunity and send signal if valid."""
        try:
            self.processed_symbols.add(symbol)
            
            logger.info(
                "Analyzing opportunity",
                symbol=symbol,
                category=category,
                price_change=ticker_data.get("price_change_pct", 0)
            )
            
            # Process with adjusted threshold for quick profits
            threshold = 2.0 if category == "SMALL_CAP" else 3.0
            
            result = await signal_processor.process_symbol(
                symbol,
                threshold_pct=threshold
            )
            
            # Add scanner context to successful signals
            if result and result.get("direction") != "NEUTRAL":
                scanner_info = {
                    "scanner_category": category,
                    "detected_at": datetime.utcnow().isoformat(),
                    "price_change_24h": ticker_data.get("price_change_pct", 0),
                    "volume_24h": ticker_data.get("volume_24h", 0),
                    "timeframe_focus": "1m/5m scalping"
                }
                
                # Send enhanced notification
                await self._send_scanner_alert(symbol, result, scanner_info)
                
        except Exception as e:
            logger.error("Opportunity analysis failed", symbol=symbol, error=str(e))
            
    async def _send_scanner_alert(
        self,
        symbol: str,
        analysis: Dict[str, Any],
        scanner_info: Dict[str, Any]
    ) -> None:
        """Send enhanced alert for scanner-detected opportunities."""
        try:
            category_emoji = {
                "GAINER": "🟢",
                "LOSER": "🔴", 
                "SMALL_CAP": "💎",
                "VOLUME_BREAKOUT": "📈"
            }
            
            emoji = category_emoji.get(scanner_info["scanner_category"], "🔍")
            category = scanner_info["scanner_category"].replace("_", " ").title()
            
            alert_message = (
                f"{emoji} *SCANNER ALERT: {category}*\n"
                f"📊 *{symbol}*\n"
                f"📈 24h Change: {scanner_info['price_change_24h']:+.1f}%\n"
                f"💰 Volume: ${scanner_info['volume_24h']:,.0f}\n"
                f"⚡ Direction: *{analysis['direction']}*\n"
                f"🎯 Entry: {analysis['entry_price']}\n"
                f"📊 Leverage: {analysis['leverage']}x\n"
                f"⏰ Timeframes: 1m/5m scalping\n"
                "🚨 *Scanner-detected opportunity!*"
            )
            
            await telegram_service.send_notification(alert_message)
            
            # Also send the full signal
            await telegram_service.send_signal(analysis)
            
        except Exception as e:
            logger.error("Failed to send scanner alert", error=str(e))
            
    async def get_scanner_status(self) -> Dict[str, Any]:
        """Get current scanner status and statistics."""
        return {
            "is_running": self.is_running,
            "last_scan_time": self.last_scan_time,
            "processed_symbols_count": len(self.processed_symbols),
            "settings": {
                "interval_minutes": settings.scanner_interval_minutes,
                "min_price_change_pct": settings.min_price_change_pct,
                "top_movers_count": settings.top_movers_count,
                "min_volume_usdt": settings.min_volume_usdt
            }
        }
        
    async def manual_scan(self, category: str = "all") -> Dict[str, Any]:
        """Manually trigger a scan for testing purposes."""
        if category == "all":
            results = {
                "top_movers": await self._scan_top_movers(),
                "small_caps": await self._scan_small_cap_movers(),
                "volume_breakouts": await self._scan_volume_breakouts()
            }
        elif category == "100_pairs":
            # Comprehensive 100-pair scan
            results = await self.scan_100_pairs()
        elif category == "top_movers":
            results = {"top_movers": await self._scan_top_movers()}
        elif category == "small_caps":
            results = {"small_caps": await self._scan_small_cap_movers()}
        elif category == "volume_breakouts":
            results = {"volume_breakouts": await self._scan_volume_breakouts()}
        else:
            results = {"error": "Invalid category"}
            
        return results

    async def scan_100_pairs(self) -> Dict[str, Any]:
        """
        Optimized scan using staged analysis for better performance.
        
        Returns:
            Dictionary with categorized opportunities and analysis
        """
        try:
            logger.info("Starting optimized 100-pair market scan with staged analysis")
            scan_start = time.time()
            
            # Get all USDT tickers for initial filtering
            all_tickers = await rest_client.get_all_tickers()
            
            # Extract symbol list
            all_symbols = [ticker["symbol"] for ticker in all_tickers 
                          if ticker.get("symbol", "").endswith("USDT")]
            
            logger.info(f"Found {len(all_symbols)} USDT pairs for analysis")
            
            # Use staged analysis for optimized processing
            from .staged_analysis import staged_analyzer
            
            analysis_results = await staged_analyzer.analyze_pairs_staged(all_symbols)
            
            # Extract final signals
            final_signals = analysis_results.get("final_signals", [])
            stage_results = analysis_results.get("stage_results", {})
            performance_stats = analysis_results.get("performance_stats", {})
            
            # Categorize opportunities based on signals
            opportunities = {
                "strong_bullish": [],
                "strong_bearish": [],
                "high_volatility": [],
                "volume_breakouts": [],
                "momentum_plays": [],
                "small_cap_gems": []
            }
            
            # Categorize signals
            for signal in final_signals:
                signal_info = {
                    "symbol": signal["symbol"],
                    "direction": signal["direction"],
                    "confidence": signal["confidence"],
                    "price_change_pct": 0,  # Will be updated from ticker data
                    "volume_24h": 0,        # Will be updated from ticker data
                    "score": signal["confidence"] * 100,
                    "source_category": "staged_analysis"
                }
                
                # Get ticker data for additional info
                ticker_map = {t["symbol"]: t for t in all_tickers}
                if signal["symbol"] in ticker_map:
                    ticker = ticker_map[signal["symbol"]]
                    signal_info["price_change_pct"] = float(ticker.get("price24hPcnt", 0)) * 100
                    signal_info["volume_24h"] = float(ticker.get("turnover24h", 0))
                
                # Categorize based on direction and characteristics
                if signal["direction"] == "LONG":
                    if signal["confidence"] > 0.8:
                        opportunities["strong_bullish"].append(signal_info)
                    else:
                        opportunities["momentum_plays"].append(signal_info)
                elif signal["direction"] == "SHORT":
                    if signal["confidence"] > 0.8:
                        opportunities["strong_bearish"].append(signal_info)
                    else:
                        opportunities["high_volatility"].append(signal_info)
                
                # Check for small cap gems (lower volume but high confidence)
                if signal_info["volume_24h"] < 5000000 and signal["confidence"] > 0.75:
                    opportunities["small_cap_gems"].append(signal_info)
            
            scan_duration = time.time() - scan_start
            
            # Sort each category by score
            for category in opportunities:
                opportunities[category] = sorted(
                    opportunities[category],
                    key=lambda x: x["score"],
                    reverse=True
                )[:10]  # Top 10 per category
            
            # Generate summary with staged analysis stats
            total_opportunities = sum(len(cat) for cat in opportunities.values())
            
            result = {
                "scan_summary": {
                    "pairs_available": len(all_symbols),
                    "pairs_pre_filtered": stage_results.get("stage0_filtering", {}).get("output_pairs", 0),
                    "quick_scan_candidates": stage_results.get("stage1_quick_scan", {}).get("output_pairs", 0),
                    "detailed_candidates": stage_results.get("stage2_detailed", {}).get("output_pairs", 0),
                    "final_signals": len(final_signals),
                    "total_opportunities": total_opportunities,
                    "scan_duration_seconds": round(scan_duration, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "optimization_method": "staged_analysis_pipeline"
                },
                "opportunities": opportunities,
                "top_picks": self._select_top_picks(opportunities),
                "stage_results": stage_results,
                "performance_stats": performance_stats
            }
            
            logger.info(
                "Optimized 100-pair scan completed",
                pairs_available=len(all_symbols),
                signals_generated=len(final_signals),
                opportunities_found=total_opportunities,
                duration_seconds=round(scan_duration, 2),
                efficiency_ratio=f"{len(final_signals)}/{len(all_symbols)}"
            )
            
            return result
            
        except Exception as e:
            logger.error("100-pair scan failed", error=str(e))
            return {"error": f"Scan failed: {str(e)}"}
    
    async def _quick_analyze_pair(self, pair_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        STRICT analysis on a trading pair using signal-grade requirements.
        Only returns pairs that have high probability of generating actual signals.
        
        Args:
            pair_data: Ticker data for the pair
            
        Returns:
            Analysis result or None
        """
        try:
            symbol = pair_data["symbol"]
            price_change = pair_data["price_change_pct"]
            volume_24h = pair_data["volume_24h"]
            last_price = pair_data["last_price"]
            high_24h = pair_data["high_24h"]
            low_24h = pair_data["low_24h"]
            
            # Calculate volatility
            volatility = ((high_24h - low_24h) / last_price * 100) if last_price > 0 else 0
            
            # ULTRA-STRICT FILTERING - Only include pairs with exceptional signal potential
            
            # Minimum requirements (much higher standards)
            min_volume = 3000000  # $3M minimum volume (was 2M)
            min_volatility = 15.0  # 15%+ volatility required (was 12%)
            min_price_change = 8.0  # 8%+ price movement required (was 6%)
            
            # Basic filters - must pass all
            if (volume_24h < min_volume or 
                volatility < min_volatility or 
                abs(price_change) < min_price_change):
                return None
                
            # ENHANCED TECHNICAL PRE-SCREENING
            # Get basic technical data for stricter validation
            try:
                from ..data.rest import rest_client
                
                # Get recent klines for technical validation
                klines = await rest_client.get_klines(symbol, "15", limit=50)
                if klines is None or klines.empty:
                    return None
                    
                # Calculate basic technical indicators for validation
                closes = klines['close']
                
                # EMA validation (basic trend structure check)
                ema_20 = closes.ewm(span=20).mean().iloc[-1]
                ema_50 = closes.ewm(span=50).mean().iloc[-1] if len(closes) >= 50 else ema_20
                current_price = closes.iloc[-1]
                
                # RSI validation (avoid extreme oversold/overbought)
                delta = closes.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                current_rsi = rsi.iloc[-1] if not rsi.empty else 50
                
                # STRICT TECHNICAL REQUIREMENTS
                trend_aligned = False
                momentum_confirmed = False
                
                # For BULLISH signals
                if price_change > 0:
                    # Trend alignment: price above EMAs and EMAs in order
                    trend_aligned = (current_price > ema_20 > ema_50)
                    # Momentum: RSI in healthy bullish range
                    momentum_confirmed = (35 < current_rsi < 75)
                    
                # For BEARISH signals  
                elif price_change < 0:
                    # Trend alignment: price below EMAs and EMAs in order
                    trend_aligned = (current_price < ema_20 < ema_50)
                    # Momentum: RSI in healthy bearish range
                    momentum_confirmed = (25 < current_rsi < 65)
                
                # Must pass technical validation
                if not (trend_aligned and momentum_confirmed):
                    return None
                    
            except Exception as tech_error:
                # If technical analysis fails, skip this pair
                logger.debug(f"Technical validation failed for {symbol}: {tech_error}")
                return None
            
            # STRICT SCORING SYSTEM (much higher thresholds)
            score = 0
            category = "NEUTRAL"
            
            # ULTRA-STRICT Strong bullish (premium quality only)
            if (price_change >= 10.0 and  # Higher threshold: 10%+ (was 8%)
                volume_24h >= 5000000 and  # $5M+ volume (was 3M)
                volatility >= 18.0 and  # 18%+ volatility (was 15%)
                trend_aligned and momentum_confirmed):
                
                score = (abs(price_change) * 2) + (volume_24h / 1000000) + volatility
                category = "STRONG_BULLISH"
                
            # ULTRA-STRICT Strong bearish
            elif (price_change <= -10.0 and  # Higher threshold: -10% (was -8%)
                  volume_24h >= 5000000 and  # $5M+ volume (was 3M)
                  volatility >= 18.0 and  # 18%+ volatility (was 15%)
                  trend_aligned and momentum_confirmed):
                
                score = (abs(price_change) * 2) + (volume_24h / 1000000) + volatility
                category = "STRONG_BEARISH"
                
            # Premium volume breakouts (institutional-level activity)
            elif (volume_24h >= 15000000 and  # $15M+ volume (was 10M)
                  abs(price_change) >= 8.0 and  # 8%+ move (was 6%)
                  volatility >= 15.0):  # 15%+ volatility (was 12%)
                
                score = (volume_24h / 1000000) + (abs(price_change) * 3) + volatility
                category = "VOLUME_BREAKOUTS"
                
            # Premium momentum plays (trend continuation setups)
            elif (abs(price_change) >= 9.0 and  # 9%+ move (was 7%)
                  volatility >= 20.0 and  # 20%+ volatility (was 18%)
                  volume_24h >= 4000000 and  # $4M+ volume (was 2.5M)
                  trend_aligned and momentum_confirmed):
                
                score = (abs(price_change) * 2.5) + volatility + (volume_24h / 2000000)
                category = "MOMENTUM_PLAYS"
                
            # Elite small cap gems (only exceptional moves)
            elif (volume_24h >= 800000 and  # $800k+ volume (was 500k)
                  volume_24h <= 4000000 and  # Under $4M (was 3M)
                  abs(price_change) >= 15.0 and  # 15%+ move (was 12%)
                  volatility >= 25.0 and  # 25%+ volatility (was 20%)
                  not any(major in symbol for major in ["BTC", "ETH", "BNB", "SOL", "ADA", "XRP"]) and
                  trend_aligned and momentum_confirmed):
                
                score = (abs(price_change) * 3) + volatility + (volume_24h / 500000)
                category = "SMALL_CAP_GEMS"
                
            # ULTRA-STRICT MINIMUM SCORE (elite quality only)
            min_score = 35.0  # Ultra-high minimum (was 25.0)
            
            if category != "NEUTRAL" and score >= min_score:
                return {
                    "symbol": symbol,
                    "category": category,
                    "score": round(score, 2),
                    "price_change_pct": round(price_change, 2),
                    "volume_24h": volume_24h,
                    "volatility": round(volatility, 2),
                    "last_price": last_price,
                    "leverage_suitable": volatility >= 15.0 and volume_24h >= 2000000,
                    "technical_validation": "PASSED",
                    "signal_probability": "HIGH",  # High probability of generating actual signal
                    "trend_aligned": trend_aligned,
                    "momentum_confirmed": momentum_confirmed,
                    "current_rsi": round(current_rsi, 1) if 'current_rsi' in locals() else None
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Strict analysis failed for {pair_data.get('symbol', 'unknown')}", error=str(e))
            return None
    
    def _select_top_picks(self, opportunities: Dict[str, List]) -> List[Dict[str, Any]]:
        """
        Select the top 5 overall picks across all categories.
        
        Args:
            opportunities: Categorized opportunities
            
        Returns:
            List of top picks
        """
        all_opportunities = []
        for category, pairs in opportunities.items():
            for pair in pairs:
                pair_copy = pair.copy()
                pair_copy["source_category"] = category
                all_opportunities.append(pair_copy)
        
        # Sort by score and return top 5
        top_picks = sorted(all_opportunities, key=lambda x: x["score"], reverse=True)[:5]
        
        return top_picks


# Global market scanner instance
market_scanner = MarketScanner() 