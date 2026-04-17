"""
Risk management module for position sizing and risk calculations.

Provides tools for calculating position sizes, risk-reward ratios, and portfolio risk.
"""

from typing import Dict, Optional, Tuple, List
import numpy as np

from ..core.logging import get_logger
from ..core.settings import settings

logger = get_logger(__name__)


class RiskManager:
    """Risk management calculations and validations."""
    
    @staticmethod
    def calculate_position_size(
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        risk_percent: float = 2.0,
        leverage: int = 1
    ) -> Dict[str, float]:
        """
        Calculate position size based on risk parameters.
        
        Args:
            account_balance: Total account balance
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            risk_percent: Percentage of account to risk
            leverage: Leverage to use
            
        Returns:
            Dictionary with position details
        """
        # Calculate risk amount
        risk_amount = account_balance * (risk_percent / 100)
        
        # Calculate price difference
        price_diff = abs(entry_price - stop_loss)
        price_diff_pct = (price_diff / entry_price) * 100
        
        # Calculate position size
        position_size = risk_amount / price_diff
        
        # Adjust for leverage
        position_value = position_size * entry_price
        margin_required = position_value / leverage
        
        # Ensure margin doesn't exceed account balance
        if margin_required > account_balance * 0.8:  # Keep 20% buffer
            # Recalculate with maximum safe position
            margin_required = account_balance * 0.8
            position_value = margin_required * leverage
            position_size = position_value / entry_price
            
        return {
            "position_size": round(position_size, 8),
            "position_value": round(position_value, 2),
            "margin_required": round(margin_required, 2),
            "risk_amount": round(risk_amount, 2),
            "stop_loss_distance": round(price_diff_pct, 2),
            "leverage": leverage
        }
        
    @staticmethod
    def calculate_risk_reward_ratio(
        entry_price: float,
        stop_loss: float,
        take_profits: List[float]
    ) -> Dict[str, float]:
        """
        Calculate risk-reward ratios for each take profit level.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profits: List of take profit prices
            
        Returns:
            Dictionary with risk-reward ratios
        """
        risk = abs(entry_price - stop_loss)
        
        ratios = {}
        for i, tp in enumerate(take_profits, 1):
            reward = abs(tp - entry_price)
            ratio = reward / risk if risk > 0 else 0
            ratios[f"tp{i}_ratio"] = round(ratio, 2)
            
        # Calculate average ratio
        avg_ratio = sum(ratios.values()) / len(ratios) if ratios else 0
        ratios["average_ratio"] = round(avg_ratio, 2)
        
        return ratios
        
    @staticmethod
    def validate_leverage(
        volatility_score: float,
        suggested_leverage: int,
        max_allowed: int = 50
    ) -> Tuple[int, str]:
        """
        Validate leverage for MAXIMUM leverage strategy.
        
        Only applies minimal safety reductions for extreme cases.
        
        Args:
            volatility_score: Current volatility score (0-100)
            suggested_leverage: Suggested leverage from strategy
            max_allowed: Maximum allowed leverage
            
        Returns:
            Tuple of (adjusted_leverage, reason)
        """
        # Only reduce for EXTREME volatility (very rare)
        if volatility_score > 95:  # Only the most extreme cases
            max_safe_leverage = int(suggested_leverage * 0.9)  # 10% reduction only
            if suggested_leverage > max_safe_leverage:
                return max_safe_leverage, "Minor reduction for extreme volatility"
                
        # Apply global maximum only
        if suggested_leverage > max_allowed:
            return max_allowed, f"Capped at maximum {max_allowed}x"
            
        return suggested_leverage, "Maximum leverage approved"
        
    @staticmethod
    def calculate_liquidation_price(
        entry_price: float,
        leverage: int,
        direction: str,
        maintenance_margin: float = 0.5
    ) -> float:
        """
        Calculate liquidation price for a leveraged position.
        
        Args:
            entry_price: Entry price
            leverage: Leverage used
            direction: Trade direction (LONG/SHORT)
            maintenance_margin: Maintenance margin percentage
            
        Returns:
            Liquidation price
        """
        # Initial margin percentage
        initial_margin = 100 / leverage
        
        # Calculate liquidation distance
        liquidation_distance = initial_margin - maintenance_margin
        
        if direction == "LONG":
            liquidation_price = entry_price * (1 - liquidation_distance / 100)
        else:  # SHORT
            liquidation_price = entry_price * (1 + liquidation_distance / 100)
            
        return round(liquidation_price, 6)
        
    @staticmethod
    def assess_trade_quality(
        risk_reward_ratios: Dict[str, float],
        confidence_score: float,
        volatility_score: float
    ) -> Dict[str, any]:
        """
        Assess overall trade quality based on multiple factors.
        
        Args:
            risk_reward_ratios: Risk-reward ratios for TPs
            confidence_score: ML model confidence (0-100)
            volatility_score: Current volatility (0-100)
            
        Returns:
            Trade quality assessment
        """
        # Base score from risk-reward ratio
        avg_rr = risk_reward_ratios.get("average_ratio", 0)
        rr_score = min(avg_rr * 20, 100)  # Cap at 100
        
        # Adjust for confidence
        confidence_weight = 0.4
        volatility_penalty = max(0, (volatility_score - 50) * 0.5)
        
        # Calculate final score
        quality_score = (
            rr_score * 0.4 +
            confidence_score * confidence_weight -
            volatility_penalty
        )
        
        # Determine quality level
        if quality_score >= 80:
            quality = "EXCELLENT"
            recommendation = "Strong setup with favorable risk-reward"
        elif quality_score >= 60:
            quality = "GOOD"
            recommendation = "Solid setup, proceed with standard risk"
        elif quality_score >= 40:
            quality = "FAIR"
            recommendation = "Acceptable setup, consider reduced position"
        else:
            quality = "POOR"
            recommendation = "Weak setup, consider skipping or minimal position"
            
        return {
            "quality_score": round(quality_score, 1),
            "quality_level": quality,
            "recommendation": recommendation,
            "factors": {
                "risk_reward_score": round(rr_score, 1),
                "confidence_score": confidence_score,
                "volatility_penalty": round(volatility_penalty, 1)
            }
        }
        
    @staticmethod
    def calculate_portfolio_heat(
        open_positions: List[Dict[str, float]],
        account_balance: float
    ) -> Dict[str, float]:
        """
        Calculate portfolio heat (total risk exposure).
        
        Args:
            open_positions: List of open position details
            account_balance: Current account balance
            
        Returns:
            Portfolio heat metrics
        """
        total_risk = 0
        total_margin = 0
        
        for position in open_positions:
            risk = position.get("risk_amount", 0)
            margin = position.get("margin_required", 0)
            
            total_risk += risk
            total_margin += margin
            
        risk_percentage = (total_risk / account_balance) * 100 if account_balance > 0 else 0
        margin_usage = (total_margin / account_balance) * 100 if account_balance > 0 else 0
        
        # Calculate heat level
        if risk_percentage > 10:
            heat_level = "CRITICAL"
        elif risk_percentage > 6:
            heat_level = "HIGH"
        elif risk_percentage > 3:
            heat_level = "MODERATE"
        else:
            heat_level = "LOW"
            
        return {
            "total_risk": round(total_risk, 2),
            "risk_percentage": round(risk_percentage, 2),
            "margin_usage": round(margin_usage, 2),
            "heat_level": heat_level,
            "positions_count": len(open_positions),
            "available_margin": round(account_balance - total_margin, 2)
        }
        
    @staticmethod
    def suggest_position_adjustments(
        current_position: Dict[str, float],
        market_conditions: Dict[str, float]
    ) -> Dict[str, any]:
        """
        Suggest position adjustments based on changing conditions.
        
        Args:
            current_position: Current position details
            market_conditions: Current market conditions
            
        Returns:
            Adjustment suggestions
        """
        suggestions = []
        
        # Check volatility changes
        initial_vol = current_position.get("initial_volatility", 50)
        current_vol = market_conditions.get("volatility_score", 50)
        
        if current_vol > initial_vol * 1.5:
            suggestions.append({
                "action": "REDUCE_POSITION",
                "reason": "Volatility increased significantly",
                "percentage": 50
            })
        
        # Check profit status
        entry = current_position.get("entry_price", 0)
        current = market_conditions.get("current_price", 0)
        pnl_pct = ((current - entry) / entry) * 100 if entry > 0 else 0
        
        if current_position.get("direction") == "SHORT":
            pnl_pct = -pnl_pct
            
        if pnl_pct > 10:
            suggestions.append({
                "action": "MOVE_STOP_TO_BREAKEVEN",
                "reason": "Secure profits by moving stop loss",
                "new_stop": entry
            })
        
        if pnl_pct > 15:
            suggestions.append({
                "action": "TAKE_PARTIAL_PROFIT",
                "reason": "Lock in substantial gains",
                "percentage": 30
            })
            
        return {
            "suggestions": suggestions,
            "current_pnl_pct": round(pnl_pct, 2),
            "volatility_change": round(current_vol - initial_vol, 1)
        } 