#!/usr/bin/env python3
"""
Debug Script for Signal Generation Issues

This script will test the signal generation pipeline to identify exactly where it's failing.
"""

import asyncio
import sys
import os
import pandas as pd
from datetime import datetime

# Add app to path
sys.path.append('/app')
sys.path.append('.')

async def debug_signal_generation():
    """Debug the signal generation pipeline step by step."""
    
    try:
        # Import modules
        from app.services.staged_analysis import staged_analyzer
        from app.services.smart_pair_filter import smart_filter
        from app.logic.rules import TradingRules
        from app.services.rate_limited_data_collector import rate_limited_collector
        
        print("🔍 Starting Signal Generation Debug...")
        
        # Test with a small set of popular pairs
        test_pairs = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT"]
        
        print(f"📊 Testing with pairs: {test_pairs}")
        
        # Step 1: Test Smart Filtering
        print("\n🎯 Step 1: Testing Smart Filtering...")
        priority_pairs = await smart_filter.get_priority_pairs(test_pairs)
        print(f"   Input pairs: {len(test_pairs)}")
        print(f"   Priority pairs: {len(priority_pairs)}")
        print(f"   Selected pairs: {priority_pairs}")
        
        if not priority_pairs:
            print("❌ FAILURE: No pairs passed smart filtering!")
            return
        
        # Step 2: Test Data Collection
        print("\n📡 Step 2: Testing Data Collection...")
        quick_data = await rate_limited_collector.get_quick_scan_data(priority_pairs[:3])
        print(f"   Data collected for: {list(quick_data.keys())}")
        
        for pair, data_dict in quick_data.items():
            print(f"   {pair}: {list(data_dict.keys())} timeframes")
            for tf, df in data_dict.items():
                if df is not None and not df.empty:
                    print(f"     {tf}: {len(df)} candles")
                else:
                    print(f"     {tf}: NO DATA")
        
        # Step 3: Test Individual Signal Analysis
        print("\n⚡ Step 3: Testing Individual Signal Analysis...")
        
        for pair in priority_pairs[:2]:  # Test first 2 pairs
            print(f"\n   Testing {pair}...")
            
            if pair not in quick_data:
                print(f"     ❌ No data for {pair}")
                continue
                
            # Test TradingRules.analyze_symbol
            try:
                analysis = await TradingRules.analyze_symbol(pair, quick_data[pair])
                direction = analysis.get("direction", "UNKNOWN")
                signal_strength = analysis.get("features", {}).get("signal_strength", 0)
                confluence_points = analysis.get("accuracy_metrics", {}).get("confluence_points", 0)
                
                print(f"     Direction: {direction}")
                print(f"     Signal Strength: {signal_strength}")
                print(f"     Confluence Points: {confluence_points}")
                
                if direction == "NEUTRAL":
                    reason = analysis.get("reason", "Unknown")
                    rejection_reasons = analysis.get("rejection_reasons", [])
                    print(f"     ❌ NEUTRAL Reason: {reason}")
                    print(f"     ❌ Rejection Reasons: {rejection_reasons}")
                else:
                    print(f"     ✅ Valid signal generated!")
                    
            except Exception as e:
                print(f"     ❌ Analysis failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Step 4: Test Staged Analysis Thresholds
        print("\n🎚️ Step 4: Testing Staged Analysis Thresholds...")
        config = staged_analyzer.get_stage_config()
        print(f"   Detailed thresholds: {config['detailed_thresholds']}")
        print(f"   Quick scan thresholds: {config['quick_scan_thresholds']}")
        
        # Step 5: Test Full Staged Pipeline
        print("\n🔄 Step 5: Testing Full Staged Pipeline...")
        results = await staged_analyzer.analyze_pairs_staged(test_pairs)
        
        print("   Pipeline Results:")
        for stage, data in results.get("stage_results", {}).items():
            print(f"     {stage}: {data.get('input_pairs', 0)} → {data.get('output_pairs', 0)} pairs")
            
        final_signals = results.get("final_signals", [])
        print(f"   Final signals generated: {len(final_signals)}")
        
        for signal in final_signals:
            print(f"     {signal.get('symbol')} {signal.get('direction')} (confidence: {signal.get('confidence', 0):.2f})")
            
        print("\n✅ Debug completed!")
        
    except Exception as e:
        print(f"\n❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_signal_generation()) 