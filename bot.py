import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Existing FastAPI instance
api = FastAPI()

# Sample catalog data (can be replaced by Google Sheets or SQLite later)
PRODUCTS = [
    {
        "id": "p1",
        "title": "FANCL Good Choice 20s (30 packs)",
        "category": "Supplements",
        "price": 28.00,
        "image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&q=80",
        "tag": "Daily Vitality"
    },
    {
        "id": "p2",
        "title": "FANCL Good Choice 30s (30 packs)",
        "category": "Supplements",
        "price": 34.00,
        "image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&q=80",
        "tag": "Anti-Aging & Collagen"
    },
    {
        "id": "p3",
        "title": "DHC Collagen (60 Days)",
        "category": "Supplements",
        "price": 15.00,
        "image": "https://images.unsplash.com/photo-1550572017-ed200f5e6343?w=500&q=80",
        "tag": "Firmness & Glow"
    },
    {
        "id": "p4",
        "title": "Quality 1st Derma Laser Super VC100",
        "category": "Skincare",
        "price": 12.50,
        "image": "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=500&q=80",
        "tag": "Pore Tightening"
    },
    {
        "id": "p5",
        "title": "Keana Nadeshiko Rice Mask (10 pcs)",
        "category": "Skincare",
        "price": 14.00,
        "image": "https://images.unsplash.com/photo-1608248597359-bb51da9c9689?w=500&q=80",
        "tag": "Hydration"
    }
]

@api.get("/api/products")
def get_products():
    return PRODUCTS

@api.post("/api/checkout")
async def checkout(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    order_summary = data.get("summary")

    # Format order alert for Admin Group Topic
    order_card = (
        f"🛍️ *NEW IN-APP ORDER SUBMITTED*\n"
        f"────────────────────\n"
        f"• Customer: {data.get('customer_name', 'Guest')}\n"
        f"• Phone: `{data.get('phone')}`\n"
        f"• Location: {data.get('address')}\n"
        f"• Total: *${data.get('total'):.2f}*\n\n"
        f"*Items:*\n{order_summary}\n"
        f"────────────────────\n"
        f"⚠️ *Action:* Check ABA Merchant app for payment confirmation before packing."
    )

    # Route order into customer's topic thread if user_id exists
    thread_id = user_to_thread.get(user_id)
    if thread_id:
        await bot_instance.send_message(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=thread_id,
            text=order_card,
            parse_mode="Markdown"
        )
    else:
        # Fallback to General topic
        await bot_instance.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=order_card,
            parse_mode="Markdown"
        )

    return {"status": "success"}

@api.get("/shop", response_class=HTMLResponse)
def serve_shop():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()
