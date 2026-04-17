import sys
import time
import random
sys.path.insert(0, "/app")

from app.services.bookmap_engine import bookmap_engine, BookmapSignal, SignalType

# Use the global bookmap engine aggregator
aggregator = bookmap_engine.signal_aggregator

print("🚀 Injecting signals for ALL trading symbols...")

# Complete list of all trading symbols from main.py
ALL_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "ADAUSDT", "DOTUSDT", 
    "LINKUSDT", "MATICUSDT", "ATOMUSDT", "NEARUSDT", "JUPUSDT", "WUSDT", 
    "APEXUSDT", "XTERUSDT", "PYTHUSDT", "RNSTUSDT", "FTMUSDT", "AAVEUSDT", 
    "UNIUSDT", "SUIUSDT", "ARBUSDT", "OPUSDT", "APTUSDT", "INJUSDT", 
    "TIAUSDT", "RUNEUSDT", "PENDLEUSDT", "JITOUSDT", "WIFUSDT", "RAYUSDT",
    "POPCATUSDT", "BOMEUSDT", "TURBOUSDT", "FIDAUSDT", "MEMEUSDT", "NOTUSDT",
    "DOGSUSDT", "TONUSDT", "HMSTRUSDT", "CATUSDT", "ACTUSDT", "EIGENUSDT",
    "SCUSDT", "SEIUSDT", "TAOUSDT", "CHZUSDT", "SANDUSDT", "MANAUSDT",
    "ALGOUSDT", "AXSUSDT", "MINAUSDT", "FILUSDT", "HBARUSDT", "VETUSDT",
    "ICPUSDT", "XLMUSDT", "TRXUSDT", "LTCUSDT", "BCHUSDT", "ETCUSDT"
]

# High-impact signal types
signal_types = [
    SignalType.WHALE_TRADE,
    SignalType.ICEBERG_DETECTION, 
    SignalType.STOP_RUN,
    SignalType.SWEEP_DETECTED
]

print(f"📊 Total symbols to process: {len(ALL_SYMBOLS)}")

# Distribute bias across symbols for realistic fusion results
# 40% bullish, 40% bearish, 20% neutral
random.seed(42)  # For reproducible results
symbols_shuffled = ALL_SYMBOLS.copy()
random.shuffle(symbols_shuffled)

bullish_count = int(len(ALL_SYMBOLS) * 0.4)  # 22 symbols
bearish_count = int(len(ALL_SYMBOLS) * 0.4)  # 22 symbols
neutral_count = len(ALL_SYMBOLS) - bullish_count - bearish_count  # 12 symbols

bullish_symbols = symbols_shuffled[:bullish_count]
bearish_symbols = symbols_shuffled[bullish_count:bullish_count + bearish_count]
neutral_symbols = symbols_shuffled[bullish_count + bearish_count:]

print(f"📈 Bullish bias: {len(bullish_symbols)} symbols")
print(f"📉 Bearish bias: {len(bearish_symbols)} symbols") 
print(f"➡️  Neutral bias: {len(neutral_symbols)} symbols")

total_signals = 0

# Inject BULLISH signals (4 BUY : 1 SELL ratio)
print("\n🟢 Injecting BULLISH signals...")
for i, symbol in enumerate(bullish_symbols, 1):
    print(f"[{i}/{len(bullish_symbols)}] {symbol} - BULLISH")
    
    for signal_type in signal_types:
        # 4 BUY signals
        for _ in range(4):
            signal = BookmapSignal(
                timestamp=time.time(),
                instrument=symbol,
                signal_type=signal_type,
                confidence=random.uniform(8.0, 9.5),  # High confidence
                triggers=["whale_detection", "order_flow_imbalance"],
                side="BUY",
                price=random.uniform(0.1, 100.0),
                details={
                    "volume": random.uniform(500000, 2000000),
                    "order_flow_imbalance": random.uniform(0.6, 0.9),
                    "depth_analysis": "strong_bullish_momentum"
                }
            )
            aggregator.process_signal(signal)
            total_signals += 1
            
        # 1 SELL signal (minority)
        signal = BookmapSignal(
            timestamp=time.time(),
            instrument=symbol,
            signal_type=signal_type,
            confidence=random.uniform(3.0, 5.0),  # Lower confidence
            triggers=["minor_resistance"],
            side="SELL",
            price=random.uniform(0.1, 100.0),
            details={
                "volume": random.uniform(100000, 500000),
                "order_flow_imbalance": random.uniform(-0.3, -0.1),
                "depth_analysis": "minor_selling_pressure"
            }
        )
        aggregator.process_signal(signal)
        total_signals += 1

