#!/usr/bin/env python3
"""
Script to start the Bookmap engine in the running bot.
"""

import asyncio
import sys
sys.path.append('/app')

async def start_bookmap_engine():
    """Start the Bookmap engine."""
    try:
        from app.services.bookmap_engine import bookmap_engine
        
        print("Starting Bookmap engine...")
        
        if not bookmap_engine.running:
            await bookmap_engine.start()
            print("✅ Bookmap engine started successfully")
        else:
            print("✅ Bookmap engine already running")
            
        print(f"Engine status: {bookmap_engine.running}")
        print(f"Receiver status: {bookmap_engine.signal_receiver.running}")
        print(f"ZeroMQ port: {bookmap_engine.signal_receiver.zmq_port}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error starting Bookmap engine: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(start_bookmap_engine())
    sys.exit(0 if success else 1) 