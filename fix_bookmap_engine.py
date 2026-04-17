#!/usr/bin/env python3
"""
Fix Bookmap Engine in Docker Container
"""

import asyncio
import sys
sys.path.append('/app')

async def fix_bookmap_engine():
    """Diagnose and fix the Bookmap engine."""
    try:
        from app.services.bookmap_engine import bookmap_engine
        
        print("=== Bookmap Engine Diagnostics ===")
        print(f"Initial Status - Running: {bookmap_engine.running}")
        print(f"Signal History: {len(bookmap_engine.signal_aggregator.signal_history)}")
        print(f"ZMQ Port: {bookmap_engine.signal_receiver.zmq_port}")
        
        # Try to start the engine
        print("\n=== Starting Bookmap Engine ===")
        if not bookmap_engine.running:
            await bookmap_engine.start()
            print(f"✅ Engine started successfully: {bookmap_engine.running}")
        else:
            print("✅ Engine already running")
            
        # Check receiver status
        print(f"Receiver running: {bookmap_engine.signal_receiver.running}")
        print(f"Aggregator initialized: {bookmap_engine.signal_aggregator is not None}")
        
        # Test ZMQ connection
        print("\n=== Testing ZMQ Connection ===")
        import zmq
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        try:
            socket.connect("tcp://localhost:5555")
            print("✅ ZMQ connection test successful")
            socket.close()
        except Exception as e:
            print(f"❌ ZMQ connection failed: {e}")
        context.term()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(fix_bookmap_engine()) 