#!/usr/bin/env python3
"""
Comprehensive Bookmap Signal Injection Script
Injects test signals for all major crypto symbols to ensure fusion analysis works
"""

import asyncio
import zmq
import json
from datetime import datetime, timezone
from typing import Dict, List, Any
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.bookmap_engine import BookmapSignalAggregator
from app.models.bookmap_signal import BookmapSignal

# Major crypto symbols to inject signals for
CRYPTO_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT", "MATICUSDT",
    "AVAXUSDT", "LTCUSDT", "UNIUSDT", "ATOMUSDT", "XLMUSDT", "XRPUSDT", "EOSUSDT",
    "THETAUSDT", "TRXUSDT", "FILUSDT", "NEARUSDT", "FTMUSDT", "AAVEUSDT", "ALGOUSDT",
    "ICPUSDT", "VETUSDT", "SANDUSDT", "MANAUSDT", "AXSUSDT", "CHZUSDT", "ENJUSDT",
    "GALAUSDT", "CRVUSDT", "COMPUSDT", "YFIUSDT", "SNXUSDT", "UMASDT", "SUSHIUSDT",
    "1INCHUSDT", "ROSEUSDT", "IOTAUSDT", "KSMUSDT", "WAVESUSDT", "APTUSDT", "SUIUSDT",
    "ARBUSDT", "OPUSDT", "JUPUSDT", "PYUSDT", "RENDERUSDT", "WLDUSDT", "TIAUSDT",
    "STRKUSDT", "INJUSDT", "PENDLEUSDT", "NOUSDT", "MNTUSDT", "SEIUSDT", "FETUSDT",
    "ETHFIUSDT", "ENAUSDT", "WIFUSDT", "ONDOUSDT", "PIXELUSDT", "STXUSDT", "ALTUSDT",
    "JUPUSDT", "PYTHUSDT", "MEMUSDT", "AIUSDT", "TNSRUSDT", "SAGAUSDT", "NOTUSDT",
    "TAOUSDT", "REZUSDT", "IOUSDT", "ZROUSDT", "GUSDT", "PEOPLEUSDT", "SATSUSDT",
    "RATSUSDT", "ACUSDT", "1000PEPEUSDT", "1000SHIBUSDT", "1000BONKUSDT", "DOGEUSDT",
    "WUSDT", "TOSHIUSDT", "APEXUSDT", "XTERUSDT", "ASRRUSDT", "BOBAUSDT", "CLOUDUSDT",
    "HUMAUSDT", "LAUSDT", "BNBUSDT", "BNXUSDT", "CAKEUSDT", "GMTUSDT", "GMXUSDT"
]

# Signal types to inject
SIGNAL_TYPES = ["WHALE_TRADE", "ICEBERG_DETECTION", "STOP_RUN", "SWEEP_DETECTED"]

class SignalInjector:
    def __init__(self):
        self.aggregator = BookmapSignalAggregator()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUSH)
        
    def create_test_signal(self, symbol: str, signal_type: str, side: str = "BUY") -> BookmapSignal:
        """Create a test Bookmap signal"""
        confidence_map = {
            "WHALE_TRADE": 0.85,
            "ICEBERG_DETECTION": 0.75,
            "STOP_RUN": 0.90,
            "SWEEP_DETECTED": 0.80
        }
        
        price_map = {
            "BTCUSDT": 97000.0,
            "ETHUSDT": 3800.0,
            "SOLUSDT": 245.0,
            "WUSDT": 0.32,
            "TOSHIUSDT": 0.00015,
            "APEXUSDT": 1.85,
            "XTERUSDT": 0.025,
            "ASRRUSDT": 2.5,
            "BOBAUSDT": 0.00085,
            "CLOUDUSDT": 0.35,
            "HUMAUSDT": 0.075,
            "LAUSDT": 0.0085,
            "DOGEUSDT": 0.38,
            "ADAUSDT": 1.05,
            "DOTUSDT": 8.5,
            "LINKUSDT": 24.0,
            "MATICUSDT": 0.62,
            "AVAXUSDT": 45.0,
            "LTCUSDT": 105.0,
            "BNBUSDT": 720.0
        }
        
        base_price = price_map.get(symbol, 1.0)
        
        signal = BookmapSignal(
            timestamp=datetime.now(timezone.utc),
            instrument=symbol,
            signal_type=signal_type,
            confidence=confidence_map.get(signal_type, 0.8),
            triggers=["level_break", "volume_spike"],
            side=side,
            price=base_price,
            details={
                "volume": 1000000.0,
                "order_flow_imbalance": 0.7,
                "depth_analysis": "strong_support",
                "market_microstructure": "active",
                "liquidity_state": "abundant"
            }
        )
        
        return signal
    
    def inject_signals_for_symbol(self, symbol: str):
        """Inject all signal types for a given symbol"""
        print(f"Injecting signals for {symbol}...")
        
        for signal_type in SIGNAL_TYPES:
            # Inject both BUY and SELL signals
            for side in ["BUY", "SELL"]:
                signal = self.create_test_signal(symbol, signal_type, side)
                
                # Add to aggregator
                self.aggregator.add_signal(signal)
        
        print(f"✅ Injected {len(SIGNAL_TYPES) * 2} signals for {symbol}")
    
    def inject_all_signals(self):
        """Inject signals for all crypto symbols"""
        print("🚀 Starting comprehensive signal injection...")
        print(f"📊 Injecting signals for {len(CRYPTO_SYMBOLS)} symbols")
        print(f"🔄 Each symbol gets {len(SIGNAL_TYPES)} types x 2 sides = {len(SIGNAL_TYPES) * 2} signals")
        print(f"📈 Total signals to inject: {len(CRYPTO_SYMBOLS) * len(SIGNAL_TYPES) * 2}")
        print()
        
        for i, symbol in enumerate(CRYPTO_SYMBOLS, 1):
            print(f"[{i}/{len(CRYPTO_SYMBOLS)}] Processing {symbol}...")
            self.inject_signals_for_symbol(symbol)
        
        print()
        print("✅ Signal injection completed!")
        print(f"📊 Total signals in aggregator: {len(self.aggregator.signals)}")
        
        # Display some stats
        signal_counts = {}
        for signal in self.aggregator.signals:
            signal_counts[signal.signal_type] = signal_counts.get(signal.signal_type, 0) + 1
        
        print("\n📈 Signal distribution:")
        for signal_type, count in signal_counts.items():
            print(f"  {signal_type}: {count} signals")
    
    def __del__(self):
        if hasattr(self, 'socket'):
            self.socket.close()
        if hasattr(self, 'context'):
            self.context.term()

def main():
    """Main function to run the signal injection"""
    try:
        injector = SignalInjector()
        injector.inject_all_signals()
        
        print("\n🎯 Testing fusion analysis with a sample signal...")
        
        # Test with BTCUSDT
        btc_signals = [s for s in injector.aggregator.signals if s.instrument == "BTCUSDT"]
        if btc_signals:
            print(f"Found {len(btc_signals)} BTC signals for testing")
            
            # Simulate a fusion request
            fusion_result = injector.aggregator.get_fusion_data("BTCUSDT", "LONG")
            print(f"Fusion result: {fusion_result}")
        
    except Exception as e:
        print(f"❌ Error during signal injection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 