"""
Enhanced Portfolio Management System

Provides advanced portfolio tracking, risk management, and performance analytics.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio

from ..core.logging import get_logger
from ..core.settings import settings

logger = get_logger(__name__)


class Position:
    """Represents a single trading position."""
    
    def __init__(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        size: float,
        leverage: int,
        entry_time: datetime,
        stop_loss: float,
        take_profits: List[float],
        signal_confidence: float
    ):
        self.symbol = symbol
        self.direction = direction  # LONG/SHORT
        self.entry_price = entry_price
        self.size = size
        self.leverage = leverage
        self.entry_time = entry_time
        self.stop_loss = stop_loss
        self.take_profits = take_profits
        self.signal_confidence = signal_confidence
        
        # Position tracking
        self.current_price = entry_price
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0
        self.max_profit = 0.0
        self.max_loss = 0.0
        self.tp_hits = []
        self.is_active = True
        
        # Performance metrics
        self.price_history = deque(maxlen=1000)
        self.pnl_history = deque(maxlen=1000)
        
    def update_price(self, current_price: float):
        """Update position with current market price."""
        self.current_price = current_price
        
        # Calculate unrealized PNL
        if self.direction == "LONG":
            pnl_pct = ((current_price - self.entry_price) / self.entry_price) * 100
        else:  # SHORT
            pnl_pct = ((self.entry_price - current_price) / self.entry_price) * 100
            
        self.unrealized_pnl = pnl_pct * self.leverage
        
        # Update max profit/loss
        if self.unrealized_pnl > self.max_profit:
            self.max_profit = self.unrealized_pnl
        if self.unrealized_pnl < self.max_loss:
            self.max_loss = self.unrealized_pnl
            
        # Store history
        self.price_history.append({
            'timestamp': datetime.utcnow(),
            'price': current_price,
            'pnl': self.unrealized_pnl
        })
        
    def check_exit_conditions(self) -> Optional[Dict[str, Any]]:
        """Check if position should be closed."""
        # Stop loss check
        if self.direction == "LONG" and self.current_price <= self.stop_loss:
            return {
                'type': 'stop_loss',
                'price': self.current_price,
                'pnl': self.unrealized_pnl
            }
        elif self.direction == "SHORT" and self.current_price >= self.stop_loss:
            return {
                'type': 'stop_loss',
                'price': self.current_price,
                'pnl': self.unrealized_pnl
            }
            
        # Take profit checks
        for i, tp in enumerate(self.take_profits):
            if i not in self.tp_hits:
                if (self.direction == "LONG" and self.current_price >= tp) or \
                   (self.direction == "SHORT" and self.current_price <= tp):
                    return {
                        'type': 'take_profit',
                        'level': i + 1,
                        'price': self.current_price,
                        'pnl': self.unrealized_pnl
                    }
                    
        return None
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get position performance metrics."""
        duration = (datetime.utcnow() - self.entry_time).total_seconds() / 3600
        
        return {
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'size': self.size,
            'leverage': self.leverage,
            'unrealized_pnl': self.unrealized_pnl,
            'max_profit': self.max_profit,
            'max_loss': self.max_loss,
            'duration_hours': round(duration, 2),
            'signal_confidence': self.signal_confidence,
            'tp_hits': len(self.tp_hits),
            'is_active': self.is_active
        }


