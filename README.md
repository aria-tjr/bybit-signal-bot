# Crypto Signal Bot for Bybit

A real-time cryptocurrency trading signal bot that analyzes multiple timeframes and delivers comprehensive trading recommendations via Telegram. The bot uses advanced technical indicators, machine learning confidence scoring, and robust risk management to generate high-quality trading signals.

## 🚀 Features

- **Multi-timeframe Analysis**: Analyzes 1m, 5m, 15m, 1h, and 4h timeframes simultaneously
- **Advanced Technical Indicators**: 15+ indicators including EMA, RSI, MACD, Bollinger Bands, ADX, and more
- **Machine Learning Confidence Scoring**: Gradient Boosting model predicts signal success probability
- **Dynamic Risk Management**: Volatility-based leverage adjustment and position sizing
- **Real-time Data**: WebSocket integration for live market data
- **Telegram Integration**: Instant signal delivery with formatted messages
- **High Performance**: < 2 second latency from request to delivery
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Docker Deployment**: Easy containerized deployment

## 📋 Requirements

- Docker & Docker Compose
- Bybit API credentials (read-only)
- Telegram Bot Token
- Ubuntu 22.04 LTS (recommended)
- 2 vCPU, 4GB RAM minimum

## 🛠 Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/crypto-signal-bot.git
cd crypto-signal-bot
```

2. **Create environment file**
```bash
cp .env.example .env
```

3. **Configure environment variables**
```bash
# Bybit API (read-only permissions)
BYBIT_API_KEY=your_api_key
BYBIT_API_SECRET=your_api_secret
BYBIT_TESTNET=false

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_IDS=["chat_id_1", "chat_id_2"]

# Optional configurations
DEFAULT_THRESHOLD_PCT=20.0
MAX_LEVERAGE=50
```

4. **Build and run with Docker Compose**
```bash
cd docker
docker-compose up -d
```

## 🎯 Usage

### Telegram Commands

- `/start` - Initialize the bot
- `/signal BTCUSDT` - Get signal for specific symbol
- `/status` - Check bot status
- `/help` - Show help message

Or simply send a symbol like `BTCUSDT` to get instant analysis.

### Signal Output Example

```
📈 BTCUSDT Signal

⏰ Time:
• UTC: 2024-01-15 14:30:00
• Berlin: 2024-01-15 15:30:00

📊 Trade Setup:
• Direction: LONG
• Timeframe: 15m
• Leverage: 25x

💰 Price Levels:
• Entry: 42,150.50
• Stop Loss: 41,500.00

🎯 Take Profit:
• TP1: 42,571.00 (10%)
• TP2: 43,413.50 (20%)
• TP3: 44,256.00 (30%)

🟢 Confidence: 82%

📝 Technical Rationale:
1. Strong bullish trend detected (strength: 75%)
2. MACD bullish crossover on 15m timeframe
3. RSI at 58 supports continued momentum
4. Above-average volume supports price action
5. Low volatility environment supports stable movement

⚠️ Risk Warning: Not financial advice. Trade at your own risk.
```

## 🏗 Architecture

```
crypto-signal-bot/
├── app/
│   ├── core/            # Settings, logging
│   ├── data/            # WebSocket, REST, cache
│   ├── indicators/      # Technical analysis
│   ├── models/          # ML confidence model
│   ├── logic/           # Trading rules, risk management
│   ├── services/        # Telegram, signal processor
│   └── main.py          # Entry point
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── tests/               # Unit and integration tests
```

## 📊 Technical Analysis

### Indicators Used
- **Trend**: EMA (20/50/200), SMA, VWAP
- **Momentum**: RSI, MACD, Stochastic
- **Volatility**: ATR, Bollinger Bands
- **Volume**: OBV, Volume MA, CMF
- **Strength**: ADX, CCI, Williams %R

### Trading Logic
1. **Trend Filter**: Ensures alignment with major trend
2. **Entry Conditions**: Multiple confirmations required
3. **Risk Management**: ATR-based stop loss
4. **Profit Targets**: Three levels based on threshold percentage

## 🤖 Machine Learning Model

- **Algorithm**: Gradient Boosting Classifier
- **Target**: Probability of hitting TP2 within 6 hours
- **Features**: 11 technical and market microstructure features
- **Performance**: >60% win rate in backtesting

## 🔧 API Endpoints

- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `POST /signal/{symbol}` - Trigger manual signal

## 📈 Performance Metrics

- **Latency**: < 2 seconds end-to-end
- **Availability**: 99.9% uptime target
- **Throughput**: 50 concurrent signals
- **Memory**: < 4GB RAM usage

## 🧪 Testing

Run the test suite:
```bash
docker-compose run app pytest -v --cov=app --cov-report=html
```

## 🚀 Deployment

### Production Deployment
```bash
make deploy
```

### Environment Variables
See `.env.example` for all configuration options.

## 📝 Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python -m app.main
```

### Code Style
- Python 3.12+
- Type hints required
- PEP 8 compliant
- 90%+ test coverage

## ⚠️ Disclaimer

This bot provides trading signals for informational purposes only. It does not constitute financial advice. Trading cryptocurrencies carries significant risk. Always do your own research and never trade with money you cannot afford to lose.

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the FAQ in the wiki
- Join our Discord server

---

Built with ❤️ for the crypto trading community 
## ⚠️ Disclaimer

This software is provided **for educational and research purposes only** and is **not** financial advice. Trading cryptocurrency derivatives carries substantial risk of loss, including leveraged liquidation. Signals generated by this bot are algorithmic outputs — not investment recommendations. The author assumes no liability for any losses arising from use of this software. Use testnet first and only operate with capital you can afford to lose.
