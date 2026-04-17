#!/bin/bash

# Crypto Signal Bot Docker Startup Script
# Usage: ./docker-start.sh [mode]
# Modes: basic, trading, full, test

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Crypto Signal Bot Docker Startup${NC}"
echo -e "${BLUE}=====================================${NC}"

# Check if .env file exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}❌ Error: .env file not found in $PROJECT_DIR${NC}"
    echo -e "${YELLOW}💡 Please copy env.example to .env and configure your settings${NC}"
    exit 1
fi

# Load environment variables safely
set -a
source "$PROJECT_DIR/.env" 2>/dev/null || true
set +a

# Verify required variables
if [ -z "$BYBIT_API_KEY" ] || [ -z "$BYBIT_API_SECRET" ]; then
    echo -e "${RED}❌ Error: Bybit API credentials not configured${NC}"
    echo -e "${YELLOW}💡 Please set BYBIT_API_KEY and BYBIT_API_SECRET in .env${NC}"
    exit 1
fi

MODE=${1:-basic}

echo -e "${GREEN}✅ Environment configured${NC}"
echo -e "${BLUE}📊 Mode: $MODE${NC}"
echo -e "${BLUE}🔗 Testnet: ${BYBIT_TESTNET:-false}${NC}"

cd "$SCRIPT_DIR"

case $MODE in
    "basic")
        echo -e "${GREEN}🏃 Starting basic signal bot (no trading)...${NC}"
        docker-compose up -d app redis timescaledb
        ;;
    "trading")
        echo -e "${GREEN}🤖 Starting with auto trading enabled...${NC}"
        AUTO_TRADING_ENABLED=true docker-compose up -d app redis timescaledb
        ;;
    "auto-trader")
        echo -e "${GREEN}🎯 Starting dedicated auto trading service...${NC}"
        docker-compose --profile auto-trading up -d
        ;;
    "full")
        echo -e "${GREEN}📈 Starting full stack (bot + monitoring)...${NC}"
        docker-compose up -d
        ;;
    "test")
        echo -e "${GREEN}🧪 Starting test environment...${NC}"
        BYBIT_TESTNET=true docker-compose up -d app redis timescaledb
        echo -e "${YELLOW}💡 Running in testnet mode for safe testing${NC}"
        ;;
    "stop")
        echo -e "${YELLOW}🛑 Stopping all services...${NC}"
        docker-compose down
        docker-compose --profile auto-trading down
        ;;
    "restart")
        echo -e "${YELLOW}🔄 Restarting services...${NC}"
        docker-compose down
        docker-compose up -d app redis timescaledb
        ;;
    "logs")
        echo -e "${BLUE}📜 Showing logs...${NC}"
        docker-compose logs -f app
        ;;
    "build")
        echo -e "${YELLOW}🔨 Rebuilding containers...${NC}"
        docker-compose build --no-cache
        ;;
    *)
        echo -e "${RED}❌ Unknown mode: $MODE${NC}"
        echo -e "${YELLOW}Available modes:${NC}"
        echo -e "  ${GREEN}basic${NC}      - Signal bot only (no trading)"
        echo -e "  ${GREEN}trading${NC}    - Signal bot with auto trading"
        echo -e "  ${GREEN}auto-trader${NC} - Dedicated auto trading service"
        echo -e "  ${GREEN}full${NC}       - Full stack with monitoring"
        echo -e "  ${GREEN}test${NC}       - Testnet mode for safe testing"
        echo -e "  ${GREEN}stop${NC}       - Stop all services"
        echo -e "  ${GREEN}restart${NC}    - Restart services"
        echo -e "  ${GREEN}logs${NC}       - Show logs"
        echo -e "  ${GREEN}build${NC}      - Rebuild containers"
        exit 1
        ;;
esac

if [ "$MODE" != "stop" ] && [ "$MODE" != "logs" ] && [ "$MODE" != "build" ]; then
    echo -e "${GREEN}✅ Services started successfully!${NC}"
    echo -e "${BLUE}📊 Access points:${NC}"
    echo -e "  ${GREEN}🤖 Bot API:${NC}        http://localhost:8000"
    echo -e "  ${GREEN}📈 Metrics:${NC}        http://localhost:8001"
    echo -e "  ${GREEN}📊 Grafana:${NC}        http://localhost:3000 (admin/admin)"
    echo -e "  ${GREEN}🔍 Prometheus:${NC}     http://localhost:9090"
    echo -e "  ${GREEN}📝 Logs:${NC}           docker-compose logs -f app"
    echo ""
    echo -e "${YELLOW}💡 To stop services: ./docker-start.sh stop${NC}"
    echo -e "${YELLOW}💡 To view logs: ./docker-start.sh logs${NC}"
fi 