class PortfolioManager:
    """Advanced portfolio management and analytics."""
    
    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.correlation_matrix = pd.DataFrame()
        self.price_data = defaultdict(deque)
        
        # Portfolio metrics
        self.total_pnl = 0.0
        self.total_realized_pnl = 0.0
        self.total_unrealized_pnl = 0.0
        self.max_drawdown = 0.0
        self.portfolio_high_water_mark = 0.0
        
        # Risk limits
        self.max_portfolio_risk = 10.0  # % of portfolio
        self.max_correlation_exposure = 60.0  # % to correlated assets
        self.max_positions = 10
        
    async def add_position(self, position: Position) -> bool:
        """Add a new position to the portfolio."""
        try:
            # Check position limits
            if len(self.positions) >= self.max_positions:
                logger.warning("Maximum positions reached", 
                             current=len(self.positions), max=self.max_positions)
                return False
                
            # Check correlation risk
            if not await self._check_correlation_risk(position.symbol):
                logger.warning("Correlation risk too high for new position",
                             symbol=position.symbol)
                return False
                
            # Add position
            position_id = f"{position.symbol}_{position.entry_time.isoformat()}"
            self.positions[position_id] = position
            
            logger.info("Position added to portfolio",
                       symbol=position.symbol,
                       direction=position.direction,
                       size=position.size)
            
            return True
            
        except Exception as e:
            logger.error("Failed to add position", error=str(e))
            return False
            
    async def close_position(self, position_id: str, exit_price: float, reason: str):
        """Close a position and update portfolio metrics."""
        try:
            if position_id not in self.positions:
                logger.warning("Position not found", position_id=position_id)
                return
                
            position = self.positions[position_id]
            position.update_price(exit_price)
            position.is_active = False
            
            # Calculate final PNL
            final_pnl = position.unrealized_pnl
            position.realized_pnl = final_pnl
            
            # Update portfolio totals
            self.total_realized_pnl += final_pnl
            
            # Move to closed positions
            self.closed_positions.append(position)
            del self.positions[position_id]
            
            logger.info("Position closed",
                       symbol=position.symbol,
                       pnl=final_pnl,
                       reason=reason)
                       
        except Exception as e:
            logger.error("Failed to close position", error=str(e))
            
    async def update_all_positions(self, price_data: Dict[str, float]):
        """Update all positions with current market prices."""
        try:
            total_unrealized = 0.0
            
            for position_id, position in self.positions.items():
                symbol = position.symbol
                if symbol in price_data:
                    position.update_price(price_data[symbol])
                    total_unrealized += position.unrealized_pnl
                    
                    # Store price data for correlation analysis
                    self.price_data[symbol].append({
                        'timestamp': datetime.utcnow(),
                        'price': price_data[symbol]
                    })
                    
                    # Check exit conditions
                    exit_signal = position.check_exit_conditions()
                    if exit_signal:
                        await self.close_position(
                            position_id, 
                            position.current_price,
                            exit_signal['type']
                        )
                        
            self.total_unrealized_pnl = total_unrealized
            self.total_pnl = self.total_realized_pnl + total_unrealized
            
            # Update drawdown
            await self._update_drawdown_metrics()
            
        except Exception as e:
            logger.error("Failed to update positions", error=str(e))
            
    async def _check_correlation_risk(self, new_symbol: str) -> bool:
        """Check if adding new symbol would exceed correlation limits."""
        try:
            if len(self.positions) == 0:
                return True
                
            # Get current portfolio symbols
            current_symbols = [pos.symbol for pos in self.positions.values()]
            all_symbols = current_symbols + [new_symbol]
            
            # Calculate correlation matrix if we have enough data
            if len(all_symbols) < 2:
                return True
                
            correlation_risk = await self._calculate_correlation_exposure(all_symbols)
            
            return correlation_risk <= self.max_correlation_exposure
            
        except Exception as e:
            logger.error("Correlation risk check failed", error=str(e))
            return True  # Allow position if check fails
            
    async def _calculate_correlation_exposure(self, symbols: List[str]) -> float:
        """Calculate portfolio exposure to correlated assets."""
        try:
            # This is a simplified correlation calculation
            # In production, you'd use proper statistical correlation
            
            # Group symbols by base asset (e.g., BTC, ETH, etc.)
            base_assets = defaultdict(list)
            for symbol in symbols:
                base = symbol.replace('USDT', '').replace('USDC', '')[:3]
                base_assets[base].append(symbol)
                
            # Calculate exposure to largest correlated group
            max_exposure = 0.0
            total_positions = len(symbols)
            
            for base, group_symbols in base_assets.items():
                if len(group_symbols) > 1:
                    exposure = (len(group_symbols) / total_positions) * 100
                    max_exposure = max(max_exposure, exposure)
                    
            return max_exposure
            
        except Exception as e:
            logger.error("Correlation calculation failed", error=str(e))
            return 0.0
            
    async def _update_drawdown_metrics(self):
        """Update portfolio drawdown metrics."""
        try:
            current_portfolio_value = self.total_pnl
            
            # Update high water mark
            if current_portfolio_value > self.portfolio_high_water_mark:
                self.portfolio_high_water_mark = current_portfolio_value
                
            # Calculate current drawdown
            current_drawdown = ((self.portfolio_high_water_mark - current_portfolio_value) / 
                              max(abs(self.portfolio_high_water_mark), 1)) * 100
                              
            # Update max drawdown
            if current_drawdown > self.max_drawdown:
                self.max_drawdown = current_drawdown
                
        except Exception as e:
            logger.error("Drawdown calculation failed", error=str(e))
            
    def get_portfolio_metrics(self) -> Dict[str, Any]:
        """Get comprehensive portfolio performance metrics."""
        try:
            active_positions = len(self.positions)
            total_positions = len(self.closed_positions) + active_positions
            
            # Calculate win rate
            winning_trades = sum(1 for pos in self.closed_positions if pos.realized_pnl > 0)
            total_closed = len(self.closed_positions)
            win_rate = (winning_trades / total_closed * 100) if total_closed > 0 else 0
            
            # Calculate average metrics
            if self.closed_positions:
                avg_profit = np.mean([pos.realized_pnl for pos in self.closed_positions])
                avg_duration = np.mean([
                    (pos.entry_time - datetime.utcnow()).total_seconds() / 3600 
                    for pos in self.closed_positions
                ])
            else:
                avg_profit = 0.0
                avg_duration = 0.0
                
            # Portfolio risk metrics
            portfolio_heat = sum(abs(pos.unrealized_pnl) for pos in self.positions.values())
            
            return {
                'total_pnl': round(self.total_pnl, 2),
                'realized_pnl': round(self.total_realized_pnl, 2),
                'unrealized_pnl': round(self.total_unrealized_pnl, 2),
                'max_drawdown': round(self.max_drawdown, 2),
                'active_positions': active_positions,
                'total_positions': total_positions,
                'win_rate': round(win_rate, 2),
                'avg_profit_per_trade': round(avg_profit, 2),
                'avg_duration_hours': round(avg_duration, 2),
                'portfolio_heat': round(portfolio_heat, 2),
                'positions_detail': [pos.get_metrics() for pos in self.positions.values()]
            }
            
        except Exception as e:
            logger.error("Portfolio metrics calculation failed", error=str(e))
            return {}
            
    def get_risk_assessment(self) -> Dict[str, Any]:
        """Assess current portfolio risk levels."""
        try:
            active_positions = len(self.positions)
            
            # Position concentration risk
            position_risk = (active_positions / self.max_positions) * 100
            
            # Portfolio heat risk
            total_exposure = sum(abs(pos.unrealized_pnl) for pos in self.positions.values())
            heat_risk = min((total_exposure / self.max_portfolio_risk) * 100, 100)
            
            # Drawdown risk
            drawdown_risk = min((self.max_drawdown / 20) * 100, 100)  # 20% max acceptable
            
            # Overall risk score
            overall_risk = (position_risk * 0.3 + heat_risk * 0.4 + drawdown_risk * 0.3)
            
            # Risk level classification
            if overall_risk <= 30:
                risk_level = "LOW"
            elif overall_risk <= 60:
                risk_level = "MEDIUM"
            elif overall_risk <= 80:
                risk_level = "HIGH"
            else:
                risk_level = "EXTREME"
                
            return {
                'overall_risk_score': round(overall_risk, 1),
                'risk_level': risk_level,
                'position_concentration': round(position_risk, 1),
                'portfolio_heat': round(heat_risk, 1),
                'drawdown_risk': round(drawdown_risk, 1),
                'max_new_positions': max(0, self.max_positions - active_positions),
                'recommended_action': self._get_risk_recommendation(overall_risk)
            }
            
        except Exception as e:
            logger.error("Risk assessment failed", error=str(e))
            return {'risk_level': 'UNKNOWN', 'overall_risk_score': 0}
            
    def _get_risk_recommendation(self, risk_score: float) -> str:
        """Get risk management recommendation."""
        if risk_score <= 30:
            return "Portfolio risk is within acceptable limits"
        elif risk_score <= 60:
            return "Consider reducing position sizes or closing weak positions"
        elif risk_score <= 80:
            return "HIGH RISK: Close unprofitable positions and avoid new trades"
        else:
            return "EXTREME RISK: Immediately close positions to preserve capital"


# Global portfolio manager instance
portfolio_manager = PortfolioManager() 