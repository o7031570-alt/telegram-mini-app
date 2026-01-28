import os
import sys
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Root directory ကို path ထဲထည့်ပေးခြင်းဖြင့် database module ကို ရှာတွေ့စေမှာပါ
# Railway ပေါ်မှာ folder structure ကြောင့် import error တက်ခြင်းကို ကာကွယ်ရန်ဖြစ်သည်
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.append(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    # database folder ထဲက storage.py ထဲမှ DatabaseManager ကို import လုပ်ခြင်း
    from database.storage import DatabaseManager
    db_manager = DatabaseManager()
except ImportError as e:
    logging.error(f"❌ Import Error: {e}")
    # Database module ရှာမတွေ့ပါက dummy class ဖြင့် bot ကို ဆက်ပွင့်စေခြင်း
    class DatabaseManager:
        def get_post_count(self): return 0
        def get_all_posts(self, limit=5): return []
        def save_message(self, **kwargs): return True
        def log_error(self, **kwargs): pass
    db_manager = DatabaseManager()
    print("⚠️ Warning: DatabaseManager could not be imported. Using dummy storage.")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment Variables မှ Configuration များရယူခြင်း
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8514370308:AAG-qf5sR3IV9Ad0T0RZM9xCXv-59FPyR7I")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003791270028"))
ADMIN_USER_ID = int(os.environ.get("ADMIN_USER_ID", "7252765971"))
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://o7031570-alt.github.io/telegram-mini-app/")

# --- Bot Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        "🤖 Welcome to **For You Today** Bot!\n\n"
        "✨ **Features:**\n"
        "✅ Capture posts from @for_you_today\n"
        "✅ Store them in our database\n"
        "✅ View them in our Mini App\n\n"
        "📱 **Commands:**\n"
        "/open - Open the Mini App\n"
        "/stats - Show statistics\n"
        "/help - Show this message\n\n"
        f"🔗 Mini App: {MINI_APP_URL}",
        parse_mode='Markdown'
    )
    logger.info(f"User {user.id} ({user.username}) started the bot")

