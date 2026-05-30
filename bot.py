import os
import json
import logging
import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID", "")
MINIAPP_URL = os.environ.get("MINIAPP_URL", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def ask_gemini(question):
    if not GEMINI_API_KEY:
        return None
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\nВопрос клиента: {question}"}]}]
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

SYSTEM_PROMPT = """Ты — вежливый менеджер по продажам Adobe Creative Cloud подписок.
Отвечай коротко и по делу, на русском языке.

Информация о продукте:
- 14 дней доступа — 249₽
- 1 месяц — 490₽
- 3 месяца — 1290₽ (выгоднее всего)
- Активация: клиент присылает свой email от Adobe, мы добавляем подписку в течение 1-3 часов
- Входит: все приложения Adobe CC (Photoshop, Illustrator, Premiere Pro, After Effects и др.), 100 ГБ облако
- Оплата: реквизиты приходят после оформления заявки
- Работаем 10:00–22:00 МСК

Если клиент хочет купить — предложи нажать кнопку "Открыть магазин" или написать /buy.
Не придумывай информацию которой нет выше. Отвечай дружелюбно и коротко (2-4 предложения)."""

bot = telebot.TeleBot(BOT_TOKEN)

PLANS = {
    "plan_14": {"name": "14 дней", "price": "249₽"},
    "plan_30": {"name": "1 месяц", "price": "490₽"},
    "plan_90": {"name": "3 месяца", "price": "1290₽"},
}

# Храним состояние пользователя
user_state = {}
user_orders = {}


def main_menu():
    kb = InlineKeyboardMarkup()
    if MINIAPP_URL:
        kb.add(InlineKeyboardButton("🛒 Открыть магазин", web_app=WebAppInfo(url=MINIAPP_URL)))
    else:
        kb.add(InlineKeyboardButton("🛒 Купить подписку", callback_data="show_plans"))
    kb.add(InlineKeyboardButton("📋 Мой заказ", callback_data="my_status"))
    kb.add(InlineKeyboardButton("❓ Помощь", callback_data="help_info"))
    return kb


def plans_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⚡ 14 дней — 249₽", callback_data="buy_plan_14"))
    kb.add(InlineKeyboardButton("📅 1 месяц — 490₽", callback_data="buy_plan_30"))
    kb.add(InlineKeyboardButton("🏆 3 месяца — 1290₽", callback_data="buy_plan_90"))
    return kb


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет! Это бот для покупки *Adobe Creative Cloud*.\n\n"
        "Активация на твой email в течение нескольких часов.\n\n"
        "Выбери действие:",
        reply_markup=main_menu(),
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["buy"])
def buy(message):
    bot.send_message(
        message.chat.id,
        "🛒 *Выбери тариф Adobe Creative Cloud:*\n\n"
        "⚡ *14 дней* — 249₽\n"
        "📅 *1 месяц* — 490₽\n"
        "🏆 *3 месяца* — 1290₽ (выгоднее всего)",
        reply_markup=plans_menu(),
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "❓ *Частые вопросы*\n\n"
        "*Как работает?*\n"
        "Мы добавляем твой email в Adobe CC — получаешь доступ ко всем приложениям.\n\n"
        "*Как быстро активируют?*\n"
        "1–3 часа в рабочее время (10:00–22:00 МСК).\n\n"
        "*Что входит?*\n"
        "Photoshop, Illustrator, Premiere Pro, After Effects и все остальные Adobe CC.\n\n"
        "*Как оплатить?*\n"
        "После заявки пришлём реквизиты.",
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["status"])
def status_cmd(message):
    order = user_orders.get(message.chat.id)
    if order:
        text = (
            f"📦 *Твой заказ:*\n\n"
            f"Тариф: {order['plan']}\n"
            f"Email: {order['email']}\n"
            f"Статус: ⏳ Ожидает активации"
        )
    else:
        text = "📦 У тебя пока нет заказов.\n\nНажми /buy чтобы оформить."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    bot.answer_callback_query(call.id)

    if call.data == "show_plans":
        bot.send_message(
            call.message.chat.id,
            "🛒 *Выбери тариф:*",
            reply_markup=plans_menu(),
            parse_mode="Markdown",
        )

    elif call.data == "my_status":
        order = user_orders.get(call.message.chat.id)
        if order:
            text = f"📦 *Твой заказ:*\n\nТариф: {order['plan']}\nEmail: {order['email']}\nСтатус: ⏳ Ожидает активации"
        else:
            text = "📦 У тебя пока нет заказов.\n\nНажми /buy чтобы оформить."
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

    elif call.data == "help_info":
        bot.send_message(
            call.message.chat.id,
            "❓ *Частые вопросы*\n\n"
            "*Как работает?*\nМы добавляем твой email в Adobe CC.\n\n"
            "*Как быстро?*\n1–3 часа в рабочее время.\n\n"
            "*Как оплатить?*\nПосле заявки пришлём реквизиты.",
            parse_mode="Markdown",
        )

    elif call.data.startswith("buy_plan_"):
        plan_key = call.data.replace("buy_", "")
        plan = PLANS.get(plan_key)
        if plan:
            user_state[call.message.chat.id] = {"step": "await_email", "plan": plan_key}
            bot.send_message(
                call.message.chat.id,
                f"✅ Ты выбрал: *{plan['name']} — {plan['price']}*\n\n"
                f"Введи свой email для активации:",
                parse_mode="Markdown",
            )


