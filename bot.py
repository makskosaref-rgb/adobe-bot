import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ─────────────────────────────────────────────
# НАСТРОЙКИ
# ─────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID", "")

# Тарифы
PLANS = {
    "plan_14": {"name": "14 дней", "price": "249₽"},
    "plan_30": {"name": "1 месяц", "price": "490₽"},
    "plan_90": {"name": "3 месяца", "price": "1290₽"},
}

ASK_EMAIL = 1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛒 Купить подписку", callback_data="show_plans")],
        [InlineKeyboardButton("📋 Мой заказ", callback_data="my_status")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help_info")],
    ]
    await update.message.reply_text(
        "👋 Привет! Это бот для покупки *Adobe Creative Cloud*.\n\n"
        "Активация на твой email в течение нескольких часов.\n\n"
        "Выбери действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────
# /help
# ─────────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "❓ *Частые вопросы*\n\n"
        "*Как работает подписка?*\n"
        "Мы добавляем твой email в Adobe CC — получаешь доступ ко всем приложениям.\n\n"
        "*Как быстро активируют?*\n"
        "1–3 часа в рабочее время (10:00–22:00 МСК).\n\n"
        "*Что входит?*\n"
        "Photoshop, Illustrator, Premiere Pro, After Effects и все остальные Adobe CC.\n\n"
        "*Как оплатить?*\n"
        "После заявки пришлём реквизиты."
    )
    msg = update.message or (update.callback_query.message if update.callback_query else None)
    if msg:
        await msg.reply_text(text, parse_mode="Markdown")


# ─────────────────────────────────────────────
# /status
# ─────────────────────────────────────────────
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order = context.user_data.get("order")
    if order:
        text = (
            f"📦 *Твой заказ:*\n\n"
            f"Тариф: {order['plan']}\n"
            f"Email: {order['email']}\n"
            f"Статус: ⏳ Ожидает активации"
        )
    else:
        text = "📦 У тебя пока нет заказов.\n\nНажми /buy чтобы оформить."
    msg = update.message or (update.callback_query.message if update.callback_query else None)
    if msg:
        await msg.reply_text(text, parse_mode="Markdown")


# ─────────────────────────────────────────────
# /buy — показать тарифы
# ─────────────────────────────────────────────
async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⚡ 14 дней — 249₽", callback_data="buy_plan_14")],
        [InlineKeyboardButton("📅 1 месяц — 490₽", callback_data="buy_plan_30")],
        [InlineKeyboardButton("🏆 3 месяца — 1290₽", callback_data="buy_plan_90")],
    ]
    text = (
        "🛒 *Выбери тариф Adobe Creative Cloud:*\n\n"
        "⚡ *14 дней* — 249₽\n"
        "📅 *1 месяц* — 490₽\n"
        "🏆 *3 месяца* — 1290₽ (выгоднее всего)"
    )
    msg = update.message or (update.callback_query.message if update.callback_query else None)
    if msg:
        await msg.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ─────────────────────────────────────────────
# Выбор тарифа
# ─────────────────────────────────────────────
async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plan_key = query.data.replace("buy_", "")
    plan = PLANS.get(plan_key)
    if not plan:
        return ConversationHandler.END

    context.user_data["selected_plan"] = plan_key
    await query.message.reply_text(
        f"✅ Ты выбрал: *{plan['name']} — {plan['price']}*\n\n"
        f"Введи свой email для активации:",
        parse_mode="Markdown",
    )
    return ASK_EMAIL


# ─────────────────────────────────────────────
# Получить email
# ─────────────────────────────────────────────
async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()

    if "@" not in email or "." not in email:
        await update.message.reply_text("❌ Это не похоже на email. Попробуй ещё раз:")
        return ASK_EMAIL

    plan_key = context.user_data.get("selected_plan", "plan_30")
    plan = PLANS[plan_key]
    user = update.effective_user

    context.user_data["order"] = {"plan": plan["name"], "email": email}

    await update.message.reply_text(
        f"🎉 *Заявка принята!*\n\n"
        f"Тариф: {plan['name']} — {plan['price']}\n"
        f"Email: `{email}`\n\n"
        f"⏳ Активация в течение 1–3 часов.\n"
        f"Реквизиты для оплаты придут отдельно.",
        parse_mode="Markdown",
    )

    if OWNER_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=int(OWNER_CHAT_ID),
                text=(
                    f"🔔 *Новый заказ!*\n\n"
                    f"👤 {user.full_name} (@{user.username or 'нет'})\n"
                    f"🆔 `{user.id}`\n"
                    f"📦 {plan['name']} — {plan['price']}\n"
                    f"📧 `{email}`"
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления: {e}")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Отменено. /buy — начать заново.")
    return ConversationHandler.END


# ─────────────────────────────────────────────
# Кнопки из /start
# ─────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "show_plans":
        await buy_command(update, context)
    elif query.data == "my_status":
        await status_command(update, context)
    elif query.data == "help_info":
        await help_command(update, context)


# ─────────────────────────────────────────────
# Запуск
# ─────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(plan_selected, pattern="^buy_plan_")],
        states={
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
