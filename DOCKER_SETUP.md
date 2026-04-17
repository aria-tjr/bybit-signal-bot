# 🐳 Docker Setup Guide - Crypto Signal Bot

This guide will help you run the Crypto Signal Bot with auto trading capabilities using Docker.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Bybit API credentials configured in `.env` file

### 1. Environment Setup
Your `.env` file is already configured with Bybit API credentials. The Docker setup will automatically use these settings.

### 2. Build and Run

**Option 1: Using the convenient startup script**
```bash
# Navigate to docker directory
cd docker/

# Basic signal bot (no trading)
./docker-start.sh basic

# With auto trading enabled
./docker-start.sh trading

# Full stack with monitoring
./docker-start.sh full

# Test mode (uses testnet)
./docker-start.sh test
```

**Option 2: Using docker-compose directly**
```bash
cd docker/

# Basic setup
docker-compose up -d app redis timescaledb

# With trading enabled
AUTO_TRADING_ENABLED=true docker-compose up -d app redis timescaledb

# Full stack
docker-compose up -d
```

## 🎯 Available Modes

### 🏃 Basic Mode
- Signal processing and analysis
- Telegram notifications
- No trading execution
```bash
./docker-start.sh basic
```

### 🤖 Trading Mode
- Full signal processing
- Auto trading enabled
- Risk management active
```bash
./docker-start.sh trading
```

### 🎯 Auto-Trader Service
- Dedicated trading service
- Can run alongside main bot
- Independent trading execution
```bash
./docker-start.sh auto-trader
```

### 📈 Full Stack Mode
- Complete monitoring stack
- Grafana dashboards
- Prometheus metrics
- Log aggregation with Loki
```bash
./docker-start.sh full
```

### 🧪 Test Mode
- Uses Bybit testnet
- Safe for testing strategies
- No real money at risk
```bash
./docker-start.sh test
```

## 📊 Service Access Points

Once running, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| Bot API | http://localhost:8000 | Main bot API and health checks |
| Metrics | http://localhost:8001 | Prometheus metrics endpoint |
| Grafana | http://localhost:3000 | Monitoring dashboards (admin/admin) |
| Prometheus | http://localhost:9090 | Metrics collection |
| Database | localhost:5434 | TimescaleDB (postgres/postgres) |
| Redis | localhost:6379 | Cache and message broker |

## 🔧 Management Commands

```bash
# View logs
./docker-start.sh logs

# Stop all services
./docker-start.sh stop

# Restart services
./docker-start.sh restart

# Rebuild containers
./docker-start.sh build

# Direct docker-compose commands
docker-compose logs -f app
docker-compose down
docker-compose up -d --build
```

## 🛡️ Environment Variables

The following environment variables control the bot behavior:

### 🔐 API Configuration
```env
BYBIT_API_KEY=your_api_key
BYBIT_API_SECRET=your_secret
BYBIT_TESTNET=false  # Set to true for testing
```

### 🤖 Trading Configuration
```env
AUTO_TRADING_ENABLED=false     # Enable/disable auto trading
MAX_POSITIONS=5                # Maximum concurrent positions
DAILY_TRADE_LIMIT=10          # Maximum trades per day
RISK_PER_TRADE=0.01           # Risk 1% of account per trade
MIN_CONFIDENCE=0.6            # Minimum signal confidence (0.0-1.0)
```

### 📊 Bot Settings
```env
SCANNER_ENABLED=false         # Enable market scanning
MAX_LEVERAGE=20              # Maximum leverage allowed
MIN_LEVERAGE=10              # Minimum leverage
DEFAULT_THRESHOLD_PCT=3.0    # Default profit target
```

## 🔍 Monitoring & Debugging

### Health Checks
Check if services are running:
```bash
curl http://localhost:8000/health
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs app
docker-compose logs redis
docker-compose logs timescaledb

# Follow logs in real-time
docker-compose logs -f app
```

### Database Access
```bash
# Connect to TimescaleDB
docker exec -it crypto-timescaledb psql -U postgres -d crypto_signals

# Common queries
SELECT * FROM signals ORDER BY created_at DESC LIMIT 10;
SELECT * FROM trades ORDER BY created_at DESC LIMIT 10;
```

### Redis Access
```bash
# Connect to Redis
docker exec -it crypto-redis redis-cli

# Check data
KEYS *
GET signal:*
```

## 🚨 Troubleshooting

### Common Issues

**1. Permission Denied**
```bash
chmod +x docker/docker-start.sh
```

**2. Port Conflicts**
```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Stop conflicting services or change ports in docker-compose.yml
```

**3. Build Failures**
```bash
# Clean rebuild
docker-compose down
docker system prune -f
./docker-start.sh build
```

**4. Database Connection Issues**
```bash
# Reset database
docker-compose down
docker volume rm docker_timescale-data
docker-compose up -d timescaledb
```

### Log Locations
- Container logs: `docker-compose logs`
- Application logs: `docker/logs/` directory
- Database logs: Inside timescaledb container

## 🔄 Updates and Maintenance

### Updating the Bot
```bash
# Pull latest changes
git pull

# Rebuild and restart
./docker-start.sh stop
./docker-start.sh build
./docker-start.sh trading
```

### Backup Data
```bash
# Backup database
docker exec crypto-timescaledb pg_dump -U postgres crypto_signals > backup.sql

# Backup Redis data
docker exec crypto-redis redis-cli BGSAVE
```

### Clean Installation
```bash
# Stop everything
./docker-start.sh stop

# Remove volumes (⚠️ This deletes all data)
docker-compose down -v

# Remove images
docker rmi $(docker images crypto-signal-bot -q)

# Fresh start
./docker-start.sh build
./docker-start.sh trading
```

## 🛡️ Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Testnet First**: Always test with testnet before mainnet
3. **Monitoring**: Monitor trades and positions regularly
4. **Limits**: Set appropriate position and daily trade limits
5. **Stop Loss**: Ensure stop-loss orders are properly configured

## 📞 Support

For issues or questions:
1. Check the logs first: `./docker-start.sh logs`
2. Verify environment configuration
3. Test with testnet mode first
4. Check the troubleshooting section above

## 🎉 Success!

If you see this in your logs, the bot is running successfully:
```
✅ Bybit connection established
🤖 Auto trading service started
📊 Signal processor active
💹 Ready to process signals
```

Happy trading! 🚀 