#!/usr/bin/env python3
"""
Comprehensive Bookmap Integration Status Checker

This script verifies all components of the Bookmap integration:
1. Bot-side Bookmap engine
2. ZeroMQ connectivity
3. External Bookmap application
4. Add-on installation
5. Signal flow testing
"""

import asyncio
import json
import time
import zmq
import subprocess
import os
from pathlib import Path

def check_bookmap_application():
    """Check if Bookmap application is running."""
    print("=== Bookmap Application Status ===")
    
    try:
        # Check if Bookmap process is running
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        bookmap_processes = [line for line in result.stdout.split('\n') if 'Bookmap' in line]
        
        if bookmap_processes:
            print("✅ Bookmap application is running")
            for process in bookmap_processes:
                print(f"   Process: {process.split()[1]} - {process.split()[-1]}")
        else:
            print("❌ Bookmap application is NOT running")
            print("   Please start Bookmap before testing the integration")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Bookmap processes: {e}")
        return False
        
    return True

def check_addon_installation():
    """Check if the Bookmap add-on is properly installed."""
    print("\n=== Add-on Installation Status ===")
    
    addon_path = Path.home() / ".bookmap" / "addons" / "python" / "bookmap_bybit_addon.py"
    
    if addon_path.exists():
        print("✅ Bookmap add-on file is installed")
        print(f"   Location: {addon_path}")
        
        # Check file size and modification time
        stat = addon_path.stat()
        print(f"   Size: {stat.st_size} bytes")
        print(f"   Modified: {time.ctime(stat.st_mtime)}")
        
        # Check if file is executable
        if os.access(addon_path, os.X_OK):
            print("✅ Add-on file is executable")
        else:
            print("⚠️  Add-on file is not executable (this is normal)")
            
    else:
        print("❌ Bookmap add-on file is NOT installed")
        print(f"   Expected location: {addon_path}")
        return False
        
    return True

def check_zmq_connectivity():
    """Test ZeroMQ connectivity on port 5555."""
    print("\n=== ZeroMQ Connectivity Test ===")
    
    try:
        # Test if port 5555 is available
        context = zmq.Context()
        
        # Try to bind to the port (this will fail if already in use)
        test_socket = context.socket(zmq.PUB)
        try:
            test_socket.bind("tcp://127.0.0.1:5555")
            print("⚠️  Port 5555 is available (no receiver listening)")
            test_socket.close()
        except zmq.ZMQError as e:
            if "Address already in use" in str(e):
                print("✅ Port 5555 is in use (receiver is listening)")
            else:
                print(f"❌ ZeroMQ error: {e}")
                
        # Test sending a message
        sender = context.socket(zmq.PUB)
        sender.connect("tcp://127.0.0.1:5555")
        
        test_message = {
            "timestamp": time.time(),
            "instrument": "TEST",
            "signal_type": "TEST_SIGNAL",
            "confidence": 5.0,
            "triggers": ["ConnectivityTest"],
            "side": "BUY",
            "price": 50000.0,
            "details": {"test": True}
        }
        
        sender.send_string(json.dumps(test_message))
        print("✅ Test message sent successfully")
        
        sender.close()
        context.term()
        
    except Exception as e:
        print(f"❌ ZeroMQ connectivity error: {e}")
        return False
        
    return True

async def check_bot_engine():
    """Check the bot's Bookmap engine status."""
    print("\n=== Bot Bookmap Engine Status ===")
    
    try:
        from app.services.bookmap_engine import bookmap_engine, BookmapSignal, SignalType
        
        print(f"Engine running: {bookmap_engine.running}")
        print(f"Receiver running: {bookmap_engine.signal_receiver.running if hasattr(bookmap_engine, 'signal_receiver') else 'N/A'}")
        
        # Check signal history
        total_signals = sum(len(signals) for signals in bookmap_engine.signal_aggregator.signal_history.values())
        print(f"Total signals received: {total_signals}")
        
        if total_signals > 0:
            print("Recent signals by symbol:")
            for symbol, signals in bookmap_engine.signal_aggregator.signal_history.items():
                if signals:
                    print(f"  {symbol}: {len(signals)} signals")
                    
        # Test signal processing
        test_signal = BookmapSignal(
            timestamp=time.time(),
            instrument="TESTUSDT",
            signal_type=SignalType.WHALE_TRADE,
            confidence=7.5,
            triggers=["StatusTest"],
            side="BUY",
            price=45000.0,
            details={"test": True, "notional": 300000}
        )
        
        bookmap_engine.signal_aggregator.process_signal(test_signal)
        print("✅ Signal processing test successful")
        
        # Get signal summary
        summary = bookmap_engine.get_signal_summary("TESTUSDT", 1)
        print(f"Test signal summary: {summary}")
        
    except Exception as e:
        print(f"❌ Bot engine error: {e}")
        return False
        
    return True

def check_configuration():
    """Check Bookmap configuration files."""
    print("\n=== Configuration Status ===")
    
    config_path = Path("bookmap_config.ini")
    if config_path.exists():
        print("✅ Bookmap configuration file found")
        with open(config_path, 'r') as f:
            content = f.read()
            print("Configuration:")
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#'):
                    print(f"   {line}")
    else:
        print("⚠️  Bookmap configuration file not found")
        
    return True

def provide_setup_instructions():
    """Provide instructions for completing the Bookmap setup."""
    print("\n" + "="*60)
    print("BOOKMAP INTEGRATION SETUP INSTRUCTIONS")
    print("="*60)
    
    print("\n1. 📱 OPEN BOOKMAP APPLICATION:")
    print("   - Ensure Bookmap is running with Global Plus license")
    print("   - Connect to Bybit exchange")
    print("   - Open BTCUSDT Perpetual chart")
    
    print("\n2. 🔧 ENABLE PYTHON ADD-ON:")
    print("   - Go to Add-ons → Add-on Manager")
    print("   - Find 'Python Add-ons' section")
    print("   - Enable 'bookmap_bybit_addon.py'")
    print("   - Check console for initialization messages")
    
    print("\n3. 📊 ACTIVATE REQUIRED ADD-ONS:")
    print("   - Enable 'Stops & Icebergs On-Chart'")
    print("   - Enable 'Large Trades Alert'")
    print("   - Enable 'Market Pulse' add-ons")
    print("   - Configure thresholds as needed")
    
    print("\n4. 🔗 VERIFY CONNECTION:")
    print("   - Check Bookmap console for 'Add-on started successfully'")
    print("   - Look for 'Subscribed to BTCUSDT' message")
    print("   - Monitor for signal publishing messages")
    
    print("\n5. 🧪 TEST SIGNAL FLOW:")
    print("   - Place large orders in Bookmap (paper trading)")
    print("   - Watch for whale trade detections")
    print("   - Check bot logs for received signals")
    
    print("\n6. 📈 MONITOR INTEGRATION:")
    print("   - Use /bookmap command in Telegram")
    print("   - Use /orderflow BTCUSDT command")
    print("   - Check signal fusion in bot signals")

async def main():
    """Run comprehensive Bookmap status check."""
    print("🗺️  BOOKMAP INTEGRATION STATUS CHECKER")
    print("="*50)
    
    checks = [
        check_bookmap_application(),
        check_addon_installation(),
        check_zmq_connectivity(),
        await check_bot_engine(),
        check_configuration()
    ]
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n📊 SUMMARY: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Bookmap integration is ready.")
        print("   Next: Enable the add-on in Bookmap and connect to BTCUSDT")
    else:
        print("⚠️  Some issues found. Please review the results above.")
        
    provide_setup_instructions()

if __name__ == "__main__":
    asyncio.run(main()) 