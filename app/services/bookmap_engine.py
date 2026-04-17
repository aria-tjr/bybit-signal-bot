"""
Bookmap Scalping Signal Engine - Advanced Order Flow Analysis

Integrates with Bookmap's Python API (Layer-1) to capture real-time order flow signals
from Bybit crypto perpetuals, leveraging Global Plus features for institutional-grade
scalping signal generation.

Features:
- Real-time order book depth analysis (spoofing, liquidity shifts)
- Volume dots and CVD (Cumulative Volume Delta) tracking
- Stops & Icebergs detection via Bookmap add-ons
- Large trade (whale) tracking with sweep detection
- Market Pulse integration (liquidations, imbalances)
- ZeroMQ signal broadcasting to main bot engine

Architecture: Bookmap Python Add-on → ZeroMQ → Signal Fusion → Telegram
"""

import asyncio
import json
import time
import zmq
import zmq.asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict, deque

from ..core.logging import get_logger
from ..core.settings import settings

logger = get_logger(__name__)


class SignalType(Enum):
    """Bookmap signal types."""
    SPOOF_DETECTED = "SPOOF_DETECTED"
    WHALE_TRADE = "WHALE_TRADE"
    SWEEP_DETECTED = "SWEEP_DETECTED"
    STOP_RUN = "STOP_RUN"
    ICEBERG_DETECTION = "ICEBERG_DETECTION"
    ICEBERG_EXECUTION = "ICEBERG_EXECUTION"
    LIQUIDATION_CLUSTER = "LIQUIDATION_CLUSTER"
    ORDERBOOK_IMBALANCE = "ORDERBOOK_IMBALANCE"
    VOLUME_BURST = "VOLUME_BURST"
    CVD_DIVERGENCE = "CVD_DIVERGENCE"


@dataclass
class BookmapSignal:
    """Structured Bookmap signal data."""
    timestamp: float
    instrument: str
    signal_type: SignalType
    confidence: float
    triggers: List[str]
    side: str  # BUY/SELL
    price: float
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "instrument": self.instrument,
            "signal_type": self.signal_type.value,
            "confidence": self.confidence,
            "triggers": self.triggers,
            "side": self.side,
            "price": self.price,
            "details": self.details
        }


