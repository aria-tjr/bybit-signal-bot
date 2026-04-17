"""
Main application entry point for the crypto signal bot.

Initializes all services and starts the bot.
"""

import asyncio
import signal
import sys
from typing import Optional
import uvloop

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from .core.logging import get_logger
from .core.settings import settings
from .data.cache import cache
from .data.websocket import ws_client
from .services.telegram import telegram_service
from .services.signal_processor import signal_processor
from .services.analytics import analytics
from .services.market_scanner import market_scanner
from .services.bookmap_engine import bookmap_engine
from .logic.portfolio import portfolio_manager
from .logic.market_regime import regime_detector

logger = get_logger(__name__)

# FastAPI app for health checks and metrics
app = FastAPI(title="Crypto Signal Bot", version=settings.app_version)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "mode": "testnet" if settings.bybit_testnet else "mainnet"
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # TODO: Implement Prometheus metrics
    return {"message": "Metrics endpoint"}


@app.post("/signal/{symbol}")
async def trigger_signal(symbol: str, threshold_pct: Optional[float] = None):
    """Manually trigger signal analysis for a symbol."""
    try:
        result = await signal_processor.process_symbol(
            symbol.upper(),
            threshold_pct
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/performance")
async def get_performance_analytics():
    """Get performance analytics summary."""
    try:
        return analytics.get_performance_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/portfolio")
async def get_portfolio_analytics():
    """Get portfolio metrics and risk assessment."""
    try:
        return {
            "metrics": portfolio_manager.get_portfolio_metrics(),
            "risk_assessment": portfolio_manager.get_risk_assessment()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/regime")
async def get_market_regime():
    """Get current market regime analysis."""
    try:
        return regime_detector.get_regime_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scanner/status")
async def get_scanner_status():
    """Get market scanner status and statistics."""
    try:
        return await market_scanner.get_scanner_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scanner/scan/{category}")
async def manual_scan(category: str = "all"):
    """Manually trigger market scan."""
    try:
        return await market_scanner.manual_scan(category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scanner/top-movers")
async def get_top_movers():
    """Get current top movers (gainers and losers)."""
    try:
        from .data.rest import rest_client
        return await rest_client.get_top_movers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scanner/small-caps")
async def get_small_cap_movers():
    """Get small cap high-volatility movers."""
    try:
        from .data.rest import rest_client
        return await rest_client.get_small_cap_movers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CryptoSignalBot:
    """Main application class."""
    
    def __init__(self):
        """Initialize the bot."""
        self.running = False
        self.tasks = []
        
    async def initialize(self):
        """Initialize all services."""
        logger.info("Initializing crypto signal bot...")
        
        try:
            # Connect to Redis
            await cache.connect()
            logger.info("Redis connected")
            
            # Initialize Telegram service
            await telegram_service.initialize()
            logger.info("Telegram service initialized")
            
            # Connect WebSocket
            await ws_client.connect()
            logger.info("WebSocket connected")
            
            # Initialize Bookmap signal engine
            await bookmap_engine.start()
            logger.info("Bookmap signal engine initialized")
            
            # Auto-inject test signals for comprehensive fusion analysis - CUSTOM ENHANCED VERSION
            # await self._inject_enhanced_bookmap_test_signals()  # DISABLED FOR REAL MARKET DATA
            logger.info("Real market data enabled - no test signal injection")
            
            # Send startup notification
            await telegram_service.send_notification(
                f"🚀 *Crypto Signal Bot Started*\n"
                f"Version: {settings.app_version}\n"
                f"Mode: {'Testnet' if settings.bybit_testnet else 'Mainnet'}\n"
                f"Focus: 1m/5m scalping with 20x leverage\n"
                f"Target: Top movers & small caps\n"
                f"🗺️ Bookmap order flow integration: Active\n"
                f"🔗 Signal fusion engine: Ready"
            )
            
            logger.info("Bot initialization complete")
            
        except Exception as e:
            logger.error("Failed to initialize bot", error=str(e))
            raise
            
    async def start(self):
        """Start the bot."""
        self.running = True
        
        try:
            # Start Telegram polling
            telegram_task = asyncio.create_task(telegram_service.start_polling())
            self.tasks.append(telegram_task)
            
            # Start market scanner
            if settings.scanner_enabled:
                scanner_task = asyncio.create_task(market_scanner.start_scanning())
                self.tasks.append(scanner_task)
                logger.info("Market scanner started")
            
            # Start FastAPI server
            config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=8000,
                log_level="info"
            )
            server = uvicorn.Server(config)
            server_task = asyncio.create_task(server.serve())
            self.tasks.append(server_task)
            
            # Subscribe to WebSocket updates
            await self._subscribe_to_updates()
            
            logger.info("Bot started successfully")
            
            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error("Bot error", error=str(e))
            raise
            
    async def _inject_enhanced_bookmap_test_signals(self):
        """Inject enhanced test signals with strong bearish bias for ETHUSDT and balanced for others."""
        import time
        import random
        from .services.bookmap_engine import BookmapSignal, SignalType
        
        # Extended symbol list for comprehensive coverage
        all_symbols = [
            "BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", 
            "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT", "UNIUSDT", "LTCUSDT",
            "BCHUSDT", "FILUSDT", "TRXUSDT", "ETCUSDT", "XLMUSDT", "VETUSDT",
            "ICPUSDT", "FTMUSDT", "HBARUSDT", "NEARUSDT", "ATOMUSDT", "MANAUSDT",
            "SANDUSDT", "AXSUSDT", "THETAUSDT", "ALGOUSDT", "EGLDUSDT", "FLOWUSDT",
            "KSMUSDT", "WAVESUSDT", "ROSEUSDT", "DYDXUSDT", "GMTUSDT", "APTUSDT",
            "OPUSDT", "ARBUSDT", "LDOUSDT", "GALAUSDT", "MASKUSDT", "COMPUSDT",
            "ENSUSDT", "LRCUSDT", "RNDRSUDT", "OCEANUSDT", "COTIUSDT", "CHZUSDT",
            "ONEUSDT", "HOTUSDT", "ZILUSDT", "ENJUSDT", "IOTAUSDT", "BATUSDT",
            "QNTUSDT", "FETUSDT", "GRTUSDT", "SUSHIUSDT", "SNXUSDT", "YFIUSDT",
            "CRVUSDT", "PEOPLEUSDT", "REIUSDT", "FLOKIUSDT", "PEPEUSDT", "1000SHIBUSDT",
            "ORDIUSDT", "TIAUSDT", "SUIUSDT"
        ]
        
        # Define bullish symbols (these get more bullish signals)
        bullish_symbols = {"BTCUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT", "AVAXUSDT"}
        
        signals_injected = 0
        
        for symbol in all_symbols:
            try:
                # Clear existing data
                bookmap_engine.signal_aggregator.signal_history[symbol] = []
                bookmap_engine.signal_aggregator.signal_scores[symbol] = 0.0
                
                # Enhanced signal injection for ALL symbols - ensure fusion analysis works for every pair
                # Each symbol gets enough signals for robust fusion analysis
                
                # Define symbol-specific biases for realistic market patterns
                bearish_symbols = {"ETHUSDT", "ADAUSDT", "MATICUSDT", "TRXUSDT", "XLMUSDT"}  # Strong bearish bias
                is_bullish_symbol = symbol in bullish_symbols
                is_bearish_symbol = symbol in bearish_symbols
                
                signal_types = [SignalType.WHALE_TRADE, SignalType.ICEBERG_DETECTION, SignalType.STOP_RUN, SignalType.SWEEP_DETECTED]
                
                # Inject 15-20 signals per symbol to ensure robust analysis
                signals_per_symbol = 18
                
                for i in range(signals_per_symbol):
                    signal_type = random.choice(signal_types)
                    signal_time = time.time() - (i * 15)  # Recent signals with 15-second intervals
                    
                    # Determine side based on symbol bias
                    if is_bearish_symbol:
                        # 80% bearish signals for bearish symbols
                        side = "SELL" if random.random() < 0.8 else "BUY"
                        confidence = random.uniform(8.0, 9.5) if side == "SELL" else random.uniform(6.0, 7.5)
                        order_flow_bias = random.uniform(-0.7, -0.9) if side == "SELL" else random.uniform(-0.2, 0.1)
                    elif is_bullish_symbol:
                        # 80% bullish signals for bullish symbols  
                        side = "BUY" if random.random() < 0.8 else "SELL"
                        confidence = random.uniform(8.0, 9.5) if side == "BUY" else random.uniform(6.0, 7.5)
                        order_flow_bias = random.uniform(0.7, 0.9) if side == "BUY" else random.uniform(-0.1, 0.2)
                    else:
                        # Balanced but with slight random bias for neutral symbols
                        bias_direction = random.choice(["BULLISH", "BEARISH", "NEUTRAL"])
                        if bias_direction == "BULLISH":
                            side = "BUY" if random.random() < 0.65 else "SELL"
                            confidence = random.uniform(7.5, 8.5) if side == "BUY" else random.uniform(6.5, 7.5)
                            order_flow_bias = random.uniform(0.3, 0.7) if side == "BUY" else random.uniform(-0.3, 0.1)
                        elif bias_direction == "BEARISH":
                            side = "SELL" if random.random() < 0.65 else "BUY"
                            confidence = random.uniform(7.5, 8.5) if side == "SELL" else random.uniform(6.5, 7.5)
                            order_flow_bias = random.uniform(-0.3, -0.7) if side == "SELL" else random.uniform(-0.1, 0.3)
                        else:
                            side = random.choice(["BUY", "SELL"])
                            confidence = random.uniform(7.0, 8.0)
                            order_flow_bias = random.uniform(-0.4, 0.4)
                    
                    # Set realistic price ranges based on symbol
                    if "BTC" in symbol:
                        base_price = random.uniform(105000, 115000)
                        volume_range = (1000000, 8000000)
                    elif "ETH" in symbol:
                        base_price = random.uniform(2600, 2800)
                        volume_range = (2000000, 6000000)
                    else:
                        base_price = random.uniform(0.1, 500.0)
                        volume_range = (500000, 3000000)
                    
                    signal = BookmapSignal(
                        timestamp=signal_time,
                        instrument=symbol,
                        signal_type=signal_type,
                        confidence=confidence,
                        triggers=[signal_type.value.lower(), 'market_microstructure'],
                        side=side,
                        price=base_price + random.uniform(-base_price*0.01, base_price*0.01),
                        details={
                            "volume": random.randint(*volume_range),
                            "order_flow_imbalance": order_flow_bias,
                            "test_signal": True,
                            "symbol_bias": "bearish" if is_bearish_symbol else "bullish" if is_bullish_symbol else "neutral"
                        }
                    )
                    
                    bookmap_engine.signal_aggregator.process_signal(signal)
                    signals_injected += 1
                            
            except Exception as e:
                logger.error(f"Failed to inject signals for {symbol}", error=str(e))
                
        logger.info(f"Injected {signals_injected} enhanced test signals for {len(all_symbols)} symbols (ETHUSDT with strong bearish bias)")

    async def _inject_bookmap_test_signals(self):
        """Inject comprehensive test signals for all major crypto symbols."""
        import time
        import random
        from .services.bookmap_engine import BookmapSignal, SignalType
        
        # Enhanced symbol list including active trading symbols and MOGUSDT
        symbols = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "ADAUSDT", "DOTUSDT", 
            "LINKUSDT", "MATICUSDT", "ATOMUSDT", "NEARUSDT", "JUPUSDT", "WUSDT", 
            "APEXUSDT", "XTERUSDT", "PYTHUSDT", "RNSTUSDT", "FTMUSDT", "AAVEUSDT", 
            "UNIUSDT", "SUIUSDT", "ARBUSDT", "OPUSDT", "APTUSDT", "INJUSDT", 
            "TIAUSDT", "RUNEUSDT", "PENDLEUSDT", "JITOUSDT", "WIFUSDT", "RAYUSDT",
            "POPCATUSDT", "BOMEUSDT", "TURBOUSDT", "FIDAUSDT", "MEMEUSDT", "NOTUSDT",
            "DOGSUSDT", "TONUSDT", "HMSTRUSDT", "CATUSDT", "ACTUSDT", "EIGENUSDT",
            "SCUSDT", "SEIUSDT", "TAOUSDT", "CHZUSDT", "SANDUSDT", "MANAUSDT",
            "ALGOUSDT", "AXSUSDT", "MINAUSDT", "FILUSDT", "HBARUSDT", "VETUSDT",
            "ICPUSDT", "XLMUSDT", "TRXUSDT", "LTCUSDT", "BCHUSDT", "ETCUSDT",
            "MOGUSDT", "SKATEUSDT", "KAIAUSDT", "MYRIAUSDT", "RVNUSDT", "UMAUSDT",
            "AIOZUSDT", "ANIMEUSDT", "VVVUSDT"  # Add actively trading symbols
        ]
        
        signal_types = [
            SignalType.WHALE_TRADE,
            SignalType.ICEBERG_DETECTION, 
            SignalType.STOP_RUN,
            SignalType.SWEEP_DETECTED
        ]
        
        # High-impact symbols that need strong bullish bias for current trading
        bullish_symbols = ["MOGUSDT", "SKATEUSDT", "KAIAUSDT", "MYRIAUSDT", "TOSHIUSDT", "WUSDT"]
        
        total_injected = 0
        random.seed(42)  # Consistent results
        
        for symbol in symbols:
            # Enhanced signal injection with bias for active symbols
            if symbol in bullish_symbols:
                # Strong bullish bias for active trading symbols
                for signal_type in signal_types:
                    # 4 BUY signals with high confidence
                    for _ in range(4):
                        try:
                            test_signal = BookmapSignal(
                                timestamp=time.time(),
                                instrument=symbol,
                                signal_type=signal_type,
                                confidence=random.uniform(8.5, 9.8),
                                triggers=["whale_flow", "order_imbalance"],
                                side="BUY",
                                price=random.uniform(0.000001, 100.0),
                                details={
                                    'volume': random.uniform(1000000, 3000000),
                                    'order_flow_imbalance': random.uniform(0.7, 0.95),
                                    'auto_generated': True,
                                    'purpose': 'fusion_analysis'
                                }
                            )
                            bookmap_engine.signal_aggregator.process_signal(test_signal)
                            total_injected += 1
                        except Exception as e:
                            logger.warning(f"Failed to inject bullish signal for {symbol}: {e}")
                    
                    # 1 SELL signal with lower confidence
                    try:
                        test_signal = BookmapSignal(
                            timestamp=time.time(),
                            instrument=symbol,
                            signal_type=signal_type,
                            confidence=random.uniform(3.0, 5.0),
                            triggers=["minor_resistance"],
                            side="SELL",
                            price=random.uniform(0.000001, 100.0),
                            details={
                                'volume': random.uniform(200000, 600000),
                                'order_flow_imbalance': random.uniform(-0.3, -0.1),
                                'auto_generated': True,
                                'purpose': 'fusion_analysis'
                            }
                        )
                        bookmap_engine.signal_aggregator.process_signal(test_signal)
                        total_injected += 1
                    except Exception as e:
                        logger.warning(f"Failed to inject bearish signal for {symbol}: {e}")
            else:
                # Balanced signals for other symbols
                for signal_type in signal_types:
                    for side in ["BUY", "SELL"]:
                        for _ in range(2):
                            try:
                                test_signal = BookmapSignal(
                                    timestamp=time.time(),
                                    instrument=symbol,
                                    signal_type=signal_type,
                                    confidence=random.uniform(7.0, 8.5),
                                    triggers=["auto_inject", "market_flow"],
                                    side=side,
                                    price=random.uniform(0.1, 100.0),
                                    details={
                                        'volume': random.uniform(500000, 1500000),
                                        'order_flow_imbalance': random.uniform(-0.5, 0.5),
                                        'auto_generated': True,
                                        'purpose': 'fusion_analysis'
                                    }
                                )
                                bookmap_engine.signal_aggregator.process_signal(test_signal)
                                total_injected += 1
                            except Exception as e:
                                logger.warning(f"Failed to inject balanced signal for {symbol}: {e}")
        
        logger.info(f"Injected {total_injected} test signals for {len(symbols)} symbols")
        logger.info(f"Enhanced signals for active symbols: {', '.join(bullish_symbols)}")
        
    async def _subscribe_to_updates(self):
        """Subscribe to WebSocket updates from Telegram."""
        # This will be called when users request signals
        # For now, we'll just log that we're ready
        logger.info("Ready to process signal requests")
        
    async def stop(self):
        """Stop the bot gracefully."""
        logger.info("Stopping bot...")
        self.running = False
        
        try:
            # Send shutdown notification
            await telegram_service.send_notification(
                "🛑 *Crypto Signal Bot Stopping*"
            )
            
            # Stop market scanner
            if settings.scanner_enabled:
                await market_scanner.stop_scanning()
                
            # Stop Bookmap signal engine
            await bookmap_engine.stop()
            
            # Cancel all tasks
            for task in self.tasks:
                task.cancel()
                
            # Wait for tasks to complete
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
            # Disconnect services
            await telegram_service.stop()
            await ws_client.close()
            await cache.disconnect()
            
            logger.info("Bot stopped successfully")
            
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
            

# Global bot instance
bot = CryptoSignalBot()


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {sig}")
    asyncio.create_task(bot.stop())
    

async def main():
    """Main entry point."""
    # Set up uvloop for better performance
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize bot
        await bot.initialize()
        
        # Start bot
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error("Fatal error", error=str(e))
        sys.exit(1)
    finally:
        await bot.stop()
        

if __name__ == "__main__":
    asyncio.run(main()) 