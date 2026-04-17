"""
Bookmap Python Add-on for Bybit Crypto Scalping Signals

This add-on runs inside Bookmap and analyzes real-time order flow for crypto perpetuals.
It detects patterns like whale trades, stop runs, icebergs, and spoofing, then sends
signals via ZeroMQ to the main crypto signal bot.

Installation:
1. Copy this file to Bookmap's Python add-ons directory
2. Enable in Bookmap Add-on Manager
3. Configure for Bybit BTCUSDT Perpetual
4. Ensure required Global Plus add-ons are active

Requirements:
- Bookmap Global Plus license
- Python 3.7+
- pyzmq library
- Stops & Icebergs On-Chart add-on
- Market Pulse add-ons
- Large Trades Alert add-on
"""

# Bookmap Python API imports
try:
    import bookmap as bm
    BOOKMAP_AVAILABLE = True
except ImportError:
    print("Bookmap API not available - running in simulation mode")
    BOOKMAP_AVAILABLE = False

import json
import time
import zmq
from typing import Dict, Any, Optional
from collections import defaultdict, deque


class OrderFlowAnalyzer:
    """Real-time order flow analysis engine."""
    
    def __init__(self):
        self.cvd = 0.0  # Cumulative Volume Delta
        self.trade_count_1s = 0
        self.last_trade_time = 0.0
        self.recent_large_trades = deque(maxlen=50)
        self.pending_spoofs = {}  # price -> timestamp for spoof detection
        self.liquidation_volume = {"buy": 0.0, "sell": 0.0}
        self.last_orderbook_imbalance = 0.0
        
        # Configurable thresholds
        self.LARGE_TRADE_USD = 200_000
        self.STOPRUN_ALERT_VOL = 500_000
        self.ICEBERG_MIN_VOL = 100_000
        self.SWEEP_LEVELS = 3
        self.SPOOF_TIME_THRESHOLD = 1.0  # seconds
        
    def update_cvd(self, size: float, is_buy: bool):
        """Update Cumulative Volume Delta."""
        self.cvd += size if is_buy else -size
        
    def track_large_trade(self, price: float, size: float, is_buy: bool, notional: float):
        """Track large trades for whale detection."""
        trade_data = {
            "timestamp": time.time(),
            "price": price,
            "size": size,
            "side": "BUY" if is_buy else "SELL",
            "notional": notional
        }
        self.recent_large_trades.append(trade_data)
        
    def detect_spoof(self, price: float, size: float, is_removal: bool, notional: float) -> Optional[Dict[str, Any]]:
        """Detect potential spoofing patterns."""
        if is_removal and price in self.pending_spoofs:
            time_held = time.time() - self.pending_spoofs[price]
            if time_held < self.SPOOF_TIME_THRESHOLD:
                del self.pending_spoofs[price]
                return {
                    "price": price,
                    "size": size,
                    "notional": notional,
                    "time_held": time_held,
                    "pattern": "quick_cancel"
                }
        elif not is_removal and notional > 500_000:  # Large order added
            self.pending_spoofs[price] = time.time()
            
        return None
        
    def calculate_orderbook_imbalance(self, order_book, levels: int = 5) -> float:
        """Calculate order book imbalance for top N levels."""
        try:
            if not BOOKMAP_AVAILABLE:
                return 0.0
                
            bid_volume = bm.get_sum(order_book, levels, True)  # True for bids
            ask_volume = bm.get_sum(order_book, levels, False)  # False for asks
            
            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return 0.0
                
            imbalance = (bid_volume - ask_volume) / total_volume
            return imbalance * 100  # Convert to percentage
            
        except Exception:
            return 0.0