class OrderFlowMetrics:
    """Real-time order flow metrics tracker."""
    
    def __init__(self):
        self.cvd = 0.0
        self.trade_count_1s = 0
        self.last_trade_time = 0.0
        self.recent_large_trades = deque(maxlen=50)
        self.pending_spoofs = {}  # price -> timestamp
        self.liquidation_volume = {"buy": 0.0, "sell": 0.0}
        self.iceberg_tracker = {}
        
        # NEW: Advanced liquidity tracking
        self.liquidity_zones = {}  # price_level -> LiquidityZone
        self.absorption_levels = deque(maxlen=100)
        self.market_maker_signatures = defaultdict(dict)
        self.volume_clusters = deque(maxlen=200)
        self.support_resistance_levels = {"support": [], "resistance": []}
        
        # Multi-timeframe analysis
        self.timeframe_metrics = {
            "1s": {"cvd": 0.0, "large_trades": 0, "imbalance": 0.0},
            "5s": {"cvd": 0.0, "large_trades": 0, "imbalance": 0.0},
            "15s": {"cvd": 0.0, "large_trades": 0, "imbalance": 0.0},
            "60s": {"cvd": 0.0, "large_trades": 0, "imbalance": 0.0}
        }
        
        # Iceberg detection sophistication
        self.order_execution_history = deque(maxlen=1000)
        self.hidden_liquidity_tracker = {}
        
    def update_cvd(self, size: float, is_buy: bool):
        """Update Cumulative Volume Delta with multi-timeframe tracking."""
        delta = size if is_buy else -size
        self.cvd += delta
        
        # Update timeframe metrics
        current_time = time.time()
        for tf, duration in [("1s", 1), ("5s", 5), ("15s", 15), ("60s", 60)]:
            self.timeframe_metrics[tf]["cvd"] += delta
            
    def detect_iceberg_order(self, price: float, size: float, is_bid: bool, 
                           execution_id: str) -> Optional[Dict[str, Any]]:
        """Advanced iceberg detection using execution pattern analysis."""
        price_key = f"{price}_{is_bid}"
        current_time = time.time()
        
        if price_key not in self.iceberg_tracker:
            self.iceberg_tracker[price_key] = {
                "executions": [],
                "total_size": 0.0,
                "first_execution": current_time,
                "avg_execution_size": 0.0,
                "execution_intervals": []
            }
            
        tracker = self.iceberg_tracker[price_key]
        tracker["executions"].append({
            "time": current_time,
            "size": size,
            "execution_id": execution_id
        })
        tracker["total_size"] += size
        
        # Calculate execution intervals for pattern detection
        if len(tracker["executions"]) > 1:
            last_time = tracker["executions"][-2]["time"]
            interval = current_time - last_time
            tracker["execution_intervals"].append(interval)
            
        # Iceberg detection criteria
        if len(tracker["executions"]) >= 5:  # Minimum executions
            avg_size = tracker["total_size"] / len(tracker["executions"])
            tracker["avg_execution_size"] = avg_size
            
            # Check for consistent sizing pattern (iceberg signature)
            size_variance = self._calculate_execution_size_variance(tracker["executions"])
            time_variance = self._calculate_time_interval_variance(tracker["execution_intervals"])
            
            # Iceberg indicators:
            # 1. Consistent execution sizes (low variance)
            # 2. Regular time intervals (algorithmic)
            # 3. Substantial total volume
            # 4. Price level persistence
            
            if (size_variance < 0.3 and  # Low size variance
                time_variance < 2.0 and  # Regular intervals
                tracker["total_size"] > self.ICEBERG_MIN_VOL and
                len(tracker["executions"]) >= 7):
                
                confidence = min(9.5, 6.0 + (len(tracker["executions"]) - 5) * 0.3)
                
                return {
                    "price": price,
                    "side": "BID" if is_bid else "ASK",
                    "total_executed": tracker["total_size"],
                    "execution_count": len(tracker["executions"]),
                    "avg_execution_size": avg_size,
                    "time_span": current_time - tracker["first_execution"],
                    "size_variance": size_variance,
                    "time_variance": time_variance,
                    "confidence": confidence,
                    "pattern": "iceberg_algo"
                }
                
        return None
        
    def _calculate_execution_size_variance(self, executions: List[Dict]) -> float:
        """Calculate variance in execution sizes."""
        if len(executions) < 2:
            return 0.0
            
        sizes = [ex["size"] for ex in executions]
        mean_size = sum(sizes) / len(sizes)
        variance = sum((size - mean_size) ** 2 for size in sizes) / len(sizes)
        
        return variance / (mean_size ** 2) if mean_size > 0 else 0.0  # Normalized variance
        
    def _calculate_time_interval_variance(self, intervals: List[float]) -> float:
        """Calculate variance in execution time intervals."""
        if len(intervals) < 2:
            return 0.0
            
        mean_interval = sum(intervals) / len(intervals)
        variance = sum((interval - mean_interval) ** 2 for interval in intervals) / len(intervals)
        
        return variance / (mean_interval ** 2) if mean_interval > 0 else 0.0
        
    def detect_liquidity_absorption(self, price: float, size: float, 
                                  is_aggressive: bool) -> Optional[Dict[str, Any]]:
        """Detect large volume absorption at key levels."""
        if not is_aggressive or size < 50000:  # Only track significant aggressive volume
            return None
            
        current_time = time.time()
        absorption_data = {
            "timestamp": current_time,
            "price": price,
            "size": size,
            "cumulative_window": 0.0
        }
        
        # Add to absorption tracking
        self.absorption_levels.append(absorption_data)
        
        # Calculate absorption in 10-second window
        window_start = current_time - 10.0
        window_volume = sum(
            a["size"] for a in self.absorption_levels 
            if a["timestamp"] >= window_start and abs(a["price"] - price) <= price * 0.001  # 0.1% price tolerance
        )
        
        absorption_data["cumulative_window"] = window_volume
        
        # Significant absorption threshold
        if window_volume > 1_000_000:  # $1M absorption in 10s window
            return {
                "price": price,
                "window_volume": window_volume,
                "time_window": 10.0,
                "absorption_strength": min(10.0, window_volume / 500_000),  # Scale 1-10
                "pattern": "volume_absorption"
            }
            
        return None
        
    def track_market_maker_behavior(self, price: float, size: float, 
                                  is_bid: bool, is_add: bool) -> Optional[Dict[str, Any]]:
        """Track and analyze market maker behavior patterns."""
        level_key = f"{round(price, 2)}"
        side = "bid" if is_bid else "ask"
        
        if level_key not in self.market_maker_signatures:
            self.market_maker_signatures[level_key] = {
                "bid": {"adds": 0, "pulls": 0, "avg_size": 0.0, "last_activity": 0.0},
                "ask": {"adds": 0, "pulls": 0, "avg_size": 0.0, "last_activity": 0.0}
            }
            
        mm_data = self.market_maker_signatures[level_key][side]
        current_time = time.time()
        
        if is_add:
            mm_data["adds"] += 1
            mm_data["avg_size"] = (mm_data["avg_size"] * (mm_data["adds"] - 1) + size) / mm_data["adds"]
        else:
            mm_data["pulls"] += 1
            
        mm_data["last_activity"] = current_time
        
        # Detect market maker patterns
        total_activity = mm_data["adds"] + mm_data["pulls"]
        if total_activity > 10:  # Sufficient activity
            pull_ratio = mm_data["pulls"] / total_activity
            
            # High pull ratio indicates potential market maker games
            if pull_ratio > 0.7:  # 70% pulls vs adds
                return {
                    "price": price,
                    "side": side,
                    "pull_ratio": pull_ratio,
                    "total_activity": total_activity,
                    "avg_size": mm_data["avg_size"],
                    "pattern": "market_maker_games",
                    "confidence": min(8.0, 4.0 + pull_ratio * 4)
                }
                
        return None
        
    def identify_support_resistance(self, price: float, volume: float, 
                                  is_rejection: bool) -> Optional[Dict[str, Any]]:
        """Identify dynamic support and resistance levels based on volume and rejection."""
        if volume < 100000:  # Only significant volume
            return None
            
        level_tolerance = price * 0.002  # 0.2% tolerance for level grouping
        current_time = time.time()
        
        # Find existing nearby level
        level_type = "resistance" if is_rejection and price > 0 else "support"
        existing_levels = self.support_resistance_levels[level_type]
        
        nearby_level = None
        for level in existing_levels:
            if abs(level["price"] - price) <= level_tolerance:
                nearby_level = level
                break
                
        if nearby_level:
            # Update existing level
            nearby_level["volume"] += volume
            nearby_level["touch_count"] += 1
            nearby_level["last_touch"] = current_time
            nearby_level["strength"] = min(10.0, nearby_level["volume"] / 500_000)
            
            # Strong level detection
            if nearby_level["touch_count"] >= 3 and nearby_level["volume"] > 2_000_000:
                return {
                    "price": nearby_level["price"],
                    "type": level_type,
                    "strength": nearby_level["strength"],
                    "volume": nearby_level["volume"],
                    "touch_count": nearby_level["touch_count"],
                    "confidence": min(9.0, 5.0 + nearby_level["touch_count"] * 0.5),
                    "pattern": f"strong_{level_type}"
                }
        else:
            # Create new level
            new_level = {
                "price": price,
                "volume": volume,
                "touch_count": 1,
                "first_touch": current_time,
                "last_touch": current_time,
                "strength": volume / 500_000
            }
            existing_levels.append(new_level)
            
            # Clean old levels (older than 1 hour)
            hour_ago = current_time - 3600
            self.support_resistance_levels[level_type] = [
                level for level in existing_levels 
                if level["last_touch"] > hour_ago
            ]
            
        return None
        
    def track_large_trade(self, price: float, size: float, is_buy: bool, notional: float):
        """Enhanced large trade tracking with clustering analysis."""
        trade_data = {
            "timestamp": time.time(),
            "price": price,
            "size": size,
            "side": "BUY" if is_buy else "SELL",
            "notional": notional
        }
        self.recent_large_trades.append(trade_data)
        
        # Add to volume clusters for analysis
        self.volume_clusters.append({
            "timestamp": trade_data["timestamp"],
            "price": price,
            "volume": notional,
            "side": trade_data["side"]
        })
        
        # Update timeframe large trade counts
        for tf, duration in [("1s", 1), ("5s", 5), ("15s", 15), ("60s", 60)]:
            if time.time() - trade_data["timestamp"] <= duration:
                self.timeframe_metrics[tf]["large_trades"] += 1
        
    def detect_volume_clustering(self, time_window: int = 30) -> Optional[Dict[str, Any]]:
        """Detect unusual volume clustering patterns."""
        current_time = time.time()
        window_start = current_time - time_window
        
        window_trades = [
            trade for trade in self.volume_clusters 
            if trade["timestamp"] >= window_start
        ]
        
        if len(window_trades) < 5:
            return None
            
        total_volume = sum(trade["volume"] for trade in window_trades)
        buy_volume = sum(trade["volume"] for trade in window_trades if trade["side"] == "BUY")
        sell_volume = total_volume - buy_volume
        
        # Detect clustering
        if total_volume > 5_000_000:  # $5M in time window
            imbalance = abs(buy_volume - sell_volume) / total_volume
            dominant_side = "BUY" if buy_volume > sell_volume else "SELL"
            
            return {
                "time_window": time_window,
                "total_volume": total_volume,
                "trade_count": len(window_trades),
                "buy_volume": buy_volume,
                "sell_volume": sell_volume,
                "imbalance": imbalance,
                "dominant_side": dominant_side,
                "clustering_strength": min(10.0, total_volume / 2_000_000),
                "pattern": "volume_clustering"
            }


