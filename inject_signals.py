import sys
sys.path.insert(0, "/app")

from app.services.bookmap_engine import BookmapSignalAggregator, BookmapSignal
from datetime import datetime, timezone

# Create aggregator
aggregator = BookmapSignalAggregator()

# Symbols to inject
symbols = ["BTCUSDT", "ETHUSDT", "WUSDT", "TOSHIUSDT", "APEXUSDT", "XTERUSDT", "ASRRUSDT", "BOBAUSDT", "CLOUDUSDT", "HUMAUSDT", "LAUSDT"]
signal_types = ["WHALE_TRADE", "ICEBERG_DETECTION", "STOP_RUN", "SWEEP_DETECTED"]

print("🚀 Starting signal injection...")

total_signals = 0
for symbol in symbols:
    print(f"Injecting signals for {symbol}...")
    for signal_type in signal_types:
        for side in ["BUY", "SELL"]:
            signal = BookmapSignal(
                timestamp=datetime.now(timezone.utc),
                instrument=symbol,
                signal_type=signal_type,
                confidence=0.85,
                triggers=["level_break", "volume_spike"],
                side=side,
                price=1.0,
                details={
                    "volume": 1000000.0,
                    "order_flow_imbalance": 0.7,
                    "depth_analysis": "strong_support"
                }
            )
            aggregator.add_signal(signal)
            total_signals += 1

print(f"✅ Injected {total_signals} signals")
print(f"📊 Total signals in aggregator: {len(aggregator.signals)}")

# Test fusion with various symbols
test_symbols = ["TOSHIUSDT", "WUSDT", "APEXUSDT", "XTERUSDT", "ASRRUSDT"]
print("\n🎯 Testing fusion analysis...")

for symbol in test_symbols:
    fusion_result = aggregator.get_fusion_data(symbol, "LONG")
    print(f"{symbol} fusion result: {fusion_result}") 