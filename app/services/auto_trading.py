"""
Automated Trading Service

Integrates signal processing with live trading execution.
Handles signal filtering, position management, and risk controls.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict

from ..core.logging import get_logger
from ..core.settings import settings
from .bybit_trading import trading_service
from .signal_processor import SignalProcessor
from .telegram import TelegramService

logger = get_logger(__name__)


class AutoTradingService:
    """Automated trading service that executes signals."""
    
    def __init__(self):
        """Initialize auto trading service."""
        self.signal_processor = SignalProcessor()
        self.telegram = TelegramService()
        
        # Trading configuration
        self.is_auto_trading_enabled = False
        self.min_signal_confidence = 0.6  # Minimum confidence to execute
        self.max_daily_trades = 10
        self.daily_trade_count = 0
        self.last_trade_reset = datetime.utcnow().date()
        
        # Signal tracking
        self.processed_signals = set()
        self.signal_history = []
        
        # Performance tracking
        self.session_stats = {
            "signals_received": 0,
            "signals_executed": 0,
            "positions_opened": 0,
            "positions_closed": 0,
            "total_pnl": 0.0
        }
        
        logger.info("Auto Trading Service initialized")
    
    async def start_auto_trading(self):
        """Start automated trading."""
        try:
            if not settings.enable_auto_trading:
                logger.warning("Global setting enable_auto_trading is False; auto trading cannot be started.")
                await self.telegram.send_message(
                    "⚠️ *Auto trading disabled by configuration*\n\nSet `ENABLE_AUTO_TRADING=true` in environment or settings to allow automated execution."
                )
                return
            # Start the trading service
            await trading_service.start_trading()
            
            # Enable auto trading
            self.is_auto_trading_enabled = True
            
            # Reset daily counters if needed
            self._reset_daily_counters_if_needed()
            
            await self.telegram.send_message(
                "🤖 **Auto Trading Started**\n\n"
                f"✅ Trading service online\n"
                f"💰 Account balance: ${trading_service.account_balance:,.2f}\n"
                f"📊 Max daily trades: {self.max_daily_trades}\n"
                f"🎯 Min confidence: {self.min_signal_confidence}\n"
                f"⚡ Ready to execute signals!"
            )
            
            logger.info("Auto trading started successfully")
            
        except Exception as e:
            logger.error("Failed to start auto trading", error=str(e))
            await self.telegram.send_message(
                f"❌ **Failed to start auto trading**\n\nError: {str(e)}"
            )
            raise
    
    async def stop_auto_trading(self):
        """Stop automated trading."""
        try:
            self.is_auto_trading_enabled = False
            
            # Get final status
            status = await trading_service.get_positions_status()
            
            await self.telegram.send_message(
                "🛑 **Auto Trading Stopped**\n\n"
                f"📊 Session stats:\n"
                f"• Signals received: {self.session_stats['signals_received']}\n"
                f"• Signals executed: {self.session_stats['signals_executed']}\n"
                f"• Active positions: {status['total_positions']}\n"
                f"• Unrealized PnL: ${status['total_unrealized_pnl']:,.2f}\n\n"
                f"⚠️ Auto trading disabled - manual control required"
            )
            
            logger.info("Auto trading stopped")
            
        except Exception as e:
            logger.error("Failed to stop auto trading", error=str(e))
    
    async def process_signal(self, signal: Dict[str, Any]) -> bool:
        """
        Process and potentially execute a trading signal.
        
        Args:
            signal: Trading signal dictionary
            
        Returns:
            True if signal was executed, False otherwise
        """
        if not self.is_auto_trading_enabled:
            logger.debug("Auto trading disabled, ignoring signal")
            return False
        
        try:
            # Update stats
            self.session_stats["signals_received"] += 1
            
            # Reset daily counters if needed
            self._reset_daily_counters_if_needed()
            
            # Check daily trade limit
            if self.daily_trade_count >= self.max_daily_trades:
                logger.warning("Daily trade limit reached", 
                             current=self.daily_trade_count,
                             limit=self.max_daily_trades)
                return False
            
            # Validate signal
            if not await self._validate_signal(signal):
                return False
            
            # Check for duplicate signals
            signal_id = self._generate_signal_id(signal)
            if signal_id in self.processed_signals:
                logger.debug("Duplicate signal ignored", signal_id=signal_id)
                return False
            
            # Enhanced signal processing
            processed_signal = await self._enhance_signal(signal)
            if not processed_signal:
                return False
            
            # Risk assessment
            risk_check = await self._assess_risk(processed_signal)
            if not risk_check["approved"]:
                logger.warning("Signal rejected by risk assessment", 
                             reason=risk_check["reason"])
                return False
            
            # Execute the signal
            position_id = await trading_service.execute_signal(processed_signal)
            
            if position_id:
                # Track executed signal
                self.processed_signals.add(signal_id)
                self.daily_trade_count += 1
                self.session_stats["signals_executed"] += 1
                self.session_stats["positions_opened"] += 1
                
                # Store signal history
                self.signal_history.append({
                    "timestamp": datetime.utcnow(),
                    "signal": processed_signal,
                    "position_id": position_id,
                    "risk_assessment": risk_check
                })
                
                # Send notification
                await self._send_execution_notification(processed_signal, position_id)
                
                logger.info("Signal executed successfully", 
                           symbol=processed_signal["symbol"],
                           position_id=position_id)
                
                return True
            else:
                logger.warning("Signal execution failed", 
                             symbol=processed_signal["symbol"])
                return False
                
        except Exception as e:
            logger.error("Failed to process signal", error=str(e))
            return False
    
    async def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate signal format and requirements."""
        required_fields = ["symbol", "direction", "entry_price", "stop_loss", "confidence"]
        
        for field in required_fields:
            if field not in signal:
                logger.warning("Missing required field in signal", field=field)
                return False
        
        # Check confidence threshold
        confidence = signal.get("confidence", 0)
        if confidence < self.min_signal_confidence:
            logger.debug("Signal confidence below threshold", 
                        confidence=confidence,
                        threshold=self.min_signal_confidence)
            return False
        
        # Validate symbol format
        symbol = signal["symbol"]
        if not symbol.endswith("USDT"):
            logger.warning("Invalid symbol format", symbol=symbol)
            return False
        
        # Validate direction
        direction = signal["direction"].upper()
        if direction not in ["LONG", "SHORT", "BUY", "SELL"]:
            logger.warning("Invalid direction", direction=direction)
            return False
        
        # Validate prices
        entry_price = signal["entry_price"]
        stop_loss = signal["stop_loss"]
        
        if entry_price <= 0 or stop_loss <= 0:
            logger.warning("Invalid price values", 
                         entry_price=entry_price,
                         stop_loss=stop_loss)
            return False
        
        return True
    
    async def _enhance_signal(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhance signal with additional analysis."""
        try:
            enhanced_signal = signal.copy()
            
            # Normalize direction
            direction = signal["direction"].upper()
            if direction in ["BUY", "LONG"]:
                enhanced_signal["direction"] = "LONG"
            else:
                enhanced_signal["direction"] = "SHORT"
            
            # Add leverage if not present
            if "leverage" not in enhanced_signal:
                enhanced_signal["leverage"] = min(settings.max_leverage, 20)
            
            # Generate take profit levels if not present
            if "take_profits" not in enhanced_signal and not any(key in enhanced_signal for key in ["tp1", "tp2", "tp3"]):
                enhanced_signal = await self._generate_take_profit_levels(enhanced_signal)
            
            # Add timestamp
            enhanced_signal["processed_at"] = datetime.utcnow().isoformat()
            
            # Add risk-reward ratio
            enhanced_signal["risk_reward_ratio"] = self._calculate_risk_reward(enhanced_signal)
            
            return enhanced_signal
            
        except Exception as e:
            logger.error("Failed to enhance signal", error=str(e))
            return None
    
    async def _generate_take_profit_levels(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Generate take profit levels based on risk-reward ratios."""
        entry_price = signal["entry_price"]
        stop_loss = signal["stop_loss"]
        direction = signal["direction"]
        
        # Calculate stop distance
        if direction == "LONG":
            stop_distance = (entry_price - stop_loss) / entry_price
            # Take profits at 1:1, 1:2, and 1:3 risk-reward ratios
            signal["tp1"] = entry_price * (1 + stop_distance * 1)
            signal["tp2"] = entry_price * (1 + stop_distance * 2)
            signal["tp3"] = entry_price * (1 + stop_distance * 3)
        else:  # SHORT
            stop_distance = (stop_loss - entry_price) / entry_price
            signal["tp1"] = entry_price * (1 - stop_distance * 1)
            signal["tp2"] = entry_price * (1 - stop_distance * 2)
            signal["tp3"] = entry_price * (1 - stop_distance * 3)
        
        return signal
    
    def _calculate_risk_reward(self, signal: Dict[str, Any]) -> float:
        """Calculate risk-reward ratio."""
        try:
            entry_price = signal["entry_price"]
            stop_loss = signal["stop_loss"]
            
            # Use first take profit for calculation
            take_profit = signal.get("tp1")
            if not take_profit:
                take_profits = signal.get("take_profits", [])
                take_profit = take_profits[0] if take_profits else None
            
            if not take_profit:
                return 0.0
            
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            
            return reward / risk if risk > 0 else 0.0
            
        except Exception:
            return 0.0
    
    async def _assess_risk(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for signal execution."""
        try:
            # Get current account status
            status = await trading_service.get_positions_status()
            
            # Check maximum positions
            if status["total_positions"] >= trading_service.max_positions:
                return {
                    "approved": False,
                    "reason": "Maximum positions reached"
                }
            
            # Check available balance
            required_margin = status["account_balance"] * 0.1  # Assume 10% margin per trade
            if required_margin > status["available_balance"]:
                return {
                    "approved": False,
                    "reason": "Insufficient margin"
                }
            
            # Check correlation with existing positions
            symbol = signal["symbol"]
            correlation_risk = await self._check_correlation_risk(symbol, status["positions"])
            if correlation_risk:
                return {
                    "approved": False,
                    "reason": "High correlation risk"
                }
            
            # Check risk-reward ratio
            risk_reward = signal.get("risk_reward_ratio", 0)
            if risk_reward < 1.0:  # Minimum 1:1 risk-reward
                return {
                    "approved": False,
                    "reason": f"Poor risk-reward ratio: {risk_reward:.2f}"
                }
            
            return {
                "approved": True,
                "reason": "Risk assessment passed",
                "risk_score": min(signal.get("confidence", 0.5) * risk_reward, 1.0)
            }
            
        except Exception as e:
            logger.error("Risk assessment failed", error=str(e))
            return {
                "approved": False,
                "reason": f"Risk assessment error: {str(e)}"
            }
    
    async def _check_correlation_risk(self, symbol: str, positions: List[Dict]) -> bool:
        """Check if symbol is too correlated with existing positions."""
        # Simple correlation check based on base asset
        base_asset = symbol.replace("USDT", "")
        
        # Define correlated groups
        correlations = {
            "BTC": ["BTC"],
            "ETH": ["ETH"],
            "BNB": ["BNB"],
            "LAYER1": ["SOL", "ADA", "DOT", "AVAX", "ATOM", "NEAR"],
            "DEFI": ["UNI", "AAVE", "COMP", "SUSHI", "CRV", "YFI"],
            "MEME": ["DOGE", "SHIB", "PEPE", "FLOKI"]
        }
        
        for group_name, group_assets in correlations.items():
            if base_asset in group_assets:
                # Check if we already have positions in this group
                for position in positions:
                    pos_symbol = position.get("symbol", "")
                    pos_base = pos_symbol.replace("USDT", "")
                    if pos_base in group_assets and pos_base != base_asset:
                        logger.warning("Correlation risk detected", 
                                     new_symbol=symbol,
                                     existing_symbol=pos_symbol,
                                     group=group_name)
                        return True
        
        return False
    
    def _generate_signal_id(self, signal: Dict[str, Any]) -> str:
        """Generate unique signal ID."""
        symbol = signal["symbol"]
        direction = signal["direction"]
        entry_price = signal["entry_price"]
        timestamp = signal.get("timestamp", datetime.utcnow().isoformat())
        
        return f"{symbol}_{direction}_{entry_price}_{timestamp[:19]}"
    
    def _reset_daily_counters_if_needed(self):
        """Reset daily counters if new day."""
        current_date = datetime.utcnow().date()
        if current_date != self.last_trade_reset:
            self.daily_trade_count = 0
            self.last_trade_reset = current_date
            logger.info("Daily trade counter reset")
    
    async def _send_execution_notification(self, signal: Dict[str, Any], position_id: str):
        """Send notification about signal execution."""
        try:
            symbol = signal["symbol"]
            direction = signal["direction"]
            entry_price = signal["entry_price"]
            stop_loss = signal["stop_loss"]
            confidence = signal.get("confidence", 0)
            leverage = signal.get("leverage", 1)
            risk_reward = signal.get("risk_reward_ratio", 0)
            
            message = (
                f"🚀 **Signal Executed**\n\n"
                f"📊 **{symbol}** - {direction}\n"
                f"💰 Entry: ${entry_price:,.4f}\n"
                f"🛑 Stop Loss: ${stop_loss:,.4f}\n"
                f"🎯 Take Profits:\n"
            )
            
            # Add take profit levels
            for i, tp_key in enumerate(["tp1", "tp2", "tp3"], 1):
                if tp_key in signal:
                    message += f"   • TP{i}: ${signal[tp_key]:,.4f}\n"
            
            message += (
                f"\n📈 Leverage: {leverage}x\n"
                f"🎯 Confidence: {confidence:.0%}\n"
                f"⚖️ Risk/Reward: 1:{risk_reward:.1f}\n"
                f"🆔 Position: `{position_id}`\n\n"
                f"Daily trades: {self.daily_trade_count}/{self.max_daily_trades}"
            )
            
            await self.telegram.send_message(message)
            
        except Exception as e:
            logger.error("Failed to send execution notification", error=str(e))
    
    async def get_auto_trading_status(self) -> Dict[str, Any]:
        """Get current auto trading status."""
        trading_status = await trading_service.get_positions_status()
        
        return {
            "auto_trading_enabled": self.is_auto_trading_enabled,
            "trading_service_enabled": trading_service.is_trading_enabled,
            "daily_trades": {
                "current": self.daily_trade_count,
                "limit": self.max_daily_trades,
                "reset_date": self.last_trade_reset.isoformat()
            },
            "session_stats": self.session_stats,
            "signal_filters": {
                "min_confidence": self.min_signal_confidence,
                "processed_signals_count": len(self.processed_signals)
            },
            "account_status": trading_status,
            "last_update": datetime.utcnow().isoformat()
        }
    
    async def set_trading_parameters(self, parameters: Dict[str, Any]):
        """Update trading parameters."""
        try:
            if "min_confidence" in parameters:
                self.min_signal_confidence = max(0.0, min(1.0, parameters["min_confidence"]))
            
            if "max_daily_trades" in parameters:
                self.max_daily_trades = max(1, min(50, parameters["max_daily_trades"]))
            
            if "auto_trading_enabled" in parameters:
                if parameters["auto_trading_enabled"] and not self.is_auto_trading_enabled:
                    await self.start_auto_trading()
                elif not parameters["auto_trading_enabled"] and self.is_auto_trading_enabled:
                    await self.stop_auto_trading()
            
            logger.info("Trading parameters updated", parameters=parameters)
            
        except Exception as e:
            logger.error("Failed to update trading parameters", error=str(e))
            raise


# Global auto trading service instance
auto_trading_service = AutoTradingService() 