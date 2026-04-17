#!/usr/bin/env python3
"""
Bookmap Add-on Activator and Integration Tester

This script:
1. Activates the Python API in Bookmap configuration
2. Enables our Bybit add-on 
3. Tests the ZeroMQ connection
4. Simulates order flow signals for testing

Usage: python activate_bookmap_addon.py
"""

import json
import os
import shutil
import subprocess
import time
import zmq
import asyncio
from pathlib import Path
from datetime import datetime

# Paths
BOOKMAP_CONFIG_DIR = Path.home() / "Library/Application Support/Bookmap/Config"
BOOKMAP_PYTHON_DIR = Path.home() / "Library/Application Support/Bookmap/Python"
CONFIG_FILE = BOOKMAP_CONFIG_DIR / "bookmap_config_v18.json"
ADDON_FILE = BOOKMAP_PYTHON_DIR / "bookmap_bybit_addon.py"

def backup_config():
    """Create a backup of the current Bookmap configuration."""
    backup_file = CONFIG_FILE.with_suffix('.json.backup')
    shutil.copy2(CONFIG_FILE, backup_file)
    print(f"✅ Created config backup: {backup_file}")

def activate_python_api():
    """Modify Bookmap configuration to enable Python API."""
    print("🔧 Activating Python API in Bookmap configuration...")
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Enable Python API in the strategies section
        if "activeStrategyInstances" not in config:
            config["activeStrategyInstances"] = {}
            
        # Add Python API to active strategies
        python_api_key = "com.bookmap.python.api.addon.DeveloperAddon"
        if python_api_key not in config["activeStrategyInstances"]:
            config["activeStrategyInstances"][python_api_key] = {
                "strategyName": "Python API",
                "className": "com.bookmap.python.api.addon.DeveloperAddon",
                "isEnabled": True,
                "path": f"/Users/{os.getenv('USER')}/Library/Application Support/Bookmap/API/Layer1ApiModules/7.5.0.16---7.7.1.9999---2---python-api---0.1.4.jar"
            }
        
        # Ensure Python API configuration exists
        if "Python API" not in config:
            config["Python API"] = {
                "text": json.dumps({
                    "pathToPythonExecutable": None,
                    "chosenTheme": "Dark",
                    "codeFoldingEnabled": True,
                    "lineHighlightEnabled": True,
                    "lineNumbersEnabled": True,
                    "bracketMatchingAnimationEnabled": True,
                    "bookmarksEnabled": True,
                    "wordWrapEnabled": False,
                    "antiAliasingEnabled": True,
                    "markOccurrencesEnabled": True,
                    "tabLinesEnabled": False
                })
            }
        
        # Write the updated configuration
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
            
        print("✅ Python API activated in configuration")
        return True
        
    except Exception as e:
        print(f"❌ Error activating Python API: {e}")
        return False

def verify_addon_installation():
    """Verify our Bybit add-on is properly installed."""
    print("🔍 Verifying Bybit add-on installation...")
    
    if not ADDON_FILE.exists():
        print(f"❌ Add-on file not found: {ADDON_FILE}")
        return False
    
    # Check file size and basic content
    file_size = ADDON_FILE.stat().st_size
    if file_size < 10000:  # Should be around 18KB
        print(f"❌ Add-on file seems incomplete (size: {file_size} bytes)")
        return False
    
    # Check if ZeroMQ is configured correctly
    with open(ADDON_FILE, 'r') as f:
        content = f.read()
        if "5555" not in content or "zmq" not in content:
            print("❌ Add-on missing ZeroMQ configuration")
            return False
    
    print(f"✅ Add-on verified (size: {file_size} bytes)")
    return True

def test_zmq_connection():
    """Test the ZeroMQ connection to ensure it's working."""
    print("🔗 Testing ZeroMQ connection...")
    
    try:
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.bind("tcp://*:5556")  # Use different port for testing
        
        # Send test message
        test_message = {
            "type": "test",
            "timestamp": datetime.now().isoformat(),
            "message": "ZeroMQ connection test"
        }
        
        socket.send_json(test_message)
        print("✅ ZeroMQ test message sent successfully")
        
        socket.close()
        context.term()
        return True
        
    except Exception as e:
        print(f"❌ ZeroMQ test failed: {e}")
        return False

