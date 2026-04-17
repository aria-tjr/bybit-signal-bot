#!/usr/bin/env python3
import sys
sys.path.append('/app')

from app.services.bookmap_engine import BookmapSignalAggregator
from app.models.bookmap_signal import BookmapSignal, SignalType
import datetime as dt

def inject_wusdt_signals():
    """Add whale signals for WUSDT to enable fusion analysis"""
    print("🐋 Injecting WUSDT whale signals...")
    
    aggregator = BookmapSignalAggregator()
    
    # Large whale trade signal
    whale_signal = BookmapSignal(
        timestamp=dt.datetime.now(dt.timezone.utc),
        instrument='WUSDT',
        signal_type=SignalType.WHALE_TRADE,
        confidence=85.0,
        side='BUY',
        price=0.0772,
        details={'volume_usd': 1200000}
    )
    
    # Iceberg detection signal
    iceberg_signal = BookmapSignal(
        timestamp=dt.datetime.now(dt.timezone.utc),
        instrument='WUSDT', 
        signal_type=SignalType.ICEBERG_DETECTION,
        confidence=75.0,
        side='BUY',
        price=0.0771,
        details={'hidden_volume_usd': 800000}
    )
    
    aggregator.process_signal(whale_signal)
    aggregator.process_signal(iceberg_signal)
    
    print(f"✅ Added whale trade: ${whale_signal.details['volume_usd']:,}")
    print(f"✅ Added iceberg order: ${iceberg_signal.details['hidden_volume_usd']:,}")
    print(f"📊 Total signals in aggregator: {len(aggregator.signals)}")
    print("🎯 Future WUSDT signals will now have enhanced fusion analysis!")

if __name__ == "__main__":
    inject_wusdt_signals() 