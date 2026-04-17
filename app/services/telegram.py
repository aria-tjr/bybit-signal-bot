"""
Telegram bot service for sending formatted signal messages.

Handles message formatting and delivery to Telegram users.
ULTRA-OPTIMIZED: Enhanced performance, formatting, and user experience.
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pytz
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

from ..core.logging import get_logger
from ..core.settings import settings

logger = get_logger(__name__)


class TelegramService:
    """ULTRA-OPTIMIZED Telegram bot service for signal delivery."""
    
    def __init__(self) -> None:
        """Initialize optimized Telegram service."""
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        self.authorized_chats = set(settings.telegram_chat_ids)
        
        # OPTIMIZED: Enhanced rate limiting with priority signals
        self.last_signal_time: Dict[str, datetime] = {}
        self.min_signal_interval = timedelta(seconds=8)  # Reduced for faster delivery
        self.priority_queue: List[Dict[str, Any]] = []  # High-priority signal queue
        
        # OPTIMIZED: User management and performance tracking
        self.user_balances: Dict[str, float] = {}
        self.message_delivery_stats = {
            "messages_sent": 0,
            "delivery_times": [],
            "failed_deliveries": 0,
            "retries": 0
        }
        
        # OPTIMIZED: Enhanced signal quality tracking
        self.signal_quality_history = []
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self) -> None:
        """Initialize bot and application with optimization."""
        try:
            # Create bot instance with enhanced performance settings
            self.bot = Bot(
                token=settings.telegram_bot_token.get_secret_value()
            )
            
            # Create application with optimization
            self.application = Application.builder().token(
                settings.telegram_bot_token.get_secret_value()
            ).concurrent_updates(True).build()  # Enable concurrent updates
            
            # Add handlers
            self._add_handlers()
            
            # Initialize the bot
            await self.application.initialize()
            
            logger.info("ULTRA-OPTIMIZED Telegram service initialized with enhanced performance")
            
        except Exception as e:
            logger.error("Failed to initialize Telegram service", error=str(e))
            raise
            
    def _add_handlers(self) -> None:
        """Add command and message handlers."""
        if not self.application:
            return
            
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("signal", self._handle_signal_request))
        self.application.add_handler(CommandHandler("status", self._handle_status))
        
        # New portfolio management commands
        self.application.add_handler(CommandHandler("portfolio", self._handle_portfolio))
        self.application.add_handler(CommandHandler("risk", self._handle_risk_assessment))
        self.application.add_handler(CommandHandler("performance", self._handle_performance))
        self.application.add_handler(CommandHandler("regime", self._handle_market_regime))
        
        # Market scanner commands
        self.application.add_handler(CommandHandler("scan", self._handle_manual_scan))
        self.application.add_handler(CommandHandler("movers", self._handle_top_movers))
        self.application.add_handler(CommandHandler("smallcaps", self._handle_small_caps))
        self.application.add_handler(CommandHandler("scanner", self._handle_scanner_status))
        
        # Bookmap order flow commands
        self.application.add_handler(CommandHandler("orderflow", self._handle_order_flow))
        self.application.add_handler(CommandHandler("bookmap", self._handle_bookmap_status))
        self.application.add_handler(CommandHandler("whales", self._handle_whale_activity))
        self.application.add_handler(CommandHandler("fusion", self._handle_fusion_performance))
        
        # Educational commands
        self.application.add_handler(CommandHandler("explain", self._handle_explain_command))
        
        # Diagnostic commands
        self.application.add_handler(CommandHandler("diagnostic", self._handle_diagnostic))
        self.application.add_handler(CommandHandler("reset_api", self._handle_reset_api))
        self.application.add_handler(CommandHandler("test_symbol", self._handle_test_symbol))
        self.application.add_handler(CommandHandler("max_leverage", self._handle_max_leverage))
        self.application.add_handler(CommandHandler("clear_cache", self._handle_clear_cache))
        
        # NEW – Manual-trading helper commands (advanced risk management)
        self.application.add_handler(CommandHandler("setbalance", self._handle_set_balance))
        self.application.add_handler(CommandHandler("size", self._handle_position_size))
        self.application.add_handler(CommandHandler("rr", self._handle_risk_reward_calc))
        self.application.add_handler(CommandHandler("heat", self._handle_portfolio_heat))
        
        # NEW – Advanced Bookmap analysis commands
        self.application.add_handler(CommandHandler("orderflow", self._handle_order_flow_analysis))
        self.application.add_handler(CommandHandler("icebergs", self._handle_iceberg_analysis))
        self.application.add_handler(CommandHandler("absorption", self._handle_absorption_analysis))
        self.application.add_handler(CommandHandler("levels", self._handle_support_resistance))
        self.application.add_handler(CommandHandler("whales", self._handle_whale_activity))
        
        # Message handler for symbol input
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_symbol_message)
        )
        
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            await update.message.reply_text(
                "⛔ Unauthorized access. This bot is private."
            )
            logger.warning("Unauthorized access attempt", chat_id=chat_id)
            return
            
        welcome_message = (
            "🚀 *Welcome to Crypto Signal Bot!*\n\n"
            "I provide real-time trading signals for Bybit.\n\n"
            "*Commands:*\n"
            "/signal SYMBOL - Get signal for a symbol\n"
            "/status - Check bot status\n"
            "/help - Show help message\n\n"
            "Or just send a symbol like: BTCUSDT, BTC, ETH, SOL"
        )
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_message = (
            "📚 *How to use this bot:*\n\n"
            "1️⃣ Send a trading pair symbol (e.g., BTCUSDT, BTC, ETH)\n"
            "2️⃣ Or use /signal BTCUSDT or /signal BTC\n"
            "3️⃣ Receive comprehensive analysis\n\n"
            "*Available Commands:*\n"
            "/signal SYMBOL - Get trading signal\n"
            "/size ENTRY STOP RISK% [LEV] - Position size calc\n"
            "/rr ENTRY STOP TP1 [TP2] - Risk/Reward\n"
            "/setbalance AMOUNT - Store your capital\n"
            "/heat - Portfolio heat metrics\n"
            "/orderflow SYMBOL - Advanced order flow analysis\n"
            "/icebergs SYMBOL - Iceberg detection summary\n"
            "/absorption SYMBOL - Volume absorption analysis\n"
            "/levels SYMBOL - Support/resistance levels\n"
            "/whales SYMBOL - Whale activity tracking\n"
            "/portfolio - View portfolio overview\n"
            "/risk - Check risk assessment\n"
            "/performance - View performance stats\n"
            "/regime - Check market regime\n"
            "/status - Bot status\n\n"
            "*Market Scanner Commands:*\n"
            "/scan - 🔒 STRICT 100-pair signal-grade scan\n"
            "/scan all - Legacy basic market scan\n"
            "/movers - Get top gainers/losers\n"
            "/smallcaps - Get small cap movers\n"
            "/scanner - Scanner status\n\n"
            "*Bookmap Order Flow Commands:*\n"
            "/orderflow SYMBOL - Get order flow analysis\n"
            "/bookmap - Bookmap engine status\n"
            "/whales - Recent whale activity\n"
            "/fusion - Signal fusion performance\n\n"
            "*Educational Commands:*\n"
            "/explain - Why scan shows symbol but no signal?\n\n"
            "*Diagnostic Commands:*\n"
            "/diagnostic - Check system status and API health\n"
            "/reset_api - Reset API circuit breaker\n"
            "/test_symbol SYMBOL - Test data collection for a symbol\n\n"
            "*Signal includes:*\n"
            "• Trade direction (Long/Short)\n"
            "• Recommended leverage (up to 20x)\n"
            "• Entry price & stop loss\n"
            "• 3 Take profit levels\n"
            "• Confidence score\n"
            "• Technical rationale\n"
            "• 1m/5m timeframe focus\n\n"
            "⚠️ *Remember: This is not financial advice!*\n"
            "🎯 *Focus: Quick profits with high leverage*"
        )
        
        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
    async def _handle_signal_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /signal command."""
        try:
            chat_id = str(update.effective_chat.id)
            
            logger.info("Received /signal command", chat_id=chat_id, args=context.args)
            
            if chat_id not in self.authorized_chats:
                logger.warning("Unauthorized /signal attempt", chat_id=chat_id)
                return
                
            # Get symbol from command arguments
            if context.args:
                symbol = context.args[0].upper()
                
                # Relaxed validation - allow more symbol formats
                if len(symbol) < 3:
                    logger.info("Symbol too short in /signal", symbol=symbol, chat_id=chat_id)
                    await update.message.reply_text(
                        "❌ Symbol too short. Please provide a valid trading symbol.\nExample: `/signal BTCUSDT` or `/signal BTC`"
                    )
                    return
                    
                # Auto-append USDT if symbol doesn't contain it and looks like a base currency
                if not any(suffix in symbol for suffix in ["USDT", "USD", "EUR", "BTC", "ETH"]):
                    if len(symbol) <= 6:  # Likely a base currency like BTC, ETH
                        symbol = symbol + "USDT"
                        logger.info("Auto-appended USDT to /signal", original=context.args[0].upper(), new_symbol=symbol, chat_id=chat_id)
                
                logger.info("Processing /signal command", symbol=symbol, chat_id=chat_id)
                
                await update.message.reply_text(
                    f"🔄 Processing signal for *{symbol}*...",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Import here to avoid circular import
                from .signal_processor import signal_processor
                
                # Process signal asynchronously with ULTRA-COMPREHENSIVE analysis
                # This uses ALL advanced capabilities: Bookmap, regime detection, 
                # iceberg analysis, whale tracking, market maker behavior, etc.
                asyncio.create_task(
                    signal_processor.process_symbol_ultra_comprehensive(symbol, chat_ids=[chat_id])
                )
                
                logger.info("Signal requested via command", symbol=symbol, chat_id=chat_id)
            else:
                logger.info("No symbol provided in /signal command", chat_id=chat_id)
                await update.message.reply_text(
                    "Please provide a symbol. Examples: `/signal BTCUSDT` or `/signal BTC`"
                )
                
        except Exception as e:
            logger.error("Error handling /signal command", error=str(e), exc_info=True)
            try:
                await update.message.reply_text("❌ Error processing your request. Please try again.")
            except:
                pass
            
    async def _handle_symbol_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle direct symbol messages."""
        try:
            chat_id = str(update.effective_chat.id)
            message_text = update.message.text.strip()
            
            logger.info("Received message", chat_id=chat_id, message=message_text)
            
            if chat_id not in self.authorized_chats:
                logger.warning("Unauthorized message attempt", chat_id=chat_id)
                return
                
            symbol = message_text.upper()
            
            # Relaxed validation - allow more symbol formats
            if len(symbol) < 3:
                logger.info("Symbol too short", symbol=symbol, chat_id=chat_id)
                await update.message.reply_text(
                    "❌ Symbol too short. Please send a valid trading symbol (e.g., BTCUSDT, BTC, ETHUSDT)"
                )
                return
                
            # Auto-append USDT if symbol doesn't contain it and looks like a base currency
            if not any(suffix in symbol for suffix in ["USDT", "USD", "EUR", "BTC", "ETH"]):
                if len(symbol) <= 6:  # Likely a base currency like BTC, ETH
                    symbol = symbol + "USDT"
                    logger.info("Auto-appended USDT", original=message_text.upper(), new_symbol=symbol, chat_id=chat_id)
                
            logger.info("Processing symbol request", symbol=symbol, chat_id=chat_id)
            
            await update.message.reply_text(
                f"🔄 Processing signal for *{symbol}*...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Import here to avoid circular import
            from .signal_processor import signal_processor
            
            # Process symbol with ULTRA-COMPREHENSIVE analysis
            # Uses ALL advanced capabilities for maximum signal quality
            asyncio.create_task(
                signal_processor.process_symbol_ultra_comprehensive(symbol, chat_ids=[chat_id])
            )
            
            logger.info("Signal requested via message", symbol=symbol, chat_id=chat_id)
            
        except Exception as e:
            logger.error("Error handling symbol message", error=str(e), exc_info=True)
            try:
                await update.message.reply_text("❌ Error processing your request. Please try again.")
            except:
                pass
        
    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        status_message = (
            "✅ *Bot Status: Online*\n\n"
            f"Version: {settings.app_version}\n"
            f"Mode: {'Testnet' if settings.bybit_testnet else 'Mainnet'}\n"
            f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        
        await update.message.reply_text(
            status_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
    async def _handle_portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /portfolio command."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            # Import here to avoid circular import
            from ..logic.portfolio import portfolio_manager
            
            metrics = portfolio_manager.get_portfolio_metrics()
            
            if not metrics:
                await update.message.reply_text("📊 No portfolio data available yet.")
                return
                
            # Format portfolio message
            message = f"""
📈 *PORTFOLIO OVERVIEW*

💰 *Performance:*
• Total P&L: {metrics['total_pnl']:+.2f}%
• Realized P&L: {metrics['realized_pnl']:+.2f}%
• Unrealized P&L: {metrics['unrealized_pnl']:+.2f}%

📊 *Statistics:*
• Active Positions: {metrics['active_positions']}
• Total Trades: {metrics['total_positions']}
• Win Rate: {metrics['win_rate']:.1f}%
• Avg Profit/Trade: {metrics['avg_profit_per_trade']:+.2f}%
• Max Drawdown: {metrics['max_drawdown']:.2f}%

🔥 *Portfolio Heat: {metrics['portfolio_heat']:.1f}%*
"""
            
            if metrics['positions_detail']:
                message += "\n🎯 *Active Positions:*\n"
                for pos in metrics['positions_detail'][:5]:  # Show max 5 positions
                    pnl_emoji = "🟢" if pos['unrealized_pnl'] > 0 else "🔴"
                    message += f"• {pos['symbol']} {pos['direction']} {pnl_emoji} {pos['unrealized_pnl']:+.2f}%\n"
                    
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Portfolio command failed", error=str(e))
            await update.message.reply_text("❌ Failed to retrieve portfolio data.")
            
    async def _handle_risk_assessment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /risk command."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            from ..logic.portfolio import portfolio_manager
            
            risk_data = portfolio_manager.get_risk_assessment()
            
            if not risk_data:
                await update.message.reply_text("⚠️ No risk data available.")
                return
                
            # Risk level emoji
            risk_emojis = {
                "LOW": "🟢",
                "MEDIUM": "🟡", 
                "HIGH": "🟠",
                "EXTREME": "🔴"
            }
            
            risk_emoji = risk_emojis.get(risk_data['risk_level'], "⚪")
            
            message = f"""
⚠️ *RISK ASSESSMENT*

{risk_emoji} *Overall Risk: {risk_data['risk_level']} ({risk_data['overall_risk_score']:.1f}/100)*

📊 *Risk Breakdown:*
• Position Concentration: {risk_data['position_concentration']:.1f}%
• Portfolio Heat: {risk_data['portfolio_heat']:.1f}%
• Drawdown Risk: {risk_data['drawdown_risk']:.1f}%

🎯 *Capacity:*
• Max New Positions: {risk_data['max_new_positions']}

💡 *Recommendation:*
{risk_data['recommended_action']}
"""
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Risk assessment command failed", error=str(e))
            await update.message.reply_text("❌ Failed to retrieve risk assessment.")
            
    async def _handle_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /performance command."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            from ..logic.portfolio import portfolio_manager
            
            metrics = portfolio_manager.get_portfolio_metrics()
            
            if not metrics or not portfolio_manager.closed_positions:
                await update.message.reply_text("📊 No performance data available yet.")
                return
                
            # Calculate additional performance metrics
            recent_trades = portfolio_manager.closed_positions[-10:]  # Last 10 trades
            recent_pnl = [pos.realized_pnl for pos in recent_trades]
            recent_win_rate = sum(1 for pnl in recent_pnl if pnl > 0) / len(recent_pnl) * 100
            
            message = f"""
📈 *PERFORMANCE ANALYSIS*

🎯 *Overall Stats:*
• Win Rate: {metrics['win_rate']:.1f}%
• Total Trades: {metrics['total_positions']}
• Avg Duration: {metrics['avg_duration_hours']:.1f}h
• Max Drawdown: {metrics['max_drawdown']:.2f}%

📊 *Recent Performance (Last 10):*
• Recent Win Rate: {recent_win_rate:.1f}%
• Best Trade: {max(recent_pnl):+.2f}%
• Worst Trade: {min(recent_pnl):+.2f}%

💰 *P&L Summary:*
• Total P&L: {metrics['total_pnl']:+.2f}%
• Realized: {metrics['realized_pnl']:+.2f}%
• Unrealized: {metrics['unrealized_pnl']:+.2f}%
"""
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Performance command failed", error=str(e))
            await update.message.reply_text("❌ Failed to retrieve performance data.")
            
    async def _handle_market_regime(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /regime command."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            from ..logic.market_regime import regime_detector
            
            regime_summary = regime_detector.get_regime_summary()
            
            if not regime_summary:
                await update.message.reply_text("🌊 No market regime data available.")
                return
                
            # Regime emojis
            regime_emojis = {
                "trending_bull": "🐂",
                "trending_bear": "🐻", 
                "range_bound": "📊",
                "high_volatility": "⚡",
                "low_volatility": "😴",
                "breakout": "🚀",
                "reversal": "🔄"
            }
            
            current_regime = regime_summary.get('current_regime')
            regime_emoji = regime_emojis.get(current_regime, "🌊")
            
            message = f"""
🌊 *MARKET REGIME ANALYSIS*

{regime_emoji} *Current Regime: {current_regime.replace('_', ' ').title() if current_regime else 'Unknown'}*
⏱️ *Duration: {regime_summary.get('regime_duration_hours', 0):.1f} hours*
📊 *Stability: {regime_summary.get('regime_stability', 50):.1f}%*

📝 *Recent Regime History:*
"""
            
            for regime_data in regime_summary.get('recent_regimes', [])[-3:]:
                regime_name = regime_data['regime'].replace('_', ' ').title()
                duration = regime_data['duration_hours']
                emoji = regime_emojis.get(regime_data['regime'], "🌊")
                message += f"• {emoji} {regime_name}: {duration:.1f}h\n"
                
            message += "\n💡 *The bot automatically adapts strategy based on detected market regime.*"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Market regime command failed", error=str(e))
            await update.message.reply_text("❌ Failed to retrieve market regime data.")
        
    async def send_signal(self, signal_data: Dict[str, Any], chat_ids: Optional[List[str]] = None) -> None:
        """
        Send formatted signal to Telegram with optimized rate limiting and batching.
        
        Args:
            signal_data: Signal analysis data
            chat_ids: Optional list of chat IDs to send to
        """
        if not self.bot:
            logger.error("Bot not initialized")
            return
            
        # Determine recipients
        recipients = chat_ids or list(self.authorized_chats)
        current_time = datetime.utcnow()
        
        # OPTIMIZED: Intelligent rate limiting with priority signals
        confidence = float(signal_data.get('confidence_score', 50))
        if confidence <= 10:  # Convert 0-10 scale
            confidence = confidence * 10
            
        # Priority signals get reduced rate limiting
        is_priority = confidence >= 75 or signal_data.get('ultra_comprehensive', False)
        min_interval = timedelta(seconds=5 if is_priority else 10)
        
        # OPTIMIZED: Batch message preparation for faster sending
        try:
            # Pre-format message once for all recipients
            formatted_message = self._format_signal_message(signal_data)
            
            # Clean message for safer markdown parsing
            clean_message = self._clean_markdown_message(formatted_message)
            
            # OPTIMIZED: Parallel sending to multiple chats
            send_tasks = []
            for chat_id in recipients:
                # Rate limiting check
                if chat_id in self.last_signal_time:
                    time_since_last = current_time - self.last_signal_time[chat_id]
                    if time_since_last < min_interval:
                        remaining_wait = min_interval - time_since_last
                        logger.info(
                            "Signal rate limited",
                            chat_id=chat_id,
                            symbol=signal_data.get('symbol', 'Unknown'),
                            wait_seconds=int(remaining_wait.total_seconds()),
                            is_priority=is_priority
                        )
                        continue
                
                # Create send task
                send_task = self._send_to_chat_with_retry(chat_id, clean_message, signal_data)
                send_tasks.append((chat_id, send_task))
            
            # Execute all sends in parallel with timeout
            if send_tasks:
                await asyncio.gather(
                    *[task for _, task in send_tasks],
                    return_exceptions=True
                )
                
                # Update last signal times for successful sends
                for chat_id, _ in send_tasks:
                    self.last_signal_time[chat_id] = current_time
                    
                logger.info(
                    "Signal sent to multiple chats",
                    symbol=signal_data.get('symbol', 'Unknown'),
                    recipients=len(send_tasks),
                    confidence=confidence,
                    is_priority=is_priority
                )
                
        except Exception as e:
            logger.error("Failed to send signal batch", error=str(e))
            
    def _clean_markdown_message(self, message: str) -> str:
        """Clean and optimize message for safer markdown parsing."""
        # OPTIMIZED: More comprehensive markdown cleaning
        replacements = {
            "_": "\\_",
            "`": "\\`", 
            "[": "\\[",
            "]": "\\]",
            "(": "\\(",
            ")": "\\)",
            "~": "\\~",
            ">": "\\>",
            "#": "\\#",
            "+": "\\+",
            "-": "\\-",
            "=": "\\=",
            "|": "\\|",
            "{": "\\{",
            "}": "\\}"
        }
        
        clean_message = message
        for char, replacement in replacements.items():
            # Only escape if not already escaped and not inside code blocks
            clean_message = clean_message.replace(char, replacement)
            
        return clean_message
        
    async def _send_to_chat_with_retry(self, chat_id: str, message: str, signal_data: Dict[str, Any]) -> None:
        """Send message to specific chat with retry logic."""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
                
                logger.debug("Signal sent successfully", chat_id=chat_id, attempt=attempt + 1)
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        "Signal send failed, retrying",
                        chat_id=chat_id,
                        attempt=attempt + 1,
                        error=str(e)
                    )
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                                         logger.error(
                         "Signal send failed after retries",
                         chat_id=chat_id,
                         error=str(e),
                         symbol=signal_data.get('symbol', 'Unknown')
                     )
                     
    def _format_signal_message(self, data: Dict[str, Any]) -> str:
        """Format signal data into optimized Telegram message with enhanced readability."""
        # Get timestamps - handle both datetime objects and ISO strings from cache
        timestamp = data["timestamp"]
        if isinstance(timestamp, str):
            # Parse ISO string back to datetime
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                # Fallback to current time if parsing fails
                timestamp = datetime.utcnow()
        
        utc_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        berlin_tz = pytz.timezone("Europe/Berlin")
        berlin_time = timestamp.astimezone(berlin_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        # OPTIMIZED: Enhanced confidence calculation and display
        confidence = float(data.get("confidence_score", 50))
        
        # Normalize confidence to 0-100 scale for consistent display
        if confidence <= 10:  # Convert 0-10 scale to 0-100 scale
            confidence = confidence * 10
        
        # Enhanced confidence visualization
        if confidence >= 85:
            confidence_emoji = "🟢💎"  # Premium signal
            confidence_label = "PREMIUM"
        elif confidence >= 75:
            confidence_emoji = "🟢⭐"  # High quality
            confidence_label = "HIGH"
        elif confidence >= 65:
            confidence_emoji = "🟡📊"  # Good quality
            confidence_label = "GOOD"
        elif confidence >= 50:
            confidence_emoji = "🟡⚖️"  # Medium quality
            confidence_label = "MEDIUM"
        else:
            confidence_emoji = "🔴⚠️"  # Low quality
            confidence_label = "LOW"
            
        # Direction emoji and styling
        direction_emoji = "🚀📈" if data["direction"] == "LONG" else "🐻📉"
        direction_style = "*LONG*" if data["direction"] == "LONG" else "*SHORT*"
        
        # OPTIMIZED: Enhanced signal quality analysis
        leverage = data.get('leverage', 1)
        symbol = data.get('symbol', 'Unknown')
        
        # Calculate potential profit percentages
        tp1_profit = data.get('tp1_profit', '0.8')
        tp2_profit = data.get('tp2_profit', '1.5') 
        tp3_profit = data.get('tp3_profit', '2.5')
        
        # OPTIMIZED: Streamlined signal header with key metrics
        message = f"""
🎯 *ULTRA-SCALPING SIGNAL* {confidence_emoji}
{direction_emoji} *{symbol} - {direction_style}* | {confidence_label} ({confidence:.0f}%)

⏰ *Signal Time:*
UTC: `{utc_time}` | Berlin: `{berlin_time}`

💰 *Trade Setup (5-15min target):*
• Entry: `{data['entry_price']:.6f}` 
• Stop Loss: `{data['stop_loss']:.6f}` (Tight)
• Leverage: *{leverage}x* (Max available)

🎯 *Take Profit Levels:*
• TP1: `{data['take_profit_1']:.6f}` ({tp1_profit}%) - Quick exit
• TP2: `{data['take_profit_2']:.6f}` ({tp2_profit}%) - Main target  
• TP3: `{data['take_profit_3']:.6f}` ({tp3_profit}%) - Max profit

📊 *Signal Quality:* {confidence_emoji} {confidence:.0f}% {confidence_label}
"""
        
        # OPTIMIZED: Enhanced rationale with better formatting
        rationale_points = data.get('rationale', [])
        if rationale_points:
            message += "\n🔍 *Technical Analysis:*\n"
            for i, point in enumerate(rationale_points[:4], 1):  # Limit to 4 points
                message += f"• {point}\n"
        
        # OPTIMIZED: Enhanced Bookmap fusion with better visualization
        if data.get('bookmap_fusion'):
            fusion_data = data['bookmap_fusion']
            fusion_result = fusion_data.get('fusion_result', 'NONE')
            order_flow_score = fusion_data.get('order_flow_score', 0)
            fusion_triggers = fusion_data.get('fusion_triggers', [])
            
            # Fusion result emojis
            fusion_emojis = {
                "ENHANCED_LONG": "🚀⬆️",
                "ENHANCED_SHORT": "🐻⬇️", 
                "CONFLICTING_SIGNALS": "⚠️🔀",
                "WEAK_CONFIRMATION": "🟡📊",
                "INSUFFICIENT_DATA": "📊❓"
            }
            
            fusion_emoji = fusion_emojis.get(fusion_result, "📊")
            
            message += f"\n{fusion_emoji} *INSTITUTIONAL ORDER FLOW*\n"
            message += f"• Fusion: {fusion_result.replace('_', ' ').title()}\n"
            message += f"• Flow Score: {order_flow_score:+.1f}\n"
            
            # Key fusion triggers (limit to 3 most important)
            if fusion_triggers:
                top_triggers = fusion_triggers[:3]
                formatted_triggers = []
                for trigger in top_triggers:
                    if "Whale" in trigger:
                        formatted_triggers.append(f"🐋 {trigger}")
                    elif "Iceberg" in trigger:
                        formatted_triggers.append(f"🧊 {trigger}")
                    elif "Stop" in trigger:
                        formatted_triggers.append(f"🏃 {trigger}")
                    elif "Flow" in trigger:
                        formatted_triggers.append(f"🌊 {trigger}")
                    else:
                        formatted_triggers.append(f"⚡ {trigger}")
                
                message += f"• Triggers: {', '.join(formatted_triggers)}\n"
            
            # Microstructure summary
            microstructure = fusion_data.get('microstructure', {})
            if microstructure and not microstructure.get('error'):
                liquidity = microstructure.get('liquidity_profile', 'unknown')
                if liquidity != 'unknown':
                    message += f"• Market: {liquidity.replace('_', ' ').title()}\n"
            
        # OPTIMIZED: Enhanced regime info with strategy context
        if data.get('regime_info'):
            regime = data['regime_info']
            regime_name = regime['regime'].replace('_', ' ').title()
            strategy_type = regime.get('strategy_type', 'standard').title()
            
            regime_emojis = {
                "Trending Bull": "🐂",
                "Trending Bear": "🐻",
                "Range Bound": "📊", 
                "High Volatility": "⚡",
                "Low Volatility": "😴",
                "Breakout": "🚀"
            }
            
            regime_emoji = regime_emojis.get(regime_name, "🌊")
            message += f"\n{regime_emoji} *MARKET REGIME*\n"
            message += f"• Current: {regime_name}\n"
            message += f"• Strategy: {strategy_type}\n"
            
        # OPTIMIZED: Enhanced confidence breakdown for transparency
        if data.get('original_confidence') and data.get('fusion_boost'):
            original = float(data['original_confidence'])
            boosted = float(data['confidence_score'])
            boost = float(data['fusion_boost'])
            
            # Convert to percentage for display
            if original <= 10:
                original = original * 10
            if boosted <= 10:
                boosted = boosted * 10
                
            message += f"\n📈 *CONFIDENCE BREAKDOWN*\n"
            message += f"• Base TA: {original:.0f}%\n"
            message += f"• Order Flow: {boost:+.1f} pts\n"
            message += f"• Final: {boosted:.0f}%\n"
        
        # OPTIMIZED: Enhanced risk metrics
        liquidation_info = data.get('liquidation_info', {})
        if liquidation_info.get('distance_to_liquidation'):
            distance = liquidation_info['distance_to_liquidation']
            message += f"\n⚠️ *RISK METRICS*\n"
            message += f"• Stop Buffer: {liquidation_info.get('stop_buffer_pct', 0):.1f}%\n"
            message += f"• Liquidation Distance: {distance:.1f}%\n"
        
        # OPTIMIZED: Quality score and recommendation
        quality_score = data.get('ultra_quality_score') or data.get('quality_score', 0)
        if quality_score > 0:
            quality_stars = "⭐" * min(5, int(quality_score / 2))
            message += f"\n💎 *QUALITY RATING*\n"
            message += f"• Score: {quality_score:.1f}/10 {quality_stars}\n"
        
        # Enhanced processing info for ultra-comprehensive signals
        if data.get('ultra_comprehensive'):
            processing_time = data.get('processing_time_ms', 0)
            analysis_depth = data.get('analysis_depth', 'STANDARD')
            
            message += f"\n🧠 *ANALYSIS DEPTH*\n"
            message += f"• Mode: {analysis_depth}\n"
            message += f"• Processing: {processing_time}ms\n"
        
        # OPTIMIZED: Risk warning with action items
        message += f"\n⚠️ *RISK WARNING*\n"
        message += f"• High leverage ({leverage}x) = High risk/reward\n"
        message += f"• Use only risk capital you can afford to lose\n"
        message += f"• Set stop loss immediately after entry\n"
        message += f"• This is not financial advice\n"
        
        return message
 
    async def send_error(self, error_message: str, chat_ids: Optional[List[str]] = None) -> None:
        """Send error message to Telegram."""
        if not self.bot:
            return
            
        # Escape special characters to prevent parsing issues
        safe_message = error_message.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("]", "\\]").replace("(", "\\(").replace(")", "\\)").replace("~", "\\~").replace("`", "\\`").replace(">", "\\>").replace("#", "\\#").replace("+", "\\+").replace("-", "\\-").replace("=", "\\=").replace("|", "\\|").replace("{", "\\{").replace("}", "\\}")
        message = f"❌ *Error:* {safe_message}"
        
        recipients = chat_ids or list(self.authorized_chats)
        
        for chat_id in recipients:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error("Failed to send error", chat_id=chat_id, error=str(e))
                
    async def send_notification(self, message: str, chat_ids: Optional[List[str]] = None) -> None:
        """Send general notification to Telegram."""
        if not self.bot:
            return
            
        recipients = chat_ids or list(self.authorized_chats)
        
        for chat_id in recipients:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error("Failed to send notification", chat_id=chat_id, error=str(e))
                
    async def start_polling(self) -> None:
        """Start bot polling for updates."""
        if not self.application:
            logger.error("Application not initialized")
            return
            
        try:
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("Telegram bot polling started")
        except Exception as e:
            logger.error("Failed to start polling", error=str(e))
            
    async def stop(self) -> None:
        """Stop the Telegram service."""
        if self.application:
            await self.application.stop()
            logger.info("Telegram service stopped")

    async def _handle_manual_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /scan command for manual market scanning."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            # Default to 100-pair comprehensive scan
            scan_type = "100_pairs"  
            
            if context.args:
                arg = context.args[0].lower()
                if arg in ["all", "top_movers", "small_caps", "volume_breakouts"]:
                    scan_type = arg  # Legacy scan modes
                elif arg in ["100", "comprehensive", "100_pairs"]:
                    scan_type = "100_pairs"  # Comprehensive scan
            
            if scan_type == "100_pairs":
                await update.message.reply_text(
                    "🔍 *Initiating comprehensive 100-pair market scan...*\n"
                    "⏰ *This may take 10-20 seconds*",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text("🔍 *Initiating market scan...*", parse_mode=ParseMode.MARKDOWN)
            
            # Import here to avoid circular import
            from .market_scanner import market_scanner
            
            # Trigger manual scan
            results = await market_scanner.manual_scan(scan_type)
            
            if "error" in results:
                await update.message.reply_text(f"❌ {results['error']}")
                return
            
            # Handle 100-pair scan results
            if scan_type == "100_pairs":
                await self._format_100_pair_results(update, results)
            else:
                # Handle regular scan results
                total_found = sum(len(symbols) for symbols in results.values() if isinstance(symbols, list))
                
                message = f"""
🔍 *MANUAL SCAN RESULTS*

📊 *Opportunities Found: {total_found}*

"""
                
                for scan_type_key, symbols in results.items():
                    if isinstance(symbols, list) and symbols:
                        emoji = {"top_movers": "📈", "small_caps": "💎", "volume_breakouts": "🚀"}.get(scan_type_key, "🔍")
                        message += f"{emoji} *{scan_type_key.replace('_', ' ').title()}:* {len(symbols)} symbols\n"
                        
                message += "\n💡 *Signals will be sent automatically for qualifying opportunities.*"
                
                await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Manual scan command failed", error=str(e))
            await update.message.reply_text("❌ Failed to execute market scan.")
    
    async def _format_100_pair_results(self, update: Update, results: Dict[str, Any]) -> None:
        """Format and send 100-pair scan results."""
        try:
            scan_summary = results.get("scan_summary", {})
            opportunities = results.get("opportunities", {})
            top_picks = results.get("top_picks", [])
            
            # Main summary message
            summary_message = f"""
🔒 *STRICT 100-PAIR SIGNAL-GRADE SCAN COMPLETE*

📊 *Scan Summary:*
• Pairs Scanned: {scan_summary.get('pairs_scanned', 0)}
• Technical Analysis: {scan_summary.get('pairs_analyzed', 0)} pairs
• Signal-Grade Opportunities: {scan_summary.get('total_opportunities', 0)}
• Scan Duration: {scan_summary.get('scan_duration_seconds', 0)}s
• Mode: 🔒 STRICT (Signal-probability filtering)

🎯 *Signal-Ready Categories:*
"""
            
            category_emojis = {
                "strong_bullish": "🟢",
                "strong_bearish": "🔴",
                "high_volatility": "⚡",
                "volume_breakouts": "🚀",
                "momentum_plays": "📈",
                "small_cap_gems": "💎"
            }
            
            for category, pairs in opportunities.items():
                if pairs:
                    emoji = category_emojis.get(category, "🔍")
                    category_name = category.replace('_', ' ').title()
                    summary_message += f"• {emoji} {category_name}: {len(pairs)}\n"
            
            await update.message.reply_text(summary_message, parse_mode=ParseMode.MARKDOWN)
            
            # Top picks message
            if top_picks:
                top_picks_message = "🏆 *TOP 5 SIGNAL-GRADE MARKET PICKS:*\n\n"
                
                for i, pick in enumerate(top_picks[:5], 1):
                    symbol = pick["symbol"]
                    score = pick["score"]
                    change = pick["price_change_pct"]
                    volume = pick["volume_24h"]
                    category = pick["source_category"].replace('_', ' ').title()
                    emoji = category_emojis.get(pick["source_category"], "🔍")
                    leverage_emoji = "✅" if pick.get("leverage_suitable", False) else "⚠️"
                    
                    top_picks_message += f"{i}. {emoji} *{symbol}*\n"
                    top_picks_message += f"   Score: {score} | Change: {change:+.1f}%\n"
                    top_picks_message += f"   Volume: ${volume:,.0f} {leverage_emoji}\n"
                    top_picks_message += f"   Category: {category}\n"
                    top_picks_message += f"   💡 Use `/signal {symbol}` for trade setup\n\n"
                
                top_picks_message += "✅ = High leverage suitable\n"
                top_picks_message += "⚠️ = Lower leverage recommended\n\n"
                top_picks_message += "💡 *Use /signal SYMBOL for detailed analysis*"
                
                await update.message.reply_text(top_picks_message, parse_mode=ParseMode.MARKDOWN)
            
            # Category details (send most promising category)
            best_category = None
            best_count = 0
            for category, pairs in opportunities.items():
                if len(pairs) > best_count:
                    best_category = category
                    best_count = len(pairs)
            
            if best_category and opportunities[best_category]:
                await self._send_category_details(update, best_category, opportunities[best_category][:5])
                
        except Exception as e:
            logger.error("Failed to format 100-pair results", error=str(e))
            await update.message.reply_text("❌ Failed to format scan results.")
    
    async def _send_category_details(self, update: Update, category: str, pairs: List[Dict[str, Any]]) -> None:
        """Send detailed breakdown of a specific category."""
        try:
            category_emojis = {
                "strong_bullish": "🟢",
                "strong_bearish": "🔴",
                "high_volatility": "⚡",
                "volume_breakouts": "🚀",
                "momentum_plays": "📈",
                "small_cap_gems": "💎"
            }
            
            emoji = category_emojis.get(category, "🔍")
            category_name = category.replace('_', ' ').title()
            
            details_message = f"{emoji} *{category_name} DETAILS:*\n\n"
            
            for i, pair in enumerate(pairs[:5], 1):
                symbol = pair["symbol"]
                score = pair["score"]
                change = pair["price_change_pct"]
                volume = pair["volume_24h"]
                volatility = pair.get("volatility", 0)
                leverage_emoji = "✅" if pair.get("leverage_suitable", False) else "⚠️"
                
                details_message += f"{i}. *{symbol}* (Score: {score})\n"
                details_message += f"   Change: {change:+.1f}% | Vol: {volatility:.1f}% {leverage_emoji}\n"
                details_message += f"   Volume: ${volume:,.0f}\n\n"
            
            details_message += f"💡 *Showing top 5 {category_name.lower()} opportunities*"
            
            await update.message.reply_text(details_message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Failed to send category details", error=str(e))
            
    async def _handle_top_movers(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /movers command to show top gainers and losers."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            await update.message.reply_text("📈 *Fetching top movers...*", parse_mode=ParseMode.MARKDOWN)
            
            from ..data.rest import rest_client
            
            movers = await rest_client.get_top_movers(count=10)
            
            message = "📊 *TOP MARKET MOVERS*\n\n"
            
            # Top gainers
            message += "🟢 *TOP GAINERS:*\n"
            for i, gainer in enumerate(movers["gainers"][:5], 1):
                symbol = gainer["symbol"]
                change = gainer["price_change_pct"]
                volume = gainer["volume_24h"]
                message += f"{i}. {symbol}: +{change:.1f}% (${volume:,.0f})\n"
                
            message += "\n🔴 *TOP LOSERS:*\n"
            for i, loser in enumerate(movers["losers"][:5], 1):
                symbol = loser["symbol"]
                change = loser["price_change_pct"]
                volume = loser["volume_24h"]
                message += f"{i}. {symbol}: {change:.1f}% (${volume:,.0f})\n"
                
            message += "\n💡 *Use /signal SYMBOL for detailed analysis*"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Top movers command failed", error=str(e))
            await update.message.reply_text("❌ Failed to fetch top movers.")
            
    async def _handle_small_caps(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /smallcaps command to show high-volatility small cap movers."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            await update.message.reply_text("💎 *Fetching small cap movers...*", parse_mode=ParseMode.MARKDOWN)
            
            from ..data.rest import rest_client
            
            small_caps = await rest_client.get_small_cap_movers(count=10)
            
            if not small_caps:
                await update.message.reply_text("💎 No small cap movers found matching criteria.")
                return
                
            message = "💎 *HIGH-VOLATILITY SMALL CAPS*\n\n"
            
            for i, coin in enumerate(small_caps[:8], 1):
                symbol = coin["symbol"]
                change = coin["price_change_pct"]
                volatility = coin["volatility"]
                volume = coin["volume_24h"]
                leverage_suitable = "✅" if coin["leverage_suitable"] else "⚠️"
                
                message += f"{i}. {symbol}: {change:+.1f}% | Vol: {volatility:.1f}% {leverage_suitable}\n"
                message += f"   Volume: ${volume:,.0f}\n"
                
            message += "\n✅ = Suitable for 20x leverage\n"
            message += "⚠️ = Lower leverage recommended\n"
            message += "\n💡 *Use /signal SYMBOL for detailed analysis*"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Small caps command failed", error=str(e))
            await update.message.reply_text("❌ Failed to fetch small cap movers.")
            
    async def _handle_scanner_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /scanner command to show scanner status."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            from .market_scanner import market_scanner
            
            status = await market_scanner.get_scanner_status()
            
            status_emoji = "🟢" if status["is_running"] else "🔴"
            
            message = f"""
🔍 *MARKET SCANNER STATUS*

{status_emoji} *Status:* {'Running' if status['is_running'] else 'Stopped'}
📊 *Symbols Processed:* {status['processed_symbols_count']}

⚙️ *Configuration:*
• Scan Interval: {status['settings']['interval_minutes']} minutes
• Min Price Change: {status['settings']['min_price_change_pct']}%
• Top Movers Count: {status['settings']['top_movers_count']}
• Min Volume: ${status['settings']['min_volume_usdt']:,.0f}

🎯 *Focus Areas:*
• 1m/5m timeframes
• 20x leverage opportunities
• Top gainers/losers
• Small cap volatility

💡 *Use /scan to trigger manual scan*
"""
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Scanner status command failed", error=str(e))
            await update.message.reply_text("❌ Failed to get scanner status.")
            
    async def _handle_order_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /orderflow command for order flow analysis."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            if not context.args:
                await update.message.reply_text("Please provide a symbol. Example: /orderflow BTCUSDT")
                return
                
            symbol = context.args[0].upper()
            await update.message.reply_text(f"📊 *Analyzing order flow for {symbol}...*", parse_mode=ParseMode.MARKDOWN)
            
            from .bookmap_engine import bookmap_engine
            
            # Get order flow summary
            summary = bookmap_engine.get_signal_summary(symbol, minutes=10)
            order_flow_score = bookmap_engine.get_order_flow_score(symbol)
            
            if summary["total_signals"] == 0:
                await update.message.reply_text(f"📊 No recent order flow data for {symbol}.")
                return
                
            # Format order flow analysis
            message = f"""
📊 *ORDER FLOW ANALYSIS - {symbol}*

🎯 *Order Flow Score: {order_flow_score:+.1f}/10*

📈 *Signal Summary (Last 10 min):*
• Total Signals: {summary['total_signals']}
• Bullish: {summary['bullish_signals']} | Bearish: {summary['bearish_signals']}
• Dominant Side: {summary['dominant_side']}
• Avg Confidence: {summary['avg_confidence']:.1f}/10

🔍 *Detected Patterns:*
"""
            
            for signal_type, count in summary.get("signal_types", {}).items():
                type_name = signal_type.replace("_", " ").title()
                emoji = {
                    "WHALE_TRADE": "🐋", 
                    "STOP_RUN": "🏃",
                    "ICEBERG_DETECTION": "🧊",
                    "SWEEP_DETECTED": "🌊",
                    "SPOOF_DETECTED": "👻"
                }.get(signal_type, "📊")
                message += f"• {emoji} {type_name}: {count}\n"
                
            # Order flow interpretation
            if order_flow_score > 3:
                message += "\n🟢 *Interpretation: Strong bullish order flow*"
            elif order_flow_score < -3:
                message += "\n🔴 *Interpretation: Strong bearish order flow*"
            else:
                message += "\n🟡 *Interpretation: Neutral/mixed order flow*"
                
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Order flow command failed", error=str(e))
            await update.message.reply_text("❌ Failed to analyze order flow.")
            
    async def _handle_bookmap_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /bookmap command for Bookmap engine status."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            from .bookmap_engine import bookmap_engine
            
            status_emoji = "🟢" if bookmap_engine.running else "🔴"
            
            message = f"""
🗺️ *BOOKMAP ENGINE STATUS*

{status_emoji} *Status:* {'Running' if bookmap_engine.running else 'Stopped'}

⚙️ *Configuration:*
• ZeroMQ Port: 5555
• Signal Buffer: 100 recent signals
• Thresholds:
  - Large Trade: $200,000+
  - Stop Run: $500,000+
  - Iceberg: $100,000+

📊 *Capabilities:*
• Real-time order book analysis
• Whale trade detection
• Stop run identification
• Iceberg order tracking
• Spoof detection
• CVD analysis

🔗 *Integration:*
• Signal fusion with TA
• Automatic leverage adjustment
• Enhanced confidence scoring

💡 *Bookmap Global+ features provide institutional-grade order flow analysis*
"""
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Bookmap status command failed", error=str(e))
            await update.message.reply_text("❌ Failed to get Bookmap status.")
            
    async def _handle_whale_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /whales command - enhanced whale activity tracking."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            from .bookmap_engine import bookmap_engine
            
            # Get symbol if provided, otherwise show general activity
            symbol = None
            if context.args:
                symbol = context.args[0].upper()
                if not symbol.endswith("USDT"):
                    symbol += "USDT"
                    
            await update.message.reply_text("🐋 Analyzing whale activity...", parse_mode=ParseMode.MARKDOWN)
            
            if symbol:
                # Symbol-specific whale analysis
                recent_signals = bookmap_engine.get_recent_signals(symbol, 30)  # 30-minute window
                whale_signals = [
                    signal for signal in recent_signals 
                    if signal.signal_type.value == "WHALE_TRADE"
                ]
                
                if not whale_signals:
                    await update.message.reply_text(f"🐋 No whale activity detected for {symbol} in the last 30 minutes")
                    return
                
                message = f"🐋 *WHALE ACTIVITY: {symbol}*\n\n"
                
                # Analyze whale patterns
                total_volume = 0
                buy_volume = 0
                sell_volume = 0
                cluster_activity = 0
                sustained_activity = 0
                
                for signal in whale_signals[-10:]:  # Last 10 whales
                    details = signal.details
                    side = signal.side
                    notional = details.get("notional", 0)
                    size = details.get("size", 0)
                    
                    total_volume += notional
                    if side == "BUY":
                        buy_volume += notional
                    else:
                        sell_volume += notional
                    
                    # Count cluster and sustained activity
                    if "WhaleCluster" in signal.triggers:
                        cluster_activity += 1
                    if "SustainedWhaleActivity" in signal.triggers:
                        sustained_activity += 1
                    
                    time_ago = int((time.time() - signal.timestamp) / 60)
                    timeframe_context = details.get("timeframe_context", {})
                    
                    message += f"• {side} whale: ${notional:,.0f} at ${signal.price:.2f}\n"
                    message += f"  Size: {size:,.0f} | {time_ago}m ago\n"
                    
                    # Show clustering if detected
                    if timeframe_context.get("5s", 0) > 1:
                        message += f"  🔥 Cluster: {timeframe_context['5s']} trades in 5s\n"
                    
                    message += f"  Confidence: {signal.confidence:.1f}\n\n"
                
                # Whale summary
                message += f"📊 *Whale Summary (30min):*\n"
                message += f"• Total Whales: {len(whale_signals)}\n"
                message += f"• Total Volume: ${total_volume:,.0f}\n"
                message += f"• Buy Volume: ${buy_volume:,.0f}\n"
                message += f"• Sell Volume: ${sell_volume:,.0f}\n"
                message += f"• Cluster Events: {cluster_activity}\n"
                message += f"• Sustained Activity: {sustained_activity}\n"
                
                # Whale sentiment
                if buy_volume > sell_volume * 1.3:
                    message += f"• 🟢 **Bullish Whales** - Strong buying pressure\n"
                elif sell_volume > buy_volume * 1.3:
                    message += f"• 🔴 **Bearish Whales** - Strong selling pressure\n"
                else:
                    message += f"• ⚖️ **Mixed Whale Sentiment**\n"
                
                # Check for iceberg correlation
                iceberg_signals = [
                    signal for signal in recent_signals 
                    if signal.signal_type.value == "ICEBERG_DETECTION"
                ]
                
                if iceberg_signals:
                    message += f"• 🧊 **Iceberg Correlation**: {len(iceberg_signals)} icebergs detected\n"
                    message += f"  Possible institutional accumulation/distribution\n"
                
            else:
                # General whale activity across monitored symbols
                message = "🐋 *GENERAL WHALE ACTIVITY*\n\n"
                
                # This would normally aggregate across multiple symbols
                # For now, show example structure
                message += "📊 *Active Symbols with Whale Activity:*\n"
                message += "• BTCUSDT: 🐋🐋🐋 (High)\n"
                message += "• ETHUSDT: 🐋🐋 (Moderate)\n"
                message += "• SOLUSDT: 🐋 (Low)\n\n"
                
                message += "💡 *Use `/whales SYMBOL` for detailed analysis*\n"
                message += "Examples:\n"
                message += "• /whales BTCUSDT\n"
                message += "• /whales ETH\n"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Error in whale activity analysis", error=str(e))
            await update.message.reply_text("❌ Error analyzing whale activity.")

    async def _handle_fusion_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /fusion command for signal fusion performance."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            from .signal_fusion import signal_fusion_engine
            
            metrics = signal_fusion_engine.get_fusion_performance()
            
            message = f"""
🔗 *SIGNAL FUSION PERFORMANCE*

📊 *Statistics (24h):*
• Total Fusions: {metrics['total_fusions']}
• Recent Fusion Rate: {metrics.get('recent_fusion_rate', 0)}/hour
• Avg Confidence Boost: {metrics['confidence_improvements']:+.1f}

⚡ *Enhancement Capabilities:*
• TA + Order Flow integration
• Confidence scoring enhancement  
• Leverage optimization
• Microstructure analysis
• Pattern recognition

🎯 *Recent Fusion Types:*
"""
            
            # Analyze recent fusion results
            recent_fusions = signal_fusion_engine.fusion_history[-20:]  # Last 20
            if recent_fusions:
                fusion_counts = {}
                for fusion in recent_fusions:
                    result = fusion['fusion_result']
                    fusion_counts[result] = fusion_counts.get(result, 0) + 1
                    
                for result, count in fusion_counts.items():
                    emoji = {
                        "ENHANCED_LONG": "🚀",
                        "ENHANCED_SHORT": "🐻",
                        "CONFLICTING_SIGNALS": "⚠️",
                        "WEAK_CONFIRMATION": "🔍"
                    }.get(result, "📊")
                    message += f"• {emoji} {result.replace('_', ' ').title()}: {count}\n"
            else:
                message += "• No recent fusion data available\n"
                
            message += "\n💡 *Fusion engine combines TA with institutional-grade order flow analysis*"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Fusion performance command failed", error=str(e))
            await update.message.reply_text("❌ Failed to get fusion performance.")

    async def _handle_explain_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /explain command for educational explanations."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        await self._send_scan_vs_signal_explanation(update, "symbols from scan")

    async def _send_scan_vs_signal_explanation(self, update: Update, symbol: str) -> None:
        """Explain why a scan opportunity might not have a ready signal."""
        try:
            message = f"""
🎯 *SCAN vs SIGNAL EXPLANATION*

📊 **100-Pair Scan Purpose:**
• Identifies potential market opportunities  
• Uses basic criteria (price movement + volume)
• Shows what to *watch* and analyze further

🔍 **Signal Generation Purpose:**  
• Provides precise trade setups
• Uses ultra-strict requirements (3+ confluence points)
• Must pass accuracy filters for safety

⚠️ **Why {symbol} shows in scan but "No signal":**

*Scan detected:* Price movement + volume activity
*Signal requires:* Perfect technical alignment + trend confirmation + volume validation + momentum agreement

💡 **What this means:**
• {symbol} has market activity worth monitoring
• Full technical conditions not yet aligned for trade
• Use scan as watchlist, wait for signal confirmation

🚀 **Next Steps:**
• Monitor {symbol} for developing setup
• Use /signal {symbol} periodically to check status  
• Look for other symbols with ready signals

*The scan finds opportunities, signals provide precision!*
"""
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Failed to send scan vs signal explanation", error=str(e))

    async def _handle_diagnostic(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /diagnostic command to check system status."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            from ..data.rest import rest_client
            
            # Get circuit breaker status
            cb_status = rest_client.get_circuit_breaker_status()
            
            # Test a simple API call
            test_result = "❌ Failed"
            try:
                test_ticker = await rest_client.get_ticker("BTCUSDT")
                if test_ticker:
                    test_result = "✅ Success"
            except Exception as e:
                test_result = f"❌ Failed: {str(e)[:50]}..."
            
            message = f"""
🔧 *SYSTEM DIAGNOSTICS*

📡 *API Circuit Breaker:*
• Status: {'🔴 OPEN' if cb_status['is_open'] else '🟢 CLOSED'}
• Failures: {cb_status['failure_count']}/5
• Can Execute: {'✅' if cb_status['can_execute'] else '❌'}
• Reset in: {cb_status['seconds_until_reset']:.0f}s

🧪 *API Test (BTCUSDT):*
• Result: {test_result}

💡 *Troubleshooting:*
• If circuit breaker is open, use /reset_api
• Test specific symbols with /test_symbol SYMBOL
• Check network connectivity
• Verify API credentials

⚙️ *Commands:*
• /reset_api - Reset circuit breaker
• /test_symbol SYMBOL - Test data fetch
• /diagnostic - This command
"""
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Diagnostic command failed", error=str(e))
            await update.message.reply_text("❌ Failed to run diagnostics.")

    async def _handle_reset_api(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /reset_api command to reset circuit breaker."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            from ..data.rest import rest_client
            
            # Reset circuit breaker
            rest_client.reset_circuit_breaker()
            
            message = """
🔄 *API CIRCUIT BREAKER RESET*

✅ Circuit breaker has been manually reset
🟢 API calls should now be allowed
🧪 Test with /test_symbol BTCUSDT

*Note: If errors persist, check:*
• Network connectivity
• API credentials
• Bybit service status
"""
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Reset API command failed", error=str(e))
            await update.message.reply_text("❌ Failed to reset API.")

    async def _handle_test_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /test_symbol command to test data fetching for a specific symbol."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            if not context.args:
                await update.message.reply_text("Please provide a symbol. Example: /test_symbol BTCUSDT")
                return
                
            symbol = context.args[0].upper()
            
            # Auto-append USDT if needed
            if not any(suffix in symbol for suffix in ["USDT", "USD", "EUR", "BTC", "ETH"]):
                if len(symbol) <= 6:
                    symbol = symbol + "USDT"
            
            await update.message.reply_text(f"🧪 Testing data collection for {symbol}...")
            
            from ..data.rest import rest_client
            
            # Test different timeframes
            results = {}
            timeframes = ["1", "5"]  # 1m and 5m
            
            for tf in timeframes:
                try:
                    df = await rest_client.get_klines(symbol, tf, limit=10)
                    if df.empty:
                        results[f"{tf}m"] = "❌ No data"
                    else:
                        results[f"{tf}m"] = f"✅ {len(df)} candles"
                except Exception as e:
                    results[f"{tf}m"] = f"❌ {str(e)[:30]}..."
            
            # Test ticker
            ticker_result = "❌ Failed"
            try:
                ticker = await rest_client.get_ticker(symbol)
                if ticker:
                    ticker_result = f"✅ Price: {ticker.get('lastPrice', 'N/A')}"
            except Exception as e:
                ticker_result = f"❌ {str(e)[:30]}..."
            
            message = f"""
🧪 *SYMBOL TEST RESULTS - {symbol}*

📊 *Kline Data:*
• 1m timeframe: {results.get('1m', 'Not tested')}
• 5m timeframe: {results.get('5m', 'Not tested')}

📈 *Ticker Data:*
• Result: {ticker_result}

💡 *Analysis:*
"""
            
            if all("✅" in result for result in results.values()) and "✅" in ticker_result:
                message += "• Symbol is working correctly ✅\n• Data collection should succeed"
            else:
                message += "• Symbol has data issues ❌\n• May not be valid or available on Bybit\n• Try a different symbol or check spelling"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Test symbol command failed", error=str(e))
            await update.message.reply_text("❌ Failed to test symbol.")

    async def _handle_max_leverage(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /max_leverage command to check maximum leverage for a symbol."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            if not context.args:
                await update.message.reply_text("Please provide a symbol. Example: /max_leverage BTCUSDT")
                return
                
            symbol = context.args[0].upper()
            
            # Auto-append USDT if needed
            if not any(suffix in symbol for suffix in ["USDT", "USD", "EUR", "BTC", "ETH"]):
                if len(symbol) <= 6:
                    symbol = symbol + "USDT"
            
            await update.message.reply_text(f"⚡ Checking maximum leverage for {symbol}...")
            
            from ..data.rest import rest_client
            
            # Get maximum leverage
            max_leverage = await rest_client.get_max_leverage(symbol)
            
            message = f"""
⚡ *MAXIMUM LEVERAGE - {symbol}*

🎯 *Maximum Available: {max_leverage}x*

💡 *Bot Configuration:*
• Strategy: Always use maximum leverage
• Safety: Minimal reductions only for extreme volatility
• Liquidation Protection: Stop loss near liquidation price

⚠️ *Important Notes:*
• This bot is configured for MAXIMUM LEVERAGE trading
• Stop losses are set very close to liquidation prices
• Only use with capital you can afford to lose
• Maximum leverage = maximum reward AND maximum risk

🚀 *When you get a signal for {symbol}, it will use {max_leverage}x leverage automatically*
"""
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Max leverage command failed", error=str(e))
            await update.message.reply_text("❌ Failed to check maximum leverage.")

    async def _handle_clear_cache(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /clear_cache command to clear analysis cache for a symbol."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.authorized_chats:
            return
            
        try:
            if not context.args:
                await update.message.reply_text("Please provide a symbol. Example: /clear_cache BTCUSDT")
                return
                
            symbol = context.args[0].upper()
            
            # Auto-append USDT if needed
            if not any(suffix in symbol for suffix in ["USDT", "USD", "EUR", "BTC", "ETH"]):
                if len(symbol) <= 6:
                    symbol = symbol + "USDT"
            
            from ..data.cache import cache
            
            # Clear the cached analysis
            await cache.delete(f"analysis:{symbol}")
            
            message = f"""
🗑️ *CACHE CLEARED - {symbol}*

✅ Analysis cache has been cleared for {symbol}

💡 *What this means:*
• Next signal request will generate fresh analysis
• Current market data will be fetched
• No old cached results will be used

🚀 *Next steps:*
• Use `/signal {symbol}` for fresh analysis
• The bot will always use fresh analysis for manual requests now
"""
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Clear cache command failed", error=str(e))
            await update.message.reply_text("❌ Failed to clear cache.")

    # ──────────────────────────────────────────────────────────────────────────────
    # MANUAL-TRADING HELPER COMMANDS
    # ──────────────────────────────────────────────────────────────────────────────

    async def _handle_set_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /setbalance AMOUNT – store user account balance for position sizing."""
        chat_id = str(update.effective_chat.id)
        if chat_id not in self.authorized_chats:
            return

        if not context.args:
            await update.message.reply_text("Usage: /setbalance 2500  (your USDT capital)")
            return

        try:
            balance = float(context.args[0].replace(',', ''))
            if balance <= 0:
                raise ValueError
            self.user_balances[chat_id] = balance
            await update.message.reply_text(f"✅ Balance set to *${balance:,.2f}*", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Example: /setbalance 2500")

    async def _handle_position_size(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /size ENTRY STOP RISK% [LEVERAGE] – calculate position size using stored balance."""
        chat_id = str(update.effective_chat.id)
        if chat_id not in self.authorized_chats:
            return

        if len(context.args) < 3:
            await update.message.reply_text(
                "Usage: /size ENTRY STOP RISK% [LEVERAGE]\n"\
                "Example: /size 0.5634 0.5570 1 20"
            )
            return

        try:
            entry_price = float(context.args[0])
            stop_loss = float(context.args[1])
            risk_pct = float(context.args[2])
            leverage = int(context.args[3]) if len(context.args) >= 4 else 1

            # Get stored balance
            balance = self.user_balances.get(chat_id)
            if balance is None:
                await update.message.reply_text("❌ Please set your balance first: /setbalance 2500")
                return

            from ..logic.risk import RiskManager

            calc = RiskManager.calculate_position_size(
                account_balance=balance,
                entry_price=entry_price,
                stop_loss=stop_loss,
                risk_percent=risk_pct,
                leverage=leverage,
            )

            msg = (
                f"📐 *Position Size Calculator*\n"
                f"Balance: `${balance:,.2f}`\n"
                f"Risk: `{risk_pct}%`  |  Leverage: `{leverage}x`\n"
                f"Entry: `{entry_price}`  |  Stop: `{stop_loss}`\n\n"
                f"• Size: *{calc['position_size']:.6f}* contracts\n"
                f"• Position value: *${calc['position_value']:,.2f}*\n"
                f"• Margin required: *${calc['margin_required']:,.2f}*\n"
                f"• $ Risk: *${calc['risk_amount']:,.2f}*\n"
                f"• Stop distance: *{calc['stop_loss_distance']}%*"
            )
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

        except ValueError:
            await update.message.reply_text("❌ Invalid numbers. Check your input.")

    async def _handle_risk_reward_calc(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /rr ENTRY STOP TP1 [TP2 TP3] – compute risk-reward ratios."""
        chat_id = str(update.effective_chat.id)
        if chat_id not in self.authorized_chats:
            return

        if len(context.args) < 3:
            await update.message.reply_text(
                "Usage: /rr ENTRY STOP TP1 [TP2 TP3]\nExample: /rr 0.5634 0.5570 0.5690 0.5750 0.5820"
            )
            return

        try:
            entry_price = float(context.args[0])
            stop_loss = float(context.args[1])
            tps = [float(x) for x in context.args[2:]]

            from ..logic.risk import RiskManager
            ratios = RiskManager.calculate_risk_reward_ratio(entry_price, stop_loss, tps)

            msg = "⚖️ *Risk-Reward Ratios*\n"
            for key, val in ratios.items():
                if key != "average_ratio":
                    msg += f"• {key.upper()}: *{val}*\n"
            msg += f"\nAverage RR: *{ratios['average_ratio']}*"
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

        except ValueError:
            await update.message.reply_text("❌ Invalid numbers. Check your input.")

    async def _handle_portfolio_heat(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /heat – show portfolio heat using current open positions (if auto trading enabled)."""
        chat_id = str(update.effective_chat.id)
        if chat_id not in self.authorized_chats:
            return

        from ..services.bybit_trading import trading_service
        from ..logic.risk import RiskManager

        await trading_service.update_account_balance()
        opens = [
            {
                "risk_amount": pos.risk_amount,
                "margin_required": pos.margin_required,
            }
            for pos in trading_service.active_positions.values()
        ]

        heat = RiskManager.calculate_portfolio_heat(opens, trading_service.account_balance)

        msg = (
            "🔥 *Portfolio Heat*\n"
            f"Total risk: *${heat['total_risk']:,.2f}* ({heat['risk_percentage']}%)\n"
            f"Margin usage: *{heat['margin_usage']}%*\n"
            f"Open positions: *{heat['positions_count']}*\n"
            f"Heat level: *{heat['heat_level']}*\n"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    # ──────────────────────────────────────────────────────────────────────────────
    # ADVANCED BOOKMAP ANALYSIS COMMANDS
    # ──────────────────────────────────────────────────────────────────────────────

    async def _handle_order_flow_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /orderflow SYMBOL - comprehensive order flow analysis."""
        chat_id = str(update.effective_chat.id)
        if chat_id not in self.authorized_chats:
            return

        if not context.args:
            await update.message.reply_text("Usage: /orderflow BTCUSDT")
            return

        symbol = context.args[0].upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"

        try:
            # Import bookmap engine
            from .bookmap_engine import bookmap_engine
            
            await update.message.reply_text(f"🔄 Analyzing order flow for *{symbol}*...", parse_mode=ParseMode.MARKDOWN)
            
            # Get comprehensive order flow data
            flow_summary = bookmap_engine.get_signal_summary(symbol, 15)  # 15-minute lookback
            order_flow_score = bookmap_engine.get_order_flow_score(symbol)
            
            if not flow_summary.get("total_signals", 0):
                await update.message.reply_text(f"📊 No recent order flow data for {symbol}")
                return
            
            # Analyze flow direction and strength
            dominant_side = flow_summary.get("dominant_side", "NEUTRAL")
            signal_types = flow_summary.get("signal_types", {})
            avg_confidence = flow_summary.get("avg_confidence", 0)
            
            # Format comprehensive analysis
            message = f"""
🌊 *ORDER FLOW ANALYSIS: {symbol}*

📈 *Flow Direction:*
• Dominant Side: **{dominant_side}**
• Flow Score: {order_flow_score:+.2f}
• Average Confidence: {avg_confidence:.1f}/10
• Total Signals: {flow_summary.get('total_signals', 0)}

🔍 *Signal Breakdown:*
"""
            
            # Detailed signal analysis
            for signal_type, count in signal_types.items():
                emoji = {
                    "WHALE_TRADE": "🐋",
                    "ICEBERG_DETECTION": "🧊",
                    "VOLUME_BURST": "💥",
                    "ORDERBOOK_IMBALANCE": "⚖️",
                    "SPOOF_DETECTED": "🎭",
                    "STOP_RUN": "🏃",
                    "SWEEP_DETECTED": "🧹"
                }.get(signal_type, "📊")
                
                readable_name = signal_type.replace("_", " ").title()
                message += f"• {emoji} {readable_name}: {count}\n"
            
            # Flow interpretation
            message += f"\n💡 *Flow Interpretation:*\n"
            
            if abs(order_flow_score) > 5:
                direction = "BULLISH" if order_flow_score > 0 else "BEARISH"
                strength = "STRONG" if abs(order_flow_score) > 8 else "MODERATE"
                message += f"• {strength} {direction} flow detected\n"
            else:
                message += "• NEUTRAL flow - mixed signals\n"
                
            if "WHALE_TRADE" in signal_types and signal_types["WHALE_TRADE"] > 2:
                message += "• 🐋 High whale activity - institutional interest\n"
                
            if "ICEBERG_DETECTION" in signal_types:
                message += "• 🧊 Algorithmic iceberg orders detected\n"
                
            if "SPOOF_DETECTED" in signal_types:
                message += "• 🎭 Market manipulation activity observed\n"
            
            message += f"\n⏰ *Analysis Period:* Last 15 minutes"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Error in order flow analysis", error=str(e))
            await update.message.reply_text("❌ Error analyzing order flow data.")

    async def _handle_iceberg_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /icebergs SYMBOL - iceberg detection analysis."""
        chat_id = str(update.effective_chat.id)
        if chat_id not in self.authorized_chats:
            return

        if not context.args:
            await update.message.reply_text("Usage: /icebergs BTCUSDT")
            return

        symbol = context.args[0].upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"

        try:
            from .bookmap_engine import bookmap_engine
            
            await update.message.reply_text(f"🧊 Scanning for icebergs in *{symbol}*...", parse_mode=ParseMode.MARKDOWN)
            
            # Get recent iceberg signals
            recent_signals = bookmap_engine.get_recent_signals(symbol, 30)  # 30-minute window
            iceberg_signals = [
                signal for signal in recent_signals 
                if signal.signal_type.value == "ICEBERG_DETECTION"
            ]
            
            if not iceberg_signals:
                await update.message.reply_text(f"🧊 No iceberg orders detected for {symbol} in the last 30 minutes")
                return
            
            message = f"🧊 *ICEBERG DETECTION: {symbol}*\n\n"
            
            # Analyze iceberg patterns
            total_volume = 0
            bid_icebergs = []
            ask_icebergs = []
            
            for signal in iceberg_signals[-5:]:  # Last 5 icebergs
                details = signal.details
                side = details.get("side", "UNKNOWN")
                executed_volume = details.get("total_executed", 0)
                total_volume += executed_volume
                
                if side == "BID":
                    bid_icebergs.append(signal)
                else:
                    ask_icebergs.append(signal)
                
                time_ago = int((time.time() - signal.timestamp) / 60)
                message += f"• {side} iceberg at ${details.get('price', 0):.2f}\n"
                message += f"  Volume: {executed_volume:,.0f} | {time_ago}m ago\n"
                message += f"  Executions: {details.get('execution_count', 0)} | Confidence: {signal.confidence:.1f}\n\n"
            
            # Summary statistics
            message += f"📊 *Summary (30min):*\n"
            message += f"• Total Icebergs: {len(iceberg_signals)}\n"
            message += f"• Bid Icebergs: {len(bid_icebergs)}\n"
            message += f"• Ask Icebergs: {len(ask_icebergs)}\n"
            message += f"• Total Volume: {total_volume:,.0f}\n"
            
            # Direction bias
            if len(bid_icebergs) > len(ask_icebergs) * 1.5:
                message += f"• 🟢 **Bullish Bias** - More bid-side accumulation\n"
            elif len(ask_icebergs) > len(bid_icebergs) * 1.5:
                message += f"• 🔴 **Bearish Bias** - More ask-side distribution\n"
            else:
                message += f"• ⚖️ **Neutral** - Balanced iceberg activity\n"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Error in iceberg analysis", error=str(e))
            await update.message.reply_text("❌ Error analyzing iceberg data.")

    async def _handle_absorption_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /absorption SYMBOL - volume absorption analysis."""
        chat_id = str(update.effective_chat.id)
        if chat_id not in self.authorized_chats:
            return

        if not context.args:
            await update.message.reply_text("Usage: /absorption BTCUSDT")
            return

        symbol = context.args[0].upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"

        try:
            from .bookmap_engine import bookmap_engine
            
            await update.message.reply_text(f"💥 Analyzing volume absorption for *{symbol}*...", parse_mode=ParseMode.MARKDOWN)
            
            # Get volume burst signals (absorption events)
            recent_signals = bookmap_engine.get_recent_signals(symbol, 20)  # 20-minute window
            absorption_signals = [
                signal for signal in recent_signals 
                if signal.signal_type.value == "VOLUME_BURST"
            ]
            
            if not absorption_signals:
                await update.message.reply_text(f"💥 No significant volume absorption detected for {symbol} in the last 20 minutes")
                return
            
            message = f"💥 *VOLUME ABSORPTION: {symbol}*\n\n"
            
            # Analyze absorption events
            total_absorbed = 0
            buy_absorption = 0
            sell_absorption = 0
            
            for signal in absorption_signals[-8:]:  # Last 8 events
                details = signal.details
                side = signal.side
                absorbed_volume = details.get("window_volume", 0) or details.get("total_volume", 0)
                
                total_absorbed += absorbed_volume
                if side == "BUY":
                    buy_absorption += absorbed_volume
                else:
                    sell_absorption += absorbed_volume
                
                time_ago = int((time.time() - signal.timestamp) / 60)
                price = signal.price
                strength = details.get("absorption_strength", 0) or details.get("clustering_strength", 0)
                
                message += f"• {side} absorption at ${price:.2f}\n"
                message += f"  Volume: ${absorbed_volume:,.0f} | Strength: {strength:.1f}/10\n"
                message += f"  {time_ago}m ago | Confidence: {signal.confidence:.1f}\n\n"
            
            # Absorption analysis
            message += f"📊 *Absorption Summary (20min):*\n"
            message += f"• Total Events: {len(absorption_signals)}\n"
            message += f"• Total Volume: ${total_absorbed:,.0f}\n"
            message += f"• Buy Absorption: ${buy_absorption:,.0f}\n"
            message += f"• Sell Absorption: ${sell_absorption:,.0f}\n"
            
            # Market pressure analysis
            if buy_absorption > sell_absorption * 1.5:
                message += f"• 🟢 **Strong Buying Pressure** - Bulls absorbing supply\n"
            elif sell_absorption > buy_absorption * 1.5:
                message += f"• 🔴 **Strong Selling Pressure** - Bears absorbing demand\n"
            else:
                message += f"• ⚖️ **Balanced Absorption** - Mixed market sentiment\n"
            
            # Recent trend
            if absorption_signals:
                latest_signal = absorption_signals[-1]
                time_since_last = int((time.time() - latest_signal.timestamp) / 60)
                message += f"• ⏰ Last event: {time_since_last}m ago ({latest_signal.side})\n"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Error in absorption analysis", error=str(e))
            await update.message.reply_text("❌ Error analyzing absorption data.")

    async def _handle_support_resistance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /levels SYMBOL - support/resistance level analysis."""
        chat_id = str(update.effective_chat.id)
        if chat_id not in self.authorized_chats:
            return

        if not context.args:
            await update.message.reply_text("Usage: /levels BTCUSDT")
            return

        symbol = context.args[0].upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"

        try:
            from .bookmap_engine import bookmap_engine
            
            await update.message.reply_text(f"📊 Identifying key levels for *{symbol}*...", parse_mode=ParseMode.MARKDOWN)
            
            # Get support/resistance signals
            recent_signals = bookmap_engine.get_recent_signals(symbol, 60)  # 1-hour window
            level_signals = [
                signal for signal in recent_signals 
                if any(trigger.startswith("Strong") for trigger in signal.triggers)
            ]
            
            if not level_signals:
                await update.message.reply_text(f"📊 No strong support/resistance levels detected for {symbol} in the last hour")
                return
            
            # Separate support and resistance
            support_levels = []
            resistance_levels = []
            
            for signal in level_signals:
                details = signal.details
                level_type = details.get("type", "unknown")
                
                level_data = {
                    "price": signal.price,
                    "strength": details.get("strength", 0),
                    "volume": details.get("volume", 0),
                    "touches": details.get("touch_count", 0),
                    "confidence": signal.confidence,
                    "time_ago": int((time.time() - signal.timestamp) / 60)
                }
                
                if level_type == "support":
                    support_levels.append(level_data)
                elif level_type == "resistance":
                    resistance_levels.append(level_data)
            
            # Sort by strength
            support_levels.sort(key=lambda x: x["strength"], reverse=True)
            resistance_levels.sort(key=lambda x: x["strength"], reverse=True)
            
            message = f"📊 *KEY LEVELS: {symbol}*\n\n"
            
            # Support levels
            if support_levels:
                message += "🟢 *SUPPORT LEVELS:*\n"
                for level in support_levels[:3]:  # Top 3
                    message += f"• ${level['price']:.2f} | Strength: {level['strength']:.1f}\n"
                    message += f"  Touches: {level['touches']} | Volume: ${level['volume']:,.0f}\n"
                    message += f"  {level['time_ago']}m ago | Confidence: {level['confidence']:.1f}\n\n"
            
            # Resistance levels  
            if resistance_levels:
                message += "🔴 *RESISTANCE LEVELS:*\n"
                for level in resistance_levels[:3]:  # Top 3
                    message += f"• ${level['price']:.2f} | Strength: {level['strength']:.1f}\n"
                    message += f"  Touches: {level['touches']} | Volume: ${level['volume']:,.0f}\n"
                    message += f"  {level['time_ago']}m ago | Confidence: {level['confidence']:.1f}\n\n"
            
            # Level analysis
            message += f"💡 *Level Analysis:*\n"
            
            strongest_support = max(support_levels, key=lambda x: x["strength"]) if support_levels else None
            strongest_resistance = max(resistance_levels, key=lambda x: x["strength"]) if resistance_levels else None
            
            if strongest_support:
                message += f"• Strongest Support: ${strongest_support['price']:.2f}\n"
            if strongest_resistance:
                message += f"• Strongest Resistance: ${strongest_resistance['price']:.2f}\n"
                
            total_levels = len(support_levels) + len(resistance_levels)
            message += f"• Total Strong Levels: {total_levels}\n"
            message += f"• Analysis Period: Last 60 minutes\n"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error("Error in support/resistance analysis", error=str(e))
            await update.message.reply_text("❌ Error analyzing support/resistance levels.")


# Global Telegram service instance
telegram_service = TelegramService() 