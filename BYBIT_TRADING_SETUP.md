# 🚀 Bybit Auto Trading Setup Guide

This guide will help you connect your crypto signal bot to Bybit for automated trading.

## 📋 Prerequisites

1. **Bybit Account**: You need a verified Bybit account
2. **API Keys**: API keys with trading permissions
3. **Funding**: USDT balance in your Bybit account
4. **Python Environment**: Python 3.8+ with required dependencies

## 🔐 Step 1: Create Bybit API Keys

### For Testnet (Recommended for First Setup)

1. Go to [Bybit Testnet](https://testnet.bybit.com/)
2. Create a testnet account
3. Navigate to API Management
4. Create new API key with these permissions:
   - ✅ **Derivatives Trading** (for futures)
   - ✅ **Spot Trading** (for spot markets)
   - ✅ **Wallet** (for balance queries)
   - ❌ **Withdrawal** (keep disabled for security)

### For Mainnet (Live Trading)

1. Go to [Bybit](https://www.bybit.com/)
2. Log into your verified account
3. Navigate to Account & Security → API Management
4. Create new API key with permissions:
   - ✅ **Derivatives Trading**
   - ✅ **Spot Trading** 
   - ✅ **Wallet**
   - ❌ **Withdrawal** (disabled for security)
   - ✅ **IP Restriction** (add your server IP for security)

⚠️ **Security Note**: Never share your API keys and keep withdrawal permissions disabled.

## ⚙️ Step 2: Configure Environment Variables

1. Copy the environment template:
```bash
cp env.example .env
```

2. Edit the `.env` file with your API credentials:

```env
# Bybit API Configuration
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_TESTNET=true  # Set to false for mainnet

# Telegram Bot (for notifications)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_IDS=["your_chat_id"]

# Trading Configuration
MAX_LEVERAGE=20  # Maximum leverage to use
MIN_LEVERAGE=5   # Minimum leverage
DEFAULT_THRESHOLD_PCT=3.0  # Profit target %

# Risk Management
MAX_CONCURRENT_JOBS=5  # Max simultaneous positions
```

## 🧪 Step 3: Test Your Connection

Run the connection test script:

```bash
cd crypto-signal-bot
python test_trading_connection.py
```

This will show an interactive menu where you can:
1. **Test API Connection** - Verify your credentials work
2. **Test Signal Processing** - Test signal validation and enhancement
3. **Show Position Status** - View current account status
4. **Demo Auto Trading** - Test with fake signals (safe)

## 🔧 Step 4: Integration with Your Signal System

### Option A: Direct Integration

Modify your existing signal processing to use the auto trading service:

```python
from app.services.auto_trading import auto_trading_service

# In your signal generation code
async def process_trading_signal(signal_data):
    """Process and execute trading signals."""
    
    # Format signal for auto trading
    formatted_signal = {
        "symbol": signal_data["symbol"],
        "direction": "LONG" or "SHORT",
        "entry_price": signal_data["price"],
        "stop_loss": signal_data["stop_loss"],
        "confidence": signal_data["confidence"],  # 0.0 to 1.0
        "leverage": signal_data.get("leverage", 10),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Execute the signal
    executed = await auto_trading_service.process_signal(formatted_signal)
    
    if executed:
        print(f"✅ Signal executed for {signal_data['symbol']}")
    else:
        print(f"❌ Signal rejected for {signal_data['symbol']}")
```

### Option B: Signal Queue Integration

Use your existing signal processing with a queue:

```python
import asyncio
from app.services.auto_trading import auto_trading_service

class SignalExecutor:
    def __init__(self):
        self.signal_queue = asyncio.Queue()
        
    async def add_signal(self, signal):
        """Add signal to execution queue."""
        await self.signal_queue.put(signal)
    
    async def process_signals(self):
        """Process signals from queue."""
        while True:
            try:
                signal = await self.signal_queue.get()
                await auto_trading_service.process_signal(signal)
                self.signal_queue.task_done()
            except Exception as e:
                print(f"Error processing signal: {e}")
            
            await asyncio.sleep(1)  # Small delay

# Start the signal processor
executor = SignalExecutor()
asyncio.create_task(executor.process_signals())
```

## 🎛️ Step 5: Configure Trading Parameters

The auto trading service has several configurable parameters:

```python
# Set trading parameters
await auto_trading_service.set_trading_parameters({
    "min_confidence": 0.7,        # Only execute signals with 70%+ confidence
    "max_daily_trades": 15,       # Maximum 15 trades per day
    "auto_trading_enabled": True  # Enable/disable auto trading
})
```

### Signal Format Requirements

Your signals must include these fields:

```python
required_signal_format = {
    "symbol": "BTCUSDT",           # Trading pair
    "direction": "LONG",           # LONG, SHORT, BUY, or SELL
    "entry_price": 95000.0,        # Entry price
    "stop_loss": 94000.0,          # Stop loss price
    "confidence": 0.85,            # Confidence (0.0-1.0)
    
    # Optional fields (auto-generated if missing):
    "leverage": 10,                # Leverage to use
    "tp1": 96000.0,               # Take profit 1
    "tp2": 97000.0,               # Take profit 2  
    "tp3": 98000.0,               # Take profit 3
    "timestamp": "2024-01-01T12:00:00"
}
```

## 🛡️ Step 6: Risk Management

The bot includes built-in risk management:

### Position Limits
- **Maximum positions**: Configurable (default: 5)
- **Daily trade limit**: Configurable (default: 10)
- **Position size**: 1% risk per trade
- **Leverage limits**: Configurable per symbol

### Risk Checks
- ✅ **Balance verification**: Ensures sufficient margin
- ✅ **Correlation risk**: Prevents over-exposure to correlated assets
- ✅ **Risk-reward ratio**: Minimum 1:1 ratio required
- ✅ **Signal validation**: Comprehensive signal format checking

### Safety Features
- 🛑 **Emergency stop**: Instantly disable auto trading
- 📊 **Position monitoring**: Real-time PnL tracking
- 🔔 **Telegram notifications**: Trade execution alerts
- 📝 **Trade logging**: Complete audit trail

## 🚀 Step 7: Start Auto Trading

### Testing Mode (Recommended First)

1. **Start with testnet**:
```bash
# Set BYBIT_TESTNET=true in .env
python test_trading_connection.py
# Choose option 4: Start Auto Trading
```

2. **Monitor the logs**:
```bash
tail -f logs/crypto_bot.log
```

### Production Mode

1. **Switch to mainnet**:
```env
BYBIT_TESTNET=false
```

2. **Start auto trading**:
```python
from app.services.auto_trading import auto_trading_service

# Start auto trading
await auto_trading_service.start_auto_trading()

# Your signal generation code continues...
# Signals will be automatically executed
```

## 📊 Monitoring and Management

### Real-time Status

Check your bot's status:

```python
status = await auto_trading_service.get_auto_trading_status()
print(f"Auto trading: {status['auto_trading_enabled']}")
print(f"Daily trades: {status['daily_trades']['current']}/{status['daily_trades']['limit']}")
print(f"Active positions: {status['account_status']['total_positions']}")
print(f"Total PnL: ${status['account_status']['total_unrealized_pnl']:,.2f}")
```

### Position Management

```python
# Get all positions
positions = await trading_service.get_positions_status()

# Close specific position
await trading_service.close_position("position_id", reason="manual_close")

# Emergency stop (cancel all orders, disable trading)
await auto_trading_service.stop_auto_trading()
```

## 🔔 Telegram Notifications

Set up Telegram notifications to monitor your bot:

1. Create a Telegram bot with [@BotFather](https://t.me/botfather)
2. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)
3. Add credentials to `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_IDS=["your_chat_id"]
```

You'll receive notifications for:
- 🚀 **Trade executions**
- 📊 **Position updates**
- ⚠️ **Risk alerts**
- 🛑 **System status changes**

## ⚠️ Important Safety Notes

### Before Going Live

1. **Test thoroughly on testnet**
2. **Start with small position sizes**
3. **Monitor closely for the first few hours**
4. **Have emergency stop procedures ready**

### Risk Warnings

- 🚨 **High leverage trading is extremely risky**
- 💰 **Never risk more than you can afford to lose**
- 📉 **Crypto markets are highly volatile**
- 🔧 **Always have manual override capabilities**

### Best Practices

1. **Start conservative**: Low leverage, small positions
2. **Monitor actively**: Check logs and notifications
3. **Set limits**: Daily trade limits, position limits
4. **Regular reviews**: Analyze performance weekly
5. **Keep updated**: Monitor for API changes

## 🔧 Troubleshooting

### Common Issues

**API Connection Failed**
```
❌ API connection failed: Invalid API key
```
- Check API key and secret in `.env`
- Verify API permissions on Bybit
- Check if using correct testnet/mainnet endpoint

**Insufficient Balance**
```
❌ Signal rejected: Insufficient margin
```
- Check your USDT balance on Bybit
- Reduce position sizes or leverage
- Ensure you have enough margin for trades

**Signal Validation Failed**
```
❌ Signal validation failed: Missing required field
```
- Check signal format matches requirements
- Ensure all required fields are present
- Verify price and confidence values

### Debug Mode

Enable debug logging:

```env
LOG_LEVEL=DEBUG
```

This will show detailed information about:
- Signal processing steps
- API calls and responses
- Risk assessment decisions
- Trade execution details

## 📞 Support

For issues or questions:

1. **Check logs** in `logs/crypto_bot.log`
2. **Run test script** to verify connection
3. **Review this guide** for configuration issues
4. **Check Bybit API status** at [status.bybit.com](https://status.bybit.com)

## 🎯 Next Steps

Once your bot is running successfully:

1. **Optimize signal generation** for better accuracy
2. **Fine-tune risk parameters** based on performance
3. **Add custom indicators** for enhanced signals
4. **Implement advanced strategies** like DCA or grid trading
5. **Set up monitoring dashboards** for better visibility

---

**Happy Trading! 🚀**

Remember: Always prioritize risk management and never invest more than you can afford to lose. 