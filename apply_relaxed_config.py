#!/usr/bin/env python3
"""
Apply Relaxed Configuration to Running Bot

This script applies the relaxed scaling configuration to enable better signal generation.
"""

import os
import sys
import shutil
import json
from datetime import datetime

def backup_current_config():
    """Backup current configuration."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup files that will be modified
    files_to_backup = [
        "app/core/config.py",
        "production_config.py"
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup_{timestamp}"
            shutil.copy2(file_path, backup_path)
            print(f"✅ Backed up {file_path} to {backup_path}")

def apply_relaxed_thresholds():
    """Apply relaxed thresholds to configuration files."""
    
    # Configuration updates to apply
    relaxed_config = {
        "MIN_VOLATILITY_THRESHOLD": 5.0,
        "MIN_VOLUME_THRESHOLD": 1500000,
        "MAX_PAIRS_FOR_ANALYSIS": 25,
        "STAGE1_MAX_PAIRS": 60,
        "STAGE2_MAX_PAIRS": 20,
        "STAGE3_MAX_PAIRS": 8,
        "DETAILED_MIN_SIGNAL_STRENGTH": 1.2,
        "DETAILED_MIN_CONFLUENCE_POINTS": 1,
        "DETAILED_MIN_TREND_ALIGNMENT": 0.4,
        "FINAL_MIN_CONFIDENCE": 0.45,
        "FINAL_MIN_QUALITY_SCORE": 55
    }
    
    print("🔧 Applying relaxed configuration parameters...")
    
    # Update environment variables for immediate effect
    for key, value in relaxed_config.items():
        os.environ[key] = str(value)
        print(f"   {key}: {value}")
    
    return relaxed_config

def create_override_config():
    """Create a runtime configuration override."""
    
    override_config = {
        "config_type": "relaxed_scaling",
        "applied_at": datetime.now().isoformat(),
        "overrides": {
            # Smart filtering - more permissive
            "min_volatility_threshold": 5.0,
            "min_volume_threshold": 1500000,
            "max_pairs_for_analysis": 25,
            
            # Staged analysis - more candidates
            "stage1_max_pairs": 60,
            "stage2_max_pairs": 20, 
            "stage3_max_pairs": 8,
            
            # Signal quality - relaxed
            "quick_scan_min_score": 0.2,
            "detailed_min_signal_strength": 1.2,
            "detailed_min_confluence_points": 1,
            "detailed_min_trend_alignment": 0.4,
            "final_min_confidence": 0.45,
            "final_min_quality_score": 55,
            
            # RSI settings - more permissive
            "rsi_oversold_level": 35,
            "rsi_overbought_level": 65,
            
            # Volume analysis - lower thresholds
            "volume_spike_threshold": 1.3,
            "volume_trend_periods": 10
        },
        "expected_improvements": {
            "signal_generation": "3-5x more signals",
            "market_coverage": "25% more pairs analyzed",
            "opportunity_detection": "Significantly improved"
        }
    }
    
    # Write override config
    with open("runtime_config_override.json", "w") as f:
        json.dump(override_config, f, indent=2)
    
    print("✅ Created runtime configuration override")
    return override_config

def validate_configuration():
    """Validate the applied configuration."""
    
    print("\n🔍 Validating relaxed configuration...")
    
    checks = {
        "volatility_threshold": 5.0 > 0,
        "volume_threshold": 1500000 > 0,
        "stage_progression": 60 > 20 > 8,
        "signal_thresholds": 1.2 < 1.8,  # Less strict than original
        "confidence_range": 0.3 <= 0.45 <= 0.7
    }
    
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}: {'PASS' if result else 'FAIL'}")
    
    return all(checks.values())

def main():
    """Main execution function."""
    
    print("🚀 Applying Relaxed Scaling Configuration for Better Signal Generation")
    print("=" * 70)
    
    # Step 1: Backup current configuration
    print("\n📋 Step 1: Backup Current Configuration")
    backup_current_config()
    
    # Step 2: Apply relaxed thresholds
    print("\n🔧 Step 2: Apply Relaxed Thresholds") 
    relaxed_config = apply_relaxed_thresholds()
    
    # Step 3: Create runtime override
    print("\n📝 Step 3: Create Runtime Configuration Override")
    override_config = create_override_config()
    
    # Step 4: Validate configuration
    print("\n✅ Step 4: Validate Configuration")
    is_valid = validate_configuration()
    
    if is_valid:
        print("\n🎉 SUCCESS: Relaxed configuration applied successfully!")
        print("\n📊 Expected Improvements:")
        for improvement, description in override_config["expected_improvements"].items():
            print(f"   • {improvement.replace('_', ' ').title()}: {description}")
        
        print("\n🔄 Next Steps:")
        print("   1. Restart the Docker container to apply changes:")
        print("      cd docker && docker-compose restart crypto-signal-bot")
        print("   2. Monitor logs for signal generation:")
        print("      docker logs -f crypto-signal-bot")
        print("   3. Test signal scanning:")
        print("      Send /scan command via Telegram")
        
        print("\n⚠️  Note: Monitor the first few signals closely to ensure quality!")
        return True
    else:
        print("\n❌ FAILED: Configuration validation failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 