@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "await_email")
def receive_email(message):
    email = message.text.strip()

    if "@" not in email or "." not in email:
        bot.send_message(message.chat.id, "❌ Это не похоже на email. Попробуй ещё раз:")
        return

    plan_key = user_state[message.chat.id]["plan"]
    plan = PLANS[plan_key]
    user_state.pop(message.chat.id, None)

    user_orders[message.chat.id] = {"plan": plan["name"], "email": email}

    bot.send_message(
        message.chat.id,
        f"🎉 *Заявка принята!*\n\n"
        f"Тариф: {plan['name']} — {plan['price']}\n"
        f"Email: `{email}`\n\n"
        f"⏳ Активация в течение 1–3 часов.\n"
        f"Реквизиты для оплаты придут отдельно.",
        parse_mode="Markdown",
    )

    if OWNER_CHAT_ID:
        try:
            user = message.from_user
            bot.send_message(
                int(OWNER_CHAT_ID),
                f"🔔 *Новый заказ!*\n\n"
                f"👤 {user.full_name} (@{user.username or 'нет'})\n"
                f"🆔 `{user.id}`\n"
                f"📦 {plan['name']} — {plan['price']}\n"
                f"📧 `{email}`",
                parse_mode="Markdown",
            )
        except Exception as e:
            logging.error(f"Ошибка уведомления: {e}")


# Обработка данных из Mini App
@bot.message_handler(content_types=['web_app_data'])
def web_app_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        plan_name = data.get("plan_name", "")
        price = data.get("price", "")
        email = data.get("email", "")
        user = message.from_user

        user_orders[message.chat.id] = {"plan": plan_name, "email": email}

        bot.send_message(
            message.chat.id,
            f"🎉 *Заявка принята!*\n\n"
            f"Тариф: {plan_name} — {price}\n"
            f"Email: `{email}`\n\n"
            f"⏳ Активация в течение 1–3 часов.\n"
            f"Реквизиты для оплаты придут отдельно.",
            parse_mode="Markdown",
        )

        if OWNER_CHAT_ID:
            try:
                bot.send_message(
                    int(OWNER_CHAT_ID),
                    f"🔔 *Новый заказ (Mini App)!*\n\n"
                    f"👤 {user.full_name} (@{user.username or 'нет'})\n"
                    f"🆔 `{user.id}`\n"
                    f"📦 {plan_name} — {price}\n"
                    f"📧 `{email}`",
                    parse_mode="Markdown",
                )
            except Exception as e:
                logging.error(f"Ошибка уведомления: {e}")
    except Exception as e:
        logging.error(f"Ошибка web_app_data: {e}")


# AI менеджер — отвечает на все остальные сообщения
@bot.message_handler(func=lambda m: True)
def ai_manager(message):
    try:
        bot.send_chat_action(message.chat.id, "typing")
        answer = ask_gemini(message.text)
        if answer:
            bot.send_message(message.chat.id, answer)
        else:
            bot.send_message(message.chat.id, "По всем вопросам: /help или /buy для заказа.")
    except Exception as e:
        logging.error(f"Ошибка AI: {e}")
        bot.send_message(message.chat.id, "По всем вопросам: /help или /buy для заказа.")


if __name__ == "__main__":
    import time
    logging.info("Бот запущен...")
    # Сбрасываем старые соединения
    try:
        bot.remove_webhook()
        time.sleep(2)
    except Exception:
        pass
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            time.sleep(15)
