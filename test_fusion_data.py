#!/usr/bin/env python3
"""
Test Bookmap Fusion Data Flow
"""

import asyncio
import zmq
import json
import sys
sys.path.append('/app')
from datetime import datetime

async def send_test_signals():
    """Send test Bookmap signals to verify fusion analysis."""
    
    # Test signals for different scenarios
    test_signals = [
        {
            "symbol": "JUPUSDT",
            "signal_type": "WHALE_TRADE",
            "price": 0.4823,
            "volume": 1500000.0,  # $1.5M whale trade
            "timestamp": datetime.utcnow().isoformat(),
            "direction": "BUY",
            "confidence": 0.92,
            "metadata": {
                "execution_algo": "iceberg",
                "time_weighted": True,
                "market_impact": "high"
            }
        },
        {
            "symbol": "JUPUSDT", 
            "signal_type": "ICEBERG_DETECTED",
            "price": 0.4821,
            "volume": 800000.0,  # $800K iceberg
            "timestamp": datetime.utcnow().isoformat(),
            "direction": "BUY",
            "confidence": 0.85,
            "metadata": {
                "hidden_size": 2000000.0,
                "revealed_ratio": 0.4
            }
        },
        {
            "symbol": "BTCUSDT",
            "signal_type": "STOP_RUN",
            "price": 110118.0,
            "volume": 750000.0,  # $750K stop run
            "timestamp": datetime.utcnow().isoformat(), 
            "direction": "SELL",
            "confidence": 0.78,
            "metadata": {
                "stop_level": 110000.0,
                "cascade_effect": True
            }
        }
    ]
    
    # Setup ZMQ connection
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect("tcp://localhost:5555")
    
    print("=== Sending Test Bookmap Signals ===")
    
    for i, signal in enumerate(test_signals, 1):
        try:
            message = json.dumps(signal)
            socket.send_string(message)
            print(f"✅ Sent signal {i}: {signal['signal_type']} for {signal['symbol']}")
            await asyncio.sleep(0.5)  # Small delay between signals
        except Exception as e:
            print(f"❌ Failed to send signal {i}: {e}")
    
    socket.close()
    context.term()
    
    print("\n=== Waiting for Signal Processing ===")
    await asyncio.sleep(2)  # Wait for signals to be processed
    
    # Check if signals were received
    try:
        from app.services.bookmap_engine import bookmap_engine
        signal_count = len(bookmap_engine.signal_aggregator.signal_history)
        print(f"📊 Signals received in aggregator: {signal_count}")
        
        if signal_count > 0:
            print("✅ Bookmap data is now flowing! Next trading signals should show enhanced fusion analysis.")
        else:
            print("⚠️  Signals sent but not received. Check ZMQ connection.")
            
    except Exception as e:
        print(f"❌ Error checking signal aggregator: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_signals()) 