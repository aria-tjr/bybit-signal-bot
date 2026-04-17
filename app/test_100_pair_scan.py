#!/usr/bin/env python3
"""
Test the new 100-pair scanning functionality.
"""

import asyncio
import sys
import os

from .services.market_scanner import market_scanner
from .core.logging import get_logger

logger = get_logger(__name__)

async def test_100_pair_scan():
    """Test the comprehensive 100-pair market scan."""
    print("🔍 Testing 100-pair market scan functionality...")
    
    try:
        # Trigger the 100-pair scan
        results = await market_scanner.scan_100_pairs()
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            return
        
        # Display results summary
        scan_summary = results.get("scan_summary", {})
        opportunities = results.get("opportunities", {})
        top_picks = results.get("top_picks", [])
        
        print(f"\n✅ 100-PAIR SCAN COMPLETE")
        print(f"📊 Pairs Scanned: {scan_summary.get('pairs_scanned', 0)}")
        print(f"📊 Pairs Analyzed: {scan_summary.get('pairs_analyzed', 0)}")
        print(f"📊 Total Opportunities: {scan_summary.get('total_opportunities', 0)}")
        print(f"⏱️ Scan Duration: {scan_summary.get('scan_duration_seconds', 0):.2f}s")
        
        print(f"\n🎯 OPPORTUNITIES BY CATEGORY:")
        for category, pairs in opportunities.items():
            if pairs:
                print(f"  • {category.replace('_', ' ').title()}: {len(pairs)} pairs")
        
        print(f"\n🏆 TOP 5 MARKET PICKS:")
        for i, pick in enumerate(top_picks[:5], 1):
            symbol = pick["symbol"]
            score = pick["score"]
            change = pick["price_change_pct"]
            volume = pick["volume_24h"]
            category = pick["source_category"].replace('_', ' ').title()
            leverage_ok = "✅" if pick.get("leverage_suitable", False) else "⚠️"
            
            print(f"  {i}. {symbol} (Score: {score})")
            print(f"     Change: {change:+.1f}% | Volume: ${volume:,.0f} {leverage_ok}")
            print(f"     Category: {category}")
        
        # Test specific categories
        print(f"\n📈 STRONG BULLISH OPPORTUNITIES:")
        bullish = opportunities.get("strong_bullish", [])
        for i, pair in enumerate(bullish[:3], 1):
            print(f"  {i}. {pair['symbol']}: {pair['price_change_pct']:+.1f}% (Score: {pair['score']})")
        
        print(f"\n📉 STRONG BEARISH OPPORTUNITIES:")
        bearish = opportunities.get("strong_bearish", [])
        for i, pair in enumerate(bearish[:3], 1):
            print(f"  {i}. {pair['symbol']}: {pair['price_change_pct']:+.1f}% (Score: {pair['score']})")
        
        print(f"\n💎 SMALL CAP GEMS:")
        gems = opportunities.get("small_cap_gems", [])
        for i, pair in enumerate(gems[:3], 1):
            print(f"  {i}. {pair['symbol']}: {pair['price_change_pct']:+.1f}% (Score: {pair['score']})")
        
        print(f"\n✅ 100-pair scan test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        logger.error("100-pair scan test failed", error=str(e))

async def test_manual_scan_categories():
    """Test different manual scan categories."""
    print("\n🔍 Testing manual scan categories...")
    
    categories = ["100_pairs", "all", "top_movers", "small_caps", "volume_breakouts"]
    
    for category in categories:
        try:
            print(f"\n📊 Testing category: {category}")
            results = await market_scanner.manual_scan(category)
            
            if "error" in results:
                print(f"❌ Error for {category}: {results['error']}")
                continue
            
            if category == "100_pairs":
                total_opportunities = results.get("scan_summary", {}).get("total_opportunities", 0)
                print(f"✅ {category}: {total_opportunities} opportunities found")
            else:
                total_found = sum(len(symbols) for symbols in results.values() if isinstance(symbols, list))
                print(f"✅ {category}: {total_found} symbols found")
                
        except Exception as e:
            print(f"❌ Error testing {category}: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting 100-pair scan tests...")
    
    # Run tests
    asyncio.run(test_100_pair_scan())
    asyncio.run(test_manual_scan_categories())
    
    print("\n🎉 All tests completed!") 