"""
Technical indicators calculation module.

Provides calculation of various technical indicators using TA-Lib and pandas_ta.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import pandas_ta as ta
# import talib  # Commented out for ARM64 compatibility
from scipy import stats

from ..core.logging import get_logger

logger = get_logger(__name__)


class TechnicalIndicators:
    """Calculate technical indicators for market analysis."""
    
    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all indicators for a DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicator columns
        """
        if df.empty:
            return df
            
        df = df.copy()
        
        # Basic indicators
        df = TechnicalIndicators.add_moving_averages(df)
        df = TechnicalIndicators.add_rsi(df)
        df = TechnicalIndicators.add_macd(df)
        df = TechnicalIndicators.add_bollinger_bands(df)
        df = TechnicalIndicators.add_atr(df)
        df = TechnicalIndicators.add_volume_indicators(df)
        
        # Advanced indicators for swing trading
        df = TechnicalIndicators.add_stochastic(df)
        df = TechnicalIndicators.add_adx(df)
        df = TechnicalIndicators.add_williams_r(df)
        df = TechnicalIndicators.add_cci(df)
        df = TechnicalIndicators.add_mfi(df)
        df = TechnicalIndicators.add_swing_indicators(df)
        
        return df
        
    @staticmethod
    def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
        """Add various moving averages."""
        # Exponential Moving Averages
        df['EMA_20'] = ta.ema(df['close'], length=20)
        df['EMA_50'] = ta.ema(df['close'], length=50)
        df['EMA_200'] = ta.ema(df['close'], length=200)
        
        # Simple Moving Averages
        df['SMA_20'] = ta.sma(df['close'], length=20)
        df['SMA_50'] = ta.sma(df['close'], length=50)
        
        # Volume Weighted Average Price
        df['VWAP'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
        
        return df
        
    @staticmethod
    def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Relative Strength Index."""
        df['RSI'] = ta.rsi(df['close'], length=period)
        
        # RSI divergence
        df['RSI_divergence'] = TechnicalIndicators._calculate_divergence(
            df['close'], df['RSI']
        )
        
        return df
        
    @staticmethod
    def add_macd(df: pd.DataFrame) -> pd.DataFrame:
        """Add MACD indicators."""
        macd_df = ta.macd(df['close'], fast=12, slow=26, signal=9)
        
        df['MACD'] = macd_df['MACD_12_26_9']
        df['MACD_signal'] = macd_df['MACDs_12_26_9']
        df['MACD_hist'] = macd_df['MACDh_12_26_9']
        
        # MACD cross signals
        df['MACD_cross_up'] = (
            (df['MACD'] > df['MACD_signal']) & 
            (df['MACD'].shift(1) <= df['MACD_signal'].shift(1))
        )
        df['MACD_cross_down'] = (
            (df['MACD'] < df['MACD_signal']) & 
            (df['MACD'].shift(1) >= df['MACD_signal'].shift(1))
        )
        
        return df
        
    @staticmethod
    def add_bollinger_bands(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """Add Bollinger Bands."""
        bb_df = ta.bbands(df['close'], length=period, std=2)
        
        df['BB_upper'] = bb_df[f'BBU_{period}_2.0']
        df['BB_middle'] = bb_df[f'BBM_{period}_2.0']
        df['BB_lower'] = bb_df[f'BBL_{period}_2.0']
        df['BB_width'] = df['BB_upper'] - df['BB_lower']
        df['BB_pct'] = (df['close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])
        
        # Bollinger Band squeeze detection
        df['BB_squeeze'] = df['BB_width'] < df['BB_width'].rolling(100).mean()
        
        return df
        
    @staticmethod
    def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Average True Range."""
        df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=period)
        df['ATR_pct'] = (df['ATR'] / df['close']) * 100
        
        # ATR percentile rank
        df['ATR_pct_rank'] = df['ATR_pct'].rolling(100).apply(
            lambda x: stats.percentileofscore(x, x.iloc[-1])
        )
        
        return df
        
    @staticmethod
    def add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based indicators."""
        # On Balance Volume
        df['OBV'] = ta.obv(df['close'], df['volume'])
        
        # Volume Moving Average
        df['Volume_MA'] = df['volume'].rolling(20).mean()
        df['Volume_ratio'] = df['volume'] / df['Volume_MA']
        
        # Accumulation/Distribution
        df['AD'] = ta.ad(df['high'], df['low'], df['close'], df['volume'])
        
        # Chaikin Money Flow
        df['CMF'] = ta.cmf(df['high'], df['low'], df['close'], df['volume'])
        
        # Volume Z-score
        df['Volume_zscore'] = (
            (df['volume'] - df['volume'].rolling(20).mean()) / 
            df['volume'].rolling(20).std()
        )
        
        return df
        
    @staticmethod
    def add_stochastic(df: pd.DataFrame) -> pd.DataFrame:
        """Add Stochastic Oscillator."""
        stoch_df = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3, smooth_k=3)
        
        df['STOCH_K'] = stoch_df['STOCHk_14_3_3']
        df['STOCH_D'] = stoch_df['STOCHd_14_3_3']
        
        # Stochastic RSI
        stochrsi_df = ta.stochrsi(df['close'], length=14, rsi_length=14, k=3, d=3)
        df['STOCHRSI_K'] = stochrsi_df['STOCHRSIk_14_14_3_3']
        df['STOCHRSI_D'] = stochrsi_df['STOCHRSId_14_14_3_3']
        
        return df
        
    @staticmethod
    def add_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Average Directional Index."""
        adx_df = ta.adx(df['high'], df['low'], df['close'], length=period)
        df['ADX'] = adx_df[f'ADX_{period}']
        df['DI_plus'] = adx_df[f'DMP_{period}']
        df['DI_minus'] = adx_df[f'DMN_{period}']
        
        # Trend strength
        df['trend_strength'] = np.where(df['ADX'] > 25, 'Strong', 'Weak')
        
        return df
        
    @staticmethod
    def add_williams_r(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Williams %R."""
        df['WILLR'] = ta.willr(df['high'], df['low'], df['close'], length=period)
        return df
        
    @staticmethod
    def add_cci(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """Add Commodity Channel Index."""
        df['CCI'] = ta.cci(df['high'], df['low'], df['close'], length=period)
        return df
        
    @staticmethod
    def add_mfi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Money Flow Index with proper data type handling."""
        try:
            # Create explicit copies to avoid pandas warnings about dtype incompatibility
            df_copy = df.copy()
            
            # Ensure all required columns are properly typed as float64
            # Convert scientific notation and large numbers properly
            for col in ['volume', 'high', 'low', 'close']:
                if col in df_copy.columns:
                    # Convert to string first to handle scientific notation, then to float
                    df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').astype(np.float64)
            
            # Calculate typical price using float64
            typical_price = ((df_copy['high'] + df_copy['low'] + df_copy['close']) / 3.0).astype(np.float64)
            
            # Calculate raw money flow using float64
            raw_money_flow = (typical_price * df_copy['volume']).astype(np.float64)
            
            # Determine positive and negative money flow
            positive_flow = pd.Series(0.0, index=df_copy.index, dtype=np.float64)
            negative_flow = pd.Series(0.0, index=df_copy.index, dtype=np.float64)
            
            # Compare typical prices to determine flow direction
            for i in range(1, len(df_copy)):
                if typical_price.iloc[i] > typical_price.iloc[i-1]:
                    positive_flow.iloc[i] = raw_money_flow.iloc[i]
                elif typical_price.iloc[i] < typical_price.iloc[i-1]:
                    negative_flow.iloc[i] = raw_money_flow.iloc[i]
            
            # Calculate money flow ratio with rolling windows
            positive_mf = positive_flow.rolling(window=period, min_periods=1).sum()
            negative_mf = negative_flow.rolling(window=period, min_periods=1).sum()
            
            # Calculate MFI (avoid division by zero)
            money_flow_ratio = positive_mf / (negative_mf + 1e-10)  # Small epsilon to avoid division by zero
            mfi = 100 - (100 / (1 + money_flow_ratio))
            
            # Ensure MFI is properly bounded and float64
            mfi = np.clip(mfi, 0, 100).astype(np.float64)
            
            # Add to dataframe with proper assignment
            df_copy.loc[:, 'MFI'] = mfi
            
            return df_copy
            
        except Exception as e:
            logger.error(f"MFI calculation failed: {e}")
            # Return original dataframe with NaN MFI column instead of failing
            df_copy = df.copy()
            df_copy['MFI'] = np.full(len(df_copy), 50.0, dtype=np.float64)  # Neutral MFI
            return df_copy
        
    @staticmethod
    def _calculate_divergence(price: pd.Series, indicator: pd.Series) -> pd.Series:
        """
        Calculate divergence between price and indicator.
        
        Args:
            price: Price series
            indicator: Indicator series
            
        Returns:
            Divergence signal series
        """
        # Find local peaks and troughs
        price_peaks = (price > price.shift(1)) & (price > price.shift(-1))
        price_troughs = (price < price.shift(1)) & (price < price.shift(-1))
        
        ind_peaks = (indicator > indicator.shift(1)) & (indicator > indicator.shift(-1))
        ind_troughs = (indicator < indicator.shift(1)) & (indicator < indicator.shift(-1))
        
        # Bullish divergence: price makes lower low, indicator makes higher low
        bullish_div = price_troughs & ind_troughs & (price < price.shift(2)) & (indicator > indicator.shift(2))
        
        # Bearish divergence: price makes higher high, indicator makes lower high
        bearish_div = price_peaks & ind_peaks & (price > price.shift(2)) & (indicator < indicator.shift(2))
        
        divergence = pd.Series(0, index=price.index)
        divergence[bullish_div] = 1
        divergence[bearish_div] = -1
        
        return divergence
        
    @staticmethod
    def calculate_volatility_score(df: pd.DataFrame) -> float:
        """
        Calculate volatility score based on multiple metrics.
        
        Args:
            df: DataFrame with OHLCV and indicators
            
        Returns:
            Volatility score (0-100)
        """
        if 'ATR_pct_rank' not in df or 'BB_width' not in df:
            return 50.0
            
        # Get latest values
        atr_rank = df['ATR_pct_rank'].iloc[-1]
        bb_width_rank = df['BB_width'].rolling(100).apply(
            lambda x: stats.percentileofscore(x, x.iloc[-1])
        ).iloc[-1]
        volume_zscore = abs(df['Volume_zscore'].iloc[-1])
        
        # Calculate weighted score
        vol_score = (
            atr_rank * 0.4 +
            bb_width_rank * 0.3 +
            min(volume_zscore * 10, 100) * 0.3
        )
        
        return float(np.clip(vol_score, 0, 100))
        
    @staticmethod
    def calculate_trend_strength(df: pd.DataFrame) -> Tuple[str, float]:
        """
        Calculate trend direction and strength.
        
        Args:
            df: DataFrame with indicators
            
        Returns:
            Tuple of (direction, strength)
        """
        if df.empty:
            return "neutral", 0.0
            
        # Check EMA alignment
        ema_bullish = (
            df['EMA_20'].iloc[-1] > df['EMA_50'].iloc[-1] > df['EMA_200'].iloc[-1]
        )
        ema_bearish = (
            df['EMA_20'].iloc[-1] < df['EMA_50'].iloc[-1] < df['EMA_200'].iloc[-1]
        )
        
        # Check ADX for trend strength
        adx = df['ADX'].iloc[-1] if 'ADX' in df else 0
        
        # Check MACD
        macd_bullish = df['MACD'].iloc[-1] > df['MACD_signal'].iloc[-1]
        
        # Determine direction
        if ema_bullish and macd_bullish:
            direction = "bullish"
        elif ema_bearish and not macd_bullish:
            direction = "bearish"
        else:
            direction = "neutral"
            
        # Calculate strength (0-100)
        strength = min(adx * 2, 100) if adx > 0 else 50
        
        return direction, strength
        
    @staticmethod
    def get_support_resistance(df: pd.DataFrame, lookback: int = 50) -> Dict[str, List[float]]:
        """
        Calculate support and resistance levels.
        
        Args:
            df: DataFrame with OHLCV data
            lookback: Number of periods to look back
            
        Returns:
            Dictionary with support and resistance levels
        """
        recent = df.tail(lookback)
        
        # Use pivot points
        highs = recent['high'].values
        lows = recent['low'].values
        closes = recent['close'].values
        
        # Find local peaks and troughs
        resistance_levels = []
        support_levels = []
        
        for i in range(2, len(highs) - 2):
            # Resistance: local high
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                resistance_levels.append(highs[i])
                
            # Support: local low
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                support_levels.append(lows[i])
                
        # Add Bollinger Bands as dynamic support/resistance
        if 'BB_upper' in df and 'BB_lower' in df:
            resistance_levels.append(df['BB_upper'].iloc[-1])
            support_levels.append(df['BB_lower'].iloc[-1])
            
        # Sort and remove duplicates
        resistance_levels = sorted(list(set(resistance_levels)), reverse=True)[:3]
        support_levels = sorted(list(set(support_levels)))[:3]
        
        return {
            "resistance": resistance_levels,
            "support": support_levels
        }
        
    @staticmethod
    def add_swing_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add indicators specifically useful for swing trading."""
        
        # Parabolic SAR
        try:
            sar = ta.psar(df['high'], df['low'], df['close'])
            if sar is not None and not sar.empty:
                df['SAR'] = sar['PSARl_0.02_0.2'] if 'PSARl_0.02_0.2' in sar.columns else sar.iloc[:, 0]
        except:
            df['SAR'] = np.nan
            
        # Supertrend
        try:
            supertrend = ta.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=3)
            if supertrend is not None and not supertrend.empty:
                df['SUPERT_trend'] = supertrend['SUPERTd_10_3.0']
                df['SUPERT_signal'] = supertrend['SUPERTs_10_3.0']
        except:
            df['SUPERT_trend'] = 1  # Default to uptrend
            df['SUPERT_signal'] = df['close']
            
        # Donchian Channels (breakout indicator)
        try:
            donchian = ta.donchian(df['high'], df['low'], lower_length=20, upper_length=20)
            if donchian is not None and not donchian.empty:
                df['DC_upper'] = donchian['DCU_20_20']
                df['DC_lower'] = donchian['DCL_20_20']
                df['DC_middle'] = (df['DC_upper'] + df['DC_lower']) / 2
        except:
            df['DC_upper'] = df['high'].rolling(20).max()
            df['DC_lower'] = df['low'].rolling(20).min()
            df['DC_middle'] = (df['DC_upper'] + df['DC_lower']) / 2
            
        # Swing High/Low detection
        df['swing_high'] = (df['high'] > df['high'].shift(1)) & (df['high'] > df['high'].shift(-1))
        df['swing_low'] = (df['low'] < df['low'].shift(1)) & (df['low'] < df['low'].shift(-1))
        
        # Price momentum for swing trades
        df['momentum_5'] = df['close'].pct_change(5) * 100
        df['momentum_10'] = df['close'].pct_change(10) * 100
        
        # Trend continuation signals
        df['higher_highs'] = (df['high'] > df['high'].rolling(5).max().shift(1))
        df['higher_lows'] = (df['low'] > df['low'].rolling(5).min().shift(1))
        df['lower_highs'] = (df['high'] < df['high'].rolling(5).max().shift(1))
        df['lower_lows'] = (df['low'] < df['low'].rolling(5).min().shift(1))
        
        return df 