import os
import io
import csv
import json
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx
import uvicorn

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.environ.get("ADMIN_GROUP_ID", 0))
PORT = int(os.environ.get("PORT", 8000))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://piecenpetal-bot.onrender.com").rstrip("/")

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "1oBJ0mo_qWO6fRo6t8YfdOG-_EaUsDwhLP5mISOw-hrE")
CSV_EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
ORDER_WEBHOOK_URL = os.environ.get("ORDER_WEBHOOK_URL", "")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

user_to_thread = {}
thread_to_user = {}
CUSTOMER_DB_FILE = "customers.json"

def save_customer(user_id: int):
    try:
        data = []
        if os.path.exists(CUSTOMER_DB_FILE):
            with open(CUSTOMER_DB_FILE, "r") as f:
                data = json.load(f)
        if user_id not in data:
            data.append(user_id)
            with open(CUSTOMER_DB_FILE, "w") as f:
                json.dump(data, f)
    except Exception as e:
        logging.error(f"Error saving customer: {e}")

def get_all_customers() -> list:
    if os.path.exists(CUSTOMER_DB_FILE):
        try:
            with open(CUSTOMER_DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

tg_app = None

async def ensure_user_topic(user, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = user.id
    save_customer(user_id)

    if user_id not in user_to_thread:
        topic_name = f"🌸 {user.full_name[:18]} ({user_id})"
        try:
            topic = await context.bot.create_forum_topic(
                chat_id=ADMIN_GROUP_ID,
                name=topic_name
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
                parse_mode="Markdown"
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
            parse_mode="Markdown"
        )

async def handle_order_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reliable callback handler that won't blink or lose state."""
    query = update.callback_query
    if not query:
        return

    # Stop Telegram's loading spinner immediately
    await query.answer()

    data = query.data.split(":")
    action = data[0]
    user_id = int(data[1])
    admin_name = update.effective_user.first_name or "Admin"
    time_str = datetime.now().strftime("%I:%M %p")

    msg = query.message
    base_text = msg.text or "Order Details"

    # Remove the call-to-action line if present
    if "💬 Tap below" in base_text:
        base_text = base_text.split("💬 Tap below")[0].strip()

    if action == "confirm_order":
        updated_card = (
            f"{base_text}\n\n"
            f"────────────────────\n"
            f"✅ PAYMENT CONFIRMED by {admin_name} at {time_str}"
        )

        try:
            # Edit the message in the forum group and remove buttons
            await context.bot.edit_message_text(
                chat_id=msg.chat.id,
                message_id=msg.message_id,
                text=updated_card,
                reply_markup=None
            )
        except Exception as e:
            logging.error(f"Failed to edit admin card: {e}")

        # Send official receipt DM to customer
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🌸 *Piece & Petal — ការទូទាត់ប្រាក់ត្រូវបានផ្ទៀងផ្ទាត់!* 🎉\n\n"
                    "ការទូទាត់ប្រាក់ (Payment) របស់បងទទួលបានជោគជ័យហើយ។\n"
                    "ក្រុមការងារកំពុងរៀបចំវេចខ្ចប់ទំនិញជូនបង និងទាក់ទងតាមទូរស័ព្ទមុនពេលដឹកជញ្ជូនណា៎ ✨"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Failed to notify customer {user_id}: {e}")

    elif action == "reject_order":
        updated_card = (
            f"{base_text}\n\n"
            f"────────────────────\n"
            f"❌ PAYMENT REJECTED by {admin_name} at {time_str}"
        )

        try:
            await context.bot.edit_message_text(
                chat_id=msg.chat.id,
                message_id=msg.message_id,
                text=updated_card,
                reply_markup=None
            )
        except Exception as e:
            logging.error(f"Failed to edit admin card: {e}")

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "⚠️ *Piece & Petal — ការទូទាត់ប្រាក់មិនទាន់ត្រឹមត្រូវ*\n\n"
                    "សូមអភ័យទោសបង ក្រុមការងារមិនទាន់អាចផ្ទៀងផ្ទាត់ Slip ការផ្ទេរប្រាក់របស់បងបាននៅឡើយទេ។\n"
                    "សូមបងផ្ញើរូបភាព Slip ចូលមកក្នុង Chat នេះម្តងទៀត ដើម្បីឱ្យក្រុមការងារជួយពិនិត្យជូនណា៎ 🙏"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Failed to notify customer {user_id}: {e}")

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
        message_id=update.message.message_id
    )

async def reply_from_admin_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id != ADMIN_GROUP_ID:
        return
    if not update.message:
        return
    if update.effective_user and update.effective_user.is_bot:
        return

    thread_id = update.message.message_thread_id
    if not thread_id:
        return

    customer_id = thread_to_user.get(thread_id)
    if not customer_id:
        await update.message.reply_text("⚠️ Mapping lost after restart. Ask customer to send a message.")
        return

    try:
        await context.bot.copy_message(
            chat_id=customer_id,
            from_chat_id=ADMIN_GROUP_ID,
            message_id=update.message.message_id
        )
    except Exception as e:
        logging.error(f"Failed to copy message: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global tg_app
    tg_app = ApplicationBuilder().token(BOT_TOKEN).build()

    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CallbackQueryHandler(handle_order_actions, pattern="^(confirm_order|reject_order):"))
    tg_app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, forward_to_admin_topic))
    tg_app.add_handler(MessageHandler(filters.Chat(ADMIN_GROUP_ID) & ~filters.COMMAND, reply_from_admin_topic))

    await tg_app.initialize()
    await tg_app.start()

    webhook_url = f"{RENDER_URL}/telegram-webhook"
    await tg_app.bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )
    logging.info(f"Telegram Webhook active at: {webhook_url}")

    yield

    await tg_app.bot.delete_webhook()
    await tg_app.stop()
    await tg_app.shutdown()

