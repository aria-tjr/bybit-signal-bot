#!/usr/bin/env python3
"""
Docker-compatible signal injection script for Bookmap engine.
Directly injects signals into the running bot's Bookmap engine.
"""

import sys
import time
import random
import asyncio
sys.path.insert(0, "/app")

from app.services.bookmap_engine import bookmap_engine, BookmapSignal, SignalType

async def inject_test_signals():
    """Inject test signals directly into the running Bookmap engine."""
    
    print("🚀 Injecting signals directly into Docker bot...")
    
    # Get the aggregator from the global engine
    aggregator = bookmap_engine.signal_aggregator
    
    # ETHUSDT test signals with strong order flow
    symbol = "ETHUSDT"
    print(f"📊 Injecting signals for {symbol}...")
    
    # High-impact signal types
    signal_types = [
        SignalType.WHALE_TRADE,
        SignalType.ICEBERG_EXECUTION, 
        SignalType.STOP_RUN,
        SignalType.SWEEP_DETECTED
    ]
    
    total_signals = 0
    
    # ETHUSDT is in neutral category, so inject balanced signals
    # But add slight bearish bias to match the -0.7 order flow we saw
    for signal_type in signal_types:
        # 3 SELL signals (bearish bias)
        for _ in range(3):
            signal = BookmapSignal(
                timestamp=time.time(),
                instrument=symbol,
                signal_type=signal_type,
                confidence=random.uniform(7.5, 9.0),  # High confidence
                triggers=["whale_dump", "order_flow_pressure"],
                side="SELL",
                price=2690.0,  # Realistic ETHUSDT price
                details={
                    "volume": random.uniform(800000, 1500000),
                    "order_flow_imbalance": random.uniform(-0.8, -0.6),
                    "depth_analysis": "bearish_pressure"
                }
            )
            aggregator.process_signal(signal)
            total_signals += 1
            print(f"  ✅ Added {signal_type.value} SELL signal")
            
        # 2 BUY signals  
        for _ in range(2):
            signal = BookmapSignal(
                timestamp=time.time(),
                instrument=symbol,
                signal_type=signal_type,
                confidence=random.uniform(6.0, 7.5),  # Medium confidence
                triggers=["support_level", "minor_bounce"],
                side="BUY",
                price=2685.0,  # Realistic ETHUSDT price
                details={
                    "volume": random.uniform(400000, 800000),
                    "order_flow_imbalance": random.uniform(0.3, 0.5),
                    "depth_analysis": "minor_support"
                }
            )
            aggregator.process_signal(signal)
            total_signals += 1
            print(f"  ✅ Added {signal_type.value} BUY signal")
    
    print(f"\n✅ INJECTION COMPLETE!")
    print(f"📊 Total signals injected: {total_signals}")
    print(f"📈 Total symbols in history: {len(aggregator.signal_history)}")
    
    # Test the results immediately
    summary = aggregator.get_signal_summary(symbol, 5)
    order_flow = aggregator.calculate_order_flow_score(symbol)
    
    print(f"\n🎯 VERIFICATION:")
    print(f"Symbol: {symbol}")
    print(f"Total signals: {summary['total_signals']}")
    print(f"Bullish signals: {summary['bullish_signals']}")
    print(f"Bearish signals: {summary['bearish_signals']}")
    print(f"Order flow score: {order_flow:.3f}")
    print(f"Dominant side: {summary['dominant_side']}")
    print(f"Avg confidence: {summary['avg_confidence']:.2f}")
    
    if summary['total_signals'] >= 2:
        print("🟢 SUCCESS: Should now show proper fusion results!")
    else:
        print("🔴 FAILED: Still insufficient signals")

if __name__ == "__main__":
    asyncio.run(inject_test_signals()) 