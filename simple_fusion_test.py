#!/usr/bin/env python3
"""
Simple Fusion Test - Use existing signal workflow
"""

import asyncio
import sys
sys.path.append('/app')
from datetime import datetime

async def simple_fusion_test():
    """Test fusion using the existing signal processing workflow."""
    
    try:
        from app.services.bookmap_engine import bookmap_engine, BookmapSignal, SignalType
        from app.services.signal_processor import SignalProcessor
        
        print("=== Simple Fusion Test ===")
        
        # Ensure Bookmap engine is running
        if not bookmap_engine.running:
            await bookmap_engine.start()
            print("✅ Started Bookmap engine")
        
        # Create and inject test signals
        whale_signal = BookmapSignal(
            timestamp=datetime.utcnow().timestamp(),
            instrument="JUPUSDT",
            signal_type=SignalType.WHALE_TRADE,
            confidence=0.92,
            triggers=["whale_detected", "large_volume"],
            side="BUY",
            price=0.4823,
            details={
                "volume": 1500000.0,  # $1.5M whale trade
                "execution_algo": "iceberg",
                "market_impact": "high"
            }
        )
        
        iceberg_signal = BookmapSignal(
            timestamp=datetime.utcnow().timestamp(),
            instrument="JUPUSDT", 
            signal_type=SignalType.ICEBERG_DETECTION,
            confidence=0.85,
            triggers=["iceberg_detected", "hidden_liquidity"],
            side="BUY",
            price=0.4821,
            details={
                "volume": 800000.0,  # $800K iceberg
                "hidden_size": 2000000.0,
                "revealed_ratio": 0.4
            }
        )
        
        print("📊 Injecting whale and iceberg signals for JUPUSDT...")
        bookmap_engine.signal_aggregator.process_signal(whale_signal)
        bookmap_engine.signal_aggregator.process_signal(iceberg_signal)
        
        signal_count = len(bookmap_engine.signal_aggregator.signal_history)
        print(f"✅ Injected {signal_count} signals into aggregator")
        
        # Now process JUPUSDT through the normal signal processor
        print("\n🔧 Processing JUPUSDT signal (should now have fusion data)...")
        
        signal_processor = SignalProcessor()
        
        # This should trigger the fusion analysis with our injected data
        result = await signal_processor.process_symbol("JUPUSDT")
        
        if result:
            print("✅ Signal processed successfully!")
            print("📈 Check your Telegram for the enhanced signal with fusion analysis!")
            print("\n🎯 The next JUPUSDT signal should show:")
            print("   • Confidence Boost: > 0.0")
            print("   • Order Flow Score: > 0.0") 
            print("   • Leverage Adjustment: ≠ 100%")
            print("   • Fusion Result: ENHANCED_LONG or similar")
        else:
            print("⚠️  Signal processing returned None")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_fusion_test()) 