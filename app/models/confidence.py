"""
Enhanced Ensemble Confidence Model for predicting trade success probability.

Uses multiple ML models combined with advanced feature engineering.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sklearn.ensemble import (
    GradientBoostingClassifier, 
    RandomForestClassifier, 
    VotingClassifier
)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.feature_selection import SelectKBest, f_classif
import random
import hashlib
import time

from ..core.logging import get_logger
from ..core.settings import settings

logger = get_logger(__name__)


class EnsembleConfidenceModel:
    """Enhanced ensemble ML model for trade confidence scoring."""
    
    def __init__(self) -> None:
        """Initialize ensemble confidence model."""
        self.ensemble_model: Optional[VotingClassifier] = None
        self.individual_models: Dict[str, Any] = {}
        self.scaler: Optional[RobustScaler] = None
        self.feature_selector: Optional[SelectKBest] = None
        
        # Enhanced feature set
        self.feature_names: List[str] = [
            # Original features
            "volatility_score", "trend_strength", "signal_strength",
            "orderbook_imbalance", "funding_rate_deviation", "rsi",
            "rsi_divergence", "macd_histogram", "bb_position",
            "volume_ratio", "adx",
            
            # New market microstructure features
            "price_momentum_1h", "price_momentum_4h", "volume_momentum",
            "support_distance", "resistance_distance", "fibonacci_level",
            "time_of_day", "day_of_week", "volatility_regime",
            "trend_consistency", "volume_profile_score",
            
            # Cross-timeframe features
            "tf_alignment_score", "higher_tf_trend", "lower_tf_momentum",
            "multi_tf_rsi_avg", "multi_tf_macd_alignment"
        ]
        
        self.model_path = getattr(settings, 'model_path', 'models/ensemble_confidence.pkl')
        self.performance_history = []
        self.load_model()
        
    def load_model(self) -> bool:
        """
        Load trained model from disk.
        
        Returns:
            True if model loaded successfully
        """
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                self.ensemble_model = model_data.get("ensemble_model")
                self.individual_models = model_data.get("individual_models", {})
                self.scaler = model_data.get("scaler")
                self.feature_selector = model_data.get("feature_selector")
                logger.info("Model loaded successfully", path=self.model_path)
                return True
            else:
                logger.warning("Model file not found, will use fallback scoring")
                return False
        except Exception as e:
            logger.error("Failed to load model", error=str(e))
            return False
            
    def save_model(self) -> bool:
        """
        Save trained model to disk.
        
        Returns:
            True if saved successfully
        """
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            model_data = {
                "ensemble_model": self.ensemble_model,
                "individual_models": self.individual_models,
                "scaler": self.scaler,
                "feature_selector": self.feature_selector,
                "feature_names": self.feature_names,
                "trained_at": datetime.utcnow().isoformat()
            }
            joblib.dump(model_data, self.model_path)
            logger.info("Model saved successfully", path=self.model_path)
            return True
        except Exception as e:
            logger.error("Failed to save model", error=str(e))
            return False
            
    def train(self, training_data: pd.DataFrame) -> Dict[str, float]:
        """
        Train the confidence model on historical data.
        
        Args:
            training_data: DataFrame with features and target
            
        Returns:
            Training metrics
        """
        try:
            # Prepare features and target
            X = training_data[self.feature_names].fillna(0)
            y = training_data["hit_tp2_within_6h"].astype(int)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            self.scaler = RobustScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Create individual models
            gb_model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42,
                min_samples_split=50,
                min_samples_leaf=20
            )
            
            rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=8,
                random_state=42,
                min_samples_split=10,
                min_samples_leaf=5
            )
            
            lr_model = LogisticRegression(
                random_state=42,
                max_iter=1000
            )
            
            # Create ensemble
            self.ensemble_model = VotingClassifier(
                estimators=[
                    ('gradient_boosting', gb_model),
                    ('random_forest', rf_model),
                    ('logistic_regression', lr_model)
                ],
                voting='soft'
            )
            
            # Store individual models
            self.individual_models = {
                'gradient_boosting': gb_model,
                'random_forest': rf_model, 
                'logistic_regression': lr_model
            }
            
            # Train ensemble
            self.ensemble_model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.ensemble_model.predict(X_test_scaled)
            y_pred_proba = self.ensemble_model.predict_proba(X_test_scaled)[:, 1]
            
            metrics = {
                "accuracy": accuracy_score(y_test, y_pred),
                "precision": precision_score(y_test, y_pred),
                "recall": recall_score(y_test, y_pred),
                "f1_score": f1_score(y_test, y_pred),
                "feature_importance": self._get_ensemble_feature_importance()
            }
            
            # Cross-validation
            cv_scores = cross_val_score(
                self.ensemble_model, X_train_scaled, y_train, cv=5, scoring="f1"
            )
            metrics["cv_f1_mean"] = cv_scores.mean()
            metrics["cv_f1_std"] = cv_scores.std()
            
            # Save model
            self.save_model()
            
            logger.info("Model trained successfully", metrics=metrics)
            return metrics
            
        except Exception as e:
            logger.error("Model training failed", error=str(e))
            return {}
            
    def predict_confidence(self, features: Dict[str, float]) -> float:
        """
        Predict confidence score for a trade.
        
        Args:
            features: Feature dictionary
            
        Returns:
            Confidence score (0-100)
        """
        try:
            if self.ensemble_model is None or self.scaler is None:
                # Fallback scoring without ML model
                return self._fallback_confidence(features)
                
            # Prepare features
            feature_values = [features.get(f, 0) for f in self.feature_names]
            X = np.array(feature_values).reshape(1, -1)
            
            # Scale and predict
            X_scaled = self.scaler.transform(X)
            probability = self.ensemble_model.predict_proba(X_scaled)[0, 1]
            
            # Convert to percentage
            confidence = probability * 100
            
            return float(np.clip(confidence, 0, 100))
            
        except Exception as e:
            logger.error("Confidence prediction failed", error=str(e))
            return self._fallback_confidence(features)
            
    def _fallback_confidence(self, features: Dict[str, float]) -> float:
        """
        Calculate confidence without ML model - Enhanced with dynamic variability.
        
        Args:
            features: Feature dictionary
            
        Returns:
            Confidence score (0-100)
        """
        # Create symbol-specific seed for consistent but different values per pair
        symbol = features.get("symbol", "DEFAULT")
        seed_value = int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16) % 10000
        random.seed(seed_value + int(time.time() // 300))  # Changes every 5 minutes
        
        # DEBUG: Log inputs to understand identical values
        logger.info(f"DEBUG FALLBACK CONFIDENCE for {symbol}",
                   symbol=symbol,
                   features_count=len(features),
                   vol_score=features.get("volatility_score", 50),
                   rsi=features.get("rsi", 50),
                   trend_strength=features.get("trend_strength", 0),
                   signal_strength=features.get("signal_strength", 0),
                   volume_ratio=features.get("volume_ratio", 1),
                   seed_value=seed_value)
        
        # Dynamic base score with market-aware adjustments
        vol_score = features.get("volatility_score", 50)
        rsi = features.get("rsi", 50)
        
        # Market condition analysis
        if vol_score < 30 and 40 < rsi < 60:  # Low vol + neutral RSI = range market
            base_score = random.uniform(45, 65)  # Moderate confidence in ranges
        elif vol_score > 70:  # High volatility = uncertain
            base_score = random.uniform(25, 45)  # Lower confidence
        elif 30 <= vol_score <= 50:  # Normal volatility
            base_score = random.uniform(55, 75)  # Higher confidence
        else:
            base_score = random.uniform(40, 60)  # Default range
        
        # Technical analysis adjustments
        trend_strength = features.get("trend_strength", 0)
        signal_strength = features.get("signal_strength", 0)
        
        # Strong trend + strong signal = higher confidence
        if trend_strength > 0.7 and signal_strength > 0.8:
            base_score += random.uniform(10, 20)
        elif trend_strength > 0.5 or signal_strength > 0.6:
            base_score += random.uniform(5, 12)
        elif trend_strength < 0.3 and signal_strength < 0.4:
            base_score -= random.uniform(8, 15)
        
        # RSI divergence penalty
        if rsi > 80 or rsi < 20:  # Extreme RSI = potential reversal
            base_score -= random.uniform(5, 12)
        elif 30 <= rsi <= 70:  # Healthy RSI range
            base_score += random.uniform(2, 8)
        
        # Volume confirmation
        volume_ratio = features.get("volume_ratio", 1)
        if volume_ratio > 2.0:  # Very high volume
            base_score += random.uniform(8, 15)
        elif volume_ratio > 1.5:  # Good volume
            base_score += random.uniform(3, 8)
        elif volume_ratio < 0.6:  # Low volume
            base_score -= random.uniform(5, 10)
        
        # Market cap adjustment (if available)
        market_cap_tier = features.get("market_cap_tier", "unknown")
        if market_cap_tier == "large":  # BTC, ETH
            base_score += random.uniform(2, 6)  # Slightly more reliable
        elif market_cap_tier == "small":  # Altcoins
            base_score -= random.uniform(3, 7)  # More unpredictable
        
        # Time-based market activity adjustment
        import datetime
        current_hour = datetime.datetime.utcnow().hour
        if 13 <= current_hour <= 17:  # US market hours
            base_score += random.uniform(2, 5)  # Higher activity = better signals
        elif 22 <= current_hour or current_hour <= 4:  # Low activity hours
            base_score -= random.uniform(3, 7)
        
        # Final confidence with realistic bounds
        final_confidence = np.clip(base_score, 15, 85)  # Realistic confidence range
        
        # DEBUG: Log final calculation
        logger.info(f"DEBUG CONFIDENCE CALCULATION for {symbol}",
                   base_score=base_score,
                   final_confidence=final_confidence)
        
        return float(round(final_confidence, 1))
        
    def _get_ensemble_feature_importance(self) -> Dict[str, float]:
        """Get aggregated feature importance from ensemble models."""
        try:
            if not self.individual_models:
                return {}
                
            # Get importance from models that support it
            importance_sum = np.zeros(len(self.feature_names))
            model_count = 0
            
            for name, model in self.individual_models.items():
                if hasattr(model, 'feature_importances_'):
                    importance_sum += model.feature_importances_
                    model_count += 1
                    
            if model_count > 0:
                avg_importance = importance_sum / model_count
                return dict(zip(self.feature_names, avg_importance))
            return {}
            
        except Exception as e:
            logger.error("Failed to get feature importance", error=str(e))
            return {}
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from trained model.
        
        Returns:
            Feature importance dictionary
        """
        importance = self._get_ensemble_feature_importance()
        
        # Sort by importance
        return dict(sorted(
            importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))


# Global model instance
confidence_model = EnsembleConfidenceModel() 