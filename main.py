import telebot
from telebot import types
import json

BOT_TOKEN = "8198002913:AAH_yu2FEag3GMeHLYDy-s7x-1jzjHLxrrU"
ADMIN_ID = 5815294733
CARD_NUMBER = "9860 6067 5024 7151"

bot = telebot.TeleBot(BOT_TOKEN)

# ---------------- Data ----------------
users = {}   # {user_id: {"balance":0, "almaz":[], "referrals":[], "used_referral":False}}
orders = {}  # {user_id: [{"order_id":..., "ff_id":..., "package":..., "status":...}]}
referral_links = {}  # {ref_code: inviter_user_id}

# ---------------- Voucher paketlari ----------------
voucher_packages = {
    "💳 Haftalik Lite [90💎] – 9,000 so‘m": 9000,
    "💳 Haftalik [450💎] – 21,000 so‘m": 21000,
    "💳 Oylik [2600💎] – 135,000 so‘m": 135000,
    "💎 LvL Up [1270💎] – 67,000 so‘m": 67000
}

# ---------------- JSON bilan saqlash va yuklash ----------------
def save_data():
    with open("users.json", "w") as f:
        json.dump(users, f)
    with open("orders.json", "w") as f:
        json.dump(orders, f)
    with open("referral.json", "w") as f:
        json.dump(referral_links, f)

def load_data():
    global users, orders, referral_links
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
        with open("orders.json", "r") as f:
            orders = json.load(f)
        with open("referral.json", "r") as f:
            referral_links = json.load(f)
    except FileNotFoundError:
        users, orders, referral_links = {}, {}, {}

load_data()

# ---------------- menu ----------------
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💎 Almaz sotib olish", "💎 Voucher sotib olish")
    markup.add("💳 Hisob to‘ldirish", "💳 Balance")
    markup.add("🛒 Mening almazim")
    markup.add("🔗 Referral olish")
    if user_id == ADMIN_ID:
        markup.add("⚙ Sozlamalar")
    return markup

# ---------------- start ----------------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    ref_code = None
    # Agar /start bilan referral keldi
    if len(message.text.split()) > 1:
        ref_code = message.text.split()[1]

    if user_id not in users:
        users[user_id] = {"balance":0, "almaz":[], "referrals":[], "used_referral":False}

        # Referral ishlashi
        if ref_code and ref_code in referral_links:
            inviter_id = referral_links[ref_code]
            if inviter_id != user_id:
                users[inviter_id]["balance"] += 1000
                users[inviter_id]["referrals"].append(user_id)
                users[user_id]["used_referral"] = True
                save_data()
                bot.send_message(inviter_id, f"🎉 Sizning referralingiz tizimga qo'shildi! Sizga 1,000 so‘m berildi.")

    save_data()
    bot.send_message(user_id, "Assalomu alekum! Free Fire almaz servisga hush kelibsiz:", reply_markup=main_menu(user_id))

# ---------------- Referral link ----------------
@bot.message_handler(func=lambda m: m.text == "🔗 Referral olish")
def referral_link(message):
    user_id = message.chat.id
    if user_id not in referral_links.values():
        ref_code = str(user_id)
        referral_links[ref_code] = user_id
        save_data()
    else:
        ref_code = next(k for k,v in referral_links.items() if v==user_id)
    
    bot.send_message(user_id, f"🔗 Sizning referral linkingiz:\n\n"
                              f"https://t.me/freefire_almaz_serverbot?start={ref_code}\n\n"
                              f"🎁 Har bir referral tizimga kirganda, sizga 1,000 so‘m beriladi.\n"
                              f"💡 Linkni do‘stlaringiz bilan ulashing!")

# ---------------- Balans ko‘rsatish ----------------
@bot.message_handler(func=lambda m: m.text == "💳 Balance")
def show_balance(message):
    user_id = message.chat.id
    if user_id not in users:
        users[user_id] = {"balance":0, "almaz":[], "referrals":[], "used_referral":False}
    bot.send_message(user_id, f"💰 Sizning balansingiz: {users[user_id]['balance']} so‘m")

# ---------------- Mening almazim ----------------
@bot.message_handler(func=lambda m: m.text == "🛒 Mening almazim")
def my_orders(message):
    user_id = message.chat.id
    if user_id not in orders or not orders[user_id]:
        bot.send_message(user_id, "Sizda buyurtmalar yo‘q.")
        return
    text = "📋 Sizning buyurtmalaringiz:\n\n"
    for o in orders[user_id]:
        text += f"🆔 Order ID: {o['order_id']}\nPaket: {o['package']}\nStatus: {o['status']}\n\n"
    bot.send_message(user_id, text)

