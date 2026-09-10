import asyncio
import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.environ.get("ADMIN_GROUP_ID", 0))
PORT = int(os.environ.get("PORT", 8000))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

user_to_thread = {}
thread_to_user = {}

tg_app = None
api = FastAPI()

# Catalog items
PRODUCTS = [
    {
        "id": "p1",
        "title": "FANCL Good Choice 20s (30 packs)",
        "category": "Supplements",
        "price": 28.00,
        "image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&q=80",
        "tag": "Daily Vitality",
    },
    {
        "id": "p2",
        "title": "FANCL Good Choice 30s (30 packs)",
        "category": "Supplements",
        "price": 34.00,
        "image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&q=80",
        "tag": "Anti-Aging & Collagen",
    },
    {
        "id": "p3",
        "title": "DHC Collagen (60 Days)",
        "category": "Supplements",
        "price": 15.00,
        "image": "https://images.unsplash.com/photo-1550572017-ed200f5e6343?w=500&q=80",
        "tag": "Firmness & Glow",
    },
    {
        "id": "p4",
        "title": "Quality 1st Derma Laser Super VC100",
        "category": "Skincare",
        "price": 12.50,
        "image": "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=500&q=80",
        "tag": "Pore Tightening",
    },
    {
        "id": "p5",
        "title": "Keana Nadeshiko Rice Mask (10 pcs)",
        "category": "Skincare",
        "price": 14.00,
        "image": "https://images.unsplash.com/photo-1608248597359-bb51da9c9689?w=500&q=80",
        "tag": "Hydration",
    },
]


@api.get("/")
@api.get("/health")
def health_check():
    return {"status": "ok", "app": "Piece & Petal Combined Store & Bot"}


@api.get("/shop", response_class=HTMLResponse)
def serve_shop():
    if os.path.exists("templates/index.html"):
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>templates/index.html not found. Please add the file.</h3>"


@api.get("/api/products")
def get_products():
    return PRODUCTS


@api.post("/api/checkout")
async def checkout(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    order_summary = data.get("summary", "")
    customer_name = data.get("customer_name", "Guest")
    phone = data.get("phone", "N/A")
    address = data.get("address", "N/A")
    total = data.get("total", 0.0)

    order_card = (
        f"🛍️ *NEW IN-APP ORDER SUBMITTED*\n"
        f"────────────────────\n"
        f"• Customer: {customer_name}\n"
        f"• Phone: `{phone}`\n"
        f"• Location: {address}\n"
        f"• Total: *${total:.2f}*\n\n"
        f"*Items:*\n{order_summary}\n"
        f"────────────────────\n"
        f"⚠️ Check ABA Mobile / Merchant App to confirm payment before preparing."
    )

    thread_id = user_to_thread.get(user_id) if user_id else None

    try:
        if thread_id:
            await tg_app.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                message_thread_id=thread_id,
                text=order_card,
                parse_mode="Markdown",
            )
        else:
            await tg_app.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=order_card,
                parse_mode="Markdown",
            )
    except Exception as e:
        logging.error(f"Error forwarding checkout order: {e}")

    return {"status": "success"}


async def ensure_user_topic(user, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = user.id
    if user_id not in user_to_thread:
        topic_name = f"🌸 {user.full_name[:18]} ({user_id})"
        try:
            topic = await context.bot.create_forum_topic(
                chat_id=ADMIN_GROUP_ID,
                name=topic_name,
            )
            thread_id = topic.message_thread_id
            user_to_thread[user_id] = thread_id
            thread_to_user[thread_id] = user_id

            profile_card = (
                f"🛍️ *New Customer Profile:*\n"
                f"• Client: {user.full_name}\n"
                f"• Handle: @{user.username if user.username else 'None'}\n"
                f"• ID: `{user_id}`\n"
                f"────────────────────"
            )
            await context.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                message_thread_id=thread_id,
                text=profile_card,
                parse_mode="Markdown",
            )
        except Exception as e:
            logging.error(f"Error creating topic: {e}")
            return None

    return user_to_thread.get(user_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type != "private":
        return
    if not update.message:
        return

    welcome_text = (
        "🌸 *Welcome to Piece & Petal* 🇯🇵✨\n\n"
        "Piece & Petal មានលក់ Supplement, Skincare, Cosmetics, និងផលិតផលផ្សេងៗនាំចូលពីជប៉ុន\n\n"
        "ឥវ៉ាន់ធានាសុទ្ធពីជប៉ុន 100% អ្នកលក់ទៅយកផ្ទាល់ពីហាង\n\n"
        "បងៗចង់ស្វែងរក ឬចង់ទិញផលិតផលអ្វី អាចទម្លាក់សារមក ក្រុមការងារនឹងឆ្លើយតបជូនភ្លាមៗណា៎ 😍"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

    thread_id = await ensure_user_topic(update.effective_user, context)
    if thread_id:
        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=thread_id,
            text="⚡ *Customer tapped /start*",
            parse_mode="Markdown",
        )


async def forward_to_admin_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type != "private":
        return
    if not update.effective_user or not update.message:
        return

    thread_id = await ensure_user_topic(update.effective_user, context)
    if not thread_id:
        return

    await context.bot.copy_message(
        chat_id=ADMIN_GROUP_ID,
        message_thread_id=thread_id,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
    )


async def reply_from_admin_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id != ADMIN_GROUP_ID:
        return
    if not update.message:
        return

    thread_id = update.message.message_thread_id
    if not thread_id or thread_id not in thread_to_user:
        return

    customer_id = thread_to_user[thread_id]
    try:
        await context.bot.copy_message(
            chat_id=customer_id,
            from_chat_id=ADMIN_GROUP_ID,
            message_id=update.message.message_id,
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send to customer: {e}")


async def main():
    global tg_app
    tg_app = ApplicationBuilder().token(BOT_TOKEN).build()

    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & ~filters.COMMAND,
            forward_to_admin_topic,
        )
    )
    tg_app.add_handler(
        MessageHandler(
            filters.Chat(ADMIN_GROUP_ID) & ~filters.COMMAND,
            reply_from_admin_topic,
        )
    )

    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_polling(drop_pending_updates=True)

    config = uvicorn.Config(app=api, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

    await tg_app.updater.stop()
    await tg_app.stop()
    await tg_app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
