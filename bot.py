import asyncio
import csv
from contextlib import asynccontextmanager
import io
import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
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

SHEET_ID = os.environ.get(
    "GOOGLE_SHEET_ID", "1oBJ0mo_qWO6fRo6t8YfdOG-_EaUsDwhLP5mISOw-hrE"
)
CSV_EXPORT_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

user_to_thread = {}
thread_to_user = {}

tg_app = None


# Handlers
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
      "Piece & Petal មានលក់ Supplement, Skincare, Cosmetics,"
      " និងផលិតផលផ្សេងៗនាំចូលពីជប៉ុន\n\n"
      "ឥវ៉ាន់ធានាសុទ្ធពីជប៉ុន 100% អ្នកលក់ទៅយកផ្ទាល់ពីហាង\n\n"
      "បងៗចង់ស្វែងរក ឬចង់ទិញផលិតផលអ្វី អាចទម្លាក់សារមក"
      " ក្រុមការងារនឹងឆ្លើយតបជូនភ្លាមៗណា៎ 😍"
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


async def forward_to_admin_topic(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
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


async def reply_from_admin_topic(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
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
    await update.message.reply_text(
        "⚠️ *Warning:* Mapping lost after server restart. Ask customer to send"
        " a message in bot.",
        parse_mode="Markdown",
    )
    return

  try:
    await context.bot.copy_message(
        chat_id=customer_id,
        from_chat_id=ADMIN_GROUP_ID,
        message_id=update.message.message_id,
    )
  except Exception as e:
    logging.error(f"Failed to copy to customer {customer_id}: {e}")
    await update.message.reply_text(f"❌ Failed to deliver: {e}")


# Lifespan context to cleanly start & stop bot without ghost instances
@asynccontextmanager
async def lifespan(app: FastAPI):
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
  # drop_pending_updates prevents backlog race conditions
  await tg_app.updater.start_polling(drop_pending_updates=True)
  logging.info("Telegram Bot successfully polling.")

  yield

  logging.info("Shutting down bot polling...")
  if tg_app.updater.running:
    await tg_app.updater.stop()
  await tg_app.stop()
  await tg_app.shutdown()


api = FastAPI(lifespan=lifespan)


# Responds to both GET and HEAD immediately for Render health checker
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
      clean_row = {
          (k.strip().lower() if k else ""): (v.strip() if v else "")
          for k, v in row.items()
      }
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
          "category": clean_row.get("category", "General"),
          "price": price_val,
          "image": clean_row.get("image", ""),
          "tag": clean_row.get("tag", ""),
      })
    return items
  except Exception as e:
    logging.error(f"Failed to fetch live products from Google Sheets: {e}")
    return []


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
    if user_id in user_to_thread:
      thread_id = user_to_thread[user_id]
    else:
      try:
        topic = await tg_app.bot.create_forum_topic(
            chat_id=ADMIN_GROUP_ID,
            name=f"🌸 {customer_name[:18]} ({user_id})",
        )
        thread_id = topic.message_thread_id
        user_to_thread[user_id] = thread_id
        thread_to_user[thread_id] = user_id
      except Exception as e:
        logging.error(f"Error creating topic during checkout: {e}")

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
      f"💬 *Action:* Reply directly in this topic to message the customer!"
  )

  try:
    if thread_id:
      await tg_app.bot.send_message(
          chat_id=ADMIN_GROUP_ID,
          message_thread_id=thread_id,
          text=order_card,
          parse_mode="Markdown",
      )
      await tg_app.bot.send_message(
          chat_id=user_id,
          text=(
              "🌸 *Piece & Petal Order Received!*\n\n"
              f"អរគុណបង {customer_name}! ក្រុមការងារបានទទួលការបញ្ជាទិញតម្លៃ"
              f" *${total:.2f}* រួចរាល់ហើយ។\n\n"
              "យើងខ្ញុំកំពុងពិនិត្យការទូទាត់ប្រាក់ (Payment Confirmation) "
              "ហើយនឹងឆ្លើយតបបញ្ជាក់ជូនបងនៅទីនេះភ្លាមៗណា៎ ✨"
          ),
          parse_mode="Markdown",
      )
    else:
      await tg_app.bot.send_message(
          chat_id=ADMIN_GROUP_ID,
          text=order_card,
          parse_mode="Markdown",
      )
  except Exception as e:
    logging.error(f"Error sending order alert: {e}")

  return {"status": "success"}


if __name__ == "__main__":
  uvicorn.run("bot:api", host="0.0.0.0", port=PORT, log_level="info")
