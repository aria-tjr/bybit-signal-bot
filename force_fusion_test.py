#!/usr/bin/env python3
"""
Force Fusion Test - Directly inject signals and test fusion analysis
"""

import asyncio
import sys
sys.path.append('/app')
from datetime import datetime, timedelta

async def force_fusion_test():
    """Directly inject signals and test fusion analysis."""
    
    try:
        from app.services.bookmap_engine import bookmap_engine, BookmapSignal, SignalType
        from app.services.signal_fusion import SignalFusionEngine
        from app.models.signal import Signal, Direction
        
        print("=== Force Fusion Test ===")
        
        # Create test Bookmap signals
        whale_signal = BookmapSignal(
            symbol="JUPUSDT",
            signal_type=SignalType.WHALE_TRADE,
            price=0.4823,
            volume=1500000.0,  # $1.5M
            timestamp=datetime.utcnow(),
            direction="BUY",
            confidence=0.92
        )
        
        iceberg_signal = BookmapSignal(
            symbol="JUPUSDT", 
            signal_type=SignalType.ICEBERG_DETECTED,
            price=0.4821,
            volume=800000.0,  # $800K
            timestamp=datetime.utcnow(),
            direction="BUY", 
            confidence=0.85
        )
        
        # Manually inject signals into aggregator
        print("📊 Injecting test signals...")
        bookmap_engine.signal_aggregator.add_signal(whale_signal)
        bookmap_engine.signal_aggregator.add_signal(iceberg_signal)
        
        signal_count = len(bookmap_engine.signal_aggregator.signal_history)
        print(f"✅ Injected signals. Total in aggregator: {signal_count}")
        
        # Create a test TA signal
        test_ta_signal = Signal(
            symbol="JUPUSDT",
            direction=Direction.LONG,
            confidence_score=85.0,
            timestamp=datetime.utcnow(),
            entry_price=0.4823,
            stop_loss=0.4782,
            targets=[0.4862, 0.4895, 0.4944],
            market_regime=None,
            technical_analysis={
                "rsi": 50.0,
                "macd": {"histogram": 0.002},
                "trend_strength": 100.0
            }
        )
        
        # Test fusion analysis
        print("\n🔧 Testing Signal Fusion...")
        fusion_engine = SignalFusionEngine()
        
        try:
            fused_signal = await fusion_engine.fuse_signals(test_ta_signal)
            
            print("✅ Fusion Analysis Results:")
            print(f"   Result: {fused_signal.fusion_result}")
            print(f"   Confidence Boost: {fused_signal.confidence_boost:+.1f}")
            print(f"   Order Flow Score: {fused_signal.order_flow_score:.1f}")
            print(f"   Leverage Adjustment: {fused_signal.leverage_adjustment:.1f}x")
            print(f"   Triggers: {fused_signal.fusion_triggers}")
            
            # Check if we have non-zero values
            if (fused_signal.confidence_boost != 0.0 or 
                fused_signal.order_flow_score != 0.0 or
                fused_signal.leverage_adjustment != 1.0):
                print("🎉 SUCCESS! Fusion analysis is working with data!")
            else:
                print("⚠️  Fusion ran but returned zero values - checking why...")
                
        except Exception as e:
            print(f"❌ Fusion test failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(force_fusion_test()) 