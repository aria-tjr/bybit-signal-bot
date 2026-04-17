#!/usr/bin/env python3
"""
Signal Integration Example

This example shows how to integrate your existing signal generation 
with the new Bybit auto trading system.

Modify this template to match your current signal format and processing.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.auto_trading import auto_trading_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class SignalIntegrator:
    """Integration layer between your signal system and auto trading."""
    
    def __init__(self):
        """Initialize the signal integrator."""
        self.auto_trading = auto_trading_service
        
        # Configure auto trading parameters
        self.trading_config = {
            "min_confidence": 0.65,  # Minimum confidence to execute
            "max_daily_trades": 12,  # Maximum trades per day
            "auto_trading_enabled": False  # Start disabled for safety
        }
        
    async def start(self):
        """Start the signal integration system."""
        try:
            print("🚀 Starting Signal Integration System...")
            
            # Configure auto trading parameters
            await self.auto_trading.set_trading_parameters(self.trading_config)
            
            # Note: Don't auto-start trading - let user decide
            print("✅ Signal integration system ready")
            print("⚠️  Auto trading is DISABLED by default")
            print("📝 Use enable_auto_trading() to start live trading")
            
        except Exception as e:
            logger.error("Failed to start signal integration", error=str(e))
            raise
    
    async def enable_auto_trading(self):
        """Enable auto trading (call this when ready to trade live)."""
        try:
            await self.auto_trading.start_auto_trading()
            print("✅ Auto trading ENABLED - Bot will execute signals")
        except Exception as e:
            logger.error("Failed to enable auto trading", error=str(e))
            raise
    
    async def disable_auto_trading(self):
        """Disable auto trading."""
        try:
            await self.auto_trading.stop_auto_trading()
            print("⛔ Auto trading DISABLED - Bot will not execute signals")
        except Exception as e:
            logger.error("Failed to disable auto trading", error=str(e))
            raise
    
    def convert_your_signal_format(self, your_signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert your existing signal format to the required format.
        
        Modify this method to match your current signal structure.
        """
        
        # Example: Your signal might look like this
        # your_signal = {
        #     "pair": "BTC-USDT",
        #     "action": "buy",
        #     "price": 95000,
        #     "sl": 94000,
        #     "tp": [96000, 97000, 98000],
        #     "score": 8.5,  # out of 10
        #     "time": "2024-01-01 12:00:00"
        # }
        
        # Convert to required format
        converted_signal = {
            "symbol": your_signal.get("pair", "").replace("-", ""),  # BTC-USDT -> BTCUSDT
            "direction": "LONG" if your_signal.get("action", "").lower() in ["buy", "long"] else "SHORT",
            "entry_price": float(your_signal.get("price", 0)),
            "stop_loss": float(your_signal.get("sl", 0)),
            "confidence": float(your_signal.get("score", 5)) / 10.0,  # Convert 0-10 to 0-1
            "timestamp": your_signal.get("time", datetime.utcnow().isoformat())
        }
        
        # Add take profits if available
        if "tp" in your_signal and isinstance(your_signal["tp"], list):
            for i, tp in enumerate(your_signal["tp"][:3], 1):  # Max 3 TPs
                converted_signal[f"tp{i}"] = float(tp)
        
        # Add leverage if available
        if "leverage" in your_signal:
            converted_signal["leverage"] = int(your_signal["leverage"])
        
        return converted_signal
    
    async def process_signal(self, your_signal: Dict[str, Any]) -> bool:
        """
        Process a signal from your existing system.
        
        Args:
            your_signal: Signal in your current format
            
        Returns:
            True if signal was executed, False otherwise
        """
        try:
            # Convert to required format
            converted_signal = self.convert_your_signal_format(your_signal)
            
            # Validate conversion
            if not converted_signal.get("symbol") or not converted_signal.get("direction"):
                logger.warning("Signal conversion failed", original=your_signal)
                return False
            
            logger.info("Processing signal", 
                       symbol=converted_signal["symbol"],
                       direction=converted_signal["direction"],
                       confidence=converted_signal["confidence"])
            
            # Execute through auto trading service
            executed = await self.auto_trading.process_signal(converted_signal)
            
            if executed:
                logger.info("Signal executed successfully", symbol=converted_signal["symbol"])
            else:
                logger.info("Signal not executed", symbol=converted_signal["symbol"])
            
            return executed
            
        except Exception as e:
            logger.error("Failed to process signal", error=str(e), signal=your_signal)
            return False
    
    async def process_signal_batch(self, signals: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Process multiple signals at once.
        
        Args:
            signals: List of signals in your format
            
        Returns:
            Dictionary with execution statistics
        """
        stats = {
            "total": len(signals),
            "executed": 0,
            "rejected": 0,
            "errors": 0
        }
        
        for signal in signals:
            try:
                executed = await self.process_signal(signal)
                if executed:
                    stats["executed"] += 1
                else:
                    stats["rejected"] += 1
            except Exception as e:
                stats["errors"] += 1
                logger.error("Error processing signal", error=str(e))
            
            # Small delay between signals
            await asyncio.sleep(0.5)
        
        logger.info("Batch processing complete", stats=stats)
        return stats
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current status of the integration system."""
        return await self.auto_trading.get_auto_trading_status()


# Example usage functions
async def example_single_signal():
    """Example: Process a single signal."""
    print("\n📊 Example: Single Signal Processing")
    
    integrator = SignalIntegrator()
    await integrator.start()
    
    # Example signal in your format
    your_signal = {
        "pair": "BTC-USDT",
        "action": "buy",
        "price": 95000,
        "sl": 94000,
        "tp": [96000, 97000, 98000],
        "score": 8.5,
        "time": datetime.utcnow().isoformat()
    }
    
    print(f"Original signal: {your_signal}")
    
    # Convert signal
    converted = integrator.convert_your_signal_format(your_signal)
    print(f"Converted signal: {converted}")
    
    # Process signal (won't execute unless auto trading is enabled)
    executed = await integrator.process_signal(your_signal)
    print(f"Signal executed: {executed}")


async def example_batch_signals():
    """Example: Process multiple signals."""
    print("\n📊 Example: Batch Signal Processing")
    
    integrator = SignalIntegrator()
    await integrator.start()
    
    # Example signals
    signals = [
        {
            "pair": "BTC-USDT",
            "action": "buy",
            "price": 95000,
            "sl": 94000,
            "score": 8.5
        },
        {
            "pair": "ETH-USDT", 
            "action": "sell",
            "price": 3500,
            "sl": 3600,
            "score": 7.0
        },
        {
            "pair": "SOL-USDT",
            "action": "buy", 
            "price": 200,
            "sl": 195,
            "score": 6.5
        }
    ]
    
    # Process batch
    stats = await integrator.process_signal_batch(signals)
    print(f"Batch processing results: {stats}")


async def example_live_integration():
    """Example: Live integration with auto trading enabled."""
    print("\n🚀 Example: Live Integration (TESTNET ONLY)")
    
    integrator = SignalIntegrator()
    await integrator.start()
    
    # Show current status
    status = await integrator.get_status()
    print(f"Auto trading enabled: {status['auto_trading_enabled']}")
    
    print("\n⚠️  WARNING: This will enable LIVE trading on testnet!")
    confirm = input("Type 'YES' to enable auto trading: ").strip()
    
    if confirm == "YES":
        # Enable auto trading
        await integrator.enable_auto_trading()
        
        # Process a test signal
        test_signal = {
            "pair": "BTC-USDT",
            "action": "buy",
            "price": 95000,
            "sl": 94500,  # Tight stop for testing
            "score": 7.5
        }
        
        print(f"\n📡 Processing test signal: {test_signal}")
        executed = await integrator.process_signal(test_signal)
        
        if executed:
            print("✅ Test signal executed successfully!")
            
            # Show position status
            status = await integrator.get_status()
            print(f"Active positions: {status['account_status']['total_positions']}")
            
        else:
            print("❌ Test signal was not executed")
        
        # Disable auto trading for safety
        await integrator.disable_auto_trading()
        
    else:
        print("Auto trading not enabled")


async def interactive_demo():
    """Interactive demo of the integration system."""
    integrator = SignalIntegrator()
    await integrator.start()
    
    while True:
        print("\n" + "="*50)
        print("📊 SIGNAL INTEGRATION DEMO")
        print("="*50)
        print("1. Test Single Signal Conversion")
        print("2. Test Batch Signal Processing")
        print("3. Show Current Status") 
        print("4. Enable Auto Trading (TESTNET)")
        print("5. Disable Auto Trading")
        print("6. Live Integration Demo")
        print("7. Exit")
        print()
        
        choice = input("Enter your choice (1-7): ").strip()
        
        try:
            if choice == "1":
                await example_single_signal()
            elif choice == "2":
                await example_batch_signals()
            elif choice == "3":
                status = await integrator.get_status()
                print(f"\nCurrent Status:")
                print(f"Auto trading: {status['auto_trading_enabled']}")
                print(f"Daily trades: {status['daily_trades']['current']}/{status['daily_trades']['limit']}")
                print(f"Active positions: {status['account_status']['total_positions']}")
            elif choice == "4":
                await integrator.enable_auto_trading()
            elif choice == "5":
                await integrator.disable_auto_trading()
            elif choice == "6":
                await example_live_integration()
            elif choice == "7":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    print("🔗 Signal Integration Example")
    print("============================")
    print("This example shows how to integrate your existing signals with auto trading.")
    print()
    
    try:
        # Run interactive demo
        asyncio.run(interactive_demo())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}") 