# Inject BEARISH signals (1 BUY : 4 SELL ratio)
print("\n🔴 Injecting BEARISH signals...")
for i, symbol in enumerate(bearish_symbols, 1):
    print(f"[{i}/{len(bearish_symbols)}] {symbol} - BEARISH")
    
    for signal_type in signal_types:
        # 1 BUY signal (minority)
        signal = BookmapSignal(
            timestamp=time.time(),
            instrument=symbol,
            signal_type=signal_type,
            confidence=random.uniform(3.0, 5.0),  # Lower confidence
            triggers=["minor_support"],
            side="BUY",
            price=random.uniform(0.1, 100.0),
            details={
                "volume": random.uniform(100000, 500000),
                "order_flow_imbalance": random.uniform(0.1, 0.3),
                "depth_analysis": "minor_buying_interest"
            }
        )
        aggregator.process_signal(signal)
        total_signals += 1
        
        # 4 SELL signals
        for _ in range(4):
            signal = BookmapSignal(
                timestamp=time.time(),
                instrument=symbol,
                signal_type=signal_type,
                confidence=random.uniform(8.0, 9.5),  # High confidence
                triggers=["whale_dump", "liquidation_cascade"],
                side="SELL",
                price=random.uniform(0.1, 100.0),
                details={
                    "volume": random.uniform(500000, 2000000),
                    "order_flow_imbalance": random.uniform(-0.9, -0.6),
                    "depth_analysis": "strong_bearish_momentum"
                }
            )
            aggregator.process_signal(signal)
            total_signals += 1

# Inject NEUTRAL signals (2 BUY : 2 SELL ratio)
print("\n🟡 Injecting NEUTRAL signals...")
for i, symbol in enumerate(neutral_symbols, 1):
    print(f"[{i}/{len(neutral_symbols)}] {symbol} - NEUTRAL")
    
    for signal_type in signal_types:
        # 2 BUY signals
        for _ in range(2):
            signal = BookmapSignal(
                timestamp=time.time(),
                instrument=symbol,
                signal_type=signal_type,
                confidence=random.uniform(6.0, 7.5),  # Medium confidence
                triggers=["sideways_action", "range_bound"],
                side="BUY",
                price=random.uniform(0.1, 100.0),
                details={
                    "volume": random.uniform(200000, 800000),
                    "order_flow_imbalance": random.uniform(0.2, 0.5),
                    "depth_analysis": "balanced_flow"
                }
            )
            aggregator.process_signal(signal)
            total_signals += 1
            
        # 2 SELL signals
        for _ in range(2):
            signal = BookmapSignal(
                timestamp=time.time(),
                instrument=symbol,
                signal_type=signal_type,
                confidence=random.uniform(6.0, 7.5),  # Medium confidence
                triggers=["sideways_action", "range_bound"],
                side="SELL",
                price=random.uniform(0.1, 100.0),
                details={
                    "volume": random.uniform(200000, 800000),
                    "order_flow_imbalance": random.uniform(-0.5, -0.2),
                    "depth_analysis": "balanced_flow"
                }
            )
            aggregator.process_signal(signal)
            total_signals += 1

print(f"\n✅ INJECTION COMPLETE!")
print(f"📊 Total signals injected: {total_signals}")
print(f"📈 Total symbols with signals: {len(aggregator.signal_history)}")

# Show distribution
print(f"\n📋 SIGNAL DISTRIBUTION:")
for symbol in aggregator.signal_history.keys():
    signal_count = len(aggregator.signal_history[symbol])
    order_flow_score = aggregator.calculate_order_flow_score(symbol)
    print(f"{symbol}: {signal_count} signals, Order Flow: {order_flow_score:.3f}")

print(f"\n🎯 Expected Fusion Results:")
print(f"📈 BULLISH symbols ({len(bullish_symbols)}): Should show ENHANCED_LONG")
print(f"📉 BEARISH symbols ({len(bearish_symbols)}): Should show ENHANCED_SHORT")  
print(f"➡️  NEUTRAL symbols ({len(neutral_symbols)}): Should show balanced results")
print(f"\n🚀 ALL {len(ALL_SYMBOLS)} symbols now have comprehensive Bookmap signals!") 