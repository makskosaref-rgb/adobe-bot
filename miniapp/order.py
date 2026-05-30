import os
import json
import urllib.request
import urllib.parse

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID", "")


def handler(request):
    if request.method != "POST":
        return {"statusCode": 405, "body": "Method Not Allowed"}

    try:
        body = json.loads(request.body)
        plan_name = body.get("plan_name", "")
        price = body.get("price", "")
        email = body.get("email", "")
        user_name = body.get("user_name", "Клиент")
        username = body.get("username", "нет")
        user_id = body.get("user_id", "")

        text = (
            f"🔔 *Новый заказ (Mini App)!*\n\n"
            f"👤 {user_name} (@{username or 'нет'})\n"
            f"🆔 `{user_id}`\n"
            f"📦 {plan_name} — {price}₽\n"
            f"📧 `{email}`"
        )

        # Отправляем уведомление владельцу
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": OWNER_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
        }).encode()

        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req)

        # Отправляем подтверждение клиенту если есть user_id
        if user_id:
            client_text = (
                f"🎉 *Заявка принята!*\n\n"
                f"Тариф: {plan_name} — {price}₽\n"
                f"Email: `{email}`\n\n"
                f"⏳ Активация в течение 1–3 часов.\n"
                f"Реквизиты для оплаты придут отдельно."
            )
            data2 = urllib.parse.urlencode({
                "chat_id": user_id,
                "text": client_text,
                "parse_mode": "Markdown",
            }).encode()
            req2 = urllib.request.Request(url, data=data2)
            try:
                urllib.request.urlopen(req2)
            except:
                pass

        return {"statusCode": 200, "body": json.dumps({"ok": True})}

    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
