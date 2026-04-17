"""
Rate Limited Data Collector

Handles data collection with proper rate limiting, batching, and optimization
to avoid API rate limits when scaling to many trading pairs.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import time
import pandas as pd

from ..core.logging import get_logger
from ..core.settings import settings
from ..data.rest import rest_client
from ..data.cache import cache

logger = get_logger(__name__)


class RateLimitedDataCollector:
    """Optimized data collector with rate limiting and smart batching."""
    
    def __init__(self):
        # Rate limiting configuration
        self.max_concurrent_requests = 10
        self.request_delay = 0.1  # 100ms between requests
        self.batch_size = 20
        
        # Semaphore for limiting concurrent requests
        self.request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        # Cache settings
        self.cache_ttl_seconds = {
            "ticker": 30,     # 30 seconds for ticker data
            "klines": 120,    # 2 minutes for kline data
            "analysis": 300   # 5 minutes for analysis results
        }
        
        # Priority timeframes
        self.primary_timeframes = ["15m", "1h"]      # Always fetch these
        self.secondary_timeframes = ["5m", "4h"]     # Fetch for top candidates only
        
    async def collect_multi_pair_data(
        self, 
        pairs: List[str], 
        include_secondary_timeframes: bool = False
    ) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Collect data for multiple pairs with optimized batching.
        
        Args:
            pairs: List of trading pairs
            include_secondary_timeframes: Whether to include 5m and 4h data
            
        Returns:
            Dictionary mapping pairs to their timeframe data
        """
        try:
            logger.info(f"Starting optimized data collection for {len(pairs)} pairs")
            start_time = time.time()
            
            # Determine timeframes to fetch
            timeframes = self.primary_timeframes.copy()
            if include_secondary_timeframes:
                timeframes.extend(self.secondary_timeframes)
            
            # Check cache first
            cache_results = await self._check_cache_batch(pairs, timeframes)
            cache_hits = cache_results["hits"]
            cache_misses = cache_results["misses"]
            
            logger.info(f"Cache check: {len(cache_hits)} hits, {len(cache_misses)} misses")
            
            # Fetch missing data in batches
            fresh_data = {}
            if cache_misses:
                fresh_data = await self._fetch_missing_data_batch(cache_misses, timeframes)
            
            # Combine cached and fresh data
            all_data = {**cache_hits, **fresh_data}
            
            elapsed = time.time() - start_time
            logger.info(
                f"Data collection completed for {len(pairs)} pairs",
                cached_pairs=len(cache_hits),
                fetched_pairs=len(fresh_data),
                elapsed_ms=round(elapsed * 1000)
            )
            
            return all_data
            
        except Exception as e:
            logger.error(f"Multi-pair data collection failed: {e}")
            return {}
    
    async def _check_cache_batch(
        self, 
        pairs: List[str], 
        timeframes: List[str]
    ) -> Dict[str, Dict]:
        """Check cache for existing data."""
        cache_hits = {}
        cache_misses = []
        
        for pair in pairs:
            pair_data = {}
            pair_complete = True
            
            for tf in timeframes:
                cached = await cache.get_kline(pair, tf)
                if cached and self._is_cache_valid(cached, tf):
                    # Convert cached data back to DataFrame
                    try:
                        df = pd.DataFrame(cached["data"])
                        if not df.empty:
                            df["timestamp"] = pd.to_datetime(df["timestamp"])
                            df.set_index("timestamp", inplace=True)
                            pair_data[tf] = df
                        else:
                            pair_complete = False
                            break
                    except Exception:
                        pair_complete = False
                        break
                else:
                    pair_complete = False
                    break
            
            if pair_complete and pair_data:
                cache_hits[pair] = pair_data
            else:
                cache_misses.append(pair)
        
        return {"hits": cache_hits, "misses": cache_misses}
    
    def _is_cache_valid(self, cached_data: Dict, timeframe: str) -> bool:
        """Check if cached data is still valid."""
        try:
            cache_time = cached_data.get("timestamp", 0)
            age_seconds = time.time() - cache_time
            ttl = self.cache_ttl_seconds.get("klines", 120)
            
            # Adjust TTL based on timeframe
            if timeframe in ["1m", "5m"]:
                ttl = 60  # 1 minute for short timeframes
            elif timeframe in ["15m", "1h"]:
                ttl = 120  # 2 minutes for medium timeframes
            else:
                ttl = 300  # 5 minutes for longer timeframes
            
            return age_seconds < ttl
            
        except Exception:
            return False
    
    async def _fetch_missing_data_batch(
        self, 
        pairs: List[str], 
        timeframes: List[str]
    ) -> Dict[str, Dict[str, pd.DataFrame]]:
        """Fetch missing data with proper rate limiting."""
        all_data = {}
        
        # Create tasks for all pair-timeframe combinations
        tasks = []
        for pair in pairs:
            for tf in timeframes:
                task = self._fetch_with_rate_limit(pair, tf)
                tasks.append((pair, tf, task))
        
        # Process tasks in batches
        for i in range(0, len(tasks), self.batch_size):
            batch = tasks[i:i + self.batch_size]
            
            logger.debug(f"Processing batch {i//self.batch_size + 1}: {len(batch)} requests")
            
            # Execute batch with timeout
            batch_tasks = [task for _, _, task in batch]
            results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for (pair, tf, _), result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.warning(f"Failed to fetch {pair} {tf}: {result}")
                    continue
                
                if result is not None and not result.empty:
                    if pair not in all_data:
                        all_data[pair] = {}
                    all_data[pair][tf] = result
                    
                    # Cache the result
                    await self._cache_data(pair, tf, result)
            
            # Small delay between batches
            if i + self.batch_size < len(tasks):
                await asyncio.sleep(0.5)
        
        return all_data
    
    async def _fetch_with_rate_limit(self, pair: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Fetch data for a single pair-timeframe with rate limiting."""
        async with self.request_semaphore:
            try:
                # Add delay to respect rate limits
                await asyncio.sleep(self.request_delay)
                
                # Convert timeframe to API interval
                interval = self._timeframe_to_interval(timeframe)
                
                # Fetch with timeout
                df = await asyncio.wait_for(
                    rest_client.get_klines(pair, interval, limit=200),
                    timeout=15.0
                )
                
                return df
                
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {pair} {timeframe}")
                return None
            except Exception as e:
                logger.debug(f"Error fetching {pair} {timeframe}: {e}")
                return None
    
    async def _cache_data(self, pair: str, timeframe: str, df: pd.DataFrame):
        """Cache DataFrame data."""
        try:
            # Convert DataFrame to cache-friendly format
            cache_data = {
                "data": df.reset_index().to_dict("records"),
                "timestamp": time.time()
            }
            
            await cache.set_kline(pair, timeframe, cache_data)
            
        except Exception as e:
            logger.debug(f"Failed to cache data for {pair} {timeframe}: {e}")
    
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
        return mapping.get(timeframe, "15")
    
    async def get_priority_data(self, pairs: List[str], max_pairs: int = 10) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Get data for priority pairs only (for staged analysis).
        
        Args:
            pairs: List of pairs (should be pre-filtered)
            max_pairs: Maximum number of pairs to process
            
        Returns:
            Data for top priority pairs with all timeframes
        """
        priority_pairs = pairs[:max_pairs]
        return await self.collect_multi_pair_data(
            priority_pairs, 
            include_secondary_timeframes=True
        )
    
    async def get_quick_scan_data(self, pairs: List[str]) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Get minimal data for quick scanning (primary timeframes only).
        
        Args:
            pairs: List of pairs to scan
            
        Returns:
            Data with primary timeframes only for faster processing
        """
        return await self.collect_multi_pair_data(
            pairs,
            include_secondary_timeframes=False
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get data collector statistics."""
        return {
            "rate_limiting": {
                "max_concurrent": self.max_concurrent_requests,
                "request_delay_ms": self.request_delay * 1000,
                "batch_size": self.batch_size
            },
            "cache_ttl": self.cache_ttl_seconds,
            "timeframes": {
                "primary": self.primary_timeframes,
                "secondary": self.secondary_timeframes
            }
        }


# Global instance
rate_limited_collector = RateLimitedDataCollector() 