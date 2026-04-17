#!/usr/bin/env python3
"""
Test script to verify Bookmap engine functionality.
"""

import asyncio
import sys
import time
from app.services.bookmap_engine import bookmap_engine, BookmapSignal, SignalType
from app.core.logging import get_logger

logger = get_logger(__name__)

async def test_bookmap_engine():
    """Test the Bookmap engine initialization and functionality."""
    
    print("=== Bookmap Engine Test ===")
    
    # Test 1: Initial state
    print(f"1. Initial state - Running: {bookmap_engine.running}")
    
    # Test 2: Start engine
    print("2. Starting Bookmap engine...")
    try:
        await bookmap_engine.start()
        print(f"   Engine running: {bookmap_engine.running}")
        print(f"   Receiver running: {bookmap_engine.signal_receiver.running}")
    except Exception as e:
        print(f"   Error starting engine: {e}")
        return False
    
    # Test 3: Test signal aggregation
    print("3. Testing signal processing...")
    try:
        # Create a mock signal
        test_signal = BookmapSignal(
            timestamp=time.time(),
            instrument="BTCUSDT",
            signal_type=SignalType.WHALE_TRADE,
            confidence=8.5,
            triggers=["LargeTrade"],
            side="BUY",
            price=50000.0,
            details={"notional": 250000, "size": 5.0}
        )
        
        # Process the signal
        bookmap_engine.signal_aggregator.process_signal(test_signal)
        print("   Test signal processed successfully")
        
        # Get signal summary
        summary = bookmap_engine.get_signal_summary("BTCUSDT", 5)
        print(f"   Signal summary: {summary}")
        
        # Get order flow score
        score = bookmap_engine.get_order_flow_score("BTCUSDT")
        print(f"   Order flow score: {score}")
        
    except Exception as e:
        print(f"   Error testing signals: {e}")
        return False
    
    # Test 4: Check ZeroMQ connection
    print("4. Testing ZeroMQ connection...")
    try:
        receiver = bookmap_engine.signal_receiver
        print(f"   ZeroMQ port: {receiver.zmq_port}")
        print(f"   Socket created: {receiver.socket is not None}")
        print(f"   Context active: {receiver.context is not None}")
    except Exception as e:
        print(f"   ZeroMQ error: {e}")
    
    # Test 5: Simulate external Bookmap signal
    print("5. Testing external signal simulation...")
    try:
        import json
        import zmq
        
        # Create a context for sending test signals
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.connect("tcp://127.0.0.1:5555")
        
        # Send a test signal
        test_data = {
            "timestamp": time.time(),
            "instrument": "ETHUSDT",
            "signal_type": "WHALE_TRADE",
            "confidence": 9.0,
            "triggers": ["LargeTrade", "SweepDetected"],
            "side": "SELL",
            "price": 3500.0,
            "details": {"notional": 300000, "size": 85.7}
        }
        
        message = json.dumps(test_data)
        socket.send_string(message)
        print("   Test signal sent via ZeroMQ")
        
        # Wait a moment for processing
        await asyncio.sleep(0.1)
        
        # Check if signal was received
        eth_summary = bookmap_engine.get_signal_summary("ETHUSDT", 1)
        print(f"   ETHUSDT signals: {eth_summary['total_signals']}")
        
        socket.close()
        context.term()
        
    except Exception as e:
        print(f"   External signal test error: {e}")
    
    # Test 6: Stop engine
    print("6. Stopping Bookmap engine...")
    try:
        await bookmap_engine.stop()
        print(f"   Engine stopped: {not bookmap_engine.running}")
    except Exception as e:
        print(f"   Error stopping engine: {e}")
    
    print("=== Test Complete ===")
    return True

if __name__ == "__main__":
    asyncio.run(test_bookmap_engine()) 