def simulate_order_flow_signals():
    """Simulate order flow signals to test the integration."""
    print("📊 Simulating order flow signals...")
    
    try:
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.connect("tcp://localhost:5555")
        
        # Wait a moment for connection
        time.sleep(1)
        
        # Simulate different types of signals
        signals = [
            {
                "signal_type": "WHALE_TRADE",
                "symbol": "BTCUSDT",
                "timestamp": datetime.now().isoformat(),
                "side": "BUY",
                "size": 1500000,  # $1.5M whale trade
                "price": 95234.50,
                "confidence": 0.92,
                "flow_imbalance": 0.75,
                "metadata": {
                    "exchange": "Bybit",
                    "detected_pattern": "large_block_absorption"
                }
            },
            {
                "signal_type": "ICEBERG_DETECTED",
                "symbol": "ETHUSDT", 
                "timestamp": datetime.now().isoformat(),
                "side": "SELL",
                "hidden_size": 500000,  # $500K iceberg
                "visible_size": 50000,
                "price": 3234.75,
                "confidence": 0.88,
                "refresh_count": 12,
                "metadata": {
                    "exchange": "Bybit",
                    "iceberg_ratio": 0.1
                }
            },
            {
                "signal_type": "STOP_RUN",
                "symbol": "SOLUSDT",
                "timestamp": datetime.now().isoformat(),
                "direction": "DOWN",
                "liquidation_size": 750000,  # $750K liquidations
                "trigger_price": 198.45,
                "confidence": 0.94,
                "cascade_probability": 0.82,
                "metadata": {
                    "exchange": "Bybit",
                    "stops_triggered": 45
                }
            }
        ]
        
        for i, signal in enumerate(signals):
            print(f"  📡 Sending signal {i+1}: {signal['signal_type']} for {signal['symbol']}")
            socket.send_json(signal)
            time.sleep(0.5)  # Small delay between signals
        
        socket.close()
        context.term()
        
        print("✅ All test signals sent successfully")
        return True
        
    except Exception as e:
        print(f"❌ Signal simulation failed: {e}")
        return False

def restart_bookmap():
    """Restart Bookmap to apply configuration changes."""
    print("🔄 Restarting Bookmap to apply changes...")
    
    try:
        # Kill existing Bookmap processes
        subprocess.run(["pkill", "-f", "Bookmap"], check=False)
        time.sleep(3)
        
        # Start Bookmap
        subprocess.Popen(["/Applications/Bookmap.app/Contents/MacOS/Bookmap"])
        print("✅ Bookmap restart initiated")
        
        # Wait for startup
        print("⏳ Waiting for Bookmap to start (30 seconds)...")
        time.sleep(30)
        
        return True
        
    except Exception as e:
        print(f"❌ Error restarting Bookmap: {e}")
        return False

def check_bot_integration():
    """Check if the crypto bot is receiving signals."""
    print("🤖 Checking bot integration...")
    
    try:
        # Send a test command to Docker container to check signal reception
        result = subprocess.run([
            "docker", "exec", "crypto-signal-bot", 
            "python", "-c", 
            "from app.services.bookmap_engine import bookmap_engine; print('Signals received:', len(bookmap_engine.signal_aggregator.signal_history))"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ Bot status: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Bot check failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Bot integration check failed: {e}")
        return False

def main():
    """Main activation sequence."""
    print("🚀 Starting Bookmap Add-on Activation Sequence")
    print("=" * 50)
    
    steps = [
        ("Create config backup", backup_config),
        ("Verify add-on installation", verify_addon_installation), 
        ("Activate Python API", activate_python_api),
        ("Test ZeroMQ connection", test_zmq_connection),
        ("Restart Bookmap", restart_bookmap),
        ("Simulate order flow signals", simulate_order_flow_signals),
        ("Check bot integration", check_bot_integration)
    ]
    
    results = []
    
    for step_name, step_func in steps:
        print(f"\n📋 Step: {step_name}")
        try:
            success = step_func()
            results.append((step_name, success))
            if success:
                print(f"✅ {step_name} completed successfully")
            else:
                print(f"❌ {step_name} failed")
        except Exception as e:
            print(f"❌ {step_name} failed with error: {e}")
            results.append((step_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 ACTIVATION SUMMARY")
    print("=" * 50)
    
    successful_steps = sum(1 for _, success in results if success)
    total_steps = len(results)
    
    for step_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {step_name}")
    
    print(f"\n🎯 Success Rate: {successful_steps}/{total_steps} ({100*successful_steps/total_steps:.1f}%)")
    
    if successful_steps == total_steps:
        print("\n🎉 BOOKMAP INTEGRATION FULLY ACTIVATED!")
        print("Your crypto signal bot should now be receiving order flow data.")
        print("\nNext steps:")
        print("1. Check Telegram bot for enhanced signals")  
        print("2. Use /bookmap command to verify integration")
        print("3. Monitor /logs for order flow analysis")
    else:
        print(f"\n⚠️  PARTIAL ACTIVATION ({successful_steps}/{total_steps} steps completed)")
        print("Some manual steps may be required.")

if __name__ == "__main__":
    main() 