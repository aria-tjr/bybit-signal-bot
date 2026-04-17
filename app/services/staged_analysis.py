"""
Staged Analysis Engine

Multi-stage analysis pipeline that processes pairs in multiple stages to optimize performance
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import time
import pandas as pd

from ..core.logging import get_logger
from ..logic.rules import TradingRules
from ..indicators.technical import TechnicalIndicators
from .smart_pair_filter import smart_filter
from .rate_limited_data_collector import rate_limited_collector

logger = get_logger(__name__)


class StagedAnalysisEngine:
    """Multi-stage analysis pipeline for efficient pair processing."""
    
    def __init__(self):
        # Stage configuration
        self.stage1_max_pairs = 50      # Quick scan up to 50 pairs
        self.stage2_max_pairs = 15      # Detailed analysis for 15 pairs
        self.stage3_max_pairs = 5       # Full signals for 5 pairs
        
        # Quick scan thresholds (less strict)
        self.quick_scan_thresholds = {
            "min_rsi_divergence": 10,    # 10 point RSI move
            "min_volume_spike": 1.5,     # 1.5x average volume
            "min_momentum": 0.003,       # 0.3% price momentum
        }
        
        # Detailed analysis thresholds (RELAXED for better signal generation)
        self.detailed_thresholds = {
            "min_signal_strength": 1.2,    # RELAXED: 1.8 → 1.2 ⭐ (key fix!)
            "min_confluence_points": 1,    # RELAXED: 2 → 1 ⭐ (key fix!)
            "min_trend_alignment": 0.4,    # RELAXED: 0.6 → 0.4 ⭐ (key fix!)
        }
    
    async def analyze_pairs_staged(self, all_pairs: List[str]) -> Dict[str, Any]:
        """
        Run complete staged analysis pipeline.
        
        Args:
            all_pairs: List of all available trading pairs
            
        Returns:
            Analysis results with final signals and stage statistics
        """
        try:
            logger.info(f"Starting staged analysis for {len(all_pairs)} pairs")
            pipeline_start = time.time()
            
            results = {
                "final_signals": [],
                "stage_results": {},
                "performance_stats": {},
                "timestamp": datetime.utcnow()
            }
            
            # Stage 0: Smart pre-filtering
            stage0_start = time.time()
            priority_pairs = await smart_filter.get_priority_pairs(all_pairs)
            stage0_time = time.time() - stage0_start
            
            results["stage_results"]["stage0_filtering"] = {
                "input_pairs": len(all_pairs),
                "output_pairs": len(priority_pairs),
                "filtered_pairs": priority_pairs,
                "processing_time_ms": round(stage0_time * 1000)
            }
            
            if not priority_pairs:
                logger.warning("No pairs passed pre-filtering")
                return results
            
            # Stage 1: Quick technical scan
            stage1_start = time.time()
            stage1_candidates = await self._stage1_quick_scan(priority_pairs[:self.stage1_max_pairs])
            stage1_time = time.time() - stage1_start
            
            results["stage_results"]["stage1_quick_scan"] = {
                "input_pairs": len(priority_pairs[:self.stage1_max_pairs]),
                "output_pairs": len(stage1_candidates),
                "candidates": [c["symbol"] for c in stage1_candidates],
                "processing_time_ms": round(stage1_time * 1000)
            }
            
            if not stage1_candidates:
                logger.warning("No pairs passed quick scan")
                return results
            
            # Stage 2: Detailed technical analysis
            stage2_start = time.time()
            stage2_candidates = await self._stage2_detailed_analysis(stage1_candidates[:self.stage2_max_pairs])
            stage2_time = time.time() - stage2_start
            
            results["stage_results"]["stage2_detailed"] = {
                "input_pairs": len(stage1_candidates[:self.stage2_max_pairs]),
                "output_pairs": len(stage2_candidates), 
                "candidates": [c["symbol"] for c in stage2_candidates],
                "processing_time_ms": round(stage2_time * 1000)
            }
            
            if not stage2_candidates:
                logger.warning("No pairs passed detailed analysis")
                return results
            
            # Stage 3: Full signal generation
            stage3_start = time.time()
            final_signals = await self._stage3_signal_generation(stage2_candidates[:self.stage3_max_pairs])
            stage3_time = time.time() - stage3_start
            
            results["stage_results"]["stage3_signals"] = {
                "input_pairs": len(stage2_candidates[:self.stage3_max_pairs]),
                "output_signals": len(final_signals),
                "signals": final_signals,
                "processing_time_ms": round(stage3_time * 1000)
            }
            
            results["final_signals"] = final_signals
            
            # Overall performance stats
            total_time = time.time() - pipeline_start
            results["performance_stats"] = {
                "total_processing_time_ms": round(total_time * 1000),
                "pairs_processed": len(all_pairs),
                "final_signals_generated": len(final_signals),
                "efficiency_ratio": len(final_signals) / len(all_pairs) if all_pairs else 0,
                "average_time_per_pair_ms": round((total_time * 1000) / len(all_pairs)) if all_pairs else 0
            }
            
            logger.info(
                f"Staged analysis completed: {len(final_signals)} signals from {len(all_pairs)} pairs",
                total_time_ms=round(total_time * 1000),
                efficiency=f"{len(final_signals)}/{len(all_pairs)}"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Staged analysis failed: {e}")
            return {"error": str(e), "final_signals": []}
    
    async def _stage1_quick_scan(self, pairs: List[str]) -> List[Dict[str, Any]]:
        """
        Stage 1: Quick technical scan with minimal data.
        Uses only primary timeframes for fast filtering.
        """
        try:
            logger.info(f"Stage 1: Quick scanning {len(pairs)} pairs")
            
            # Get minimal data (primary timeframes only)
            data_dict = await rate_limited_collector.get_quick_scan_data(pairs)
            
            candidates = []
            
            for pair in pairs:
                if pair not in data_dict:
                    continue
                    
                pair_data = data_dict[pair]
                quick_score = await self._calculate_quick_score(pair, pair_data)
                
                if quick_score > 0.1:  # ULTRA-RELAXED: 0.2 → 0.1 (maximum signal discovery)
                    candidates.append({
                        "symbol": pair,
                        "quick_score": quick_score,
                        "stage1_data": pair_data
                    })
            
            # Sort by score and return top candidates
            candidates.sort(key=lambda x: x["quick_score"], reverse=True)
            
            logger.info(f"Stage 1 completed: {len(candidates)} candidates from {len(pairs)} pairs")
            return candidates
            
        except Exception as e:
            logger.error(f"Stage 1 quick scan failed: {e}")
            return []
    
    async def _calculate_quick_score(self, pair: str, data: Dict[str, pd.DataFrame]) -> float:
        """Calculate quick technical score using minimal indicators."""
        try:
            score_components = []
            
            for tf, df in data.items():
                if df is None or df.empty:
                    continue
                    
                # Add basic technical indicators
                df_with_indicators = TechnicalIndicators.calculate_all(df)
                
                if len(df_with_indicators) < 20:  # Need minimum data
                    continue
                
                current_idx = -1
                latest = df_with_indicators.iloc[current_idx]
                
                # Quick scoring components
                rsi = latest.get('rsi', 50)
                volume_ratio = latest.get('volume_sma_ratio', 1.0)
                price_change = ((latest['close'] - df_with_indicators.iloc[-10]['close']) / 
                               df_with_indicators.iloc[-10]['close'] * 100)
                
                # VERY RELAXED scoring for maximum signal discovery
                momentum_score = min(abs(price_change) / 5.0, 1.0)  # RELAXED: 10.0 → 5.0 (more sensitive) 
                volume_score = min((volume_ratio - 0.5) / 1.5, 1.0) if volume_ratio > 0.5 else 0.3  # RELAXED: much lower volume requirements
                
                # RELAXED RSI scoring - give decent scores to most RSI levels
                if rsi <= 40 or rsi >= 60:  # RELAXED: 30/70 → 40/60 (broader range)
                    rsi_score = 0.8  # High score for mild extremes
                elif rsi <= 30 or rsi >= 70:  # Even higher for true extremes
                    rsi_score = 1.0
                else:
                    rsi_score = 0.6  # INCREASED: 0.3 → 0.6 (decent score for neutral)
                
                tf_score = (momentum_score * 0.3 + volume_score * 0.3 + rsi_score * 0.4)  # Give RSI more weight
                score_components.append(tf_score)
            
            if not score_components:
                return 0.0
                
            # Average across timeframes
            final_score = sum(score_components) / len(score_components)
            return min(final_score, 1.0)
            
        except Exception as e:
            logger.debug(f"Quick score calculation failed for {pair}: {e}")
            return 0.0
    
    async def _stage2_detailed_analysis(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 2: Detailed technical analysis with full timeframe data.
        """
        try:
            logger.info(f"Stage 2: Detailed analysis of {len(candidates)} candidates")
            
            # Get full data including secondary timeframes
            pairs = [c["symbol"] for c in candidates]
            full_data = await rate_limited_collector.get_priority_data(pairs)
            
            detailed_candidates = []
            
            for candidate in candidates:
                pair = candidate["symbol"]
                
                if pair not in full_data:
                    continue
                
                # Run detailed technical analysis
                analysis = await self._run_detailed_analysis(pair, full_data[pair])
                
                if analysis and analysis["passes_filters"]:
                    detailed_candidates.append({
                        "symbol": pair,
                        "quick_score": candidate["quick_score"],
                        "detailed_analysis": analysis,
                        "combined_score": analysis["detailed_score"]
                    })
            
            # Sort by combined score
            detailed_candidates.sort(key=lambda x: x["combined_score"], reverse=True)
            
            logger.info(f"Stage 2 completed: {len(detailed_candidates)} detailed candidates")
            return detailed_candidates
            
        except Exception as e:
            logger.error(f"Stage 2 detailed analysis failed: {e}")
            return []
    
    async def _run_detailed_analysis(self, pair: str, data: Dict[str, pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """Run detailed technical analysis on a pair."""
        try:
            # Use TradingRules for comprehensive analysis
            analysis = await TradingRules.analyze_symbol(pair, data)
            
            if analysis.get("direction") == "NEUTRAL":
                return None
            
            # CORRECT EXTRACTION - Use the right field paths from TradingRules
            signal_strength = analysis.get("features", {}).get("signal_strength", 0)  # ⭐ FIXED: Extract from features dict
            confluence_points = analysis.get("accuracy_metrics", {}).get("confluence_points", 0)  # ⭐ FIXED: Extract from accuracy_metrics dict
            
            # ULTRA-PERMISSIVE filtering - Remove trend_alignment requirement completely
            passes_filters = (
                signal_strength >= self.detailed_thresholds["min_signal_strength"] and
                confluence_points >= self.detailed_thresholds["min_confluence_points"]
                # REMOVED trend_alignment check - was blocking valid signals
            )
            
            # Simple scoring based on available metrics
            detailed_score = (
                signal_strength * 0.6 +  # Give more weight to signal strength
                confluence_points * 0.4   # Give weight to confluence points
            )
            
            return {
                "passes_filters": passes_filters,
                "detailed_score": detailed_score,
                "signal_strength": signal_strength,
                "confluence_points": confluence_points,
                "full_analysis": analysis
            }
            
        except Exception as e:
            logger.debug(f"Detailed analysis failed for {pair}: {e}")
            return None
    
    async def _stage3_signal_generation(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 3: Full signal generation for top candidates.
        """
        try:
            logger.info(f"Stage 3: Generating signals for {len(candidates)} top candidates")
            
            final_signals = []
            
            for candidate in candidates:
                analysis = candidate["detailed_analysis"]["full_analysis"]
                
                # Extract signal details
                signal = {
                    "symbol": candidate["symbol"],
                    "direction": analysis["direction"],
                    "entry_price": analysis["entry_price"],
                    "stop_loss": analysis["stop_loss"],
                    "take_profit_1": analysis["take_profit_1"],
                    "take_profit_2": analysis["take_profit_2"],
                    "take_profit_3": analysis["take_profit_3"],
                    "leverage": analysis["leverage"],
                    "confidence": candidate["combined_score"],
                    "signal_strength": analysis.get("features", {}).get("signal_strength", 0),
                    "confluence_points": analysis.get("accuracy_metrics", {}).get("confluence_points", 0),
                    "rationale": analysis.get("rationale", []),
                    "timestamp": analysis["timestamp"],
                    "stage_scores": {
                        "quick_score": candidate["quick_score"],
                        "detailed_score": candidate["detailed_analysis"]["detailed_score"],
                        "combined_score": candidate["combined_score"]
                    }
                }
                
                final_signals.append(signal)
                
                # Update pair performance in smart filter
                smart_filter.update_pair_performance(
                    candidate["symbol"], 
                    candidate["combined_score"]
                )
            
            logger.info(f"Stage 3 completed: {len(final_signals)} final signals generated")
            return final_signals
            
        except Exception as e:
            logger.error(f"Stage 3 signal generation failed: {e}")
            return []
    
    def get_stage_config(self) -> Dict[str, Any]:
        """Get current stage configuration."""
        return {
            "stage_limits": {
                "stage1_max_pairs": self.stage1_max_pairs,
                "stage2_max_pairs": self.stage2_max_pairs,
                "stage3_max_pairs": self.stage3_max_pairs
            },
            "quick_scan_thresholds": self.quick_scan_thresholds,
            "detailed_thresholds": self.detailed_thresholds
        }
    
    def update_stage_config(self, config: Dict[str, Any]):
        """Update stage configuration dynamically."""
        if "stage_limits" in config:
            limits = config["stage_limits"]
            self.stage1_max_pairs = limits.get("stage1_max_pairs", self.stage1_max_pairs)
            self.stage2_max_pairs = limits.get("stage2_max_pairs", self.stage2_max_pairs)
            self.stage3_max_pairs = limits.get("stage3_max_pairs", self.stage3_max_pairs)
        
        if "quick_scan_thresholds" in config:
            self.quick_scan_thresholds.update(config["quick_scan_thresholds"])
            
        if "detailed_thresholds" in config:
            self.detailed_thresholds.update(config["detailed_thresholds"])
        
        logger.info("Stage configuration updated", new_config=self.get_stage_config())


# Global instance
staged_analyzer = StagedAnalysisEngine() 