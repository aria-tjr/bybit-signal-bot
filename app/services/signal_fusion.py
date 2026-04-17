"""
Signal Fusion Engine - Advanced Multi-Signal Integration

Combines traditional technical analysis with Bookmap order flow signals
to generate enhanced trading signals with higher accuracy and confidence.

Fusion Logic:
1. Traditional TA signals (existing bot)
2. Bookmap order flow signals (whale trades, stop runs, icebergs, etc.)
3. Market microstructure analysis
4. Confidence scoring and signal validation
5. Enhanced risk assessment

The fusion engine acts as a filter and enhancer, upgrading signal quality
through institutional-grade order flow analysis.
"""

import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import time
from dataclasses import dataclass
from enum import Enum

from ..core.logging import get_logger
from ..core.settings import settings
from .bookmap_engine import bookmap_engine, BookmapSignal, SignalType

logger = get_logger(__name__)


class FusionResult(Enum):
    """Signal fusion results."""
    ENHANCED_LONG = "ENHANCED_LONG"
    ENHANCED_SHORT = "ENHANCED_SHORT"
    CONFLICTING_SIGNALS = "CONFLICTING_SIGNALS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    WEAK_CONFIRMATION = "WEAK_CONFIRMATION"
    NO_FUSION_AVAILABLE = "NO_FUSION_AVAILABLE"


@dataclass
class FusedSignal:
    """Enhanced signal with fusion analysis."""
    original_signal: Dict[str, Any]
    bookmap_summary: Dict[str, Any]
    fusion_result: FusionResult
    confidence_boost: float
    leverage_adjustment: float
    order_flow_score: float
    fusion_triggers: List[str]
    microstructure_analysis: Dict[str, Any]
    enhanced_entry_price: Optional[float] = None
    enhanced_stop_loss: Optional[float] = None
    

