import os
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

users_file = "users.json"
if not os.path.exists(users_file):
    with open(users_file, "w") as f:
        json.dump({}, f)

def load_users():
    with open(users_file) as f:
        return json.load(f)

def save_users(data):
    with open(users_file, "w") as f:
        json.dump(data, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_users()
    if str(user.id) not in users:
        users[str(user.id)] = {
            "name": user.full_name,
            "balance": 0.00,
            "referrals": 0,
            "referred_by": None,
        }
        save_users(users)

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral")],
        [InlineKeyboardButton("🏦 Withdraw", callback_data="withdraw")]
    ])

    await update.message.reply_text(
        f"👋 Welcome, {user.first_name}!\n\n💡 Use the buttons below to navigate.",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    users = load_users()
    user_data = users.get(user_id, {})

    if query.data == "balance":
        await query.answer()
        await query.edit_message_text(f"💰 Your balance: ${user_data.get('balance', 0):.2f}")

    elif query.data == "referral":
        await query.answer()
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(
            f"👥 Your Referrals: {user_data.get('referrals', 0)}\n🔗 Referral Link:\n{ref_link}"
        )

    elif query.data == "withdraw":
        await query.answer()
        await query.edit_message_text(
            "🏦 Withdraw feature coming soon. Stay tuned!"
        )

async def referral_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_users()
    args = context.args

    referred_by = args[0] if args else None
    user_id = str(user.id)

    if user_id not in users:
        users[user_id] = {
            "name": user.full_name,
            "balance": 0.00,
            "referrals": 0,
            "referred_by": referred_by if referred_by != user_id else None,
        }

        if referred_by and referred_by in users:
            users[referred_by]["referrals"] += 1
            users[referred_by]["balance"] += 0.05  # $0.05 bonus per referral

        save_users(users)

    await start(update, context)

# === Flask Admin Panel ===
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "✅ SLI Bot is running"

@flask_app.route('/admin')
def admin():
    users = load_users()
    return jsonify(users)

# === Run Flask in a Thread ===
import threading

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

# === Start Bot ===
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", referral_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    thread = threading.Thread(target=run_flask)
    thread.start()

    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
