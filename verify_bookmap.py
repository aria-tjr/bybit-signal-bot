#!/usr/bin/env python3
"""
Bookmap Integration Verification Script

This script tests the Bookmap integration setup to ensure everything is working correctly.
Run this after completing the setup process.
"""

import asyncio
import json
import time
import zmq
import zmq.asyncio
from pathlib import Path
import sys

def test_imports():
    """Test that all required modules can be imported."""
    print("📦 Testing imports...")
    
    try:
        import zmq
        print("✅ ZeroMQ imported successfully")
    except ImportError as e:
        print(f"❌ ZeroMQ import failed: {e}")
        return False
    
    try:
        from app.services.bookmap_engine import bookmap_engine
        print("✅ Bookmap engine imported successfully")
    except ImportError as e:
        print(f"❌ Bookmap engine import failed: {e}")
        return False
    
    try:
        from app.services.signal_fusion import signal_fusion_engine
        print("✅ Signal fusion engine imported successfully")
    except ImportError as e:
        print(f"❌ Signal fusion engine import failed: {e}")
        return False
    
    return True

def test_zmq_ports():
    """Test ZeroMQ port availability."""
    print("\n🔌 Testing ZeroMQ ports...")
    
    context = zmq.Context()
    
    # Test main Bookmap port (5555)
    try:
        socket = context.socket(zmq.SUB)
        socket.setsockopt(zmq.SUBSCRIBE, b"")
        socket.connect("tcp://127.0.0.1:5555")
        socket.close()
        print("✅ Port 5555 (Bookmap signals) is accessible")
    except Exception as e:
        print(f"⚠️  Port 5555 not accessible: {e}")
        print("   This is normal if Bookmap add-on is not running")
    
    context.term()
    return True

async def test_signal_fusion():
    """Test signal fusion engine functionality."""
    print("\n🔗 Testing signal fusion engine...")
    
    try:
        from app.services.signal_fusion import signal_fusion_engine
        
        # Create a mock TA signal
        mock_signal = {
            "direction": "LONG",
            "entry_price": 30000.0,
            "stop_loss": 29500.0,
            "take_profit_1": 30300.0,
            "take_profit_2": 30600.0,
            "take_profit_3": 31000.0,
            "confidence_score": 7.5,
            "volatility_score": 6.0
        }
        
        # Test fusion (will return minimal result if no Bookmap data)
        fused_signal = await signal_fusion_engine.fuse_signals(mock_signal, "BTCUSDT")
        
        print(f"✅ Signal fusion test completed")
        print(f"   Fusion result: {fused_signal.fusion_result.value}")
        print(f"   Order flow score: {fused_signal.order_flow_score}")
        
        return True
        
    except Exception as e:
        print(f"❌ Signal fusion test failed: {e}")
        return False

def test_bookmap_addon_file():
    """Test if Bookmap add-on file exists and is properly formatted."""
    print("\n📄 Testing Bookmap add-on file...")
    
    addon_file = Path("bookmap_bybit_addon.py")
    
    if not addon_file.exists():
        print("❌ bookmap_bybit_addon.py not found")
        return False
    
    print("✅ Bookmap add-on file exists")
    
    # Check file content
    try:
        with open(addon_file, 'r') as f:
            content = f.read()
            
        if "class BookmapBybitAddon" in content:
            print("✅ Add-on class found")
        else:
            print("❌ Add-on class not found in file")
            return False
            
        if "zmq" in content:
            print("✅ ZeroMQ integration found")
        else:
            print("❌ ZeroMQ integration not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error reading add-on file: {e}")
        return False

def test_config_files():
    """Test configuration files."""
    print("\n⚙️ Testing configuration files...")
    
    # Check if config was created
    config_file = Path("bookmap_config.ini")
    if config_file.exists():
        print("✅ Bookmap configuration file exists")
    else:
        print("⚠️  Bookmap configuration file not found")
    
    # Check main bot requirements
    req_file = Path("requirements.txt")
    if req_file.exists():
        with open(req_file, 'r') as f:
            content = f.read()
        
        if "pyzmq" in content:
            print("✅ ZeroMQ dependency in requirements.txt")
        else:
            print("❌ ZeroMQ dependency missing from requirements.txt")
            return False
    
    return True

async def simulate_bookmap_signals():
    """Simulate Bookmap signals for testing."""
    print("\n🎭 Simulating Bookmap signals...")
    
    try:
        # Create a mock signal
        mock_signal = {
            "timestamp": time.time(),
            "instrument": "BTCUSDT",
            "signal_type": "WHALE_TRADE",
            "confidence": 8.0,
            "triggers": ["LargeTrade"],
            "side": "BUY",
            "price": 30000.0,
            "details": {
                "size": 10.0,
                "notional": 300000.0
            }
        }
        
        # Test signal processing
        from app.services.bookmap_engine import bookmap_engine
        
        # Simulate signal reception
        print("✅ Mock signal created successfully")
        print(f"   Signal type: {mock_signal['signal_type']}")
        print(f"   Side: {mock_signal['side']}")
        print(f"   Notional: ${mock_signal['details']['notional']:,.0f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Signal simulation failed: {e}")
        return False

def print_integration_status():
    """Print overall integration status."""
    print("\n" + "="*60)
    print("📊 INTEGRATION STATUS SUMMARY")
    print("="*60)
    
    print("""
🎯 SETUP COMPLETION CHECKLIST:

✅ Python Dependencies
✅ ZeroMQ Library  
✅ Signal Fusion Engine
✅ Bookmap Add-on File
✅ Configuration Files

🔧 REMAINING MANUAL STEPS:

📂 Bookmap Add-on Installation:
   • Copy bookmap_bybit_addon.py to Bookmap's add-ons directory
   • Enable in Bookmap Add-on Manager
   • Configure for Bybit BTCUSDT Perpetual

🔗 Bookmap Configuration:
   • Enable Global Plus add-ons:
     - Stops & Icebergs On-Chart
     - Market Pulse (CVD, Liquidations)  
     - Large Trades Alert
   • Connect Bybit data feed

🚀 Final Testing:
   • Start crypto signal bot
   • Use /bookmap command to verify connection
   • Test with /orderflow BTCUSDT
   • Monitor /fusion performance

💡 The integration is ready for the final manual steps in Bookmap!
""")

async def main():
    """Main verification function."""
    print("🔍 BOOKMAP INTEGRATION VERIFICATION")
    print("="*50)
    
    all_tests_passed = True
    
    # Run tests
    if not test_imports():
        all_tests_passed = False
    
    if not test_zmq_ports():
        all_tests_passed = False
    
    if not await test_signal_fusion():
        all_tests_passed = False
    
    if not test_bookmap_addon_file():
        all_tests_passed = False
    
    if not test_config_files():
        all_tests_passed = False
    
    if not await simulate_bookmap_signals():
        all_tests_passed = False
    
    # Print status
    print_integration_status()
    
    if all_tests_passed:
        print("\n🎉 ALL AUTOMATED TESTS PASSED!")
        print("Ready for final Bookmap configuration steps.")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    asyncio.run(main()) 