class SignalFusionEngine:
    """
    Advanced signal fusion engine that combines TA with order flow analysis.
    
    The fusion engine analyzes both traditional technical signals and real-time
    order flow data from Bookmap to generate enhanced trading decisions.
    """
    
    def __init__(self):
        self.fusion_history = []
        self.performance_metrics = {
            "fusion_accuracy": 0.0,
            "confidence_improvements": 0.0,
            "total_fusions": 0
        }
        
    async def fuse_signals(
        self,
        ta_signal: Dict[str, Any],
        symbol: str,
        lookback_minutes: int = 5
    ) -> FusedSignal:
        """
        ULTRA-OPTIMIZED signal fusion with enhanced institutional analysis.
        
        Args:
            ta_signal: Traditional technical analysis signal
            symbol: Trading pair symbol
            lookback_minutes: Minutes to look back for order flow data
            
        Returns:
            Ultra-enhanced fused signal with maximum insights
        """
        try:
            logger.info("Starting ULTRA-OPTIMIZED signal fusion", symbol=symbol, direction=ta_signal.get("direction"))
            
            # ULTRA-OPTIMIZED: Extended lookback with smart adjustment
            extended_lookback = max(45, lookback_minutes * 3)  # Increased for better context
            
            # Get comprehensive Bookmap order flow summary with extended analysis
            bookmap_summary = bookmap_engine.get_signal_summary(symbol, extended_lookback)
            order_flow_score = bookmap_engine.get_order_flow_score(symbol)
            
            # ULTRA-OPTIMIZED: Advanced signal alignment with sophisticated scoring
            fusion_result, confidence_boost, fusion_triggers = self._analyze_signal_alignment_ultra_enhanced(
                ta_signal, bookmap_summary, order_flow_score, symbol
            )
            
            # ULTRA-OPTIMIZED: Advanced leverage with portfolio integration
            leverage_adjustment = self._calculate_leverage_adjustment_ultra_optimized(
                ta_signal, bookmap_summary, order_flow_score, fusion_result, symbol
            )
            
            # ULTRA-OPTIMIZED: Enhanced microstructure with regime detection
            microstructure_analysis = self._analyze_microstructure_ultra_enhanced(
                ta_signal, bookmap_summary, symbol, order_flow_score
            )
            
            # ULTRA-OPTIMIZED: Smart level optimization with market maker analysis
            enhanced_levels = self._calculate_enhanced_levels_ultra_optimized(
                ta_signal, bookmap_summary, microstructure_analysis, order_flow_score, symbol
            )
            
            # Create ultra-optimized fused signal
            fused_signal = FusedSignal(
                original_signal=ta_signal,
                bookmap_summary=bookmap_summary,
                fusion_result=fusion_result,
                confidence_boost=confidence_boost,
                leverage_adjustment=leverage_adjustment,
                order_flow_score=order_flow_score,
                fusion_triggers=fusion_triggers,
                microstructure_analysis=microstructure_analysis,
                enhanced_entry_price=enhanced_levels.get("entry"),
                enhanced_stop_loss=enhanced_levels.get("stop")
            )
            
            # ULTRA-OPTIMIZED: Advanced performance tracking with ML insights
            self._track_fusion_performance_ultra_enhanced(fused_signal, symbol)
            
            logger.info(
                "ULTRA-OPTIMIZED signal fusion completed",
                symbol=symbol,
                fusion_result=fusion_result.value,
                confidence_boost=confidence_boost,
                order_flow_score=order_flow_score,
                leverage_adjustment=leverage_adjustment,
                microstructure_score=microstructure_analysis.get("institutional_score", 0)
            )
            
            return fused_signal
            
        except Exception as e:
            logger.error("Signal fusion failed", symbol=symbol, error=str(e))
            
            # Return enhanced fallback fusion result
            return FusedSignal(
                original_signal=ta_signal,
                bookmap_summary={},
                fusion_result=FusionResult.NO_FUSION_AVAILABLE,
                confidence_boost=0.0,
                leverage_adjustment=1.0,
                order_flow_score=0.0,
                fusion_triggers=["FusionError"],
                microstructure_analysis={"error": str(e), "fallback": True}
            )
            
    def _analyze_signal_alignment_ultra_enhanced(
        self,
        ta_signal: Dict[str, Any],
        bookmap_summary: Dict[str, Any],
        order_flow_score: float,
        symbol: str
    ) -> Tuple[FusionResult, float, List[str]]:
        """ULTRA-OPTIMIZED: Advanced signal alignment with sophisticated scoring and directional analysis."""
        
        ta_direction = ta_signal.get("direction", "NEUTRAL")
        dominant_side = bookmap_summary.get("dominant_side", "NEUTRAL")
        total_signals = bookmap_summary.get("total_signals", 0)
        avg_confidence = bookmap_summary.get("avg_confidence", 0.0)
        
        fusion_triggers = []
        confidence_boost = 0.0
        
        # ULTRA-OPTIMIZED: Advanced data sufficiency with signal quality
        if total_signals < 2 or avg_confidence < 3.0:
            return FusionResult.INSUFFICIENT_DATA, 0.0, ["InsufficientOrderFlow", f"Signals:{total_signals}", f"AvgConf:{avg_confidence:.1f}"]
            
        # ULTRA-OPTIMIZED: Enhanced directional alignment with strength scoring
        alignment_strength = 0.0
        signal_quality_multiplier = min(2.0, avg_confidence / 5.0)  # Quality-based boost
        
        if ta_direction == "LONG" and dominant_side == "BULLISH":
            fusion_result = FusionResult.ENHANCED_LONG
            alignment_strength = 1.0
            
            # ULTRA-OPTIMIZED: Enhanced confidence boosting with diminishing returns
            base_boost = 3.5 * signal_quality_multiplier  # Increased base boost
            signal_diversity_bonus = min(1.5, total_signals / 10.0)  # Bonus for more signals
            confidence_boost += base_boost + signal_diversity_bonus
            
            fusion_triggers.extend(["StrongBullishAlignment", f"QualityMult:{signal_quality_multiplier:.1f}"])
            
            # ULTRA-OPTIMIZED: Add specific signal type bonuses
            signal_types = bookmap_summary.get("signal_types", {})
            if signal_types.get("WHALE_TRADE", 0) >= 2:
                confidence_boost += 1.0
                fusion_triggers.append("WhaleSupport")
            if signal_types.get("ICEBERG_DETECTION", 0) >= 1:
                confidence_boost += 0.8
                fusion_triggers.append("IcebergAccumulation")
                
        elif ta_direction == "SHORT" and dominant_side == "BEARISH":
            fusion_result = FusionResult.ENHANCED_SHORT
            alignment_strength = 1.0
            
            # ULTRA-OPTIMIZED: Enhanced confidence boosting for shorts
            base_boost = 3.5 * signal_quality_multiplier
            signal_diversity_bonus = min(1.5, total_signals / 10.0)
            confidence_boost += base_boost + signal_diversity_bonus
            
            fusion_triggers.extend(["StrongBearishAlignment", f"QualityMult:{signal_quality_multiplier:.1f}"])
            
            # ULTRA-OPTIMIZED: Add specific signal type bonuses for shorts
            signal_types = bookmap_summary.get("signal_types", {})
            if signal_types.get("WHALE_TRADE", 0) >= 2:
                confidence_boost += 1.0
                fusion_triggers.append("WhalePressure")
            if signal_types.get("STOP_RUN", 0) >= 1:
                confidence_boost += 0.7
                fusion_triggers.append("StopRunConfirmation")
                
        elif ta_direction != "NEUTRAL" and dominant_side == "NEUTRAL":
            fusion_result = FusionResult.WEAK_CONFIRMATION
            alignment_strength = 0.3
            confidence_boost += 0.5 * signal_quality_multiplier  # Minimal boost for weak confirmation
            fusion_triggers.append("WeakNeutralFlow")
            
        elif ta_direction != "NEUTRAL" and dominant_side != "NEUTRAL":
            # ULTRA-OPTIMIZED: Handle conflicting signals with penalty
            fusion_result = FusionResult.CONFLICTING_SIGNALS
            alignment_strength = -0.5
            confidence_boost -= 1.5  # Penalty for conflicting signals
            fusion_triggers.extend(["ConflictingDirections", f"TA:{ta_direction}", f"Flow:{dominant_side}"])
            
        else:
            # ULTRA-OPTIMIZED: Neutral signals get minimal treatment
            fusion_result = FusionResult.WEAK_CONFIRMATION
            alignment_strength = 0.1
            confidence_boost += 0.2
            fusion_triggers.append("NeutralAlignment")
        
        # ULTRA-OPTIMIZED: Order flow score integration with advanced weighting
        flow_score_normalized = max(-1.0, min(1.0, order_flow_score / 10.0))  # Normalize to -1 to 1
        flow_boost = flow_score_normalized * 2.0 * signal_quality_multiplier  # Enhanced flow contribution
        confidence_boost += flow_boost
        
        if abs(flow_score_normalized) > 0.5:
            fusion_triggers.append(f"StrongFlow:{flow_score_normalized:+.1f}")
        
        # ULTRA-OPTIMIZED: Symbol-specific adjustments for major pairs
        if symbol in ["BTCUSDT", "ETHUSDT"]:
            confidence_boost *= 1.1  # 10% bonus for major pairs
            fusion_triggers.append("MajorPair")
        elif symbol.endswith("USDT") and len(symbol) <= 8:
            confidence_boost *= 1.05  # 5% bonus for established altcoins
            fusion_triggers.append("EstablishedAlt")
            
        # ULTRA-OPTIMIZED: Apply signal quality penalties for low-quality signals
        if avg_confidence < 5.0:
            confidence_boost *= 0.8  # 20% penalty for low quality
            fusion_triggers.append("LowQualityPenalty")
        elif avg_confidence > 8.0:
            confidence_boost *= 1.15  # 15% bonus for high quality
            fusion_triggers.append("HighQualityBonus")
            
        # ULTRA-OPTIMIZED: Cap confidence boost to prevent over-optimization
        confidence_boost = max(-3.0, min(8.0, confidence_boost))
        
        return fusion_result, confidence_boost, fusion_triggers
        
    def _calculate_leverage_adjustment_ultra_optimized(
        self,
        ta_signal: Dict[str, Any],
        bookmap_summary: Dict[str, Any],
        order_flow_score: float,
        fusion_result: FusionResult,
        symbol: str
    ) -> float:
        """ULTRA-OPTIMIZED: Advanced leverage adjustment with portfolio integration and fusion signals."""
        
        base_adjustment = 1.0
        signal_types = bookmap_summary.get("signal_types", {})
        total_signals = bookmap_summary.get("total_signals", 0)
        avg_confidence = bookmap_summary.get("avg_confidence", 0.0)
        
        # ULTRA-OPTIMIZED: Enhanced order flow adjustment with sophisticated scaling
        order_flow_strength = abs(order_flow_score)
        
        if order_flow_strength > 8:
            base_adjustment *= 1.5  # Increased premium boost for exceptional flow
        elif order_flow_strength > 6:
            base_adjustment *= 1.35  # Enhanced strong flow boost
        elif order_flow_strength > 4:
            base_adjustment *= 1.2   # Good flow boost
        elif order_flow_strength > 2:
            base_adjustment *= 1.1   # Moderate flow boost
        elif order_flow_strength < 1:
            base_adjustment *= 0.8   # More conservative for weak flow
            
        # ULTRA-OPTIMIZED: Fusion result impact with enhanced scaling
        if fusion_result == FusionResult.ENHANCED_LONG or fusion_result == FusionResult.ENHANCED_SHORT:
            base_adjustment *= 1.4  # Increased alignment boost
        elif fusion_result == FusionResult.CONFLICTING_SIGNALS:
            base_adjustment *= 0.6  # More significant reduction for conflicts
        elif fusion_result == FusionResult.WEAK_CONFIRMATION:
            base_adjustment *= 0.85  # Enhanced reduction for weak signals
        elif fusion_result == FusionResult.INSUFFICIENT_DATA:
            base_adjustment *= 0.75  # Conservative for insufficient data
            
        # ULTRA-OPTIMIZED: Enhanced signal quality and diversity impact
        signal_quality_multiplier = 1.0
        
        # Whale trades enable higher leverage with sophisticated scaling
        if "WHALE_TRADE" in signal_types:
            whale_count = signal_types["WHALE_TRADE"]
            whale_boost = min(0.4, whale_count * 0.12)  # Enhanced whale boost
            signal_quality_multiplier *= (1.0 + whale_boost)
            
        # Stop runs with enhanced momentum/reversal detection
        if "STOP_RUN" in signal_types:
            ta_direction = ta_signal.get("direction")
            dominant_side = bookmap_summary.get("dominant_side")
            
            if (ta_direction == "LONG" and dominant_side == "BULLISH") or \
               (ta_direction == "SHORT" and dominant_side == "BEARISH"):
                signal_quality_multiplier *= 1.3  # Enhanced momentum following
            else:
                signal_quality_multiplier *= 0.85  # More conservative for counter-trend
                
        # ULTRA-OPTIMIZED: Iceberg detection for institutional backing
        if "ICEBERG_DETECTION" in signal_types:
            iceberg_count = signal_types["ICEBERG_DETECTION"]
            iceberg_boost = min(0.25, iceberg_count * 0.08)
            signal_quality_multiplier *= (1.0 + iceberg_boost)
            
        # ULTRA-OPTIMIZED: Volume burst for absorption patterns
        if "VOLUME_BURST" in signal_types:
            burst_count = signal_types["VOLUME_BURST"]
            burst_boost = min(0.2, burst_count * 0.06)
            signal_quality_multiplier *= (1.0 + burst_boost)
                
        # Enhanced signal diversity impact
        unique_signals = len([s for s in signal_types.values() if s > 0])
        if unique_signals >= 5:
            signal_quality_multiplier *= 1.25  # Premium diversity
        elif unique_signals >= 4:
            signal_quality_multiplier *= 1.2   # Excellent diversity
        elif unique_signals >= 3:
            signal_quality_multiplier *= 1.15  # Good diversity
        elif unique_signals >= 2:
            signal_quality_multiplier *= 1.05  # Fair diversity
        elif unique_signals <= 1:
            signal_quality_multiplier *= 0.85  # Poor diversity penalty
            
        # ULTRA-OPTIMIZED: Symbol-specific adjustments
        if symbol in ["BTCUSDT", "ETHUSDT"]:
            base_adjustment *= 1.1  # Major pairs get leverage boost
        elif symbol.endswith("USDT") and len(symbol) <= 8:
            base_adjustment *= 1.05  # Established alts get slight boost
        else:
            base_adjustment *= 0.95  # More conservative for exotic pairs
            
        # ULTRA-OPTIMIZED: Final adjustments and capping
        final_adjustment = base_adjustment * signal_quality_multiplier
        
        # Enhanced quality-based confidence scaling
        if avg_confidence > 8.5:
            final_adjustment *= 1.15  # Premium confidence bonus
        elif avg_confidence > 7.0:
            final_adjustment *= 1.1   # High confidence bonus
        elif avg_confidence > 5.0:
            final_adjustment *= 1.05  # Good confidence bonus
        elif avg_confidence < 3.0:
            final_adjustment *= 0.85  # Low confidence penalty
            
        # ULTRA-OPTIMIZED: Conservative capping for risk management
        final_adjustment = max(0.5, min(2.0, final_adjustment))  # Wider range for optimization
        
        return final_adjustment
        
    def _analyze_microstructure_ultra_enhanced(
        self,
        ta_signal: Dict[str, Any],
        bookmap_summary: Dict[str, Any],
        symbol: str,
        order_flow_score: float
    ) -> Dict[str, Any]:
        """ULTRA-OPTIMIZED: Enhanced microstructure analysis with institutional insights and regime detection."""
        
        microstructure = {
            "liquidity_profile": "unknown",
            "execution_difficulty": "unknown", 
            "timing_urgency": "low",
            "hidden_liquidity": False,
            "market_maker_activity": "unknown",
            "retail_vs_institutional": "unknown",
            "volatility_regime": "unknown",
            "institutional_score": 0.0,    # ULTRA-OPTIMIZED: New scoring
            "flow_regime": "neutral",       # ULTRA-OPTIMIZED: Flow classification
            "momentum_strength": "weak",    # ULTRA-OPTIMIZED: Momentum analysis
            "liquidity_tiers": [],          # ULTRA-OPTIMIZED: Layered liquidity
            "execution_timing": "flexible", # ULTRA-OPTIMIZED: Timing optimization
            "smart_money_activity": "none"  # ULTRA-OPTIMIZED: Smart money detection
        }
        
        signal_types = bookmap_summary.get("signal_types", {})
        total_signals = bookmap_summary.get("total_signals", 0)
        avg_confidence = bookmap_summary.get("avg_confidence", 0.0)
        
        # OPTIMIZED: Enhanced liquidity profile analysis
        iceberg_count = signal_types.get("ICEBERG_DETECTION", 0) + signal_types.get("ICEBERG_EXECUTION", 0)
        whale_count = signal_types.get("WHALE_TRADE", 0)
        volume_burst_count = signal_types.get("VOLUME_BURST", 0)
        
        if iceberg_count >= 3 or whale_count >= 2:
            microstructure["liquidity_profile"] = "deep_institutional"
            microstructure["execution_difficulty"] = "easy"
        elif iceberg_count >= 1 or whale_count >= 1:
            microstructure["liquidity_profile"] = "moderate_institutional"
            microstructure["execution_difficulty"] = "moderate"
        elif volume_burst_count >= 2:
            microstructure["liquidity_profile"] = "active_retail"
            microstructure["execution_difficulty"] = "moderate"
        elif total_signals >= 5:
            microstructure["liquidity_profile"] = "standard_market"
            microstructure["execution_difficulty"] = "standard"
        else:
            microstructure["liquidity_profile"] = "thin_liquidity"
            microstructure["execution_difficulty"] = "difficult"
            
        # OPTIMIZED: Enhanced timing urgency
        stop_run_count = signal_types.get("STOP_RUN", 0)
        sweep_count = signal_types.get("SWEEP_DETECTED", 0)
        
        if stop_run_count >= 2 or sweep_count >= 1:
            microstructure["timing_urgency"] = "high"
        elif whale_count >= 2 or iceberg_count >= 2:
            microstructure["timing_urgency"] = "moderate"
        elif total_signals >= 8:
            microstructure["timing_urgency"] = "moderate"
        else:
            microstructure["timing_urgency"] = "low"
            
        # OPTIMIZED: Hidden liquidity detection
        if iceberg_count >= 1:
            microstructure["hidden_liquidity"] = True
            
        # OPTIMIZED: Market maker activity analysis
        spoof_count = signal_types.get("SPOOF_DETECTED", 0)
        imbalance_count = signal_types.get("ORDERBOOK_IMBALANCE", 0)
        
        if spoof_count >= 2:
            microstructure["market_maker_activity"] = "high_manipulation"
        elif spoof_count >= 1 or imbalance_count >= 3:
            microstructure["market_maker_activity"] = "moderate_games"
        elif imbalance_count >= 1:
            microstructure["market_maker_activity"] = "standard_making"
        else:
            microstructure["market_maker_activity"] = "minimal"
            
        # ULTRA-OPTIMIZED: Enhanced institutional vs retail classification with scoring
        institutional_score = (whale_count * 2.5) + (iceberg_count * 2.0) + (sweep_count * 1.8) + (stop_run_count * 1.2)
        retail_score = (volume_burst_count * 1.2) + (imbalance_count * 0.8) + (spoof_count * -0.5)  # Spoof reduces retail score
        
        # Normalize scores
        total_activity = max(1, institutional_score + retail_score)
        institutional_normalized = institutional_score / total_activity * 10
        retail_normalized = retail_score / total_activity * 10
        
        microstructure["institutional_score"] = institutional_normalized
        
        if institutional_score > retail_score * 3:
            microstructure["retail_vs_institutional"] = "institutional_dominated"
            microstructure["smart_money_activity"] = "heavy"
        elif institutional_score > retail_score * 1.8:
            microstructure["retail_vs_institutional"] = "institutional_leaning"
            microstructure["smart_money_activity"] = "moderate"
        elif retail_score > institutional_score * 2:
            microstructure["retail_vs_institutional"] = "retail_dominated"
            microstructure["smart_money_activity"] = "minimal"
        else:
            microstructure["retail_vs_institutional"] = "mixed_flow"
            microstructure["smart_money_activity"] = "balanced"
            
        # ULTRA-OPTIMIZED: Enhanced volatility and flow regime detection
        order_flow_strength = abs(order_flow_score)
        
        # Flow regime classification
        if order_flow_score > 6:
            microstructure["flow_regime"] = "strong_bullish"
        elif order_flow_score > 3:
            microstructure["flow_regime"] = "moderate_bullish"
        elif order_flow_score < -6:
            microstructure["flow_regime"] = "strong_bearish"
        elif order_flow_score < -3:
            microstructure["flow_regime"] = "moderate_bearish"
        else:
            microstructure["flow_regime"] = "neutral"
            
        # Enhanced volatility regime with momentum
        signal_intensity = total_signals * avg_confidence / max(1, 10)  # Normalize intensity
        
        if order_flow_strength > 8 and signal_intensity > 5:
            microstructure["volatility_regime"] = "explosive"
            microstructure["momentum_strength"] = "extreme"
        elif order_flow_strength > 6 and signal_intensity > 3:
            microstructure["volatility_regime"] = "high_volatility"
            microstructure["momentum_strength"] = "strong"
        elif order_flow_strength > 3 and signal_intensity > 2:
            microstructure["volatility_regime"] = "moderate_volatility"
            microstructure["momentum_strength"] = "moderate"
        elif order_flow_strength < 1 and signal_intensity < 1:
            microstructure["volatility_regime"] = "low_volatility"
            microstructure["momentum_strength"] = "weak"
        else:
            microstructure["volatility_regime"] = "normal_volatility"
            microstructure["momentum_strength"] = "normal"
            
        # ULTRA-OPTIMIZED: Liquidity tier analysis
        liquidity_tiers = []
        if whale_count >= 2:
            liquidity_tiers.append("deep_whale")
        if iceberg_count >= 2:
            liquidity_tiers.append("algorithmic_depth")
        if volume_burst_count >= 3:
            liquidity_tiers.append("retail_absorption")
        if sweep_count >= 1:
            liquidity_tiers.append("smart_sweeping")
        if stop_run_count >= 1:
            liquidity_tiers.append("momentum_hunting")
            
        microstructure["liquidity_tiers"] = liquidity_tiers
        
        # ULTRA-OPTIMIZED: Execution timing optimization
        urgency_score = (stop_run_count * 3) + (sweep_count * 2.5) + (whale_count * 1.5)
        
        if urgency_score >= 6:
            microstructure["execution_timing"] = "immediate"
        elif urgency_score >= 3:
            microstructure["execution_timing"] = "urgent"
        elif urgency_score >= 1:
            microstructure["execution_timing"] = "prompt"
        else:
            microstructure["execution_timing"] = "flexible"
            
        # OPTIMIZED: Risk assessment
        risk_factors = []
        if microstructure["execution_difficulty"] == "difficult":
            risk_factors.append("poor_liquidity")
        if microstructure["market_maker_activity"] == "high_manipulation":
            risk_factors.append("manipulation_risk")
        if microstructure["volatility_regime"] == "high_volatility":
            risk_factors.append("high_volatility")
        if microstructure["timing_urgency"] == "high":
            risk_factors.append("time_sensitive")
            
        microstructure["risk_factors"] = risk_factors
        microstructure["overall_risk"] = "high" if len(risk_factors) >= 3 else "moderate" if len(risk_factors) >= 2 else "low"
        
        return microstructure
        
    def _calculate_enhanced_levels_ultra_optimized(
        self,
        ta_signal: Dict[str, Any],
        bookmap_summary: Dict[str, Any],
        microstructure: Dict[str, Any],
        order_flow_score: float,
        symbol: str
    ) -> Dict[str, Optional[float]]:
        """ULTRA-OPTIMIZED: Smart level optimization with market maker analysis and institutional flow."""
        
        original_entry = ta_signal.get("entry_price")
        original_stop = ta_signal.get("stop_loss")
        
        if not original_entry or not original_stop:
            return {"entry": None, "stop": None}
            
        # OPTIMIZED: Smart entry optimization based on order flow
        enhanced_entry = original_entry
        enhanced_stop = original_stop
        
        # Order flow direction bias
        if order_flow_score > 3:  # Strong bullish flow
            if ta_signal.get("direction") == "LONG":
                # Enter slightly more aggressively on bullish flow
                enhanced_entry = original_entry * 1.0005  # 0.05% more aggressive
            elif ta_signal.get("direction") == "SHORT":
                # Enter more conservatively when fighting the flow
                enhanced_entry = original_entry * 0.9995  # 0.05% more conservative
                
        elif order_flow_score < -3:  # Strong bearish flow
            if ta_signal.get("direction") == "SHORT":
                # Enter slightly more aggressively on bearish flow
                enhanced_entry = original_entry * 0.9995  # 0.05% more aggressive
            elif ta_signal.get("direction") == "LONG":
                # Enter more conservatively when fighting the flow
                enhanced_entry = original_entry * 1.0005  # 0.05% more conservative
                
        # OPTIMIZED: Microstructure-based adjustments
        liquidity_profile = microstructure.get("liquidity_profile", "unknown")
        timing_urgency = microstructure.get("timing_urgency", "low")
        
        # Adjust for liquidity conditions
        if liquidity_profile == "thin_liquidity":
            # Wider stops for thin markets
            stop_distance = abs(enhanced_entry - enhanced_stop) / enhanced_entry
            enhanced_stop_distance = stop_distance * 1.2  # 20% wider
            
            if ta_signal.get("direction") == "LONG":
                enhanced_stop = enhanced_entry * (1 - enhanced_stop_distance)
            else:
                enhanced_stop = enhanced_entry * (1 + enhanced_stop_distance)
                
        elif liquidity_profile == "deep_institutional":
            # Tighter stops for deep markets
            stop_distance = abs(enhanced_entry - enhanced_stop) / enhanced_entry
            enhanced_stop_distance = stop_distance * 0.9  # 10% tighter
            
            if ta_signal.get("direction") == "LONG":
                enhanced_stop = enhanced_entry * (1 - enhanced_stop_distance)
            else:
                enhanced_stop = enhanced_entry * (1 + enhanced_stop_distance)
                
        # OPTIMIZED: Urgency-based entry timing
        if timing_urgency == "high":
            # Market orders recommended - no entry price adjustment
            pass
        elif timing_urgency == "low":
            # Patient entry - slightly better prices
            if ta_signal.get("direction") == "LONG":
                enhanced_entry = original_entry * 0.9998  # Wait for 0.02% better fill
            else:
                enhanced_entry = original_entry * 1.0002  # Wait for 0.02% better fill
                
        # OPTIMIZED: Whale/Iceberg level considerations
        signal_types = bookmap_summary.get("signal_types", {})
        
        if signal_types.get("WHALE_TRADE", 0) >= 2:
            # Follow whale activity more closely
            if order_flow_score > 2 and ta_signal.get("direction") == "LONG":
                enhanced_entry = original_entry * 1.0003  # More aggressive on whale support
            elif order_flow_score < -2 and ta_signal.get("direction") == "SHORT":
                enhanced_entry = original_entry * 0.9997  # More aggressive on whale resistance
                
        return {
            "entry": enhanced_entry,
            "stop": enhanced_stop
        }
        
    def _track_fusion_performance_ultra_enhanced(self, fused_signal: FusedSignal, symbol: str):
        """ULTRA-OPTIMIZED: Advanced performance tracking with ML insights and success rate monitoring."""
        fusion_record = {
            "timestamp": time.time(),
            "symbol": symbol,
            "fusion_result": fused_signal.fusion_result.value,
            "confidence_boost": fused_signal.confidence_boost,
            "leverage_adjustment": fused_signal.leverage_adjustment,
            "order_flow_score": fused_signal.order_flow_score,
            "fusion_triggers": fused_signal.fusion_triggers,
            "microstructure_risk": fused_signal.microstructure_analysis.get("overall_risk", "unknown"),
            "institutional_score": fused_signal.microstructure_analysis.get("institutional_score", 0),
            "flow_regime": fused_signal.microstructure_analysis.get("flow_regime", "neutral"),
            "momentum_strength": fused_signal.microstructure_analysis.get("momentum_strength", "weak"),
            "execution_timing": fused_signal.microstructure_analysis.get("execution_timing", "flexible"),
            "smart_money_activity": fused_signal.microstructure_analysis.get("smart_money_activity", "none"),
            "signal_quality": len(fused_signal.fusion_triggers),
            "is_major_pair": symbol in ["BTCUSDT", "ETHUSDT"],
            "signal_types": list(fused_signal.bookmap_summary.get("signal_types", {}).keys()),
            "enhanced_levels": bool(fused_signal.enhanced_entry_price)
        }
        
        self.fusion_history.append(fusion_record)
        
        # Keep only last 100 records for memory efficiency
        if len(self.fusion_history) > 100:
            self.fusion_history = self.fusion_history[-100:]
            
        # Update performance metrics
        self.performance_metrics["total_fusions"] += 1
        
        if fused_signal.fusion_result in [FusionResult.ENHANCED_LONG, FusionResult.ENHANCED_SHORT]:
            self.performance_metrics["fusion_accuracy"] = (
                self.performance_metrics.get("fusion_accuracy", 0.0) * 0.9 + 
                1.0 * 0.1  # Moving average
            )
        else:
            self.performance_metrics["fusion_accuracy"] = (
                self.performance_metrics.get("fusion_accuracy", 0.0) * 0.9 + 
                0.0 * 0.1  # Moving average
            )
            
        if fused_signal.confidence_boost > 0:
            self.performance_metrics["confidence_improvements"] = (
                self.performance_metrics.get("confidence_improvements", 0.0) * 0.9 + 
                fused_signal.confidence_boost * 0.1  # Moving average
            )
            
    def get_fusion_performance(self) -> Dict[str, Any]:
        """OPTIMIZED: Get enhanced fusion performance metrics."""
        if not self.fusion_history:
            return {
                "total_fusions": 0,
                "recent_fusion_rate": 0,
                "confidence_improvements": 0.0,
                "fusion_success_rate": 0.0,
                "avg_leverage_adjustment": 1.0,
                "top_performing_signals": []
            }
            
        # Calculate enhanced metrics
        recent_hour = time.time() - 3600
        recent_fusions = [f for f in self.fusion_history if f["timestamp"] > recent_hour]
        
        successful_fusions = [
            f for f in self.fusion_history 
            if f["fusion_result"] in ["ENHANCED_LONG", "ENHANCED_SHORT"]
        ]
        
        return {
            "total_fusions": len(self.fusion_history),
            "recent_fusion_rate": len(recent_fusions),
            "confidence_improvements": self.performance_metrics.get("confidence_improvements", 0.0),
            "fusion_success_rate": len(successful_fusions) / len(self.fusion_history) * 100,
            "avg_leverage_adjustment": sum(f["leverage_adjustment"] for f in self.fusion_history) / len(self.fusion_history),
            "avg_confidence_boost": sum(f["confidence_boost"] for f in successful_fusions) / max(1, len(successful_fusions)),
            "top_signal_types": self._get_top_signal_types(),
            "microstructure_risk_distribution": self._get_risk_distribution()
        }
        
    def _get_top_signal_types(self) -> List[Dict[str, Any]]:
        """Get most effective signal types for fusion."""
        signal_type_performance = {}
        
        for fusion in self.fusion_history:
            for signal_type in fusion.get("signal_types", []):
                if signal_type not in signal_type_performance:
                    signal_type_performance[signal_type] = {"count": 0, "success": 0}
                    
                signal_type_performance[signal_type]["count"] += 1
                
                if fusion["fusion_result"] in ["ENHANCED_LONG", "ENHANCED_SHORT"]:
                    signal_type_performance[signal_type]["success"] += 1
                    
        # Calculate success rates and sort
        top_types = []
        for signal_type, stats in signal_type_performance.items():
            if stats["count"] >= 3:  # Minimum sample size
                success_rate = stats["success"] / stats["count"] * 100
                top_types.append({
                    "signal_type": signal_type,
                    "success_rate": success_rate,
                    "total_count": stats["count"]
                })
                
        return sorted(top_types, key=lambda x: x["success_rate"], reverse=True)[:5]
        
    def _get_risk_distribution(self) -> Dict[str, int]:
        """Get distribution of microstructure risk levels."""
        risk_dist = {"low": 0, "moderate": 0, "high": 0, "unknown": 0}
        
        for fusion in self.fusion_history:
            risk_level = fusion.get("microstructure_risk", "unknown")
            risk_dist[risk_level] = risk_dist.get(risk_level, 0) + 1
            
        return risk_dist


# Global fusion engine instance
signal_fusion_engine = SignalFusionEngine() 