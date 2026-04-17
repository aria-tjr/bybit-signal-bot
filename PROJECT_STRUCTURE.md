# Crypto Signal Bot - Project Structure

## Overview
This document provides a detailed overview of the project structure and architecture.

## Directory Structure

```
crypto-signal-bot/
├── app/                        # Main application code
│   ├── __init__.py            # Package initialization
│   ├── main.py                # Application entry point
│   │
│   ├── core/                  # Core functionality
│   │   ├── __init__.py
│   │   ├── settings.py        # Configuration management
│   │   └── logging.py         # Structured logging setup
│   │
│   ├── data/                  # Data layer
│   │   ├── __init__.py
│   │   ├── websocket.py       # Bybit WebSocket client
│   │   ├── rest.py            # Bybit REST API client
│   │   └── cache.py           # Redis cache management
│   │
│   ├── indicators/            # Technical analysis
│   │   ├── __init__.py
│   │   └── technical.py       # Technical indicators (TA-Lib)
│   │
│   ├── logic/                 # Business logic
│   │   ├── __init__.py
│   │   ├── rules.py           # Trading rules engine
│   │   └── risk.py            # Risk management
│   │
│   ├── models/                # Machine learning
│   │   ├── __init__.py
│   │   └── confidence.py      # Confidence scoring model
│   │
│   ├── services/              # External services
│   │   ├── __init__.py
│   │   ├── telegram.py        # Telegram bot service
│   │   └── signal_processor.py # Signal orchestration
│   │
│   └── tests/                 # Test suite
│       ├── __init__.py
│       └── test_trading_rules.py
│
├── docker/                    # Docker configuration
│   ├── Dockerfile            # Container definition
│   ├── docker-compose.yml    # Service orchestration
│   └── prometheus.yml        # Monitoring config
│
├── .github/                  # GitHub configuration
│   └── workflows/
│       └── ci.yml           # CI/CD pipeline
│
├── requirements.txt          # Python dependencies
├── Makefile                 # Build automation
├── README.md               # Project documentation
├── env.example             # Environment variables template
├── .gitignore              # Git ignore rules
└── PROJECT_STRUCTURE.md    # This file
```

## Component Architecture

### 1. Core Layer (`app/core/`)
- **settings.py**: Centralized configuration using Pydantic
- **logging.py**: Structured logging with structlog

### 2. Data Layer (`app/data/`)
- **websocket.py**: Real-time market data via WebSocket
- **rest.py**: Historical data and API calls
- **cache.py**: Redis caching for performance

### 3. Analysis Layer (`app/indicators/`)
- **technical.py**: 15+ technical indicators
  - Moving averages (EMA, SMA, VWAP)
  - Oscillators (RSI, MACD, Stochastic)
  - Volatility (ATR, Bollinger Bands)
  - Volume indicators (OBV, CMF)

### 4. Logic Layer (`app/logic/`)
- **rules.py**: Trading signal generation
  - Multi-timeframe analysis
  - Entry/exit logic
  - Signal filtering
- **risk.py**: Risk management
  - Position sizing
  - Leverage calculation
  - Risk-reward analysis

### 5. ML Layer (`app/models/`)
- **confidence.py**: Gradient Boosting model
  - Predicts signal success probability
  - Uses 11 technical features
  - Fallback rule-based scoring

### 6. Services Layer (`app/services/`)
- **telegram.py**: User interface
  - Command handling
  - Message formatting
  - User authentication
- **signal_processor.py**: Orchestration
  - Data collection
  - Analysis coordination
  - Result delivery

## Data Flow

1. **User Request** → Telegram Bot
2. **Data Collection** → REST API + WebSocket
3. **Technical Analysis** → Calculate indicators
4. **Signal Generation** → Apply trading rules
5. **Risk Assessment** → Calculate position size
6. **Confidence Scoring** → ML model prediction
7. **Result Delivery** → Formatted Telegram message

## External Services

### Required Services
- **Redis**: Caching and pub/sub
- **TimescaleDB**: Time-series data storage
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **Loki**: Log aggregation

### API Integrations
- **Bybit API**: Market data and trading
- **Telegram Bot API**: User interface

## Configuration

### Environment Variables
- API credentials (Bybit, Telegram)
- Service URLs (Redis, Database)
- Trading parameters
- Performance settings

### Docker Services
- **app**: Main application
- **redis**: Cache layer
- **timescaledb**: Database
- **prometheus**: Monitoring
- **grafana**: Dashboards
- **loki**: Logging

## Development Workflow

### Local Development
```bash
make dev-setup  # Set up environment
make run        # Start services
make logs       # View logs
make test       # Run tests
```

### Code Quality
```bash
make lint       # Run linters
make format     # Format code
make test       # Run test suite
```

### Deployment
```bash
make deploy     # Deploy to production
make backup     # Backup database
make monitor    # Open dashboards
```

## Testing Strategy

### Unit Tests
- Individual component testing
- Mock external dependencies
- High coverage target (>90%)

### Integration Tests
- Service interaction testing
- Database operations
- API integration

### Performance Tests
- Latency measurements
- Concurrent request handling
- Memory usage monitoring

## Security Considerations

1. **API Security**
   - Read-only Bybit permissions
   - Encrypted credentials
   - Environment variable usage

2. **Telegram Security**
   - Chat ID whitelist
   - Command authentication
   - Private bot access

3. **Infrastructure Security**
   - Docker network isolation
   - Database access control
   - HTTPS for external APIs

## Monitoring & Observability

### Metrics (Prometheus)
- Request latency
- Signal generation time
- API call success rates
- Cache hit rates

### Logs (Loki + Grafana)
- Structured JSON logs
- Centralized aggregation
- Search and filtering

### Alerts
- High latency warnings
- API failures
- System resource usage

## Maintenance

### Regular Tasks
- Model retraining (90 days)
- Database cleanup
- Log rotation
- Dependency updates

### Backup Strategy
- Automated database backups
- Model versioning
- Configuration backups

## Performance Optimization

### Caching Strategy
- Redis for real-time data
- Analysis result caching
- Configurable TTLs

### Async Processing
- Concurrent API calls
- Non-blocking I/O
- uvloop for performance

### Resource Management
- Connection pooling
- Memory limits
- CPU throttling 