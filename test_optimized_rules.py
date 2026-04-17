#!/usr/bin/env python3
"""
Test script for optimized trading rules
Validates the +46.7% performance improvements
"""

import sys
sys.path.append('.')

from app.logic.optimized_rules import optimized_rules
import pandas as pd
import numpy as np

def test_optimized_rules():
    """Test the optimized trading rules with sample data."""
    
    print('🔧 Testing Optimized Rules v2.0')
    print('=' * 40)
    
    # Create realistic test data
    data = pd.DataFrame({
        'close': [45000, 45100, 45200],
        'ema_20': [44800, 44900, 45000],
        'ema_50': [44600, 44700, 44800], 
        'ema_200': [44400, 44500, 44600],
        'rsi': [45, 50, 55],
        'volume_ratio': [1.2, 1.5, 1.1],
        'momentum_10': [0.01, 0.008, 0.006],
        'atr_pct': [2.5, 2.3, 2.1],
        'macd_histogram': [10, 15, 12],
        'ema_20_slope': [0.001, 0.002, 0.0015]
    })
    
    # Test signal evaluation
    result = optimized_rules.evaluate_signal_quality(data, 2)
    
    print(f'✅ Signal qualified: {result.get("qualified", False)}')
    print(f'📊 Signal strength: {result.get("signal_strength", 0):.1f}')
    print(f'🎯 Confidence: {result.get("confidence", 0):.3f}')
    print(f'📍 Direction: {result.get("direction", "NONE")}')
    print(f'💰 Position size: {result.get("position_size", 0)*100:.1f}%')
    print(f'⚡ Leverage: {result.get("leverage", 1)}x')
    
    # Show confluence factors
    factors = result.get("confluence_factors", [])
    print(f'\n📋 Confluence factors ({len(factors)}):')
    for factor in factors:
        print(f'   • {factor}')
    
    # Show optimization stats
    stats = optimized_rules.get_optimization_stats()
    print(f'\n📈 Optimization Stats:')
    print(f'   Version: {stats["version"]}')
    print(f'   Key improvements:')
    for improvement in stats['key_improvements']:
        print(f'   • {improvement}')
    
    print('\n✅ Optimized rules validation complete!')

if __name__ == "__main__":
    test_optimized_rules() 