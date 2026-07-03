import os
import logging
from datetime import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Fallback token for testing, but it should ideally come from environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Simple in-memory storage (Resets when server restarts. Use a DB like PostgreSQL for production)
user_habits = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message using HTML parsing."""
    user_id = update.effective_user.id
    if user_id not in user_habits:
        user_habits[user_id] = []
        
    welcome_text = (
        "<b>Welcome to your personal Habit Tracker!</b> 🎯\n\n"
        "Small daily wins lead to massive long-term results.\n\n"
        "<b>Commands:</b>\n"
        "➕ /add [habit name] - Create a new habit\n"
        "📋 /habits - View your habits\n"
        "✅ /done [habit name] - Mark a habit as completed\n"
        "⚡ /clear - Reset your habits list"
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML")

async def add_habit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adds a new habit to the user's list."""
    user_id = update.effective_user.id
    habit = " ".join(context.args).strip()
    
    if not habit:
        await update.message.reply_text("❌ Please specify a habit. Example: <code>/add 10k Steps</code>", parse_mode="HTML")
        return
        
    if user_id not in user_habits:
        user_habits[user_id] = []
        
    user_habits[user_id].append({"name": habit, "done": False})
    await update.message.reply_text(f"🎯 Added habit: <b>{habit}</b>", parse_mode="HTML")

async def list_habits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lists all habits and their status."""
    user_id = update.effective_user.id
    habits = user_habits.get(user_id, [])
    
    if not habits:
        await update.message.reply_text("You haven't added any habits yet! Use /add to begin.", parse_mode="HTML")
        return
        
    text = "📋 <b>Your Daily Habits:</b>\n\n"
    for h in habits:
        status = "✅ Done" if h["done"] else "⏳ Pending"
        text += f"• <b>{h['name']}</b> — {status}\n"
        
    await update.message.reply_text(text, parse_mode="HTML")

async def done_habit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Marks a habit as completed."""
    user_id = update.effective_user.id
    habit_name = " ".join(context.args).strip()
    habits = user_habits.get(user_id, [])
    
    for h in habits:
        if h["name"].lower() == habit_name.lower():
            h["done"] = True
            await update.message.reply_text(f"🔥 Awesome! <b>{h['name']}</b> is marked as done.", parse_mode="HTML")
            return
            
    await update.message.reply_text(f"❌ Could not find habit named '{habit_name}'. Type /habits to see your list.", parse_mode="HTML")

async def clear_habits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears the current user's habits list."""
    user_id = update.effective_user.id
    user_habits[user_id] = []
    await update.message.reply_text("🧹 Your habit list has been cleared.", parse_mode="HTML")

async def daily_reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Background task that sends a reminder to all active users."""
    reminder_text = (
        "🔔 <b>Daily Evening Reminder!</b>\n\n"
        "Don't break your streak! Don't forget to check your 📋 /habits and mark them finished."
    )
    for user_id in user_habits.keys():
        try:
            await context.bot.send_message(chat_id=user_id, text=reminder_text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Could not send reminder to {user_id}: {e}")

def main() -> None:
    """Starts the bot and sets up background workers."""
    # Build application
    application = Application.builder().token(TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_habit))
    application.add_handler(CommandHandler("habits", list_habits))
    application.add_handler(CommandHandler("done", done_habit))
    application.add_handler(CommandHandler("clear", clear_habits))

    # Background Job Queue for Daily Reminder (Runs every day at 8:00 PM / 20:00 UTC)
    job_queue = application.job_queue
    job_queue.run_daily(daily_reminder_job, time=time(hour=20, minute=0))

    # Run the bot with polling (Ideal for background workers)
    print("Bot is starting up smoothly...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
                                        
