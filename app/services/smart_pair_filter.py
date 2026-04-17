"""
Smart Pair Filtering Service

Pre-filters trading pairs based on volatility, volume, and other criteria
to avoid expensive analysis on low-probability pairs.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import time

from ..core.logging import get_logger
from ..core.settings import settings
from ..data.rest import rest_client

logger = get_logger(__name__)


class SmartPairFilter:
    """Intelligent pre-filtering for trading pairs to optimize performance."""
    
    def __init__(self):
        self.filter_cache = {}  # Cache filter results
        self.pair_scores = {}   # Track pair performance scores
        self.last_scan_time = None
        
        # Filter thresholds (RELAXED for better signal generation)
        self.min_volatility_threshold = 2.0  # RELAXED: 8.0 → 2.0 (2%+ 24h change) ⭐
        self.min_volume_threshold = 500000   # RELAXED: 3M → 500K volume ⭐
        self.max_pairs_for_analysis = 25     # INCREASED: 20 → 25 pairs ⭐
        
    async def get_priority_pairs(self, all_pairs: List[str]) -> List[str]:
        """
        Filter and prioritize pairs for analysis.
        
        Args:
            all_pairs: List of all available trading pairs
            
        Returns:
            Filtered list of high-priority pairs
        """
        try:
            logger.info(f"Smart filtering {len(all_pairs)} pairs")
            start_time = time.time()
            
            # Get all tickers for quick filtering
            all_tickers = await rest_client.get_all_tickers()
            ticker_map = {ticker["symbol"]: ticker for ticker in all_tickers}
            
            # Score and filter pairs
            scored_pairs = []
            
            for pair in all_pairs:
                if pair not in ticker_map:
                    continue
                    
                ticker = ticker_map[pair]
                score = await self._calculate_pair_score(pair, ticker)
                
                if score > 0:  # Only include pairs that pass filters
                    scored_pairs.append((pair, score))
            
            # Sort by score and take top pairs
            scored_pairs.sort(key=lambda x: x[1], reverse=True)
            priority_pairs = [pair for pair, score in scored_pairs[:self.max_pairs_for_analysis]]
            
            elapsed = time.time() - start_time
            logger.info(
                f"Smart filtering completed: {len(priority_pairs)} priority pairs selected",
                total_pairs=len(all_pairs),
                selected_pairs=len(priority_pairs),
                elapsed_ms=round(elapsed * 1000)
            )
            
            return priority_pairs
            
        except Exception as e:
            logger.error(f"Smart filtering failed: {e}")
            # Fallback to first N pairs if filtering fails
            return all_pairs[:self.max_pairs_for_analysis]
    
    async def _calculate_pair_score(self, pair: str, ticker: Dict[str, Any]) -> float:
        """
        Calculate priority score for a trading pair.
        
        Higher score = higher priority for analysis.
        Score of 0 = filtered out.
        """
        try:
            # Extract ticker data
            price_change_pct = abs(float(ticker.get("price24hPcnt", 0)) * 100)
            volume_24h = float(ticker.get("turnover24h", 0))
            last_price = float(ticker.get("lastPrice", 0))
            high_24h = float(ticker.get("highPrice24h", 0))
            low_24h = float(ticker.get("lowPrice24h", 0))
            
            # Basic filters - must pass to get any score
            if (price_change_pct < self.min_volatility_threshold or 
                volume_24h < self.min_volume_threshold or
                last_price <= 0):
                return 0.0
            
            # Calculate scoring components
            volatility_score = min(price_change_pct / 20.0, 1.0)  # Normalize to 0-1
            volume_score = min(volume_24h / 10000000, 1.0)        # $10M = max score
            
            # Calculate price range volatility
            if last_price > 0:
                range_volatility = ((high_24h - low_24h) / last_price) * 100
                range_score = min(range_volatility / 25.0, 1.0)   # 25% range = max score
            else:
                range_score = 0.0
            
            # Historical performance bonus (if available)
            historical_bonus = self.pair_scores.get(pair, 0.0)
            
            # Combine scores with weights
            final_score = (
                volatility_score * 0.4 +    # 40% weight on price movement
                volume_score * 0.3 +        # 30% weight on volume
                range_score * 0.2 +         # 20% weight on volatility
                historical_bonus * 0.1      # 10% weight on historical performance
            )
            
            logger.debug(f"Pair {pair} score: {final_score:.3f}", 
                        volatility=price_change_pct,
                        volume=volume_24h,
                        final_score=final_score)
            
            return final_score
            
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to score pair {pair}: {e}")
            return 0.0
    
    def update_pair_performance(self, pair: str, performance_score: float):
        """
        Update historical performance score for a pair.
        
        Args:
            pair: Trading pair symbol
            performance_score: Performance score (-1 to 1, where 1 = excellent)
        """
        if pair not in self.pair_scores:
            self.pair_scores[pair] = 0.0
            
        # Exponential moving average of performance
        alpha = 0.3  # Learning rate
        self.pair_scores[pair] = (alpha * performance_score + 
                                 (1 - alpha) * self.pair_scores[pair])
        
        # Keep scores in reasonable range
        self.pair_scores[pair] = max(-0.5, min(0.5, self.pair_scores[pair]))
    
    async def get_market_conditions_filter(self) -> Dict[str, Any]:
        """
        Get current market conditions to adjust filtering thresholds.
        
        Returns:
            Market condition adjustments
        """
        try:
            # Get major pair data for market sentiment
            btc_ticker = await rest_client.get_ticker("BTCUSDT")
            eth_ticker = await rest_client.get_ticker("ETHUSDT")
            
            btc_change = float(btc_ticker.get("price24hPcnt", 0)) * 100
            eth_change = float(eth_ticker.get("price24hPcnt", 0)) * 100
            
            # Determine market regime
            avg_major_change = (abs(btc_change) + abs(eth_change)) / 2
            
            if avg_major_change > 10:
                # High volatility market - be more selective
                return {
                    "market_regime": "high_volatility",
                    "volatility_multiplier": 1.2,
                    "volume_multiplier": 1.5,
                    "max_pairs_adjustment": -5
                }
            elif avg_major_change < 3:
                # Low volatility market - look for any movement
                return {
                    "market_regime": "low_volatility", 
                    "volatility_multiplier": 0.8,
                    "volume_multiplier": 0.7,
                    "max_pairs_adjustment": 5
                }
            else:
                # Normal market conditions
                return {
                    "market_regime": "normal",
                    "volatility_multiplier": 1.0,
                    "volume_multiplier": 1.0,
                    "max_pairs_adjustment": 0
                }
                
        except Exception as e:
            logger.warning(f"Failed to analyze market conditions: {e}")
            return {
                "market_regime": "unknown",
                "volatility_multiplier": 1.0,
                "volume_multiplier": 1.0,
                "max_pairs_adjustment": 0
            }
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """Get filtering statistics and performance metrics."""
        return {
            "total_pairs_tracked": len(self.pair_scores),
            "last_scan_time": self.last_scan_time,
            "filter_thresholds": {
                "min_volatility": self.min_volatility_threshold,
                "min_volume": self.min_volume_threshold,
                "max_pairs": self.max_pairs_for_analysis
            },
            "top_performing_pairs": dict(sorted(
                self.pair_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10])
        }


# Global instance
smart_filter = SmartPairFilter() 