class BookmapPythonAddon:
    """
    Bookmap Python API Add-on implementation.
    
    This class would be the actual Bookmap add-on that runs inside Bookmap's
    Python environment. It subscribes to market data and indicator broadcasts,
    processes them for signals, and sends via ZeroMQ.
    """
    
    def __init__(self, zmq_port: int = 5555):
        self.zmq_port = zmq_port
        self.context = None
        self.socket = None
        self.order_flow = OrderFlowMetrics()
        self.instrument = None
        self.order_book = None
        
        # Depth tracking for advanced imbalance detection
        self.bid_depth_sum = 0.0
        self.ask_depth_sum = 0.0
        self.last_imbalance_time = 0.0
        
        # Thresholds (configurable)
        self.LARGE_TRADE_USD = 200_000
        self.STOPRUN_ALERT_VOL = 500_000
        self.ICEBERG_MIN_VOL = 100_000
        self.SWEEP_LEVELS = 3
        self.MAX_SPREAD_TICKS = 5
        
    def initialize_addon(self):
        """Initialize Bookmap add-on (pseudo-code for actual Bookmap integration)."""
        # This is the structure that would be used in the actual Bookmap Python add-on
        logger.info("Initializing Bookmap Python add-on")
        
        # ZeroMQ setup
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://127.0.0.1:{self.zmq_port}")
        
        # Note: Actual Bookmap API calls would be here
        # import bookmap as bm
        # self.addon = bm.create_addon()
        # bm.add_depth_handler(self.addon, self.on_depth)
        # bm.add_trades_handler(self.addon, self.on_trade)
        # etc.
        
    def on_depth(self, addon, alias: str, is_bid: bool, price_level: int, size_level: int):
        """Handle order book depth updates from Bookmap."""
        try:
            # Convert Bookmap data to real values
            price = price_level * addon.pips
            size = size_level / addon.size_multiplier
            
            # ──────────────────────────────────────────────────────────────────
            # MARKET MAKER BEHAVIOR TRACKING
            # ──────────────────────────────────────────────────────────────────
            is_add = size > 0
            mm_behavior = self.order_flow.track_market_maker_behavior(
                price, abs(size), is_bid, is_add
            )
            if mm_behavior:
                signal = BookmapSignal(
                    timestamp=time.time(),
                    instrument=alias,
                    signal_type=SignalType.SPOOF_DETECTED,
                    confidence=mm_behavior["confidence"],
                    triggers=["MarketMakerGames"],
                    side=mm_behavior["side"].upper(),
                    price=price,
                    details=mm_behavior
                )
                self.publish_signal(signal)
            
            # ──────────────────────────────────────────────────────────────────
            # SPOOF DETECTION (Enhanced)
            # ──────────────────────────────────────────────────────────────────
            is_removal = size == 0
            spoof_data = self._detect_enhanced_spoof(price, abs(size), is_removal, is_bid)
            if spoof_data:
                signal = BookmapSignal(
                    timestamp=time.time(),
                    instrument=alias,
                    signal_type=SignalType.SPOOF_DETECTED,
                    confidence=spoof_data["confidence"],
                    triggers=["EnhancedSpoofing"],
                    side="BID" if is_bid else "ASK",
                    price=price,
                    details=spoof_data
                )
                self.publish_signal(signal)
            
            # ──────────────────────────────────────────────────────────────────
            # SUPPORT/RESISTANCE LEVEL IDENTIFICATION
            # ──────────────────────────────────────────────────────────────────
            if is_removal and abs(size) > 100000:  # Large order removed (potential rejection)
                sr_analysis = self.order_flow.identify_support_resistance(
                    price, abs(size) * price, True  # Volume in USD, is_rejection=True
                )
                if sr_analysis:
                    signal_type = SignalType.STOP_RUN if sr_analysis["type"] == "support" else SignalType.SPOOF_DETECTED
                    signal = BookmapSignal(
                        timestamp=time.time(),
                        instrument=alias,
                        signal_type=signal_type,
                        confidence=sr_analysis["confidence"],
                        triggers=[f"Strong{sr_analysis['type'].title()}"],
                        side="BUY" if sr_analysis["type"] == "support" else "SELL",
                        price=price,
                        details=sr_analysis
                    )
                    self.publish_signal(signal)
            
            # ─── Track cumulative depth ───────────────────────────────────────
            depth_change = size  # Positive when add, zero when removal handled below
            if is_bid:
                # If removal (size==0) fetch previous? Simplified: ignore
                self.bid_depth_sum += depth_change if size > 0 else 0
            else:
                self.ask_depth_sum += depth_change if size > 0 else 0

            # Advanced imbalance detection
            total_depth = self.bid_depth_sum + self.ask_depth_sum
            if total_depth > 0:
                bid_ratio = self.bid_depth_sum / total_depth
                ask_ratio = self.ask_depth_sum / total_depth
                extreme_threshold = 0.8  # 80% depth on one side
                now = time.time()
                if (bid_ratio > extreme_threshold or ask_ratio > extreme_threshold) and (now - self.last_imbalance_time > 2):
                    dominant_side = "BUY" if bid_ratio > ask_ratio else "SELL"
                    confidence = 6.0 + abs(bid_ratio - ask_ratio) * 5  # 6-10 scale
                    signal = BookmapSignal(
                        timestamp=now,
                        instrument=alias,
                        signal_type=SignalType.ORDERBOOK_IMBALANCE,
                        confidence=min(confidence, 9.5),
                        triggers=["DepthImbalance"],
                        side=dominant_side,
                        price=price,
                        details={
                            "bid_ratio": round(bid_ratio, 2),
                            "ask_ratio": round(ask_ratio, 2),
                            "bid_depth": round(self.bid_depth_sum, 1),
                            "ask_depth": round(self.ask_depth_sum, 1)
                        }
                    )
                    self.publish_signal(signal)
                    self.last_imbalance_time = now
                
        except Exception as e:
            logger.error("Error in depth handler", error=str(e))
            
    def _detect_enhanced_spoof(self, price: float, size: float, is_removal: bool, is_bid: bool) -> Optional[Dict[str, Any]]:
        """Enhanced spoofing detection with pattern analysis."""
        spoof_key = f"{price}_{is_bid}"
        current_time = time.time()
        
        if is_removal and spoof_key in self.order_flow.pending_spoofs:
            spoof_data = self.order_flow.pending_spoofs[spoof_key]
            time_held = current_time - spoof_data["timestamp"]
            
            # Enhanced spoof detection criteria
            if time_held < 2.0:  # Quick cancellation
                confidence = 7.0
                pattern = "quick_cancel"
                
                # Additional confidence factors
                if time_held < 0.5:  # Very quick
                    confidence += 1.5
                    pattern = "flash_spoof"
                    
                if spoof_data["size"] > 1_000_000:  # Large order
                    confidence += 1.0
                    pattern += "_large_order"
                    
                # Check for repeated spoofing at same level
                recent_spoofs = [
                    s for s in self.order_flow.pending_spoofs.values()
                    if abs(s["price"] - price) <= price * 0.001 and 
                    current_time - s["timestamp"] < 60
                ]
                
                if len(recent_spoofs) > 2:
                    confidence += 0.5
                    pattern += "_repeated"
                
                del self.order_flow.pending_spoofs[spoof_key]
                
                return {
                    "price": price,
                    "size": size,
                    "time_held": time_held,
                    "pattern": pattern,
                    "confidence": min(confidence, 9.5),
                    "spoof_count_nearby": len(recent_spoofs)
                }
                
        elif not is_removal and size > 500_000:  # Large order added
            self.order_flow.pending_spoofs[spoof_key] = {
                "timestamp": current_time,
                "price": price,
                "size": size,
                "side": "bid" if is_bid else "ask"
            }
            
        return None
        
    def on_trade(self, addon, alias: str, price_level: float, size_level: int, 
                 is_otc: bool, is_bid: bool, is_execution_start: bool, 
                 is_execution_end: bool, aggressor_order_id: str, passive_order_id: str):
        """Handle trade events from Bookmap."""
        try:
            price = price_level
            size = size_level / addon.size_multiplier
            notional = price * size
            
            # Update CVD
            self.order_flow.update_cvd(size, is_bid)
            
            # ──────────────────────────────────────────────────────────────────
            # ADVANCED ICEBERG DETECTION
            # ──────────────────────────────────────────────────────────────────
            if size > 10000:  # Only track substantial executions
                iceberg_detection = self.order_flow.detect_iceberg_order(
                    price, size, is_bid, aggressor_order_id or passive_order_id
                )
                if iceberg_detection:
                    signal = BookmapSignal(
                        timestamp=time.time(),
                        instrument=alias,
                        signal_type=SignalType.ICEBERG_DETECTION,
                        confidence=iceberg_detection["confidence"],
                        triggers=["IcebergAlgo"],
                        side=iceberg_detection["side"],
                        price=price,
                        details=iceberg_detection
                    )
                    self.publish_signal(signal)
            
            # ──────────────────────────────────────────────────────────────────
            # VOLUME ABSORPTION ANALYSIS
            # ──────────────────────────────────────────────────────────────────
            absorption_analysis = self.order_flow.detect_liquidity_absorption(
                price, notional, True  # Treat all trades as aggressive for simplification
            )
            if absorption_analysis:
                signal = BookmapSignal(
                    timestamp=time.time(),
                    instrument=alias,
                    signal_type=SignalType.VOLUME_BURST,
                    confidence=min(9.0, 6.0 + absorption_analysis["absorption_strength"] * 0.3),
                    triggers=["VolumeAbsorption"],
                    side="BUY" if is_bid else "SELL",
                    price=price,
                    details=absorption_analysis
                )
                self.publish_signal(signal)
            
            # ──────────────────────────────────────────────────────────────────
            # VOLUME CLUSTERING DETECTION
            # ──────────────────────────────────────────────────────────────────
            clustering = self.order_flow.detect_volume_clustering()
            if clustering:
                signal = BookmapSignal(
                    timestamp=time.time(),
                    instrument=alias,
                    signal_type=SignalType.VOLUME_BURST,
                    confidence=min(9.0, 5.0 + clustering["clustering_strength"] * 0.4),
                    triggers=["VolumeClustering"],
                    side=clustering["dominant_side"],
                    price=price,
                    details=clustering
                )
                self.publish_signal(signal)
            
            # Large trade detection (enhanced)
            if notional >= self.LARGE_TRADE_USD:
                self.order_flow.track_large_trade(price, size, is_bid, notional)
                
                # Enhanced whale signal with multi-timeframe context
                timeframe_context = {
                    tf: self.order_flow.timeframe_metrics[tf]["large_trades"] 
                    for tf in ["1s", "5s", "15s", "60s"]
                }
                
                confidence = 8.0
                triggers = ["WhaleSpotted"]
                
                # Boost confidence based on timeframe clustering
                if timeframe_context["5s"] >= 3:  # 3+ large trades in 5s
                    confidence += 1.0
                    triggers.append("WhaleCluster")
                    
                if timeframe_context["15s"] >= 5:  # 5+ large trades in 15s
                    confidence += 0.5
                    triggers.append("SustainedWhaleActivity")
                
                signal = BookmapSignal(
                    timestamp=time.time(),
                    instrument=alias,
                    signal_type=SignalType.WHALE_TRADE,
                    confidence=min(confidence, 9.5),
                    triggers=triggers,
                    side="BUY" if is_bid else "SELL",
                    price=price,
                    details={
                        "notional": notional,
                        "size": size,
                        "timeframe_context": timeframe_context,
                        "order_ids": {
                            "aggressor": aggressor_order_id,
                            "passive": passive_order_id
                        }
                    }
                )
                self.publish_signal(signal)
                
        except Exception as e:
            logger.error("Error in trade handler", error=str(e))
            
    def on_broadcasting_event(self, addon, generator_name: str, event: dict):
        """Handle events from Bookmap add-ons (Stops & Icebergs, etc.)."""
        try:
            # Parse Stops & Icebergs events
            if "STOP" in str(event).upper():
                volume = event.get("volume", 0)
                side = "BUY" if "buy" in str(event).lower() else "SELL"
                
                if volume >= self.STOPRUN_ALERT_VOL:
                    signal = BookmapSignal(
                        timestamp=time.time(),
                        instrument=self.instrument,
                        signal_type=SignalType.STOP_RUN,
                        confidence=8.5,
                        triggers=["StopRun"],
                        side=side,
                        price=event.get("price", 0),
                        details={"volume": volume, "num_orders": event.get("numOrders", 1)}
                    )
                    self.publish_signal(signal)
                    
            # Parse Iceberg events
            elif "ICEBERG" in str(event).upper():
                event_type = event.get("type", "").upper()
                volume = event.get("volume", 0)
                side = event.get("side", "BUY")
                
                if volume >= self.ICEBERG_MIN_VOL:
                    signal_type = (SignalType.ICEBERG_EXECUTION if event_type == "EXECUTION" 
                                 else SignalType.ICEBERG_DETECTION)
                    
                    signal = BookmapSignal(
                        timestamp=time.time(),
                        instrument=self.instrument,
                        signal_type=signal_type,
                        confidence=7.5,
                        triggers=["Iceberg"],
                        side=side,
                        price=event.get("price", 0),
                        details={
                            "volume": volume,
                            "event_type": event_type,
                            "hidden_size": event.get("hiddenSize", 0)
                        }
                    )
                    self.publish_signal(signal)
                    
        except Exception as e:
            logger.error("Error in broadcasting handler", error=str(e))
            
    def publish_signal(self, signal: BookmapSignal):
        """Publish signal via ZeroMQ."""
        try:
            message = json.dumps(signal.to_dict())
            self.socket.send_string(message, flags=zmq.NOBLOCK)
            logger.debug("Published Bookmap signal", signal_type=signal.signal_type.value)
        except zmq.Again:
            logger.warning("ZMQ send buffer full, signal dropped")
        except Exception as e:
            logger.error("Failed to publish signal", error=str(e))


