"""
Bybit Trading Service for Live Order Execution

Provides comprehensive trading functionality including:
- Order placement and management
- Position tracking and monitoring
- Risk management integration
- Real-time PnL calculation
- Auto trade execution from signals
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from dataclasses import dataclass, asdict
from enum import Enum

from pybit.unified_trading import HTTP
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.logging import get_logger
from ..core.settings import settings
from ..logic.risk import RiskManager
from ..data.rest import rest_client

logger = get_logger(__name__)


class OrderType(Enum):
    """Order types supported by Bybit."""
    MARKET = "Market"
    LIMIT = "Limit"
    STOP_MARKET = "StopMarket"
    STOP_LIMIT = "StopLimit"
    TAKE_PROFIT_MARKET = "TakeProfitMarket"
    TAKE_PROFIT_LIMIT = "TakeProfitLimit"


class OrderSide(Enum):
    """Order sides."""
    BUY = "Buy"
    SELL = "Sell"


class PositionMode(Enum):
    """Position modes."""
    HEDGE = "BothSide"
    ONE_WAY = "MergedSingle"


class OrderStatus(Enum):
    """Order status."""
    NEW = "New"
    PARTIALLY_FILLED = "PartiallyFilled"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"


@dataclass
class TradingPosition:
    """Represents an active trading position."""
    symbol: str
    side: str  # Buy/Sell
    size: float
    entry_price: float
    mark_price: float
    leverage: int
    unrealized_pnl: float
    percentage: float
    created_time: datetime
    risk_amount: float = 0.0
    margin_required: float = 0.0
    stop_loss_order_id: Optional[str] = None
    take_profit_orders: List[str] = None
    
    def __post_init__(self):
        if self.take_profit_orders is None:
            self.take_profit_orders = []


@dataclass
class TradingOrder:
    """Represents a trading order."""
    order_id: str
    symbol: str
    side: str
    order_type: str
    qty: float
    price: Optional[float]
    status: str
    created_time: datetime
    updated_time: datetime
    filled_qty: float = 0.0
    avg_price: float = 0.0


class BybitTradingService:
    """Comprehensive Bybit trading service for live execution."""
    
    def __init__(self):
        """Initialize trading service."""
        self.client = HTTP(
            testnet=settings.bybit_testnet,
            api_key=settings.bybit_api_key.get_secret_value(),
            api_secret=settings.bybit_api_secret.get_secret_value(),
        )
        self.risk_manager = RiskManager()
        
        # Position tracking
        self.active_positions: Dict[str, TradingPosition] = {}
        self.active_orders: Dict[str, TradingOrder] = {}
        
        # Account info
        self.account_balance = 0.0
        self.available_balance = 0.0
        self.last_balance_update = None
        
        # Trading state
        self.is_trading_enabled = False
        self.max_positions = settings.max_concurrent_jobs if hasattr(settings, 'max_concurrent_jobs') else 5
        
        logger.info("Bybit Trading Service initialized", testnet=settings.bybit_testnet)
    
    async def start_trading(self):
        """Start the trading service."""
        try:
            # Verify API connection
            await self._verify_api_connection()
            
            # Update account balance
            await self.update_account_balance()
            
            # Load existing positions
            await self._load_existing_positions()
            
            self.is_trading_enabled = True
            logger.info("Trading service started successfully", 
                       balance=self.account_balance, 
                       positions=len(self.active_positions))
            
        except Exception as e:
            logger.error("Failed to start trading service", error=str(e))
            raise
    
    async def stop_trading(self):
        """Stop trading and close all positions."""
        self.is_trading_enabled = False
        
        # Cancel all open orders
        await self._cancel_all_orders()
        
        # Optionally close all positions (commented for safety)
        # await self._close_all_positions()
        
        logger.info("Trading service stopped")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _verify_api_connection(self):
        """Verify API connection and permissions."""
        try:
            response = self.client.get_wallet_balance(accountType="UNIFIED")
            
            if response["retCode"] != 0:
                raise Exception(f"API connection failed: {response['retMsg']}")
            
            logger.info("API connection verified successfully")
            
        except Exception as e:
            logger.error("API connection verification failed", error=str(e))
            raise
    
    async def update_account_balance(self):
        """Update account balance information."""
        try:
            response = self.client.get_wallet_balance(accountType="UNIFIED")
            
            if response["retCode"] != 0:
                raise Exception(f"Failed to get wallet balance: {response['retMsg']}")
            
            wallet_data = response["result"]["list"][0] if response["result"]["list"] else {}
            coin_data = next((coin for coin in wallet_data.get("coin", []) if coin["coin"] == "USDT"), {})
            
            self.account_balance = float(coin_data.get("walletBalance", 0))
            self.available_balance = float(coin_data.get("availableToWithdraw", 0))
            self.last_balance_update = datetime.utcnow()
            
            logger.debug("Account balance updated", 
                        balance=self.account_balance, 
                        available=self.available_balance)
            
        except Exception as e:
            logger.error("Failed to update account balance", error=str(e))
            raise
    
    async def execute_signal(self, signal: Dict[str, Any]) -> Optional[str]:
        """
        Execute a trading signal.
        
        Args:
            signal: Trading signal dictionary containing:
                - symbol: Trading pair
                - direction: LONG/SHORT
                - entry_price: Entry price
                - stop_loss: Stop loss price
                - take_profits: List of take profit levels
                - leverage: Leverage to use
                - confidence: Signal confidence (0-1)
                
        Returns:
            Position ID if successful, None otherwise
        """
        if not settings.enable_auto_trading:
            logger.warning("Auto trading globally disabled - execute_signal aborted", symbol=signal.get("symbol"))
            return None
        
        if not self.is_trading_enabled:
            logger.warning("Trading is disabled, skipping signal", symbol=signal.get("symbol"))
            return None
        
        if len(self.active_positions) >= self.max_positions:
            logger.warning("Maximum positions reached", 
                          current=len(self.active_positions), 
                          max=self.max_positions)
            return None
        
        symbol = signal.get("symbol")
        direction = signal.get("direction")
        confidence = signal.get("confidence", 0.5)
        
        try:
            # Update account balance
            await self.update_account_balance()
            
            # Calculate position size
            position_info = await self._calculate_position_size(signal)
            if not position_info:
                return None

            # Store risk data for later use
            signal["risk_amount"] = position_info["risk_amount"]
            signal["margin_required"] = position_info["margin_required"]

            # Portfolio heat check BEFORE opening new position
            open_positions = [
                {
                    "risk_amount": pos.risk_amount,
                    "margin_required": pos.margin_required if hasattr(pos, "margin_required") else 0.0,
                }
                for pos in self.active_positions.values()
            ]
            # Include the prospective new position
            open_positions.append(
                {
                    "risk_amount": position_info["risk_amount"],
                    "margin_required": position_info["margin_required"],
                }
            )
            heat_metrics = self.risk_manager.calculate_portfolio_heat(
                open_positions, self.account_balance
            )
            if heat_metrics.get("heat_level") == "CRITICAL":
                logger.warning(
                    "Portfolio heat critical, skipping new trade", heat=heat_metrics
                )
                return None

            # Set leverage
            await self._set_leverage(symbol, signal.get("leverage", 10))
            
            # Place market entry order
            order_id = await self._place_market_order(
                symbol=symbol,
                side="Buy" if direction == "LONG" else "Sell",
                qty=position_info["position_size"]
            )
            
            if not order_id:
                logger.error("Failed to place entry order", symbol=symbol)
                return None
            
            # Wait for order to fill and create position
            position = await self._wait_for_order_fill(order_id, signal)
            if not position:
                return None
            
            # Place stop loss and take profit orders
            await self._place_risk_management_orders(position, signal)
            
            # Track position
            position_id = f"{symbol}_{int(time.time())}"
            self.active_positions[position_id] = position
            
            logger.info("Signal executed successfully", 
                       symbol=symbol, 
                       direction=direction,
                       size=position_info["position_size"],
                       position_id=position_id)
            
            return position_id
            
        except Exception as e:
            logger.error("Failed to execute signal", symbol=symbol, error=str(e))
            return None
    
    async def _calculate_position_size(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate position size based on risk management."""
        try:
            symbol = signal["symbol"]
            entry_price = signal["entry_price"]
            stop_loss = signal["stop_loss"]
            leverage = signal.get("leverage", 10)
            
            # Get current ticker for precise pricing
            ticker = await rest_client.get_ticker(symbol)
            if not ticker:
                logger.error("Failed to get ticker data", symbol=symbol)
                return None
            
            current_price = float(ticker.get("lastPrice", entry_price))
            
            # Calculate position size using risk management
            risk_percent = 1.0  # Risk 1% of account per trade
            position_calc = self.risk_manager.calculate_position_size(
                account_balance=self.available_balance,
                entry_price=current_price,
                stop_loss=stop_loss,
                risk_percent=risk_percent,
                leverage=leverage
            )
            
            # Get minimum order size
            min_order_size = await self._get_min_order_size(symbol)
            if position_calc["position_size"] < min_order_size:
                logger.warning("Calculated position size below minimum", 
                              calculated=position_calc["position_size"],
                              minimum=min_order_size)
                return None
            
            # Check if we have sufficient margin
            if position_calc["margin_required"] > self.available_balance * 0.8:
                logger.warning("Insufficient margin for position", 
                              required=position_calc["margin_required"],
                              available=self.available_balance)
                return None
            
            return position_calc
            
        except Exception as e:
            logger.error("Failed to calculate position size", error=str(e))
            return None
    
    async def _place_market_order(self, symbol: str, side: str, qty: float) -> Optional[str]:
        """Place a market order."""
        try:
            # Format quantity to appropriate precision
            formatted_qty = await self._format_quantity(symbol, qty)
            
            response = self.client.place_order(
                category="linear",  # For futures trading
                symbol=symbol,
                side=side,
                orderType="Market",
                qty=str(formatted_qty),
                timeInForce="IOC"  # Immediate or Cancel
            )
            
            if response["retCode"] != 0:
                logger.error("Market order failed", 
                           symbol=symbol, 
                           error=response["retMsg"])
                return None
            
            order_id = response["result"]["orderId"]
            logger.info("Market order placed", 
                       symbol=symbol, 
                       side=side, 
                       qty=formatted_qty,
                       order_id=order_id)
            
            return order_id
            
        except Exception as e:
            logger.error("Failed to place market order", symbol=symbol, error=str(e))
            return None
    
    async def _place_conditional_order(self, symbol: str, side: str, qty: float, 
                                     trigger_price: float, order_type: str) -> Optional[str]:
        """Place a conditional order (stop loss or take profit)."""
        try:
            formatted_qty = await self._format_quantity(symbol, qty)
            formatted_price = await self._format_price(symbol, trigger_price)
            
            response = self.client.place_order(
                category="linear",
                symbol=symbol,
                side=side,
                orderType=order_type,
                qty=str(formatted_qty),
                triggerPrice=str(formatted_price),
                timeInForce="GTC"  # Good Till Cancelled
            )
            
            if response["retCode"] != 0:
                logger.error("Conditional order failed", 
                           symbol=symbol, 
                           order_type=order_type,
                           error=response["retMsg"])
                return None
            
            order_id = response["result"]["orderId"]
            logger.debug("Conditional order placed", 
                        symbol=symbol, 
                        order_type=order_type,
                        trigger_price=formatted_price,
                        order_id=order_id)
            
            return order_id
            
        except Exception as e:
            logger.error("Failed to place conditional order", symbol=symbol, error=str(e))
            return None
    
    async def _set_leverage(self, symbol: str, leverage: int):
        """Set leverage for a symbol."""
        try:
            response = self.client.set_leverage(
                category="linear",
                symbol=symbol,
                buyLeverage=str(leverage),
                sellLeverage=str(leverage)
            )
            
            if response["retCode"] != 0:
                logger.warning("Failed to set leverage", 
                             symbol=symbol, 
                             leverage=leverage,
                             error=response["retMsg"])
            else:
                logger.debug("Leverage set", symbol=symbol, leverage=leverage)
                
        except Exception as e:
            logger.error("Failed to set leverage", symbol=symbol, error=str(e))
    
    async def _wait_for_order_fill(self, order_id: str, signal: Dict[str, Any], 
                                   timeout: int = 30) -> Optional[TradingPosition]:
        """Wait for order to fill and create position object."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check order status
                response = self.client.get_open_orders(
                    category="linear",
                    orderId=order_id
                )
                
                if response["retCode"] != 0:
                    logger.error("Failed to check order status", order_id=order_id)
                    return None
                
                orders = response["result"]["list"]
                if not orders:
                    # Order not found in open orders, check if it's filled
                    break
                
                order = orders[0]
                if order["orderStatus"] in ["Filled", "PartiallyFilled"]:
                    break
                elif order["orderStatus"] in ["Cancelled", "Rejected"]:
                    logger.error("Order was cancelled or rejected", 
                               order_id=order_id, 
                               status=order["orderStatus"])
                    return None
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error("Error checking order status", order_id=order_id, error=str(e))
                return None
        
        # Get filled order details and position
        try:
            # Get position information
            response = self.client.get_positions(
                category="linear",
                symbol=signal["symbol"]
            )
            
            if response["retCode"] != 0:
                logger.error("Failed to get position", symbol=signal["symbol"])
                return None
            
            positions = response["result"]["list"]
            position_data = None
            
            for pos in positions:
                if float(pos["size"]) > 0:  # Active position
                    position_data = pos
                    break
            
            if not position_data:
                logger.error("No active position found after order fill", symbol=signal["symbol"])
                return None
            
            # Create position object
            position = TradingPosition(
                symbol=signal["symbol"],
                side=position_data["side"],
                size=float(position_data["size"]),
                entry_price=float(position_data["avgPrice"]),
                mark_price=float(position_data["markPrice"]),
                leverage=int(position_data["leverage"]),
                unrealized_pnl=float(position_data["unrealisedPnl"]),
                percentage=float(position_data["unrealisedPnl"]) / float(position_data["positionValue"]) * 100,
                created_time=datetime.utcnow(),
                risk_amount=signal.get("risk_amount", 0.0),
                margin_required=signal.get("margin_required", 0.0)
            )
            
            return position
            
        except Exception as e:
            logger.error("Failed to create position object", error=str(e))
            return None
    
    async def _place_risk_management_orders(self, position: TradingPosition, signal: Dict[str, Any]):
        """Place stop loss and take profit orders for a position."""
        try:
            symbol = position.symbol
            side = "Sell" if position.side == "Buy" else "Buy"  # Opposite side to close
            qty = position.size
            
            # Place stop loss
            stop_loss_price = signal.get("stop_loss")
            if stop_loss_price:
                stop_order_id = await self._place_conditional_order(
                    symbol=symbol,
                    side=side,
                    qty=qty,
                    trigger_price=stop_loss_price,
                    order_type="StopMarket"
                )
                position.stop_loss_order_id = stop_order_id
            
            # Place take profit orders
            take_profits = signal.get("take_profits", [])
            if not take_profits and "tp1" in signal:
                # Extract from individual TP fields
                take_profits = []
                for tp_key in ["tp1", "tp2", "tp3"]:
                    if tp_key in signal and signal[tp_key]:
                        take_profits.append(signal[tp_key])
            
            for i, tp_price in enumerate(take_profits):
                if tp_price:
                    # Use partial quantities for multiple TPs
                    tp_qty = qty / len(take_profits) if len(take_profits) > 1 else qty
                    
                    tp_order_id = await self._place_conditional_order(
                        symbol=symbol,
                        side=side,
                        qty=tp_qty,
                        trigger_price=tp_price,
                        order_type="TakeProfitMarket"
                    )
                    
                    if tp_order_id:
                        position.take_profit_orders.append(tp_order_id)
            
            logger.info("Risk management orders placed", 
                       symbol=symbol,
                       stop_loss=stop_loss_price,
                       take_profits=len(position.take_profit_orders))
            
        except Exception as e:
            logger.error("Failed to place risk management orders", error=str(e))
    
    async def _load_existing_positions(self):
        """Load existing positions from exchange."""
        try:
            response = self.client.get_positions(category="linear")
            
            if response["retCode"] != 0:
                logger.error("Failed to load positions", error=response["retMsg"])
                return
            
            positions = response["result"]["list"]
            
            for pos_data in positions:
                if float(pos_data["size"]) > 0:  # Active position
                    position = TradingPosition(
                        symbol=pos_data["symbol"],
                        side=pos_data["side"],
                        size=float(pos_data["size"]),
                        entry_price=float(pos_data["avgPrice"]),
                        mark_price=float(pos_data["markPrice"]),
                        leverage=int(pos_data["leverage"]),
                        unrealized_pnl=float(pos_data["unrealisedPnl"]),
                        percentage=float(pos_data["unrealisedPnl"]) / float(pos_data["positionValue"]) * 100,
                        created_time=datetime.utcnow()  # Approximate
                    )
                    
                    position_id = f"{position.symbol}_{int(time.time())}"
                    self.active_positions[position_id] = position
            
            logger.info("Loaded existing positions", count=len(self.active_positions))
            
        except Exception as e:
            logger.error("Failed to load existing positions", error=str(e))
    
    async def _cancel_all_orders(self):
        """Cancel all open orders."""
        try:
            response = self.client.get_open_orders(category="linear")
            
            if response["retCode"] != 0:
                logger.error("Failed to get open orders", error=response["retMsg"])
                return
            
            orders = response["result"]["list"]
            
            for order in orders:
                try:
                    cancel_response = self.client.cancel_order(
                        category="linear",
                        symbol=order["symbol"],
                        orderId=order["orderId"]
                    )
                    
                    if cancel_response["retCode"] == 0:
                        logger.info("Order cancelled", order_id=order["orderId"])
                    
                except Exception as e:
                    logger.error("Failed to cancel order", 
                               order_id=order["orderId"], 
                               error=str(e))
            
        except Exception as e:
            logger.error("Failed to cancel all orders", error=str(e))
    
    async def get_positions_status(self) -> Dict[str, Any]:
        """Get current positions status."""
        await self.update_account_balance()
        
        total_unrealized_pnl = 0.0
        total_position_value = 0.0
        
        for position in self.active_positions.values():
            # Update position with current market price
            try:
                ticker = await rest_client.get_ticker(position.symbol)
                if ticker:
                    current_price = float(ticker.get("lastPrice", position.mark_price))
                    
                    # Calculate current PnL
                    if position.side == "Buy":
                        pnl = (current_price - position.entry_price) / position.entry_price * 100
                    else:
                        pnl = (position.entry_price - current_price) / position.entry_price * 100
                    
                    position.percentage = pnl * position.leverage
                    position.unrealized_pnl = pnl * position.leverage * (position.size * position.entry_price / 100)
                    position.mark_price = current_price
                    
                    total_unrealized_pnl += position.unrealized_pnl
                    total_position_value += position.size * position.entry_price
                    
            except Exception as e:
                logger.error("Failed to update position", symbol=position.symbol, error=str(e))
        
        return {
            "account_balance": self.account_balance,
            "available_balance": self.available_balance,
            "total_positions": len(self.active_positions),
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_position_value": total_position_value,
            "positions": [asdict(pos) for pos in self.active_positions.values()],
            "is_trading_enabled": self.is_trading_enabled,
            "last_update": datetime.utcnow().isoformat()
        }
    
    async def close_position(self, position_id: str, reason: str = "manual") -> bool:
        """Close a specific position."""
        if position_id not in self.active_positions:
            logger.warning("Position not found", position_id=position_id)
            return False
        
        position = self.active_positions[position_id]
        
        try:
            # Place market order to close position
            close_side = "Sell" if position.side == "Buy" else "Buy"
            
            order_id = await self._place_market_order(
                symbol=position.symbol,
                side=close_side,
                qty=position.size
            )
            
            if order_id:
                # Cancel associated risk management orders
                if position.stop_loss_order_id:
                    await self._cancel_order(position.stop_loss_order_id)
                
                for tp_order_id in position.take_profit_orders:
                    await self._cancel_order(tp_order_id)
                
                # Remove position
                del self.active_positions[position_id]
                
                logger.info("Position closed", 
                           symbol=position.symbol,
                           reason=reason,
                           final_pnl=position.unrealized_pnl)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to close position", position_id=position_id, error=str(e))
            return False
    
    async def _cancel_order(self, order_id: str) -> bool:
        """Cancel a specific order."""
        try:
            response = self.client.cancel_all_orders(category="linear")
            
            if response["retCode"] == 0:
                logger.debug("Order cancelled", order_id=order_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to cancel order", order_id=order_id, error=str(e))
            return False
    
    async def _get_min_order_size(self, symbol: str) -> float:
        """Get minimum order size for a symbol."""
        try:
            response = self.client.get_instruments_info(category="linear", symbol=symbol)
            
            if response["retCode"] != 0:
                return 0.001  # Default fallback
            
            instruments = response["result"]["list"]
            if instruments:
                lot_size_filter = instruments[0].get("lotSizeFilter", {})
                min_order_qty = float(lot_size_filter.get("minOrderQty", 0.001))
                return min_order_qty
            
            return 0.001
            
        except Exception as e:
            logger.error("Failed to get min order size", symbol=symbol, error=str(e))
            return 0.001
    
    async def _format_quantity(self, symbol: str, qty: float) -> float:
        """Format quantity to exchange precision."""
        try:
            # Get tick size info
            response = self.client.get_instruments_info(category="linear", symbol=symbol)
            
            if response["retCode"] != 0:
                return round(qty, 3)  # Default precision
            
            instruments = response["result"]["list"]
            if instruments:
                lot_size_filter = instruments[0].get("lotSizeFilter", {})
                qty_step = float(lot_size_filter.get("qtyStep", 0.001))
                
                # Round down to nearest step
                formatted_qty = float(Decimal(str(qty)) // Decimal(str(qty_step)) * Decimal(str(qty_step)))
                return formatted_qty
            
            return round(qty, 3)
            
        except Exception as e:
            logger.error("Failed to format quantity", symbol=symbol, error=str(e))
            return round(qty, 3)
    
    async def _format_price(self, symbol: str, price: float) -> float:
        """Format price to exchange precision."""
        try:
            response = self.client.get_instruments_info(category="linear", symbol=symbol)
            
            if response["retCode"] != 0:
                return round(price, 2)  # Default precision
            
            instruments = response["result"]["list"]
            if instruments:
                price_filter = instruments[0].get("priceFilter", {})
                tick_size = float(price_filter.get("tickSize", 0.01))
                
                # Round to nearest tick
                formatted_price = round(price / tick_size) * tick_size
                return formatted_price
            
            return round(price, 2)
            
        except Exception as e:
            logger.error("Failed to format price", symbol=symbol, error=str(e))
            return round(price, 2)


# Global trading service instance
trading_service = BybitTradingService()