# ---------------- Ortga qaytish ----------------
@bot.message_handler(func=lambda m: m.text == "⬅️ Ortga qaytish")
def back_to_menu(message):
    bot.send_message(message.chat.id, "⬅️ Asosiy menyuga qaytdingiz.", reply_markup=main_menu(message.chat.id))

# ---------------- Voucher menyusi ----------------
@bot.message_handler(func=lambda m: m.text == "💎 Voucher sotib olish")
def voucher_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for pkg in voucher_packages.keys():
        markup.add(pkg)
    markup.add("⬅️ Ortga qaytish")
    bot.send_message(message.chat.id, "Qaysi voucher paketini sotib olasiz?", reply_markup=markup)

# ---------------- Voucher sotib olish ----------------
@bot.message_handler(func=lambda m: m.text in voucher_packages.keys())
def buy_voucher(message):
    user_id = message.chat.id
    if user_id not in users:
        users[user_id] = {"balance":0, "almaz":[], "referrals":[], "used_referral":False}
    package_name = message.text
    price = voucher_packages[package_name]

    if users[user_id]["balance"] < price:
        bot.send_message(user_id, f"❌ Balansingiz yetarli emas ({price} so‘m kerak).")
        return

    msg = bot.send_message(user_id, "🆔 Free Fire IDingizni kiriting:")
    bot.register_next_step_handler(msg, lambda m: process_voucher_order(m, package_name, price))

def process_voucher_order(message, package_name, price):
    user_id = message.chat.id
    ff_id = message.text.strip()

    users[user_id]["balance"] -= price
    if user_id not in orders:
        orders[user_id] = []

    order_id = len(orders[user_id]) + 1
    orders[user_id].append({
        "order_id": order_id,
        "ff_id": ff_id,
        "package": package_name,
        "status": "Jarayonda"
    })
    save_data()

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{user_id}_{order_id}"))
    markup.add(types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{user_id}_{order_id}"))

    try:
        bot.send_message(ADMIN_ID, f"💳 Voucher buyurtma:\n🆔 UserID: {user_id}\nFree Fire ID: {ff_id}\nPaket: {package_name}\nNarx: {price} so‘m\nStatus: Jarayonda", reply_markup=markup)
        bot.send_message(user_id, f"✅ Voucher buyurtma qabul qilindi!\n{package_name}\nStatus: Jarayonda")
    except:
        pass

# ---------------- Almaz sotib olish ----------------
@bot.message_handler(func=lambda m: m.text == "💎 Almaz sotib olish")
def almaz_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        "💎 105 Almaz – 13,250 so‘m", "💎 326 Almaz – 40,000 so‘m",
        "💎 546 Almaz – 65,000 so‘m", "💎 1113 Almaz – 131,250 so‘m",
        "💎 2398 Almaz – 262,500 so‘m", "💎 6160 Almaz – 650,000 so‘m"
    )
    markup.add("⬅️ Ortga qaytish")
    bot.send_message(message.chat.id, "Qaysi paketni sotib olasiz?", reply_markup=markup)

