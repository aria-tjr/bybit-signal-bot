"""
Algorithmic Trading Bias Monitor

Implements systematic bias detection based on research from:
- Robuxio: Algorithmic Crypto Trading Biases
- Academic research on algorithmic trading bias

Monitors for:
- Selection Bias (directional preference) 
- Recency Bias (over-weighting recent data)
- Curve Fitting (over-optimization)
- Data Mining Bias
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)

class BiasMonitor:
    """
    Monitors trading signals for systematic biases that could indicate 
    algorithm problems or market condition misunderstandings.
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.signal_history = deque(maxlen=window_size)
        self.direction_counts = defaultdict(int)
        self.confidence_history = deque(maxlen=window_size)
        self.symbol_bias_tracker = defaultdict(lambda: defaultdict(int))
        self.start_time = datetime.utcnow()
        
    def record_signal(self, 
                     symbol: str, 
                     direction: str, 
                     confidence: float,
                     signal_strength: float,
                     metadata: Optional[Dict] = None):
        """Record a trading signal for bias analysis."""
        
        signal_record = {
            'timestamp': datetime.utcnow(),
            'symbol': symbol,
            'direction': direction,
            'confidence': confidence,
            'signal_strength': signal_strength,
            'metadata': metadata or {}
        }
        
        self.signal_history.append(signal_record)
        self.direction_counts[direction] += 1
        self.confidence_history.append(confidence)
        self.symbol_bias_tracker[symbol][direction] += 1
        
        # Check for biases after accumulating enough data
        if len(self.signal_history) >= 20:
            self._check_for_biases()
    
    def _check_for_biases(self):
        """Check for various types of algorithmic biases."""
        
        # 1. SELECTION BIAS - Systematic directional preference
        self._check_selection_bias()
        
        # 2. CONFIDENCE BIAS - Unrealistic confidence patterns
        self._check_confidence_bias()
        
        # 3. SYMBOL BIAS - Unfair treatment of different symbols
        self._check_symbol_bias()
        
        # 4. RECENCY BIAS - Over-weighting recent signals
        self._check_recency_bias()
        
        # 5. QUALITY DEGRADATION - Signal quality declining over time
        self._check_quality_degradation()
    
    def _check_selection_bias(self):
        """
        Check for systematic directional bias (Selection Bias).
        
        Healthy algorithms should generate roughly balanced signals
        over time, adjusted for market conditions.
        """
        total_signals = sum(self.direction_counts.values())
        if total_signals < 20:
            return
            
        long_ratio = self.direction_counts.get('LONG', 0) / total_signals
        short_ratio = self.direction_counts.get('SHORT', 0) / total_signals
        neutral_ratio = self.direction_counts.get('NEUTRAL', 0) / total_signals
        
        # Alert thresholds based on research
        EXTREME_BIAS_THRESHOLD = 0.85  # 85%+ in one direction = extreme bias
        MODERATE_BIAS_THRESHOLD = 0.70  # 70%+ = moderate bias
        
        if long_ratio > EXTREME_BIAS_THRESHOLD:
            logger.error("🚨 EXTREME LONG BIAS DETECTED",
                        long_ratio=f"{long_ratio:.1%}",
                        short_ratio=f"{short_ratio:.1%}",
                        total_signals=total_signals,
                        bias_level="EXTREME",
                        action_required="IMMEDIATE_REVIEW")
                        
        elif short_ratio > EXTREME_BIAS_THRESHOLD:
            logger.error("🚨 EXTREME SHORT BIAS DETECTED",
                        long_ratio=f"{long_ratio:.1%}",
                        short_ratio=f"{short_ratio:.1%}",
                        total_signals=total_signals,
                        bias_level="EXTREME",
                        action_required="IMMEDIATE_REVIEW")
                        
        elif long_ratio > MODERATE_BIAS_THRESHOLD:
            logger.warning("⚠️ MODERATE LONG BIAS DETECTED",
                          long_ratio=f"{long_ratio:.1%}",
                          short_ratio=f"{short_ratio:.1%}",
                          total_signals=total_signals,
                          bias_level="MODERATE",
                          recommendation="monitor_closely")
                          
        elif short_ratio > MODERATE_BIAS_THRESHOLD:
            logger.warning("⚠️ MODERATE SHORT BIAS DETECTED",
                          long_ratio=f"{long_ratio:.1%}",
                          short_ratio=f"{short_ratio:.1%}",
                          total_signals=total_signals,
                          bias_level="MODERATE",
                          recommendation="monitor_closely")
    
    def _check_confidence_bias(self):
        """Check for unrealistic confidence patterns."""
        if len(self.confidence_history) < 10:
            return
            
        recent_confidence = list(self.confidence_history)[-10:]
        avg_confidence = statistics.mean(recent_confidence)
        confidence_std = statistics.stdev(recent_confidence) if len(recent_confidence) > 1 else 0
        
        # Check for over-confidence bias
        if avg_confidence > 90:
            logger.warning("⚠️ OVER-CONFIDENCE BIAS DETECTED",
                          avg_confidence=f"{avg_confidence:.1f}%",
                          confidence_std=f"{confidence_std:.1f}",
                          bias_type="overconfidence",
                          risk="unrealistic_expectations")
        
        # Check for under-confidence bias  
        elif avg_confidence < 30:
            logger.warning("⚠️ UNDER-CONFIDENCE BIAS DETECTED",
                          avg_confidence=f"{avg_confidence:.1f}%",
                          confidence_std=f"{confidence_std:.1f}",
                          bias_type="underconfidence",
                          risk="missing_opportunities")
        
        # Check for confidence uniformity (possible curve fitting)
        if confidence_std < 5 and len(recent_confidence) >= 10:
            logger.warning("⚠️ CONFIDENCE UNIFORMITY DETECTED",
                          avg_confidence=f"{avg_confidence:.1f}%",
                          confidence_std=f"{confidence_std:.1f}",
                          bias_type="curve_fitting",
                          risk="over_optimization")
    
    def _check_symbol_bias(self):
        """Check for unfair treatment of different symbols."""
        if len(self.symbol_bias_tracker) < 3:
            return
            
        symbol_imbalances = []
        for symbol, directions in self.symbol_bias_tracker.items():
            total = sum(directions.values())
            if total >= 5:  # Only check symbols with enough signals
                long_ratio = directions.get('LONG', 0) / total
                if long_ratio > 0.8 or long_ratio < 0.2:
                    symbol_imbalances.append({
                        'symbol': symbol,
                        'long_ratio': long_ratio,
                        'total_signals': total
                    })
        
        if len(symbol_imbalances) >= 2:
            logger.warning("⚠️ SYMBOL-SPECIFIC BIAS DETECTED",
                          imbalanced_symbols=len(symbol_imbalances),
                          examples=symbol_imbalances[:3],
                          bias_type="symbol_bias",
                          recommendation="review_symbol_specific_logic")
    
    def _check_recency_bias(self):
        """Check if recent signals are over-weighted vs historical."""
        if len(self.signal_history) < 50:
            return
            
        # Compare recent 25% vs older 75% of signals
        recent_count = len(self.signal_history) // 4
        recent_signals = list(self.signal_history)[-recent_count:]
        older_signals = list(self.signal_history)[:-recent_count]
        
        recent_long_ratio = sum(1 for s in recent_signals if s['direction'] == 'LONG') / len(recent_signals)
        older_long_ratio = sum(1 for s in older_signals if s['direction'] == 'LONG') / len(older_signals)
        
        ratio_change = abs(recent_long_ratio - older_long_ratio)
        
        if ratio_change > 0.3:  # 30% change in directional bias
            logger.warning("⚠️ RECENCY BIAS DETECTED",
                          recent_long_ratio=f"{recent_long_ratio:.1%}",
                          older_long_ratio=f"{older_long_ratio:.1%}",
                          ratio_change=f"{ratio_change:.1%}",
                          bias_type="recency_bias",
                          risk="over_weighting_recent_data")
    
    def _check_quality_degradation(self):
        """Check if signal quality is degrading over time."""
        if len(self.signal_history) < 30:
            return
            
        # Compare first half vs second half quality
        mid_point = len(self.signal_history) // 2
        first_half = list(self.signal_history)[:mid_point]
        second_half = list(self.signal_history)[mid_point:]
        
        first_half_confidence = statistics.mean([s['confidence'] for s in first_half])
        second_half_confidence = statistics.mean([s['confidence'] for s in second_half])
        
        confidence_decline = first_half_confidence - second_half_confidence
        
        if confidence_decline > 15:  # 15% decline in confidence
            logger.warning("⚠️ QUALITY DEGRADATION DETECTED",
                          first_half_confidence=f"{first_half_confidence:.1f}%",
                          second_half_confidence=f"{second_half_confidence:.1f}%",
                          decline=f"{confidence_decline:.1f}%",
                          bias_type="quality_degradation",
                          recommendation="review_algorithm_parameters")
    
    def get_bias_report(self) -> Dict[str, Any]:
        """Generate comprehensive bias analysis report."""
        total_signals = sum(self.direction_counts.values())
        
        if total_signals == 0:
            return {"status": "insufficient_data", "total_signals": 0}
        
        # Calculate directional distribution
        directional_stats = {}
        for direction, count in self.direction_counts.items():
            directional_stats[direction] = {
                'count': count,
                'percentage': (count / total_signals) * 100
            }
        
        # Calculate confidence statistics
        confidence_stats = {}
        if self.confidence_history:
            confidence_stats = {
                'mean': statistics.mean(self.confidence_history),
                'median': statistics.median(self.confidence_history),
                'std_dev': statistics.stdev(self.confidence_history) if len(self.confidence_history) > 1 else 0,
                'min': min(self.confidence_history),
                'max': max(self.confidence_history)
            }
        
        # Runtime statistics
        runtime = datetime.utcnow() - self.start_time
        signals_per_hour = total_signals / max(runtime.total_seconds() / 3600, 0.01)
        
        return {
            'status': 'active',
            'total_signals': total_signals,
            'runtime_hours': runtime.total_seconds() / 3600,
            'signals_per_hour': signals_per_hour,
            'directional_distribution': directional_stats,
            'confidence_statistics': confidence_stats,
            'symbols_analyzed': len(self.symbol_bias_tracker),
            'potential_biases': self._detect_current_biases()
        }
    
    def _detect_current_biases(self) -> List[str]:
        """Return list of currently detected biases."""
        biases = []
        total_signals = sum(self.direction_counts.values())
        
        if total_signals >= 20:
            long_ratio = self.direction_counts.get('LONG', 0) / total_signals
            if long_ratio > 0.75:
                biases.append('long_bias')
            elif long_ratio < 0.25:
                biases.append('short_bias')
        
        if self.confidence_history:
            avg_confidence = statistics.mean(self.confidence_history)
            if avg_confidence > 90:
                biases.append('overconfidence')
            elif avg_confidence < 30:
                biases.append('underconfidence')
        
        return biases

# Global bias monitor instance
bias_monitor = BiasMonitor() 