api = FastAPI(lifespan=lifespan)

if os.path.exists("templates"):
    api.mount("/static", StaticFiles(directory="templates"), name="static")

@api.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    try:
        req_data = await request.json()
        update = Update.de_json(req_data, tg_app.bot)
        asyncio.create_task(tg_app.process_update(update))
    except Exception as e:
        logging.error(f"Error handling webhook: {e}")
    return Response(status_code=200)

@api.api_route("/", methods=["GET", "HEAD"])
@api.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    return JSONResponse({"status": "ok", "app": "Piece & Petal Combined Service"})

@api.get("/shop", response_class=HTMLResponse)
def serve_shop():
    if os.path.exists("templates/index.html"):
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>templates/index.html not found.</h3>"

@api.get("/api/products")
async def get_products():
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(CSV_EXPORT_URL)
            resp.raise_for_status()

        f = io.StringIO(resp.text)
        reader = csv.DictReader(f)
        items = []

        for row in reader:
            clean_row = {(k.strip().lower() if k else ''): (v.strip() if v else '') for k, v in row.items()}
            prod_id = clean_row.get("id")
            title = clean_row.get("title")
            if not prod_id or not title:
                continue

            raw_price = clean_row.get("price", "0")
            try:
                price_val = float(str(raw_price).replace("$", "").strip())
            except ValueError:
                price_val = 0.0

            items.append({
                "id": prod_id,
                "title": title,
                "brand": clean_row.get("brand", "Tokyo Sourcing"),
                "category": clean_row.get("category", "General"),
                "price": price_val,
                "availability": clean_row.get("availability", "In Stock"),
                "size": clean_row.get("size", "-"),
                "image": clean_row.get("image", ""),
                "tag": clean_row.get("tag", ""),
                "description": clean_row.get("description", "Authentic Japanese product curated directly from Tokyo.")
            })
        return items
    except Exception as e:
        logging.error(f"Failed to fetch products: {e}")
        return []

