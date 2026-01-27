#!/usr/bin/env python3
"""
Telegram Bot for Termux - Channel Post Capture & Mini App Integration
"""

import logging
import asyncio
from datetime import datetime
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode

import sys
sys.path.append('.')
from database.storage import ChannelStorage

# Termux-compatible paths
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configuration - REPLACE WITH YOUR VALUES
BOT_TOKEN = "8514370308:AAG-qf5sR3IV9Ad0T0RZM9xCXv-59FPyR7I"
CHANNEL_USERNAME = "@for_you_today"
CHANNEL_ID = -1003791270028
ADMIN_USER_ID = 7252765971
MINI_APP_URL = "https://o7031570-alt.github.io/telegram-mini-app/"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_DIR / "bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

storage = ChannelStorage()

MEDIA_TYPES = {
    'photo': 'photo', 'video': 'video', 'document': 'document',
    'audio': 'audio', 'voice': 'audio', 'animation': 'video',
    'sticker': 'sticker', 'text': 'text'
}

def get_media_type(message):
    if message.photo: return 'photo'
    elif message.video: return 'video'
    elif message.document: return 'document'
    elif message.audio: return 'audio'
    elif message.voice: return 'audio'
    elif message.animation: return 'video'
    elif message.sticker: return 'sticker'
    else: return 'text'

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"👋 Hello {user.first_name}!\n\n"
        f"🤖 I'm a channel post archiver bot.\n"
        f"📊 Currently monitoring: {CHANNEL_USERNAME}\n"
        f"💾 Posts saved: {storage.count_posts()}\n\n"
        f"Commands:\n"
        f"/open - Open Mini App\n"
        f"/stats - Show statistics\n"
        f"/posts [category] - View recent posts\n"
    )
    await update.message.reply_text(welcome_text)

async def open_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Open Mini App", web_app={"url": MINI_APP_URL})],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_mini_app")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📱 **Mini App Launcher**\n\n"
        "Click the button below to open the Mini App in Telegram:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ Admin only command.")
        return
    
    total_posts = storage.count_posts()
    categories = storage.get_categories()
    
    stats_text = "📊 **Bot Statistics**\n\n"
    stats_text += f"**Total Posts:** {total_posts}\n\n"
    stats_text += "**Posts by Category:**\n"
    
    for category in categories:
        count = storage.count_posts(category)
        stats_text += f"• {category}: {count}\n"
    
    posts = storage.fetch_posts(limit=1000)
    media_counts = {}
    for post in posts:
        media_type = post.get('media_type', 'text')
        media_counts[media_type] = media_counts.get(media_type, 0) + 1
    
    stats_text += f"\n**Media Types:**\n"
    for media_type, count in media_counts.items():
        stats_text += f"• {media_type}: {count}\n"
    
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def posts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = context.args[0] if context.args else None
    limit = 10
    
    posts = storage.fetch_posts(category=category, limit=limit)
    
    if not posts:
        await update.message.reply_text(
            f"No posts found{f' in category: {category}' if category else ''}."
        )
        return
    
    response_text = f"📝 **Recent Posts**\n"
    if category:
        response_text += f"**Category:** {category}\n"
    response_text += f"**Showing:** {len(posts)} posts\n\n"
    
    for i, post in enumerate(posts, 1):
        truncated = post['content'][:100] + "..." if len(post['content']) > 100 else post['content']
        response_text += (
            f"{i}. **ID:** {post['message_id']}\n"
            f"   **Type:** {post['media_type']}\n"
            f"   **Category:** {post['category']}\n"
            f"   **Content:** {truncated}\n"
            f"   **Time:** {post['timestamp'][:19]}\n\n"
        )
    
    keyboard = []
    if category:
        keyboard.append([InlineKeyboardButton(f"📁 All Categories", callback_data="posts_all")])
    if len(posts) == limit:
        keyboard.append([InlineKeyboardButton("📜 Load More", callback_data="posts_more")])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await update.message.reply_text(
        response_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.channel_post
        
        if message.chat.id != CHANNEL_ID:
            logger.info(f"Ignoring post from chat ID: {message.chat.id}")
            return
        
        content = ""
        if message.text:
            content = message.text
        elif message.caption:
            content = message.caption
        elif message.sticker:
            content = message.sticker.emoji or "Sticker"
        
        media_type = get_media_type(message)
        
        category = 'general'
        if media_type != 'text':
            category = 'media'
        if any(keyword in content.lower() for keyword in ['news', 'update', 'announcement']):
            category = 'news'
        if any(keyword in content.lower() for keyword in ['important', 'urgent', 'alert']):
            category = 'important'
        
        saved = storage.save_post(
            message_id=message.message_id,
            content=content,
            media_type=media_type,
            category=category
        )
        
        if saved:
            logger.info(f"Saved post {message.message_id} from {CHANNEL_USERNAME}")
            
            if ADMIN_USER_ID and message.chat.id != ADMIN_USER_ID:
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_USER_ID,
                        text=f"✅ Saved post {message.message_id}\n"
                             f"📝 {content[:100]}..."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin: {e}")
        
    except Exception as e:
        logger.error(f"Error handling channel post: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "refresh_mini_app":
        keyboard = [
            [InlineKeyboardButton("🚀 Open Mini App", web_app={"url": MINI_APP_URL})]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📱 **Mini App Launcher**\n\n"
            "Mini App refreshed. Click to open:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    elif query.data == "posts_all":
        await query.edit_message_text("Fetching all posts...")
        context.args = []
        await posts_command(update, context)
    elif query.data == "posts_more":
        await query.answer("Load more functionality would be implemented here!")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error: {context.error}")
    
    if ADMIN_USER_ID:
        try:
            error_msg = f"❌ Bot Error:\n{context.error}"
            await context.bot.send_message(chat_id=ADMIN_USER_ID, text=error_msg[:4000])
        except:
            pass

def check_config():
    if BOT_TOKEN == "8514370308:AAG-qf5sR3IV9Ad0T0RZM9xCXv-59FPyR7I":
        raise ValueError("❌ Please set BOT_TOKEN in the script!")
    if CHANNEL_USERNAME == "@for_you_today":
        logger.warning("⚠️  CHANNEL_USERNAME not configured")
    if CHANNEL_ID == -1003791270028:
        logger.warning("⚠️  CHANNEL_ID not configured")
    if ADMIN_USER_ID == 7252765971:
        logger.warning("⚠️  ADMIN_USER_ID not configured")
    if MINI_APP_URL == "https://o7031570-alt.github.io/telegram-mini-app/":
        logger.warning("⚠️  MINI_APP_URL not configured")

async def run_bot():
    check_config()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("open", open_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("posts", posts_command))
    
    application.add_handler(
        MessageHandler(filters.ChatType.CHANNEL, handle_channel_post)
    )
    
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_error_handler(error_handler)
    
    logger.info("🤖 Bot starting...")
    logger.info(f"📊 Database has {storage.count_posts()} posts")
    logger.info(f"📱 Mini App URL: {MINI_APP_URL}")
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    logger.info("✅ Bot is running. Press Ctrl+C to stop.")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Error: {e}")
        print("💡 Make sure you:")
        print("   1. Replaced BOT_TOKEN with your bot token")
        print("   2. Installed requirements")
        print("   3. Added bot to your channel as admin")