class BookmapSignalReceiver:
    """ZeroMQ signal receiver for the main bot."""
    
    def __init__(self, zmq_port: int = 5555):
        self.zmq_port = zmq_port
        self.context = None
        self.socket = None
        self.running = False
        self.signal_handlers: List[Callable[[BookmapSignal], None]] = []
        self.recent_signals = deque(maxlen=100)
        
    async def start(self):
        """Start the ZeroMQ signal receiver."""
        try:
            self.context = zmq.asyncio.Context()
            self.socket = self.context.socket(zmq.SUB)
            self.socket.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all messages
            self.socket.connect(f"tcp://127.0.0.1:{self.zmq_port}")
            
            self.running = True
            logger.info("Bookmap signal receiver started", port=self.zmq_port)
            
            # Start receiving loop
            asyncio.create_task(self._receive_loop())
            
        except Exception as e:
            logger.error("Failed to start signal receiver", error=str(e))
            
    async def stop(self):
        """Stop the signal receiver."""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        logger.info("Bookmap signal receiver stopped")
        
    def add_signal_handler(self, handler: Callable[[BookmapSignal], None]):
        """Add a signal handler function."""
        self.signal_handlers.append(handler)
        
    async def _receive_loop(self):
        """Main signal receiving loop."""
        while self.running:
            try:
                # Non-blocking receive with timeout
                message = await self.socket.recv_string(flags=zmq.NOBLOCK)
                signal_data = json.loads(message)
                
                # Convert to BookmapSignal object
                signal = BookmapSignal(
                    timestamp=signal_data["timestamp"],
                    instrument=signal_data["instrument"],
                    signal_type=SignalType(signal_data["signal_type"]),
                    confidence=signal_data["confidence"],
                    triggers=signal_data["triggers"],
                    side=signal_data["side"],
                    price=signal_data["price"],
                    details=signal_data["details"]
                )
                
                # Store recent signal
                self.recent_signals.append(signal)
                
                # Call all handlers
                for handler in self.signal_handlers:
                    try:
                        handler(signal)
                    except Exception as e:
                        logger.error("Signal handler failed", error=str(e))
                        
            except zmq.Again:
                # No message available, continue
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error("Error in signal receive loop", error=str(e))
                await asyncio.sleep(0.1)
                
    def get_recent_signals(self, symbol: str = None, minutes: int = 5) -> List[BookmapSignal]:
        """Get recent signals for analysis."""
        cutoff_time = time.time() - (minutes * 60)
        
        signals = [
            signal for signal in self.recent_signals
            if signal.timestamp >= cutoff_time
        ]
        
        if symbol:
            signals = [s for s in signals if s.instrument == symbol]
            
        return signals


