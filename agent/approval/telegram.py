"""
Telegram Approval Bot

Handles trade approval requests via Telegram.
"""

import asyncio
from typing import Optional, Callable
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from ..config import get_config
from ..db import get_session, ApprovalRepository, Approval


class TelegramApprovalBot:
    """Telegram bot for trade approvals."""
    
    def __init__(self, on_approval: Optional[Callable] = None):
        """
        Initialize the Telegram bot.
        
        Args:
            on_approval: Callback function when approval is received
        """
        cfg = get_config()
        self.token = cfg.telegram_bot_token
        self.chat_id = cfg.telegram_chat_id
        self.on_approval = on_approval
        self.app: Optional[Application] = None
        self._pending_approvals: dict[str, int] = {}  # message_id -> approval_id
    
    async def start(self):
        """Start the Telegram bot."""
        if not self.token:
            print("[TELEGRAM] No bot token configured, skipping...")
            return
        
        self.app = Application.builder().token(self.token).build()
        
        # Add handlers
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("status", self._handle_status))
        self.app.add_handler(CommandHandler("positions", self._handle_positions))
        self.app.add_handler(CommandHandler("panic", self._handle_panic))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Start polling
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        print(f"[TELEGRAM] Bot started!")
    
    async def stop(self):
        """Stop the Telegram bot."""
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
    
    async def request_approval(
        self,
        approval_id: int,
        coin: str,
        direction: str,
        size_usd: float,
        entry_price: float,
        sl_pct: float,
        tp_pct: float,
        leverage: int,
        reasoning: str
    ) -> Optional[str]:
        """
        Send approval request to Telegram.
        
        Returns message_id if sent successfully.
        """
        if not self.app or not self.chat_id:
            return None
        
        message = f"""🔔 **Trade Approval Required**

**{coin} {direction}**
Entry: ~${entry_price:,.2f}
Size: ${size_usd:,.2f}
Leverage: {leverage}x

Stop Loss: -{sl_pct*100:.1f}%
Take Profit: +{tp_pct*100:.1f}%

**Reasoning:**
{reasoning[:300]}{"..." if len(reasoning) > 300 else ""}
"""
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{approval_id}"),
                InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{approval_id}")
            ]
        ])
        
        try:
            sent = await self.app.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
            self._pending_approvals[str(sent.message_id)] = approval_id
            return str(sent.message_id)
            
        except Exception as e:
            print(f"[TELEGRAM] Failed to send: {e}")
            return None
    
    async def send_notification(self, message: str):
        """Send a simple notification."""
        if not self.app or not self.chat_id:
            return
        
        try:
            await self.app.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"[TELEGRAM] Failed to send notification: {e}")
    
    # Handler methods
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        await update.message.reply_text(
            "🤖 **Hyperliquid Trading Agent**\n\n"
            "I'll send you trade approval requests.\n\n"
            "Commands:\n"
            "/status - Agent status\n"
            "/positions - Open positions\n"
            "/panic - Emergency close all",
            parse_mode="Markdown"
        )
    
    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        pending = len([a for a in self._pending_approvals.values()])
        await update.message.reply_text(
            f"📊 **Agent Status**\n\n"
            f"Pending Approvals: {pending}\n"
            f"Bot: Running",
            parse_mode="Markdown"
        )
    
    async def _handle_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /positions command."""
        # This would need MCP access - placeholder for now
        await update.message.reply_text(
            "📈 **Open Positions**\n\n"
            "Use the web dashboard for full details.",
            parse_mode="Markdown"
        )
    
    async def _handle_panic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /panic command."""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⚠️ CONFIRM PANIC", callback_data="panic_confirm"),
                InlineKeyboardButton("Cancel", callback_data="panic_cancel")
            ]
        ])
        await update.message.reply_text(
            "🚨 **PANIC MODE**\n\n"
            "This will:\n"
            "- Cancel ALL open orders\n"
            "- Close ALL positions at market\n\n"
            "Are you sure?",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("approve_"):
            approval_id = int(data.split("_")[1])
            await self._process_approval(query, approval_id, "APPROVED")
            
        elif data.startswith("reject_"):
            approval_id = int(data.split("_")[1])
            await self._process_approval(query, approval_id, "REJECTED")
            
        elif data == "panic_confirm":
            await query.edit_message_text("🚨 PANIC triggered! Closing all...")
            if self.on_approval:
                await self.on_approval("PANIC", None)
                
        elif data == "panic_cancel":
            await query.edit_message_text("Panic cancelled.")
    
    async def _process_approval(self, query, approval_id: int, status: str):
        """Process an approval response."""
        
        with get_session() as session:
            approval = ApprovalRepository.respond(
                session,
                approval_id,
                status,
                query.from_user.username or str(query.from_user.id)
            )
        
        if status == "APPROVED":
            await query.edit_message_text(
                f"✅ **APPROVED**\n\nExecuting trade...",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"❌ **REJECTED**\n\nTrade cancelled.",
                parse_mode="Markdown"
            )
        
        # Trigger callback
        if self.on_approval:
            await self.on_approval(status, approval_id)


# Singleton instance
_bot_instance: Optional[TelegramApprovalBot] = None


def get_telegram_bot() -> TelegramApprovalBot:
    """Get or create the Telegram bot instance."""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = TelegramApprovalBot()
    return _bot_instance
