import asyncio
import csv
from contextlib import asynccontextmanager
from datetime import datetime
import io
import json
import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import httpx
import uvicorn
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.environ.get("ADMIN_GROUP_ID", 0))
PORT = int(os.environ.get("PORT", 8000))
RENDER_URL = os.environ.get(
    "RENDER_EXTERNAL_URL", "https://piecenpetal-bot.onrender.com"
).rstrip("/")

SHEET_ID = os.environ.get(
    "GOOGLE_SHEET_ID", "1oBJ0mo_qWO6fRo6t8YfdOG-_EaUsDwhLP5mISOw-hrE"
)
CSV_EXPORT_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
)
ORDER_WEBHOOK_URL = os.environ.get("ORDER_WEBHOOK_URL", "")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
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


# Helpers & Handlers
async def ensure_user_topic(user, context: ContextTypes.DEFAULT_TYPE) -> int:
  user_id = user.id
  save_customer(user_id)

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


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.effective_chat or update.effective_chat.id != ADMIN_GROUP_ID:
    return

  msg_text = " ".join(context.args)
  if not msg_text:
    await update.message.reply_text(
        "Usage: `/broadcast Hello everyone! Drop 02 is now live!`",
        parse_mode="Markdown",
    )
    return

  customers = get_all_customers()
  sent = 0
  for uid in customers:
    try:
      await context.bot.send_message(
          chat_id=uid, text=msg_text, parse_mode="Markdown"
      )
      sent += 1
      await asyncio.sleep(0.05)
    except Exception:
      pass

  await update.message.reply_text(
      f"📢 Broadcast sent to *{sent}/{len(customers)}* customers.",
      parse_mode="Markdown",
  )


async def handle_order_actions(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  """Handles one-tap order confirmation or rejection from the admin forum."""
  query = update.callback_query
  await query.answer()

  data = query.data.split(":")
  action = data[0]
  user_id = int(data[1])
  admin_name = update.effective_user.first_name or "Admin"

  original_text = query.message.text

  if action == "confirm_order":
    updated_card = (
        f"{original_text}\n\n"
        f"────────────────────\n"
        f"✅ *PAYMENT CONFIRMED* by {admin_name} on"
        f" {datetime.now().strftime('%H:%M')}"
    )
    await query.edit_message_text(
        text=updated_card, parse_mode="Markdown", reply_markup=None
    )

    # Notify customer directly
    try:
      await context.bot.send_message(
          chat_id=user_id,
          text=(
              "🌸 *Piece & Petal — ការទូទាត់ប្រាក់ត្រូវបានផ្ទៀងផ្ទាត់!* 🎉\n\n"
              "ការទូទាត់ប្រាក់ (Payment) របស់បងទទួលបានជោគជ័យហើយ។\n"
              "ក្រុមការងារកំពុងរៀបចំវេចខ្ចប់ទំនិញជូនបង"
              " និងទាក់ទងតាមទូរស័ព្ទមុនពេលដឹកជញ្ជូនណា៎ ✨"
          ),
          parse_mode="Markdown",
      )
    except Exception as e:
      logging.error(f"Failed to notify customer {user_id}: {e}")

  elif action == "reject_order":
    updated_card = (
        f"{original_text}\n\n"
        f"────────────────────\n"
        f"❌ *PAYMENT REJECTED/INVALID* by {admin_name} on"
        f" {datetime.now().strftime('%H:%M')}"
    )
    await query.edit_message_text(
        text=updated_card, parse_mode="Markdown", reply_markup=None
    )

    try:
      await context.bot.send_message(
          chat_id=user_id,
          text=(
              "⚠️ *Piece & Petal — ការទូទាត់ប្រាក់មិនទាន់ត្រឹមត្រូវ*\n\n"
              "សូមអភ័យទោសបង ក្រុមការងារមិនទាន់អាចផ្ទៀងផ្ទាត់ Slip"
              " ការផ្ទេរប្រាក់របស់បងបាននៅឡើយទេ។\n"
              "សូមបងផ្ញើ Screenshot ឬរូបភាព Slip ចូលមកក្នុង Chat"
              " នេះម្តងទៀតដើម្បីឱ្យក្រុមការងារជួយពិនិត្យជូនណា៎ 🙏"
          ),
          parse_mode="Markdown",
      )
    except Exception as e:
      logging.error(f"Failed to notify customer {user_id}: {e}")


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


@asynccontextmanager
async def lifespan(app: FastAPI):
  global tg_app
  tg_app = ApplicationBuilder().token(BOT_TOKEN).build()

  tg_app.add_handler(CommandHandler("start", start))
  tg_app.add_handler(CommandHandler("broadcast", broadcast))
  tg_app.add_handler(
      CallbackQueryHandler(
          handle_order_actions, pattern="^(confirm_order|reject_order):"
      )
  )
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

  webhook_url = f"{RENDER_URL}/telegram-webhook"
  await tg_app.bot.set_webhook(
      url=webhook_url,
      drop_pending_updates=True,
      allowed_updates=Update.ALL_TYPES,
  )
  logging.info(f"Telegram Webhook set to: {webhook_url}")

  yield

  logging.info("Shutting down bot...")
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
    await tg_app.process_update(update)
    return Response(status_code=200)
  except Exception as e:
    logging.error(f"Error processing webhook update: {e}")
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
    save_customer(user_id)
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

  # 1. Sync to Google Sheets
  if ORDER_WEBHOOK_URL:
    try:
      order_payload = {
          "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "customer_name": customer_name,
          "user_id": str(user_id or "Direct Web"),
          "phone": phone,
          "address": address,
          "total": total,
          "summary": order_summary,
      }
      async with httpx.AsyncClient(
          timeout=15.0, follow_redirects=True
      ) as client:
        await client.post(ORDER_WEBHOOK_URL, json=order_payload)
    except Exception as e:
      logging.error(f"Failed to sync order to Google Sheets: {repr(e)}")

  # 2. Interactive Admin Buttons
  keyboard = None
  if user_id:
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Confirm Payment", callback_data=f"confirm_order:{user_id}"
            ),
            InlineKeyboardButton(
                "❌ Invalid / Reject", callback_data=f"reject_order:{user_id}"
            ),
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
          reply_markup=keyboard,
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
          reply_markup=keyboard,
      )
  except Exception as e:
    logging.error(f"Error sending order alert: {e}")

  return {"status": "success"}


if __name__ == "__main__":
  uvicorn.run("bot:api", host="0.0.0.0", port=PORT, log_level="info")