class BookmapBybitAddon:
    """Main Bookmap Python add-on for Bybit crypto signals."""
    
    def __init__(self):
        self.addon = None
        self.instrument = None
        self.order_book = None
        self.analyzer = OrderFlowAnalyzer()
        
        # ZeroMQ setup for signal publishing
        self.zmq_context = zmq.Context()
        self.zmq_socket = self.zmq_context.socket(zmq.PUB)
        self.zmq_socket.bind("tcp://127.0.0.1:5555")
        
        # State tracking
        self.last_price = 0.0
        self.price_multiplier = 1.0
        self.size_multiplier = 1.0
        
        print("Bookmap Bybit Add-on initialized")
        
    def initialize_addon(self):
        """Initialize the Bookmap add-on."""
        if not BOOKMAP_AVAILABLE:
            print("Bookmap not available - running in simulation mode")
            return
            
        try:
            # Create the add-on
            self.addon = bm.create_addon()
            
            # Add event handlers
            bm.add_depth_handler(self.addon, self.on_depth)
            bm.add_trades_handler(self.addon, self.on_trade)
            bm.add_on_interval_handler(self.addon, self.on_interval)
            
            # Add broadcasting handlers for Global Plus add-ons
            bm.add_broadcasting_status_handler(self.addon, self.on_broadcasting_status)
            bm.add_broadcasting_handler(self.addon, self.on_broadcasting_event)
            
            # Start the add-on
            bm.start_addon(
                self.addon,
                self.handle_subscribe_instrument,
                self.handle_unsubscribe_instrument
            )
            
            print("Bookmap add-on started successfully")
            
        except Exception as e:
            print(f"Failed to initialize Bookmap add-on: {e}")
            
    def handle_subscribe_instrument(self, addon, alias: str, full_name: str, is_crypto: bool,
                                   pips: float, size_multiplier: float, inst_multiplier: float,
                                   supported_features: Dict[str, object]) -> None:
        """Handle instrument subscription."""
        self.instrument = alias
        self.price_multiplier = pips
        self.size_multiplier = size_multiplier
        
        print(f"Subscribed to {alias} ({full_name})")
        print(f"Crypto: {is_crypto}, Pips: {pips}, Size multiplier: {size_multiplier}")
        
        # Subscribe to market data
        if BOOKMAP_AVAILABLE:
            bm.subscribe_to_depth(addon, alias, req_id=1)
            bm.subscribe_to_trades(addon, alias, req_id=2)
            
            # Create order book for analysis
            self.order_book = bm.create_order_book()
            
        print(f"Market data subscriptions active for {alias}")
        
    def handle_unsubscribe_instrument(self, addon, alias: str) -> None:
        """Handle instrument unsubscription."""
        print(f"Unsubscribed from {alias}")
        self.instrument = None
        
    def on_depth(self, addon, alias: str, is_bid: bool, price_level: int, size_level: int) -> None:
        """Handle order book depth updates."""
        try:
            if not BOOKMAP_AVAILABLE:
                return
                
            # Update internal order book
            bm.on_depth(self.order_book, is_bid, price_level, size_level)
            
            # Convert to real values
            price = price_level * self.price_multiplier
            size = size_level / self.size_multiplier
            notional = price * size
            
            # Spoof detection
            is_removal = size_level == 0
            spoof_data = self.analyzer.detect_spoof(price, size, is_removal, notional)
            
            if spoof_data:
                signal = {
                    "timestamp": time.time(),
                    "instrument": alias,
                    "signal_type": "SPOOF_DETECTED",
                    "confidence": 7.5,
                    "triggers": ["QuickCancel"],
                    "side": "BID" if is_bid else "ASK",
                    "price": price,
                    "details": spoof_data
                }
                self.publish_signal(signal)
                
        except Exception as e:
            print(f"Error in depth handler: {e}")
            
    def on_trade(self, addon, alias: str, price_level: float, size_level: int,
                 is_otc: bool, is_bid: bool, is_execution_start: bool,
                 is_execution_end: bool, aggressor_order_id: str, passive_order_id: str) -> None:
        """Handle trade events."""
        try:
            price = price_level
            size = size_level / self.size_multiplier
            notional = price * size
            
            self.last_price = price
            
            # Update CVD
            self.analyzer.update_cvd(size, is_bid)
            
            # Large trade detection
            if notional >= self.analyzer.LARGE_TRADE_USD:
                self.analyzer.track_large_trade(price, size, is_bid, notional)
                
                signal = {
                    "timestamp": time.time(),
                    "instrument": alias,
                    "signal_type": "WHALE_TRADE",
                    "confidence": 8.0,
                    "triggers": ["LargeTrade"],
                    "side": "BUY" if is_bid else "SELL",
                    "price": price,
                    "details": {
                        "size": size,
                        "notional": notional,
                        "aggressor_id": aggressor_order_id,
                        "is_execution_start": is_execution_start,
                        "is_execution_end": is_execution_end
                    }
                }
                self.publish_signal(signal)
                
            # Sweep detection (simplified)
            if notional > 100_000:  # Basic sweep threshold
                signal = {
                    "timestamp": time.time(),
                    "instrument": alias,
                    "signal_type": "SWEEP_DETECTED",
                    "confidence": 7.0,
                    "triggers": ["LargeTrade"],
                    "side": "BUY" if is_bid else "SELL",
                    "price": price,
                    "details": {
                        "size": size,
                        "notional": notional
                    }
                }
                self.publish_signal(signal)
                
        except Exception as e:
            print(f"Error in trade handler: {e}")
            
    def on_interval(self, addon, alias: str) -> None:
        """Periodic processing (called every 100ms)."""
        try:
            if not self.order_book or not BOOKMAP_AVAILABLE:
                return
                
            # Calculate order book imbalance
            imbalance = self.analyzer.calculate_orderbook_imbalance(self.order_book, 5)
            
            # Check for significant imbalance changes
            if abs(imbalance - self.analyzer.last_orderbook_imbalance) > 20:  # 20% threshold
                signal = {
                    "timestamp": time.time(),
                    "instrument": alias,
                    "signal_type": "ORDERBOOK_IMBALANCE",
                    "confidence": 6.0,
                    "triggers": ["ImbalanceShift"],
                    "side": "BUY" if imbalance > 0 else "SELL",
                    "price": self.last_price,
                    "details": {
                        "current_imbalance": imbalance,
                        "previous_imbalance": self.analyzer.last_orderbook_imbalance,
                        "change": imbalance - self.analyzer.last_orderbook_imbalance
                    }
                }
                self.publish_signal(signal)
                
            self.analyzer.last_orderbook_imbalance = imbalance
            
        except Exception as e:
            print(f"Error in interval handler: {e}")
            
    def on_broadcasting_status(self, addon, status: dict) -> None:
        """Handle broadcasting status updates from Global Plus add-ons."""
        try:
            if not BOOKMAP_AVAILABLE:
                return
                
            print(f"Broadcasting providers available: {list(status.keys())}")
            
            # Auto-subscribe to relevant providers
            for provider, generators in status.items():
                provider_name = str(provider).lower()
                
                # Subscribe to Stops & Icebergs
                if "stop" in provider_name or "iceberg" in provider_name:
                    bm.subscribe_to_provider(addon, provider)
                    for gen in generators:
                        gen_name = gen.get("generator_name") if isinstance(gen, dict) else str(gen)
                        bm.subscribe_to_generator(addon, provider, gen_name, False)
                    print(f"Subscribed to {provider}")
                    
                # Subscribe to Market Pulse components
                elif "pulse" in provider_name or "liquidation" in provider_name:
                    bm.subscribe_to_provider(addon, provider)
                    for gen in generators:
                        gen_name = gen.get("generator_name") if isinstance(gen, dict) else str(gen)
                        bm.subscribe_to_generator(addon, provider, gen_name, False)
                    print(f"Subscribed to {provider}")
                    
        except Exception as e:
            print(f"Error in broadcasting status handler: {e}")
            
    def on_broadcasting_event(self, addon, generator_name: str, event: dict) -> None:
        """Handle events from Global Plus add-ons."""
        try:
            event_str = str(event).upper()
            
            # Handle Stops & Icebergs events
            if "STOP" in event_str:
                volume = event.get("volume", 0)
                side = "BUY" if "BUY" in event_str else "SELL"
                
                if volume >= self.analyzer.STOPRUN_ALERT_VOL:
                    signal = {
                        "timestamp": time.time(),
                        "instrument": self.instrument,
                        "signal_type": "STOP_RUN",
                        "confidence": 8.5,
                        "triggers": ["StopRun"],
                        "side": side,
                        "price": event.get("price", self.last_price),
                        "details": {
                            "volume": volume,
                            "num_orders": event.get("numOrders", 1),
                            "generator": generator_name
                        }
                    }
                    self.publish_signal(signal)
                    
            elif "ICEBERG" in event_str:
                event_type = event.get("type", "").upper()
                volume = event.get("volume", 0)
                side = event.get("side", "BUY").upper()
                
                if volume >= self.analyzer.ICEBERG_MIN_VOL:
                    signal_type = "ICEBERG_EXECUTION" if event_type == "EXECUTION" else "ICEBERG_DETECTION"
                    
                    signal = {
                        "timestamp": time.time(),
                        "instrument": self.instrument,
                        "signal_type": signal_type,
                        "confidence": 7.5,
                        "triggers": ["Iceberg"],
                        "side": side,
                        "price": event.get("price", self.last_price),
                        "details": {
                            "volume": volume,
                            "event_type": event_type,
                            "hidden_size": event.get("hiddenSize", 0),
                            "generator": generator_name
                        }
                    }
                    self.publish_signal(signal)
                    
            # Handle liquidation events
            elif "LIQUIDATION" in event_str:
                volume = event.get("volume", 0)
                side = event.get("side", "SELL").upper()  # Most liquidations are sell
                
                signal = {
                    "timestamp": time.time(),
                    "instrument": self.instrument,
                    "signal_type": "LIQUIDATION_CLUSTER",
                    "confidence": 7.0,
                    "triggers": ["Liquidation"],
                    "side": side,
                    "price": event.get("price", self.last_price),
                    "details": {
                        "volume": volume,
                        "liquidation_type": event.get("type", "unknown"),
                        "generator": generator_name
                    }
                }
                self.publish_signal(signal)
                
        except Exception as e:
            print(f"Error in broadcasting event handler: {e}")
            
    def publish_signal(self, signal: Dict[str, Any]) -> None:
        """Publish signal via ZeroMQ."""
        try:
            message = json.dumps(signal)
            self.zmq_socket.send_string(message, flags=zmq.NOBLOCK)
            print(f"Published signal: {signal['signal_type']} for {signal['instrument']}")
        except zmq.Again:
            print("ZMQ send buffer full, signal dropped")
        except Exception as e:
            print(f"Failed to publish signal: {e}")
            
    def cleanup(self):
        """Clean up resources."""
        if self.zmq_socket:
            self.zmq_socket.close()
        if self.zmq_context:
            self.zmq_context.term()
        print("Add-on cleanup completed")


# Main entry point for Bookmap
def main():
    """Main function - entry point for Bookmap Python add-on."""
    addon_instance = BookmapBybitAddon()
    
    try:
        addon_instance.initialize_addon()
        
        if BOOKMAP_AVAILABLE:
            # This will block until the add-on is stopped
            bm.wait_until_addon_is_turned_off(addon_instance.addon)
        else:
            print("Running in simulation mode - Bookmap API not available")
            print("This would normally run inside Bookmap environment")
            
    except KeyboardInterrupt:
        print("Add-on interrupted by user")
    except Exception as e:
        print(f"Add-on error: {e}")
    finally:
        addon_instance.cleanup()


if __name__ == "__main__":
    main() 