# Endpoint for "Ask about this product" button
@api.post("/api/inquire")
async def inquire(request: Request):
    data = await request.json()
    raw_user_id = data.get("user_id")
    product_title = data.get("product_title", "Unknown item")
    customer_name = data.get("customer_name", "Customer")

    user_id = int(raw_user_id) if raw_user_id else None
    if not user_id:
        return {"status": "ignored"}

    thread_id = user_to_thread.get(user_id)
    if not thread_id:
        try:
            topic = await tg_app.bot.create_forum_topic(chat_id=ADMIN_GROUP_ID, name=f"🌸 {customer_name[:18]} ({user_id})")
            thread_id = topic.message_thread_id
            user_to_thread[user_id] = thread_id
            thread_to_user[thread_id] = user_id
        except Exception as e:
            logging.error(f"Topic creation failed during inquiry: {e}")

    inquiry_msg = (
        f"🙋 *PRODUCT INQUIRY*\n"
        f"────────────────────\n"
        f"Customer is asking about:\n"
        f"👉 *{product_title}*\n\n"
        f"💬 Reply directly in this topic to chat with them."
    )

    try:
        if thread_id:
            await tg_app.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                message_thread_id=thread_id,
                text=inquiry_msg,
                parse_mode="Markdown"
            )
            await tg_app.bot.send_message(
                chat_id=user_id,
                text=f"🌸 បងចង់សាកសួរពី *{product_title}* មែនទេ? សូមបងផ្ញើសំណួរមកទីនេះ ក្រុមការងារនឹងឆ្លើយតបជូនភ្លាមៗណា៎ ✨",
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.error(f"Error routing inquiry: {e}")

    return {"status": "ok"}

@api.post("/api/checkout")
async def checkout(request: Request):
    data = await request.json()
    raw_user_id = data.get("user_id")
    order_summary = data.get("summary", "")
    customer_name = data.get("customer_name", "Guest")
    phone = data.get("phone", "N/A")
    address = data.get("address", "N/A")
    total = data.get("total", 0.0)

    user_id = int(raw_user_id) if raw_user_id else None
    thread_id = None

    if user_id:
        save_customer(user_id)
        if user_id in user_to_thread:
            thread_id = user_to_thread[user_id]
        else:
            try:
                topic = await tg_app.bot.create_forum_topic(
                    chat_id=ADMIN_GROUP_ID,
                    name=f"🌸 {customer_name[:18]} ({user_id})"
                )
                thread_id = topic.message_thread_id
                user_to_thread[user_id] = thread_id
                thread_to_user[thread_id] = user_id
            except Exception as e:
                logging.error(f"Error creating topic: {e}")

    if ORDER_WEBHOOK_URL:
        try:
            order_payload = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "customer_name": customer_name,
                "user_id": str(user_id or "Direct Web"),
                "phone": phone,
                "address": address,
                "total": total,
                "summary": order_summary
            }
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                await client.post(ORDER_WEBHOOK_URL, json=order_payload)
        except Exception as e:
            logging.error(f"Google Sheet logging error: {repr(e)}")

    keyboard = None
    if user_id:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Confirm Payment", callback_data=f"confirm_order:{user_id}"),
                InlineKeyboardButton("❌ Invalid / Reject", callback_data=f"reject_order:{user_id}")
            ]
        ])

    order_card = (
        f"🛍️ *NEW IN-APP ORDER SUBMITTED*\n"
        f"────────────────────\n"
        f"• Customer: {customer_name}\n"
        f"• Telegram ID: `{user_id if user_id else 'Direct Web'}`\n"
        f"• Phone: `{phone}`\n"
        f"• Location: {address}\n"
        f"• Total: *${total:.2f}*\n\n"
        f"*Items:*\n{order_summary}\n"
        f"────────────────────\n"
        f"💬 Tap below to confirm or reject payment:"
    )

    try:
        if thread_id:
            await tg_app.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                message_thread_id=thread_id,
                text=order_card,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            await tg_app.bot.send_message(
                chat_id=user_id,
                text=(
                    f"🌸 *Piece & Petal Order Received!*\n\n"
                    f"អរគុណបង {customer_name}! ក្រុមការងារបានទទួលការបញ្ជាទិញតម្លៃ *${total:.2f}* រួចរាល់ហើយ។\n\n"
                    f"យើងខ្ញុំកំពុងពិនិត្យការទូទាត់ប្រាក់ (Payment Confirmation) ហើយនឹងឆ្លើយតបបញ្ជាក់ជូនបងនៅទីនេះភ្លាមៗណា៎ ✨"
                ),
                parse_mode="Markdown"
            )
        else:
            await tg_app.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=order_card,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    except Exception as e:
        logging.error(f"Error sending order alert: {e}")

    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run("bot:api", host="0.0.0.0", port=PORT, log_level="info")
