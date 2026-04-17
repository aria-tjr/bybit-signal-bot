"""
Advanced Analytics Service

Provides comprehensive performance metrics, tracking, and reporting.
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio
import json

from ..core.logging import get_logger
from ..core.settings import settings

logger = get_logger(__name__)


class PerformanceAnalytics:
    """Advanced performance analytics and reporting."""
    
    def __init__(self):
        self.signal_history = deque(maxlen=1000)  # Last 1000 signals
        self.trade_history = deque(maxlen=500)    # Last 500 trades
        self.equity_curve = deque(maxlen=2000)    # 2000 data points
        
        # Performance tracking
        self.daily_stats = defaultdict(dict)
        self.symbol_performance = defaultdict(dict)
        self.timeframe_performance = defaultdict(dict)
        self.regime_performance = defaultdict(dict)
        
        # Real-time metrics
        self.current_equity = 10000.0  # Starting equity
        self.peak_equity = 10000.0
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0
        
    async def track_signal(self, signal_data: Dict[str, Any]):
        """Track a new signal for analytics."""
        try:
            signal_record = {
                'timestamp': datetime.utcnow(),
                'symbol': signal_data.get('symbol'),
                'direction': signal_data.get('direction'),
                'confidence': signal_data.get('confidence_score', 50),
                'leverage': signal_data.get('leverage', 1),
                'entry_price': signal_data.get('entry_price'),
                'stop_loss': signal_data.get('stop_loss'),
                'take_profits': [
                    signal_data.get('take_profit_1'),
                    signal_data.get('take_profit_2'),
                    signal_data.get('take_profit_3')
                ],
                'regime': signal_data.get('regime_info', {}).get('regime'),
                'strategy_type': signal_data.get('regime_info', {}).get('strategy_type'),
                'volatility_score': signal_data.get('volatility_score'),
                'dominant_timeframe': signal_data.get('dominant_timeframe'),
                'risk_reward_ratio': signal_data.get('risk_reward', {}).get('average_ratio', 0)
            }
            
            self.signal_history.append(signal_record)
            
            # Update symbol stats
            symbol = signal_data.get('symbol')
            if symbol:
                if symbol not in self.symbol_performance:
                    self.symbol_performance[symbol] = {
                        'total_signals': 0,
                        'avg_confidence': 0,
                        'direction_distribution': {'LONG': 0, 'SHORT': 0}
                    }
                
                self.symbol_performance[symbol]['total_signals'] += 1
                self.symbol_performance[symbol]['direction_distribution'][signal_data.get('direction', 'NEUTRAL')] += 1
                
            logger.info("Signal tracked for analytics", symbol=symbol)
            
        except Exception as e:
            logger.error("Failed to track signal", error=str(e))
            
    async def track_trade_outcome(
        self, 
        signal_id: str, 
        outcome: str, 
        pnl_percent: float,
        duration_hours: float,
        exit_reason: str
    ):
        """Track trade outcome for performance analysis."""
        try:
            # Find corresponding signal
            signal_record = None
            for signal in reversed(self.signal_history):
                signal_timestamp = signal['timestamp'].isoformat()
                if signal_timestamp == signal_id:
                    signal_record = signal
                    break
                    
            if not signal_record:
                logger.warning("Signal not found for trade outcome", signal_id=signal_id)
                return
                
            trade_record = {
                'timestamp': datetime.utcnow(),
                'signal_timestamp': signal_record['timestamp'],
                'symbol': signal_record['symbol'],
                'direction': signal_record['direction'],
                'outcome': outcome,  # 'win', 'loss', 'breakeven'
                'pnl_percent': pnl_percent,
                'duration_hours': duration_hours,
                'exit_reason': exit_reason,  # 'tp1', 'tp2', 'tp3', 'stop_loss', 'manual'
                'leverage': signal_record['leverage'],
                'confidence': signal_record['confidence'],
                'regime': signal_record['regime'],
                'strategy_type': signal_record['strategy_type']
            }
            
            self.trade_history.append(trade_record)
            
            # Update equity curve
            self.current_equity *= (1 + pnl_percent / 100)
            if self.current_equity > self.peak_equity:
                self.peak_equity = self.current_equity
                self.current_drawdown = 0.0
            else:
                self.current_drawdown = ((self.peak_equity - self.current_equity) / self.peak_equity) * 100
                if self.current_drawdown > self.max_drawdown:
                    self.max_drawdown = self.current_drawdown
                    
            self.equity_curve.append({
                'timestamp': datetime.utcnow(),
                'equity': self.current_equity,
                'pnl': pnl_percent,
                'drawdown': self.current_drawdown
            })
            
            # Update performance stats
            await self._update_performance_stats(trade_record)
            
            logger.info("Trade outcome tracked",
                       symbol=signal_record['symbol'],
                       outcome=outcome,
                       pnl=pnl_percent)
                       
        except Exception as e:
            logger.error("Failed to track trade outcome", error=str(e))
            
    async def _update_performance_stats(self, trade_record: Dict[str, Any]):
        """Update various performance statistics."""
        try:
            symbol = trade_record['symbol']
            regime = trade_record['regime']
            strategy_type = trade_record['strategy_type']
            outcome = trade_record['outcome']
            
            # Update symbol performance
            if symbol not in self.symbol_performance:
                self.symbol_performance[symbol] = {
                    'trades': 0, 'wins': 0, 'total_pnl': 0.0,
                    'avg_duration': 0.0, 'best_trade': 0.0, 'worst_trade': 0.0
                }
                
            stats = self.symbol_performance[symbol]
            stats['trades'] += 1
            if outcome == 'win':
                stats['wins'] += 1
            stats['total_pnl'] += trade_record['pnl_percent']
            stats['avg_duration'] = (stats.get('avg_duration', 0) * (stats['trades'] - 1) + 
                                   trade_record['duration_hours']) / stats['trades']
            stats['best_trade'] = max(stats.get('best_trade', 0), trade_record['pnl_percent'])
            stats['worst_trade'] = min(stats.get('worst_trade', 0), trade_record['pnl_percent'])
            
            # Update regime performance
            if regime and regime not in self.regime_performance:
                self.regime_performance[regime] = {
                    'trades': 0, 'wins': 0, 'total_pnl': 0.0, 'avg_confidence': 0.0
                }
                
            if regime:
                regime_stats = self.regime_performance[regime]
                regime_stats['trades'] += 1
                if outcome == 'win':
                    regime_stats['wins'] += 1
                regime_stats['total_pnl'] += trade_record['pnl_percent']
                regime_stats['avg_confidence'] = (
                    regime_stats.get('avg_confidence', 0) * (regime_stats['trades'] - 1) + 
                    trade_record['confidence']
                ) / regime_stats['trades']
                
        except Exception as e:
            logger.error("Failed to update performance stats", error=str(e))
            
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        try:
            if not self.trade_history:
                return {'message': 'No trade data available'}
                
            trades = list(self.trade_history)
            recent_trades = trades[-30:]  # Last 30 trades
            
            # Basic metrics
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t['outcome'] == 'win')
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            # PnL metrics
            total_pnl = sum(t['pnl_percent'] for t in trades)
            avg_win = np.mean([t['pnl_percent'] for t in trades if t['outcome'] == 'win']) if winning_trades > 0 else 0
            avg_loss = np.mean([t['pnl_percent'] for t in trades if t['outcome'] == 'loss']) if total_trades > winning_trades else 0
            
            # Risk metrics
            returns = [t['pnl_percent'] for t in trades]
            volatility = np.std(returns) if len(returns) > 1 else 0
            sharpe_ratio = (np.mean(returns) / volatility) if volatility > 0 else 0
            
            # Recent performance
            recent_win_rate = (sum(1 for t in recent_trades if t['outcome'] == 'win') / 
                             len(recent_trades) * 100) if recent_trades else 0
            recent_pnl = sum(t['pnl_percent'] for t in recent_trades)
            
            # Duration analysis
            avg_duration = np.mean([t['duration_hours'] for t in trades])
            
            return {
                'total_trades': total_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'profit_factor': round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': round(self.max_drawdown, 2),
                'current_drawdown': round(self.current_drawdown, 2),
                'recent_win_rate': round(recent_win_rate, 2),
                'recent_pnl': round(recent_pnl, 2),
                'avg_duration_hours': round(avg_duration, 2),
                'current_equity': round(self.current_equity, 2),
                'equity_growth': round(((self.current_equity / 10000) - 1) * 100, 2)
            }
            
        except Exception as e:
            logger.error("Failed to generate performance summary", error=str(e))
            return {'error': 'Failed to calculate performance metrics'}
            
    def get_symbol_analytics(self) -> Dict[str, Any]:
        """Get performance analytics by symbol."""
        try:
            symbol_stats = {}
            
            for symbol, stats in self.symbol_performance.items():
                if stats.get('trades', 0) > 0:
                    win_rate = (stats.get('wins', 0) / stats['trades']) * 100
                    avg_pnl = stats.get('total_pnl', 0) / stats['trades']
                    
                    symbol_stats[symbol] = {
                        'trades': stats['trades'],
                        'win_rate': round(win_rate, 2),
                        'avg_pnl': round(avg_pnl, 2),
                        'total_pnl': round(stats.get('total_pnl', 0), 2),
                        'avg_duration': round(stats.get('avg_duration', 0), 2),
                        'best_trade': round(stats.get('best_trade', 0), 2),
                        'worst_trade': round(stats.get('worst_trade', 0), 2)
                    }
                    
            # Sort by total PnL
            sorted_symbols = sorted(
                symbol_stats.items(),
                key=lambda x: x[1]['total_pnl'],
                reverse=True
            )
            
            return {
                'top_performers': dict(sorted_symbols[:5]),
                'worst_performers': dict(sorted_symbols[-3:]),
                'total_symbols_traded': len(symbol_stats)
            }
            
        except Exception as e:
            logger.error("Failed to generate symbol analytics", error=str(e))
            return {}
            
    def get_regime_analytics(self) -> Dict[str, Any]:
        """Get performance analytics by market regime."""
        try:
            regime_stats = {}
            
            for regime, stats in self.regime_performance.items():
                if stats.get('trades', 0) > 0:
                    win_rate = (stats.get('wins', 0) / stats['trades']) * 100
                    avg_pnl = stats.get('total_pnl', 0) / stats['trades']
                    
                    regime_stats[regime] = {
                        'trades': stats['trades'],
                        'win_rate': round(win_rate, 2),
                        'avg_pnl': round(avg_pnl, 2),
                        'total_pnl': round(stats.get('total_pnl', 0), 2),
                        'avg_confidence': round(stats.get('avg_confidence', 0), 2)
                    }
                    
            return regime_stats
            
        except Exception as e:
            logger.error("Failed to generate regime analytics", error=str(e))
            return {}
            
    def get_signal_quality_metrics(self) -> Dict[str, Any]:
        """Analyze signal quality and accuracy."""
        try:
            if not self.signal_history:
                return {'message': 'No signal data available'}
                
            signals = list(self.signal_history)
            
            # Confidence analysis
            confidence_ranges = {
                '80+': [s for s in signals if s['confidence'] >= 80],
                '60-79': [s for s in signals if 60 <= s['confidence'] < 80],
                '40-59': [s for s in signals if 40 <= s['confidence'] < 60],
                '<40': [s for s in signals if s['confidence'] < 40]
            }
            
            # Direction distribution
            direction_dist = {
                'LONG': sum(1 for s in signals if s['direction'] == 'LONG'),
                'SHORT': sum(1 for s in signals if s['direction'] == 'SHORT')
            }
            
            # Timeframe analysis
            timeframe_dist = defaultdict(int)
            for signal in signals:
                tf = signal.get('dominant_timeframe', 'unknown')
                timeframe_dist[tf] += 1
                
            return {
                'total_signals': len(signals),
                'avg_confidence': round(np.mean([s['confidence'] for s in signals]), 2),
                'confidence_distribution': {
                    k: len(v) for k, v in confidence_ranges.items()
                },
                'direction_distribution': direction_dist,
                'timeframe_distribution': dict(timeframe_dist),
                'avg_risk_reward': round(np.mean([
                    s['risk_reward_ratio'] for s in signals 
                    if s['risk_reward_ratio'] and s['risk_reward_ratio'] > 0
                ]), 2) if any(s['risk_reward_ratio'] for s in signals) else 0
            }
            
        except Exception as e:
            logger.error("Failed to generate signal quality metrics", error=str(e))
            return {}
            
    def get_equity_curve_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get equity curve data for the last N days."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            filtered_data = [
                point for point in self.equity_curve
                if point['timestamp'] >= cutoff_time
            ]
            
            return filtered_data
            
        except Exception as e:
            logger.error("Failed to get equity curve data", error=str(e))
            return []
            
    def export_performance_report(self) -> Dict[str, Any]:
        """Export comprehensive performance report."""
        try:
            return {
                'generated_at': datetime.utcnow().isoformat(),
                'performance_summary': self.get_performance_summary(),
                'symbol_analytics': self.get_symbol_analytics(),
                'regime_analytics': self.get_regime_analytics(),
                'signal_quality': self.get_signal_quality_metrics(),
                'equity_curve_30d': self.get_equity_curve_data(30),
                'recent_trades': [
                    {
                        'timestamp': t['timestamp'].isoformat(),
                        'symbol': t['symbol'],
                        'direction': t['direction'],
                        'outcome': t['outcome'],
                        'pnl': t['pnl_percent'],
                        'duration': t['duration_hours']
                    }
                    for t in list(self.trade_history)[-20:]  # Last 20 trades
                ]
            }
            
        except Exception as e:
            logger.error("Failed to export performance report", error=str(e))
            return {'error': 'Failed to generate report'}


# Global analytics instance
analytics = PerformanceAnalytics() 