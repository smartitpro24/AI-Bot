import requests
import asyncio
from telegram import Bot

# =========================
# CONFIG
# =========================
BOT_TOKEN = "86xxxxxxxxxxxxxxxxxxxxxxxxx"
CHAT_ID = "5xxxxxxxxxxxxxxx"

TARGET_PRICE = 126.6
CHECK_INTERVAL = 20   # seconds

# =========================
bot = Bot(token=BOT_TOKEN)

# =========================
# GET FILTERED PRICE
# =========================
def get_price():
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    
    data = {
        "asset": "USDT",
        "fiat": "BDT",
        "tradeType": "BUY",
        "page": 1,
        "rows": 20 or 50
    }

    try:
        res = requests.post(url, json=data)
        result = res.json()

        valid_ads = []

        for ad in result['data']:
            adv = ad['adv']
            advertiser = ad['advertiser']

            price = float(adv['price'])

            # =========================
            # ✅ Payment Filter (Bkash/Nagad)
            # =========================
            methods = [m['identifier'].lower() for m in adv['tradeMethods']]

            if not any(m in ["bkash", "nagad"] for m in methods):
                continue

            # =========================
            # ✅ Minimum Limit Filter (>=500 BDT)
            # =========================
            min_limit = float(adv['minSingleTransAmount'])

            if min_limit < 500:
                continue

            # =========================
            # OPTIONAL: Seller Info
            # =========================
            seller_name = advertiser['nickName']

            valid_ads.append({
                "price": price,
                "seller": seller_name,
                "limit": min_limit,
                "methods": methods
            })

        if valid_ads:
            # lowest price ad select
            best = min(valid_ads, key=lambda x: x['price'])
            return best
        else:
            return None

    except Exception as e:
        print("Error:", e)
        return None


# =========================
# MAIN LOOP
# =========================
async def main():
    while True:
        ad = get_price()

        if ad:
            print("Best Price:", ad['price'])

            if ad['price'] <= TARGET_PRICE:
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"""
🔥 P2P Alert!

💰 Price: {ad['price']} BDT
👤 Seller: {ad['seller']}
💳 Payment: Bkash/Nagad
📉 Min Limit: {ad['limit']} BDT

🎯 Target: {TARGET_PRICE}
"""
                )

                # anti-spam delay
                await asyncio.sleep(300)

        else:
            print("No valid ads found")

        await asyncio.sleep(CHECK_INTERVAL)


# =========================
# RUN BOT
# =========================
asyncio.run(main())
