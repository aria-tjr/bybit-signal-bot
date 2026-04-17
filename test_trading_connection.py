#!/usr/bin/env python3
"""
Test script for Bybit trading connection and auto trading functionality.

This script demonstrates how to:
1. Connect to Bybit API
2. Start the auto trading service
3. Send test signals
4. Monitor positions
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.bybit_trading import trading_service
from app.services.auto_trading import auto_trading_service
from app.core.logging import get_logger

logger = get_logger(__name__)


async def test_api_connection():
    """Test basic API connection."""
    print("🔌 Testing Bybit API connection...")
    
    try:
        await trading_service._verify_api_connection()
        await trading_service.update_account_balance()
        
        print(f"✅ API connection successful!")
        print(f"💰 Account Balance: ${trading_service.account_balance:,.2f}")
        print(f"💵 Available Balance: ${trading_service.available_balance:,.2f}")
        
        return True
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False


async def test_signal_processing():
    """Test signal processing without executing trades."""
    print("\n📊 Testing signal processing...")
    
    # Create a test signal
    test_signal = {
        "symbol": "BTCUSDT",
        "direction": "LONG",
        "entry_price": 95000.0,
        "stop_loss": 94000.0,
        "confidence": 0.8,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # Test signal validation
        is_valid = await auto_trading_service._validate_signal(test_signal)
        print(f"Signal validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        # Test signal enhancement
        enhanced_signal = await auto_trading_service._enhance_signal(test_signal)
        if enhanced_signal:
            print("✅ Signal enhanced successfully")
            print(f"   Leverage: {enhanced_signal.get('leverage')}x")
            print(f"   Take Profits: TP1=${enhanced_signal.get('tp1', 0):,.2f}, TP2=${enhanced_signal.get('tp2', 0):,.2f}, TP3=${enhanced_signal.get('tp3', 0):,.2f}")
            print(f"   Risk/Reward: 1:{enhanced_signal.get('risk_reward_ratio', 0):.1f}")
        
        # Test risk assessment
        risk_check = await auto_trading_service._assess_risk(enhanced_signal)
        print(f"Risk assessment: {'✅ Approved' if risk_check['approved'] else '❌ Rejected'}")
        if not risk_check['approved']:
            print(f"   Reason: {risk_check['reason']}")
        
        return enhanced_signal
    except Exception as e:
        print(f"❌ Signal processing failed: {e}")
        return None


async def demo_auto_trading():
    """Demonstrate auto trading functionality."""
    print("\n🤖 Auto Trading Demo")
    
    try:
        # Check current status
        status = await auto_trading_service.get_auto_trading_status()
        print(f"Auto trading enabled: {status['auto_trading_enabled']}")
        print(f"Daily trades: {status['daily_trades']['current']}/{status['daily_trades']['limit']}")
        
        # Create demo signals
        demo_signals = [
            {
                "symbol": "BTCUSDT",
                "direction": "LONG",
                "entry_price": 95000.0,
                "stop_loss": 94000.0,
                "confidence": 0.75,
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "symbol": "ETHUSDT", 
                "direction": "SHORT",
                "entry_price": 3500.0,
                "stop_loss": 3600.0,
                "confidence": 0.65,
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        print(f"\n📡 Processing {len(demo_signals)} demo signals...")
        
        for i, signal in enumerate(demo_signals, 1):
            print(f"\nSignal {i}: {signal['symbol']} {signal['direction']}")
            
            # Process signal (this will validate and potentially execute)
            executed = await auto_trading_service.process_signal(signal)
            
            if executed:
                print(f"   ✅ Signal executed successfully")
            else:
                print(f"   ❌ Signal not executed")
                
            # Small delay between signals
            await asyncio.sleep(1)
        
        # Show final status
        final_status = await auto_trading_service.get_auto_trading_status()
        print(f"\n📊 Final Status:")
        print(f"   Signals received: {final_status['session_stats']['signals_received']}")
        print(f"   Signals executed: {final_status['session_stats']['signals_executed']}")
        print(f"   Active positions: {final_status['account_status']['total_positions']}")
        
    except Exception as e:
        print(f"❌ Auto trading demo failed: {e}")


async def show_position_status():
    """Show current position status."""
    print("\n📈 Current Position Status")
    
    try:
        status = await trading_service.get_positions_status()
        
        print(f"Account Balance: ${status['account_balance']:,.2f}")
        print(f"Available Balance: ${status['available_balance']:,.2f}")
        print(f"Total Positions: {status['total_positions']}")
        print(f"Total Unrealized PnL: ${status['total_unrealized_pnl']:,.2f}")
        
        if status['positions']:
            print("\nActive Positions:")
            for i, position in enumerate(status['positions'], 1):
                print(f"  {i}. {position['symbol']} - {position['side']}")
                print(f"     Size: {position['size']}")
                print(f"     Entry: ${position['entry_price']:,.4f}")
                print(f"     Current: ${position['mark_price']:,.4f}")
                print(f"     PnL: {position['percentage']:+.2f}% (${position['unrealized_pnl']:+,.2f})")
                print()
        else:
            print("No active positions")
            
    except Exception as e:
        print(f"❌ Failed to get position status: {e}")


async def interactive_menu():
    """Interactive menu for testing different features."""
    while True:
        print("\n" + "="*50)
        print("🚀 BYBIT AUTO TRADING TEST MENU")
        print("="*50)
        print("1. Test API Connection")
        print("2. Test Signal Processing")
        print("3. Show Position Status")
        print("4. Start Auto Trading (LIVE)")
        print("5. Stop Auto Trading")
        print("6. Demo Auto Trading (SAFE)")
        print("7. Set Trading Parameters")
        print("8. Exit")
        print()
        
        choice = input("Enter your choice (1-8): ").strip()
        
        try:
            if choice == "1":
                await test_api_connection()
            elif choice == "2":
                await test_signal_processing()
            elif choice == "3":
                await show_position_status()
            elif choice == "4":
                print("\n⚠️  WARNING: This will enable LIVE trading!")
                confirm = input("Type 'YES' to confirm: ").strip()
                if confirm == "YES":
                    await auto_trading_service.start_auto_trading()
                    print("✅ Auto trading started")
                else:
                    print("❌ Auto trading start cancelled")
            elif choice == "5":
                await auto_trading_service.stop_auto_trading()
                print("✅ Auto trading stopped")
            elif choice == "6":
                await demo_auto_trading()
            elif choice == "7":
                await set_trading_parameters()
            elif choice == "8":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("\nPress Enter to continue...")


async def set_trading_parameters():
    """Interactive parameter setting."""
    print("\n⚙️  Trading Parameters")
    
    try:
        current_status = await auto_trading_service.get_auto_trading_status()
        current_params = current_status['signal_filters']
        
        print(f"Current min confidence: {current_params['min_confidence']}")
        print(f"Current max daily trades: {current_status['daily_trades']['limit']}")
        
        # Get new parameters
        new_confidence = input(f"New min confidence (0.0-1.0, current: {current_params['min_confidence']}): ").strip()
        new_max_trades = input(f"New max daily trades (current: {current_status['daily_trades']['limit']}): ").strip()
        
        parameters = {}
        if new_confidence:
            parameters['min_confidence'] = float(new_confidence)
        if new_max_trades:
            parameters['max_daily_trades'] = int(new_max_trades)
        
        if parameters:
            await auto_trading_service.set_trading_parameters(parameters)
            print("✅ Parameters updated successfully")
        else:
            print("No parameters changed")
            
    except Exception as e:
        print(f"❌ Failed to set parameters: {e}")


async def main():
    """Main function."""
    print("🚀 Bybit Auto Trading Test Script")
    print("==================================")
    
    # Check if we have API credentials
    try:
        from app.core.settings import settings
        
        if not settings.bybit_api_key.get_secret_value():
            print("❌ No Bybit API key found!")
            print("Please set BYBIT_API_KEY and BYBIT_API_SECRET in your .env file")
            return
        
        print(f"📡 Using {'TESTNET' if settings.bybit_testnet else 'MAINNET'}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Show main menu
    await interactive_menu()


if __name__ == "__main__":
    asyncio.run(main()) 