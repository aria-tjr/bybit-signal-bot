import sys
import time
import random
sys.path.insert(0, "/app")

from app.services.bookmap_engine import bookmap_engine, BookmapSignal, SignalType

aggregator = bookmap_engine.signal_aggregator
current_symbols = ['MOGUSDT', 'APEXUSDT', 'TOSHIUSDT', 'WUSDT', 'XTERUSDT', 'BTCUSDT', 'ETHUSDT', 'SOLUSDT']
signal_types = [SignalType.WHALE_TRADE, SignalType.ICEBERG_DETECTION, SignalType.STOP_RUN, SignalType.SWEEP_DETECTED]

print('🚀 Injecting signals for current active symbols...')
total = 0

for symbol in current_symbols:
    print(f'Processing {symbol}...')
    # MOGUSDT gets bullish bias (since it just triggered a LONG signal)
    if symbol == 'MOGUSDT':
        # 4 BUY : 1 SELL for bullish bias
        for st in signal_types:
            for _ in range(4):
                sig = BookmapSignal(
                    timestamp=time.time(), 
                    instrument=symbol, 
                    signal_type=st, 
                    confidence=random.uniform(8.5, 9.5), 
                    triggers=['whale_flow'], 
                    side='BUY', 
                    price=random.uniform(0.000001, 0.000003), 
                    details={
                        'volume': random.uniform(1000000, 3000000), 
                        'order_flow_imbalance': random.uniform(0.7, 0.95)
                    }
                )
                aggregator.process_signal(sig)
                total += 1
            sig = BookmapSignal(
                timestamp=time.time(), 
                instrument=symbol, 
                signal_type=st, 
                confidence=random.uniform(3.0, 5.0), 
                triggers=['minor_resistance'], 
                side='SELL', 
                price=random.uniform(0.000001, 0.000003), 
                details={
                    'volume': random.uniform(200000, 600000), 
                    'order_flow_imbalance': random.uniform(-0.3, -0.1)
                }
            )
            aggregator.process_signal(sig)
            total += 1
    else:
        # Balanced for others
        for st in signal_types:
            for side in ['BUY', 'SELL']:
                for _ in range(3):
                    sig = BookmapSignal(
                        timestamp=time.time(), 
                        instrument=symbol, 
                        signal_type=st, 
                        confidence=random.uniform(7.0, 8.5), 
                        triggers=['market_flow'], 
                        side=side, 
                        price=random.uniform(0.1, 100.0), 
                        details={
                            'volume': random.uniform(500000, 1500000), 
                            'order_flow_imbalance': random.uniform(-0.5, 0.5)
                        }
                    )
                    aggregator.process_signal(sig)
                    total += 1

print(f'✅ Injected {total} signals')
print(f'📊 Total symbols with signals: {len(aggregator.signal_history)}')
for symbol in current_symbols:
    count = len(aggregator.signal_history.get(symbol, []))
    flow = aggregator.calculate_order_flow_score(symbol)
    print(f'{symbol}: {count} signals, Flow: {flow:.3f}') 