async def open_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /open command - send Mini App URL"""
    keyboard = [
        [InlineKeyboardButton("📱 Open For You Today Mini App", url=MINI_APP_URL)],
        [InlineKeyboardButton("👁️ View Channel", url="https://t.me/for_you_today")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✨ **Open our Mini App to view all posts from @for_you_today**\n\n"
        "Click below to open:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - show database statistics"""
    try:
        count = db_manager.get_post_count()
        await update.message.reply_text(
            f"📊 **@for_you_today Statistics**\n\n"
            f"• Total posts captured: {count}\n"
            f"• Channel: @for_you_today\n"
            f"• Mini App: {MINI_APP_URL}\n"
            f"• Bot Status: ✅ Active and running\n"
            f"• Database: Connected\n\n"
            f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        await update.message.reply_text("❌ Error getting statistics")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "🆘 **Help - For You Today Bot**\n\n"
        "🤖 **What I do:**\n"
        "• I automatically save posts from @for_you_today channel\n"
        "• Store them in a secure database\n"
        "• Make them available in our Mini App\n\n"
        "📱 **Commands:**\n"
        "/start - Welcome message\n"
        "/open - Open the Mini App\n"
        "/stats - Show statistics\n"
        "/help - This help message\n\n"
        "🔗 **Links:**\n"
        "• Channel: https://t.me/for_you_today\n"
        "• Mini App: {MINI_APP_URL}\n\n"
        "👨‍💻 **Admin:** @o7031570",
        parse_mode='Markdown'
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only commands"""
    user = update.effective_user
    if user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ This command is for administrators only.")
        return
    
    try:
        # Get system statistics
        posts = db_manager.get_all_posts(limit=5)
        recent_count = len(posts)
        
        await update.message.reply_text(
            f"👨‍💻 **Admin Dashboard**\n\n"
            f"• Admin ID: {ADMIN_USER_ID}\n"
            f"• Channel ID: {CHANNEL_ID}\n"
            f"• Total Posts: {db_manager.get_post_count()}\n"
            f"• Recent Posts (last 5): {recent_count}\n"
            f"• Bot Token: {BOT_TOKEN[:10]}...\n"
            f"• Mini App URL: {MINI_APP_URL}\n\n"
            f"✅ System is operational",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Admin command error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

# --- Channel Post Processing ---

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle posts from @for_you_today channel"""
    try:
        message = update.channel_post
        if not message:
            return
        
        # Check if it's from our channel
        if int(message.chat.id) != CHANNEL_ID:
            logger.info(f"Ignoring message from chat {message.chat.id}")
            return
        
        logger.info(f"Processing message {message.message_id} from @for_you_today")
        
        # Extract message data
        content = message.text or message.caption or ""
        message_id = message.message_id
        
        # Determine media type and additional info
        if message.photo:
            media_type = "photo"
            media_info = f"Photo (size: {message.photo[-1].file_size} bytes)"
        elif message.video:
            media_type = "video"
            media_info = f"Video (duration: {message.video.duration}s)"
        elif message.document:
            media_type = "document"
            media_info = f"Document: {message.document.file_name}"
        elif message.audio:
            media_type = "audio"
            media_info = f"Audio: {message.audio.title or 'Audio file'}"
        else:
            media_type = "text"
            media_info = "Text message"
        
        # Categorize based on content
        content_lower = content.lower()
        if any(keyword in content_lower for keyword in ['news', 'update', 'breaking', 'новости']):
            category = "news"
        elif any(keyword in content_lower for keyword in ['announce', 'important', 'notice', 'объявление']):
            category = "announcement"
        elif any(keyword in content_lower for keyword in ['quote', 'цитата', 'мысли']):
            category = "quotes"
        elif any(keyword in content_lower for keyword in ['photo', 'image', 'picture', 'фото', 'картинка']):
            category = "photos"
        elif any(keyword in content_lower for keyword in ['video', 'видео']):
            category = "videos"
        elif media_type != "text":
            category = "media"
        else:
            category = "general"
        
        # Save to database
        success = db_manager.save_message(
            message_id=message_id,
            content=content,
            media_type=media_type,
            category=category,
            timestamp=message.date or datetime.now(),
            additional_info=media_info
        )
        
        if success:
            logger.info(f"✅ Saved message {message_id} ({media_type}/{category}) from @for_you_today")
            
            # Notify admin about important posts
            if category in ["announcement", "important"] and content:
                try:
                    preview = content[:100] + "..." if len(content) > 100 else content
                    await context.bot.send_message(
                        chat_id=ADMIN_USER_ID,
                        text=f"📢 **New Announcement Saved**\n\n"
                             f"From: @for_you_today\n"
                             f"Type: {media_type}\n"
                             f"Preview: {preview}\n\n"
                             f"View in Mini App: {MINI_APP_URL}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin: {e}")
        else:
            logger.error(f"❌ Failed to save message {message_id}")
            
    except Exception as e:
        logger.error(f"Error handling channel post: {e}")
        try:
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=f"❌ **Bot Error**\n\nError processing message: {str(e)[:200]}"
            )
        except: pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bot errors"""
    error = context.error
    logger.error(f"Bot error: {error}")
    
    try:
        db_manager.log_error(
            error_type=type(error).__name__,
            error_message=str(error),
            update_id=update.update_id if update else None
        )
    except: pass
    
    if error and ("critical" in str(error).lower() or "token" in str(error).lower()):
        try:
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=f"⚠️ **Critical Bot Error**\n\n{str(error)[:200]}..."
            )
        except: pass

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set.")
        return
    
    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("open", open_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("admin", admin_command))
        
        # Add channel message handler
        channel_filter = filters.Chat(chat_id=CHANNEL_ID) & filters.UpdateType.CHANNEL_POST
        application.add_handler(MessageHandler(channel_filter, handle_channel_post))
        
        logger.info(f"✅ Bot configured for channel ID: {CHANNEL_ID}")
        logger.info(f"✅ Admin user ID: {ADMIN_USER_ID}")
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Start polling
        logger.info("🤖 Starting @for_you_today Bot...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    main()
