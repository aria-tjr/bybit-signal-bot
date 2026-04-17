# Crypto Signal Bot - Scalping Enhancement

## Overview

The bot has been enhanced for **short-term scalping** with focus on:
- **1-minute and 5-minute timeframes only**
- **20x leverage for high-volatility opportunities**
- **Automated market scanning for top movers**
- **Quick profit targets (2-5% gains)**
- **Small cap and high-volatility coin detection**

## Key Features

### 🔍 Automated Market Scanner

The bot continuously scans the market every 5 minutes for:

1. **Top Gainers (Green Coins)** 📈
   - Coins with +3% or more price movement
   - High volume confirmation
   - Suitable for long positions

2. **Top Losers (Red Coins)** 📉
   - Coins with -3% or more price movement
   - High volume confirmation
   - Suitable for short positions

3. **Small Cap Movers** 💎
   - Lower market cap coins with high volatility
   - 5%+ price movements
   - Optimal for high leverage trading

4. **Volume Breakouts** 🚀
   - Unusual volume spikes
   - Early breakout detection
   - High probability setups

### ⚡ Scalping Optimizations

- **Fast Timeframes**: Focus on 1m/5m charts
- **High Leverage**: 15-20x for suitable opportunities
- **Quick Profits**: 2-5% target gains
- **Tight Stop Losses**: Minimize risk per trade
- **Fast Execution**: Sub-500ms latency targets

### 🎯 Trading Strategy

**Position Duration**: 5-15 minutes
**Leverage**: 10-20x (based on volatility)
**Profit Targets**:
- TP1: 1-2% (fast exit)
- TP2: 2-3% (main target)
- TP3: 3-5% (maximum profit)

## Telegram Commands

### Basic Commands
- `/signal SYMBOL` - Get scalping signal for specific symbol
- `/status` - Bot status and configuration
- `/help` - Complete command list

### Market Scanner Commands
- `/scan` - Trigger manual market scan
- `/movers` - Show top 10 gainers/losers
- `/smallcaps` - Show high-volatility small caps
- `/scanner` - Scanner status and configuration

### Portfolio Commands
- `/portfolio` - Portfolio overview
- `/risk` - Risk assessment
- `/performance` - Performance statistics
- `/regime` - Current market regime

## Configuration

Key settings optimized for scalping:

```python
# Timeframes
time_frames = ["1m", "5m"]

# Trading Parameters
default_threshold_pct = 3.0  # Quick profit target
max_leverage = 20           # High leverage for scalping
min_leverage = 10           # Minimum for small coins

# Scanner Settings
scanner_interval_minutes = 5        # Scan every 5 minutes
min_price_change_pct = 3.0         # Minimum movement to trigger
top_movers_count = 20              # Track top 20 movers
min_volume_usdt = 1000000          # Minimum $1M volume

# Performance
latency_threshold_ms = 500         # Sub-500ms execution
max_concurrent_jobs = 100          # High concurrency
```

## API Endpoints

### Scanner Endpoints
- `GET /scanner/status` - Scanner status
- `POST /scanner/scan/{category}` - Manual scan
- `GET /scanner/top-movers` - Current top movers
- `GET /scanner/small-caps` - Small cap opportunities

### Signal Endpoints
- `POST /signal/{symbol}` - Generate signal
- `GET /analytics/performance` - Performance metrics
- `GET /analytics/portfolio` - Portfolio status

## Market Categories

### 1. Top Gainers (Green Coins) 🟢
- **Criteria**: +3% or more in 24h
- **Volume**: Minimum $1M daily volume
- **Strategy**: Long positions with tight stops
- **Leverage**: 15-20x based on volatility

### 2. Top Losers (Red Coins) 🔴
- **Criteria**: -3% or more in 24h
- **Volume**: Minimum $1M daily volume
- **Strategy**: Short positions on continued weakness
- **Leverage**: 15-20x based on volatility

### 3. Small Caps (Diamond Coins) 💎
- **Criteria**: High volatility, lower market cap
- **Volume**: $500K - $10M range
- **Strategy**: Both long/short based on momentum
- **Leverage**: Up to 20x for suitable coins

### 4. Volume Breakouts 🚀
- **Criteria**: Unusual volume spikes
- **Detection**: Real-time volume analysis
- **Strategy**: Momentum following
- **Leverage**: Moderate to high based on setup

## Risk Management

### Leverage Guidelines
- **20x**: High volatility small caps with clear setup
- **15x**: Major coins with strong momentum
- **10x**: Conservative approach for uncertain setups

### Stop Loss Strategy
- **Tight Stops**: 0.5-1% for scalping
- **Volume Stops**: Exit on volume exhaustion
- **Time Stops**: Exit after 15 minutes if no progress

### Position Sizing
- **Risk per Trade**: 1-2% of portfolio
- **Maximum Positions**: 3-5 concurrent trades
- **Portfolio Heat**: Maximum 10% at risk

## Signal Quality Indicators

### Confidence Scoring
- **🟢 80%+**: High confidence, full leverage
- **🟡 60-80%**: Medium confidence, reduced size
- **🔴 <60%**: Low confidence, minimal size

### Signal Strength Factors
1. **Volume Confirmation**: Unusual volume spike
2. **Multi-timeframe Alignment**: 1m and 5m agreement
3. **Market Regime**: Suitable market conditions
4. **Volatility**: Adequate movement potential
5. **Liquidity**: Sufficient orderbook depth

## Performance Tracking

### Key Metrics
- **Win Rate**: Target 60-70%
- **Average Win**: 2-3%
- **Average Loss**: 0.5-1%
- **Profit Factor**: Target >2.0
- **Max Drawdown**: <5%

### Real-time Monitoring
- Position tracking
- P&L calculation
- Risk exposure monitoring
- Performance analytics

## Best Practices

### Entry Strategy
1. Wait for scanner alerts
2. Confirm on 1m/5m charts
3. Enter on momentum continuation
4. Use limit orders when possible

### Exit Strategy
1. Take TP1 quickly (50% position)
2. Trail stop for remaining position
3. Exit all if setup invalidated
4. Time-based exits after 15 minutes

### Risk Controls
1. Never exceed 20x leverage
2. Always use stop losses
3. Limit concurrent positions
4. Monitor portfolio heat

## Troubleshooting

### Common Issues
1. **High Latency**: Check network connection
2. **Missed Signals**: Increase scan frequency
3. **False Signals**: Adjust minimum criteria
4. **Low Volume**: Increase volume thresholds

### Support
- Check logs: `/docker/logs/`
- API status: `GET /health`
- Scanner status: `/scanner`
- Performance metrics: `/analytics/performance`

## Disclaimer

⚠️ **High-Risk Trading**: Scalping with high leverage involves significant risk. This bot is for educational purposes only and should not be considered financial advice. Always:

- Use proper risk management
- Start with small position sizes
- Test thoroughly in testnet mode
- Understand the risks involved
- Never risk more than you can afford to lose

🎯 **Focus**: Quick profits with disciplined risk management 