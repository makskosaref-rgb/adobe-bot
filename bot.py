import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ─────────────────────────────────────────────
# НАСТРОЙКИ — заполни перед запуском
# ─────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")
OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID", "ВСТАВЬ_СВОЙ_CHAT_ID")  # твой Telegram ID

# ─────────────────────────────────────────────
# Тарифы
# ─────────────────────────────────────────────
PLANS = {
    "plan_14": {"name": "14 дней", "price": "249₽", "days": 14},
    "plan_30": {"name": "1 месяц", "price": "490₽", "days": 30},
    "plan_90": {"name": "3 месяца", "price": "1290₽", "days": 90},
}

# Состояния диалога /buy
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
        "Здесь ты можешь оформить подписку — активация на твой email в течение нескольких часов.\n\n"
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
        "Ты покупаешь доступ к Adobe Creative Cloud. Мы добавляем твой email в подписку — "
        "ты получаешь доступ ко всем приложениям Adobe.\n\n"
        "*Как быстро активируют?*\n"
        "Обычно в течение 1–3 часов в рабочее время (10:00–22:00 МСК).\n\n"
        "*Что нужно для активации?*\n"
        "Только твой email от Adobe (или любой — создадим аккаунт).\n\n"
        "*Что входит в подписку?*\n"
        "Photoshop, Illustrator, Premiere Pro, After Effects и все остальные приложения Adobe CC.\n\n"
        "*Как оплатить?*\n"
        "После оформления заявки мы пришлём реквизиты для оплаты.\n\n"
        "По другим вопросам пиши: @твой_юзернейм"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")


# ─────────────────────────────────────────────
# /status
# ─────────────────────────────────────────────
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Простая версия: выводим статус из user_data (сохраняется пока бот запущен)
    order = context.user_data.get("order")
    if order:
        text = (
            f"📦 *Твой последний заказ:*\n\n"
            f"Тариф: {order['plan']}\n"
            f"Email: {order['email']}\n"
            f"Статус: ⏳ Ожидает активации\n\n"
            f"Активация обычно занимает 1–3 часа."
        )
    else:
        text = (
            "📦 У тебя пока нет активных заказов.\n\n"
            "Нажми /buy чтобы оформить подписку."
        )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")


# ─────────────────────────────────────────────
# /buy — шаг 1: показать тарифы
# ─────────────────────────────────────────────
async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"⚡ 14 дней — 249₽", callback_data="buy_plan_14")],
        [InlineKeyboardButton(f"📅 1 месяц — 490₽", callback_data="buy_plan_30")],
        [InlineKeyboardButton(f"🏆 3 месяца — 1290₽", callback_data="buy_plan_90")],
    ]
    text = (
        "🛒 *Выбери тариф Adobe Creative Cloud:*\n\n"
        "⚡ *14 дней* — 249₽\n"
        "📅 *1 месяц* — 490₽\n"
        "🏆 *3 месяца* — 1290₽ (выгоднее всего)\n\n"
        "После выбора введи свой email для активации."
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ─────────────────────────────────────────────
# Callback: выбор тарифа → запросить email
# ─────────────────────────────────────────────
async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plan_key = query.data.replace("buy_", "")  # plan_14 / plan_30 / plan_90
    plan = PLANS.get(plan_key)
    if not plan:
        return

    context.user_data["selected_plan"] = plan_key
    await query.message.reply_text(
        f"✅ Ты выбрал: *{plan['name']} — {plan['price']}*\n\n"
        f"Введи свой email (аккаунт Adobe) для активации подписки:",
        parse_mode="Markdown",
    )
    return ASK_EMAIL


# ─────────────────────────────────────────────
# Шаг 2: получить email и создать заказ
# ─────────────────────────────────────────────
async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()

    # Базовая проверка email
    if "@" not in email or "." not in email:
        await update.message.reply_text("❌ Похоже, это не email. Попробуй ещё раз:")
        return ASK_EMAIL

    plan_key = context.user_data.get("selected_plan", "plan_30")
    plan = PLANS[plan_key]
    user = update.effective_user

    # Сохраняем заказ
    context.user_data["order"] = {"plan": plan["name"], "email": email}

    # Сообщение клиенту
    await update.message.reply_text(
        f"🎉 *Заявка принята!*\n\n"
        f"Тариф: {plan['name']} — {plan['price']}\n"
        f"Email: `{email}`\n\n"
        f"⏳ Мы активируем подписку в течение 1–3 часов.\n"
        f"Реквизиты для оплаты придут отдельным сообщением.\n\n"
        f"По вопросам: /help",
        parse_mode="Markdown",
    )

    # Уведомление владельцу
    owner_text = (
        f"🔔 *Новый заказ!*\n\n"
        f"👤 Клиент: {user.full_name} (@{user.username or 'нет'})\n"
        f"🆔 ID: `{user.id}`\n"
        f"📦 Тариф: {plan['name']} — {plan['price']}\n"
        f"📧 Email: `{email}`"
    )
    try:
        await context.bot.send_message(
            chat_id=OWNER_CHAT_ID,
            text=owner_text,
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление владельцу: {e}")

    return ConversationHandler.END


# ─────────────────────────────────────────────
# Отмена диалога
# ─────────────────────────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Покупка отменена. Используй /buy чтобы начать заново.")
    return ConversationHandler.END


# ─────────────────────────────────────────────
# Callback-кнопки из /start
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
# Запуск бота
# ─────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler для /buy
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("buy", buy_command),
            CallbackQueryHandler(plan_selected, pattern="^buy_plan_"),
        ],
        states={
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(plan_selected, pattern="^buy_plan_"))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