# ---------------- Hisob to‘ldirish ----------------
@bot.message_handler(func=lambda m: m.text == "💳 Hisob to‘ldirish")
def deposit(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("⬅️ Ortga qaytish")
    msg = bot.send_message(message.chat.id, "💳 Summani kiriting (10,000 – 10,000,000 so‘m):", reply_markup=markup)
    bot.register_next_step_handler(msg, process_deposit)

def process_deposit(message):
    if message.text == "⬅️ Ortga qaytish":
        bot.send_message(message.chat.id, "⬅️ Asosiy menyuga qaytdingiz.", reply_markup=main_menu(message.chat.id))
        return
    try:
        amount = int(message.text)
        if amount < 10000 or amount > 10000000:
            bot.send_message(message.chat.id, "❌ Noto‘g‘ri summa. Qayta urinib ko‘ring.")
            deposit(message)
            return
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ To‘lov qildim", callback_data=f"paid_{amount}"))
        bot.send_message(message.chat.id, f"💳 To‘lov uchun karta:\n{CARD_NUMBER}\n💰 Summa: {amount} so‘m", reply_markup=markup)
    except:
        bot.send_message(message.chat.id, "❌ Iltimos, faqat raqam kiriting.")
        deposit(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def paid_callback(call):
    amount = int(call.data.split("_")[1])
    bot.send_message(call.message.chat.id, "✅ To‘lovni tasdiqlash uchun chek rasm yuboring:")
    bot.register_next_step_handler(call.message, lambda m: send_check(m, amount))

def send_check(message, amount):
    if not message.photo:
        bot.send_message(message.chat.id, "❌ Faqat rasm yuboring (chek skrinshot).")
        return
    file_id = message.photo[-1].file_id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_deposit_{message.chat.id}_{amount}"))
    markup.add(types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_deposit_{message.chat.id}_{amount}"))
    bot.send_photo(ADMIN_ID, file_id, caption=f"💳 Yangi to‘lov:\n🆔 UserID: {message.chat.id}\n💰 Summa: {amount} so‘m", reply_markup=markup)
    bot.send_message(message.chat.id, "✅ Chek yuborildi, admin tasdiqlashini kuting.")

# ---------------- Admin tasdiqlash / rad etish ----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_deposit") or call.data.startswith("reject_deposit"))
def confirm_reject_deposit(call):
    parts = call.data.split("_")
    action, user_id, amount = parts[0]+"_"+parts[1], int(parts[2]), int(parts[3])
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Siz admin emassiz!")
        return
    if action == "confirm_deposit":
        users[user_id]["balance"] += amount
        save_data()
        bot.send_message(user_id, f"✅ To‘lov tasdiqlandi! {amount} so‘m balansingizga qo‘shildi.")
        bot.send_message(ADMIN_ID, f"✅ UserID {user_id} balansiga {amount} so‘m qo‘shildi.")
    else:
        bot.send_message(user_id, "❌ To‘lov rad etildi. Qayta urinib ko‘ring.")
        bot.send_message(ADMIN_ID, f"❌ UserID {user_id} to‘lovi rad etildi.")

# ---------------- Admin menyusi ----------------
@bot.message_handler(func=lambda m: m.text == "⚙ Sozlamalar" and m.chat.id == ADMIN_ID)
def settings(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📰 Reklama yuborish", "📋 Buyurtmalar")
    markup.add("⬅️ Ortga qaytish")
    bot.send_message(message.chat.id, "⚙ Sozlamalar menyusi:", reply_markup=markup)

# ---------------- Reklama yuborish ----------------
@bot.message_handler(func=lambda m: m.text == "📰 Reklama yuborish" and m.chat.id == ADMIN_ID)
def send_news(message):
    msg = bot.send_message(message.chat.id, "📰 Reklama matnini yoki rasm + matn yuboring:")
    bot.register_next_step_handler(msg, process_news)

def process_news(message):
    for user_id in users.keys():
        try:
            if message.photo:
                bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            else:
                bot.send_message(user_id, message.text)
        except:
            pass
    bot.send_message(ADMIN_ID, "✅ Reklama yuborildi!")

# ---------------- Buyurtmalarni ko‘rish (admin) ----------------
@bot.message_handler(func=lambda m: m.text == "📋 Buyurtmalar" and m.chat.id == ADMIN_ID)
def show_orders(message):
    if not orders:
        bot.send_message(ADMIN_ID, "📋 Hali buyurtmalar yo‘q.")
        return
    for user_id, user_orders in orders.items():
        for o in user_orders:
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_admin_{user_id}_{o['order_id']}"),
                types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_admin_{user_id}_{o['order_id']}")
            )
            bot.send_message(
                ADMIN_ID,
                f"👤 UserID: {user_id}\n🆔 Order ID: {o['order_id']}\nFree Fire ID: {o.get('ff_id','')}\nPaket: {o['package']}\nStatus: {o['status']}",
                reply_markup=markup
            )

# ---------------- Admin tasdiqlash / rad etish buyurtma ----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_admin") or call.data.startswith("reject_admin"))
def admin_confirm_reject(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Siz admin emassiz!")
        return

    parts = call.data.split("_")
    action = parts[0]
    user_id = int(parts[2])
    order_id = int(parts[3])

    order = next((o for o in orders[user_id] if o["order_id"] == order_id), None)
    if not order: return
    if order["status"] in ["Bajarildi", "Rad etildi"]:
        bot.answer_callback_query(call.id, "❌ Bu buyurtma allaqachon tasdiqlangan yoki rad etilgan!")
        return

    price_text = order["package"].split("–")[-1].replace("so‘m","").replace(",","").strip()
    price = int(price_text)

    if action == "confirm":
        order["status"] = "Bajarildi"
        if "almaz" not in users[user_id]:
            users[user_id]["almaz"] = []
        users[user_id]["almaz"].append(order["package"])
        save_data()
        bot.send_message(user_id, f"✅ Buyurtmangiz bajarildi! {order['package']} sizning almazingizga tushdi.")
        bot.answer_callback_query(call.id, "✅ Buyurtmani tasdiqladingiz.")
    else:
        order["status"] = "Rad etildi"
        users[user_id]["balance"] += price
        save_data()
        bot.send_message(user_id, f"❌ Buyurtmangiz rad etildi. {price} so‘m balansingizga qaytarildi.")
        bot.answer_callback_query(call.id, "❌ Buyurtmani rad etdiniz.")

# ---------------- Bot start ----------------
print("🤖 Bot ishga tushdi...")
bot.polling(none_stop=True)