class BookmapSignalEngine:
    """Main Bookmap signal engine orchestrator."""
    
    def __init__(self):
        self.signal_receiver = BookmapSignalReceiver()
        self.signal_aggregator = BookmapSignalAggregator()
        self.running = False
        
    async def start(self):
        """Start the Bookmap signal engine."""
        try:
            # Start signal receiver
            await self.signal_receiver.start()
            
            # Add signal handler
            self.signal_receiver.add_signal_handler(self.signal_aggregator.process_signal)
            
            self.running = True
            logger.info("Bookmap signal engine started")
            
        except Exception as e:
            logger.error("Failed to start Bookmap signal engine", error=str(e))
            
    async def stop(self):
        """Stop the signal engine."""
        self.running = False
        await self.signal_receiver.stop()
        logger.info("Bookmap signal engine stopped")
        
    def get_signal_summary(self, symbol: str, minutes: int = 5) -> Dict[str, Any]:
        """Get aggregated signal summary for a symbol."""
        return self.signal_aggregator.get_signal_summary(symbol, minutes)
        
    def get_order_flow_score(self, symbol: str) -> float:
        """Get overall order flow score for signal fusion."""
        return self.signal_aggregator.calculate_order_flow_score(symbol)
    
    def get_recent_signals(self, symbol: str = None, minutes: int = 5) -> List[BookmapSignal]:
        """Get recent signals for analysis - delegates to signal receiver."""
        return self.signal_receiver.get_recent_signals(symbol, minutes)


