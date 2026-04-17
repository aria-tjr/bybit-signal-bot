#!/usr/bin/env python3
"""
Bookmap Integration Setup Script

This script automates the setup process for Bookmap integration with the crypto signal bot.
It handles Python environment verification, dependency installation, and provides guidance
for Bookmap add-on installation.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible with Bookmap (3.7+)."""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Error: Python 3.7+ is required for Bookmap integration")
        print("Please install Python 3.7 or newer")
        return False
    
    print("✅ Python version is compatible with Bookmap")
    return True

def check_platform():
    """Check if running on macOS (required for Bookmap Apple Silicon)."""
    system = platform.system()
    machine = platform.machine()
    
    print(f"🖥️  Platform: {system} {machine}")
    
    if system == "Darwin":
        if machine == "arm64":
            print("✅ Running on Apple Silicon Mac - optimal for Bookmap")
        else:
            print("⚠️  Running on Intel Mac - Bookmap Apple Silicon version recommended")
        return True
    else:
        print("⚠️  Not running on macOS - Bookmap integration designed for Mac")
        return False

def install_dependencies():
    """Install required Python dependencies."""
    print("\n📦 Installing Python dependencies...")
    
    try:
        # Install pyzmq specifically
        print("Installing pyzmq for ZeroMQ communication...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyzmq==26.0.3"])
        print("✅ pyzmq installed successfully")
        
        # Install all requirements
        if Path("requirements.txt").exists():
            print("Installing all bot requirements...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ All requirements installed successfully")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def find_bookmap_directory():
    """Find Bookmap installation directory on macOS."""
    possible_paths = [
        "/Applications/Bookmap.app",
        "/Applications/Bookmap/Bookmap.app",
        "~/Applications/Bookmap.app",
        "~/Applications/Bookmap/Bookmap.app"
    ]
    
    for path in possible_paths:
        expanded_path = Path(path).expanduser()
        if expanded_path.exists():
            print(f"✅ Found Bookmap at: {expanded_path}")
            return expanded_path
    
    print("⚠️  Bookmap installation not found in standard locations")
    return None

def get_bookmap_addon_directory():
    """Get the Bookmap add-ons directory path."""
    bookmap_path = find_bookmap_directory()
    
    if bookmap_path:
        # Standard Bookmap add-ons directory structure
        addon_paths = [
            bookmap_path / "Contents" / "Resources" / "addons" / "python",
            bookmap_path / "Contents" / "addons" / "python",
            bookmap_path / "addons" / "python"
        ]
        
        for addon_path in addon_paths:
            if addon_path.exists():
                print(f"✅ Found Bookmap Python add-ons directory: {addon_path}")
                return addon_path
    
    # Fallback to user directory
    user_addon_path = Path.home() / ".bookmap" / "addons" / "python"
    print(f"📁 Using user add-ons directory: {user_addon_path}")
    return user_addon_path

def copy_bookmap_addon():
    """Copy the Bookmap add-on to the correct directory."""
    addon_source = Path("bookmap_bybit_addon.py")
    
    if not addon_source.exists():
        print("❌ Error: bookmap_bybit_addon.py not found in current directory")
        return False
    
    addon_dir = get_bookmap_addon_directory()
    
    try:
        # Create directory if it doesn't exist
        addon_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy the add-on file
        addon_dest = addon_dir / "bookmap_bybit_addon.py"
        shutil.copy2(addon_source, addon_dest)
        
        print(f"✅ Bookmap add-on copied to: {addon_dest}")
        
        # Make it executable
        os.chmod(addon_dest, 0o755)
        
        return True
        
    except Exception as e:
        print(f"❌ Error copying add-on: {e}")
        return False

def test_zmq_connection():
    """Test ZeroMQ connection capability."""
    print("\n🔌 Testing ZeroMQ connectivity...")
    
    try:
        import zmq
        
        # Test basic ZeroMQ functionality
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.bind("tcp://127.0.0.1:5556")  # Use different port for testing
        
        print("✅ ZeroMQ test successful")
        
        socket.close()
        context.term()
        return True
        
    except Exception as e:
        print(f"❌ ZeroMQ test failed: {e}")
        return False

def create_bookmap_config():
    """Create a Bookmap configuration file."""
    config_content = """# Bookmap Add-on Configuration
# 
# This file contains configuration for the Bybit crypto signal add-on
# Place this in your Bookmap user directory or reference it in the add-on

[BookmapBybitAddon]
instrument = BTCUSDT
exchange = Bybit
zmq_port = 5555

[Thresholds]
large_trade_usd = 200000
stoprun_alert_vol = 500000
iceberg_min_vol = 100000
spoof_time_threshold = 1.0

[Features]
whale_detection = true
stop_run_analysis = true
iceberg_tracking = true
spoof_detection = true
orderbook_imbalance = true
"""
    
    config_path = Path("bookmap_config.ini")
    
    try:
        with open(config_path, "w") as f:
            f.write(config_content)
        
        print(f"✅ Created Bookmap configuration: {config_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating config: {e}")
        return False

def print_manual_steps():
    """Print manual steps that user needs to complete."""
    print("\n" + "="*60)
    print("📋 MANUAL STEPS REQUIRED")
    print("="*60)
    
    addon_dir = get_bookmap_addon_directory()
    
    print(f"""
🎯 NEXT STEPS IN BOOKMAP:

1. 📂 Verify Add-on Installation:
   • Open Bookmap
   • Go to Settings → Add-ons → Python Add-ons
   • Verify 'bookmap_bybit_addon.py' appears in the list
   • If not found, manually copy it to: {addon_dir}

2. ⚙️ Configure the Add-on:
   • Enable the 'Bookmap Bybit Addon'
   • Set instrument to: 'Bybit BTCUSDT Perpetual'
   • Ensure Bybit data feed is connected

3. 🔧 Enable Required Global Plus Add-ons:
   • Stops & Icebergs On-Chart
   • Market Pulse (CVD, Liquidations)
   • Large Trades Alert

4. 🚀 Start the Integration:
   • Start your crypto signal bot
   • The bot will automatically connect to Bookmap via ZeroMQ
   • Use /bookmap command in Telegram to verify connection

5. ✅ Verify Integration:
   • /bookmap - Check engine status
   • /orderflow BTCUSDT - Test order flow analysis
   • /fusion - View fusion performance
""")

def main():
    """Main setup function."""
    print("🗺️  BOOKMAP INTEGRATION SETUP")
    print("="*50)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    platform_ok = check_platform()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        sys.exit(1)
    
    # Test ZeroMQ
    if not test_zmq_connection():
        print("⚠️  ZeroMQ test failed - integration may not work properly")
    
    # Copy Bookmap add-on
    if copy_bookmap_addon():
        print("✅ Bookmap add-on installation completed")
    else:
        print("⚠️  Add-on copy failed - manual installation required")
    
    # Create configuration
    create_bookmap_config()
    
    # Print manual steps
    print_manual_steps()
    
    print("\n🎉 AUTOMATED SETUP COMPLETED!")
    print("Please complete the manual steps above to finish the integration.")

if __name__ == "__main__":
    main() 