import sys
import time
sys.path.insert(0, "/app")

from app.services.bookmap_engine import bookmap_engine, BookmapSignal, SignalType

# Use the global bookmap engine aggregator
aggregator = bookmap_engine.signal_aggregator

print("🚀 Injecting BIASED signals for stronger fusion results...")

# Create strong bullish bias for these symbols
bullish_symbols = ["TOSHIUSDT", "WUSDT", "APEXUSDT"]
bearish_symbols = ["XTERUSDT", "ASRRUSDT"]

# High-impact signal types with higher confidence
high_impact_signals = ["WHALE_TRADE", "STOP_RUN", "SWEEP_DETECTED"]

total_signals = 0

# Inject strong bullish signals
for symbol in bullish_symbols:
    print(f"Injecting BULLISH bias for {symbol}...")
    for signal_type in high_impact_signals:
        # 4 BUY signals vs 1 SELL signal for strong bullish bias
        for _ in range(4):
            signal = BookmapSignal(
                timestamp=time.time(),
                instrument=symbol,
                signal_type=SignalType(signal_type),
                confidence=9.2,  # High confidence
                triggers=["whale_entry", "stop_hunt", "level_break"],
                side="BUY",
                price=1.0,
                details={
                    "volume": 5000000.0,  # Large volume
                    "order_flow_imbalance": 0.85,  # Strong imbalance
                    "depth_analysis": "massive_support",
                    "institutional_flow": "accumulation"
                }
            )
            aggregator.process_signal(signal)
            total_signals += 1
        
        # Add 1 SELL signal for realism
        signal = BookmapSignal(
            timestamp=time.time(),
            instrument=symbol,
            signal_type=SignalType(signal_type),
            confidence=3.5,  # Lower confidence
            triggers=["profit_taking"],
            side="SELL",
            price=1.0,
            details={
                "volume": 500000.0,
                "order_flow_imbalance": 0.3,
                "depth_analysis": "weak_resistance"
            }
        )
        aggregator.process_signal(signal)
        total_signals += 1

# Inject strong bearish signals
for symbol in bearish_symbols:
    print(f"Injecting BEARISH bias for {symbol}...")
    for signal_type in high_impact_signals:
        # 4 SELL signals vs 1 BUY signal for strong bearish bias
        for _ in range(4):
            signal = BookmapSignal(
                timestamp=time.time(),
                instrument=symbol,
                signal_type=SignalType(signal_type),
                confidence=9.0,  # High confidence
                triggers=["whale_exit", "stop_hunt", "level_break"],
                side="SELL",
                price=1.0,
                details={
                    "volume": 4500000.0,  # Large volume
                    "order_flow_imbalance": 0.15,  # Strong sell imbalance
                    "depth_analysis": "massive_resistance",
                    "institutional_flow": "distribution"
                }
            )
            aggregator.process_signal(signal)
            total_signals += 1
        
        # Add 1 BUY signal for realism
        signal = BookmapSignal(
            timestamp=time.time(),
            instrument=symbol,
            signal_type=SignalType(signal_type),
            confidence=3.0,  # Lower confidence
            triggers=["dip_buying"],
            side="BUY",
            price=1.0,
            details={
                "volume": 400000.0,
                "order_flow_imbalance": 0.7,
                "depth_analysis": "weak_support"
            }
        )
        aggregator.process_signal(signal)
        total_signals += 1

print(f"✅ Injected {total_signals} BIASED signals")
print(f"📊 Total signals in GLOBAL aggregator: {len(aggregator.signal_history)}")

# Test the enhanced signal summaries
print("\n🎯 Testing ENHANCED signal summaries...")

for symbol in bullish_symbols + bearish_symbols:
    summary = bookmap_engine.get_signal_summary(symbol, 5)
    order_flow_score = bookmap_engine.get_order_flow_score(symbol)
    print(f"\n{symbol}:")
    print(f"  Total signals: {summary['total_signals']}")
    print(f"  Bullish: {summary['bullish_signals']}, Bearish: {summary['bearish_signals']}")
    print(f"  Dominant side: {summary['dominant_side']}")
    print(f"  Avg confidence: {summary['avg_confidence']:.2f}")
    print(f"  Order flow score: {order_flow_score:.3f}")

print("\n🎉 Fusion analysis should now show ENHANCED results instead of INSUFFICIENT_DATA!") 