class BookmapSignalAggregator:
    """Aggregates and analyzes Bookmap signals for decision making."""
    
    def __init__(self):
        self.signal_history = defaultdict(list)
        self.signal_scores = defaultdict(float)
        
    def process_signal(self, signal: BookmapSignal):
        """Process incoming Bookmap signal."""
        try:
            # Store signal
            self.signal_history[signal.instrument].append(signal)
            
            # Update signal scores
            self._update_signal_scores(signal)
            
            logger.debug(
                "Processed Bookmap signal",
                instrument=signal.instrument,
                signal_type=signal.signal_type.value,
                confidence=signal.confidence
            )
            
        except Exception as e:
            logger.error("Failed to process Bookmap signal", error=str(e))
            
    def _update_signal_scores(self, signal: BookmapSignal):
        """Update aggregated signal scores."""
        symbol = signal.instrument
        weight = signal.confidence / 10.0  # Normalize confidence to 0-1
        
        # Apply signal type weights
        type_weights = {
            SignalType.WHALE_TRADE: 2.0,
            SignalType.STOP_RUN: 1.8,
            SignalType.SWEEP_DETECTED: 1.5,
            SignalType.ICEBERG_EXECUTION: 1.3,
            SignalType.LIQUIDATION_CLUSTER: 1.6,
            SignalType.SPOOF_DETECTED: 1.0,
            SignalType.ORDERBOOK_IMBALANCE: 0.8,
            SignalType.VOLUME_BURST: 1.2,
            SignalType.CVD_DIVERGENCE: 1.4
        }
        
        base_score = weight * type_weights.get(signal.signal_type, 1.0)
        
        # Apply directional scoring
        if signal.side == "BUY":
            self.signal_scores[symbol] += base_score
        else:
            self.signal_scores[symbol] -= base_score
            
        # Only apply decay if score is getting too extreme (prevent runaway scores)
        # Removed aggressive 5% decay that was clearing our test signals
        if abs(self.signal_scores[symbol]) > 20:
            self.signal_scores[symbol] *= 0.9
        
    def get_signal_summary(self, symbol: str, minutes: int = 5) -> Dict[str, Any]:
        """Get signal summary for the past N minutes."""
        cutoff_time = time.time() - (minutes * 60)
        
        recent_signals = [
            s for s in self.signal_history[symbol]
            if s.timestamp >= cutoff_time
        ]
        
        # Categorize signals
        summary = {
            "total_signals": len(recent_signals),
            "bullish_signals": len([s for s in recent_signals if s.side == "BUY"]),
            "bearish_signals": len([s for s in recent_signals if s.side == "SELL"]),
            "signal_types": {},
            "avg_confidence": 0.0,
            "dominant_side": "NEUTRAL",
            "order_flow_score": self.signal_scores.get(symbol, 0.0)
        }
        
        if recent_signals:
            # Count signal types
            for signal in recent_signals:
                signal_type = signal.signal_type.value
                summary["signal_types"][signal_type] = summary["signal_types"].get(signal_type, 0) + 1
                
            # Calculate average confidence
            summary["avg_confidence"] = sum(s.confidence for s in recent_signals) / len(recent_signals)
            
            # Determine dominant side
            if summary["bullish_signals"] > summary["bearish_signals"]:
                summary["dominant_side"] = "BULLISH"
            elif summary["bearish_signals"] > summary["bullish_signals"]:
                summary["dominant_side"] = "BEARISH"
                
        return summary
        
    def calculate_order_flow_score(self, symbol: str) -> float:
        """Calculate overall order flow score for signal fusion."""
        base_score = self.signal_scores.get(symbol, 0.0)
        
        # Normalize to -10 to +10 range
        normalized_score = max(-10, min(10, base_score))
        
        return normalized_score


# Global instances
bookmap_engine = BookmapSignalEngine() 