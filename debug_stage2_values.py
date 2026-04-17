#!/usr/bin/env python3
"""
Debug Stage 2 Values - Print exact extraction results

This script will show exactly what values Stage 2 is extracting from TradingRules
to identify why the filtering is failing.
"""

import asyncio
import sys
import os
import pandas as pd
from datetime import datetime

# Add app to path
sys.path.append('/app')
sys.path.append('.')

async def debug_stage2_values():
    """Debug the exact values Stage 2 extracts from TradingRules."""
    
    try:
        # Import modules
        from app.logic.rules import TradingRules
        from app.services.rate_limited_data_collector import rate_limited_collector
        
        print("🔍 Testing Stage 2 Value Extraction...")
        
        # Test one pair that we know generates a signal
        test_pairs = ["ETHUSDT"]
        
        for pair in test_pairs:
            print(f"\n📊 Testing {pair}:")
            
            # Get data
            try:
                data = await rate_limited_collector.get_priority_data([pair])
                if pair not in data:
                    print(f"❌ No data for {pair}")
                    continue
                    
                pair_data = data[pair]
                print(f"✅ Got data for {pair}")
                
                # Run TradingRules analysis
                analysis = await TradingRules.analyze_symbol(pair, pair_data)
                print(f"✅ TradingRules analysis completed")
                
                print(f"\n🔍 FULL ANALYSIS STRUCTURE:")
                for key, value in analysis.items():
                    if isinstance(value, dict):
                        print(f"  {key}: (dict with {len(value)} keys)")
                        for subkey, subvalue in value.items():
                            print(f"    {subkey}: {subvalue}")
                    else:
                        print(f"  {key}: {value}")
                
                print(f"\n🔍 STAGE 2 EXTRACTIONS:")
                
                # Test Stage 2 extractions
                direction = analysis.get("direction")
                signal_strength = analysis.get("strength", 0)
                confluence_points = analysis.get("confluence_points", 0)
                
                print(f"  direction: {direction}")
                print(f"  signal_strength (from 'strength'): {signal_strength}")
                print(f"  confluence_points: {confluence_points}")
                
                # Test Stage 2 filtering
                detailed_thresholds = {
                    "min_signal_strength": 1.2,
                    "min_confluence_points": 1,
                }
                
                passes_filters = (
                    signal_strength >= detailed_thresholds["min_signal_strength"] and
                    confluence_points >= detailed_thresholds["min_confluence_points"]
                )
                
                print(f"\n🎯 STAGE 2 FILTERING:")
                print(f"  signal_strength >= 1.2? {signal_strength} >= 1.2 = {signal_strength >= 1.2}")
                print(f"  confluence_points >= 1? {confluence_points} >= 1 = {confluence_points >= 1}")
                print(f"  direction != 'NEUTRAL'? {direction} != 'NEUTRAL' = {direction != 'NEUTRAL'}")
                print(f"  PASSES ALL FILTERS? {passes_filters and direction != 'NEUTRAL'}")
                
            except Exception as e:
                print(f"❌ Error analyzing {pair}: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_stage2_values()) 