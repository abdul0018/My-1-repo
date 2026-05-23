import logging
import sqlite3
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)

# ==================== SOZLAMALAR ====================
BOT_TOKEN = "8790387724:AAE_yu0FTWkZf7oB1KLYyOorzfVoihGPHiY"  # <-- YANGI TOKEN QOYING
ADMIN_ID = 1196260972        # <-- O'zingizning Telegram ID (@userinfobot dan oling)
ADMIN_USERNAME = "@positive_prog"    # <-- O'zingizning @username

# Conversation states
(REG_NAME, REG_PHONE, REG_ADDRESS,
 ORDER_QTY, ORDER_CONFIRM,
 ADMIN_CAT_NAME,
 ADMIN_PROD_NAME, ADMIN_PROD_DESC,
 ADMIN_PROD_PRICE, ADMIN_PROD_IMG, ADMIN_PROD_CAT) = range(11)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== DATABASE ====================
def init_db():
    conn = sqlite3.connect('arzon_shop.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER UNIQUE,
        name TEXT,
        phone TEXT,
        address TEXT,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        emoji TEXT DEFAULT "🛍️"
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        price REAL,
        image_id TEXT,
        category_id INTEGER,
        available INTEGER DEFAULT 1,
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        product_name TEXT,
        quantity INTEGER,
        total_price REAL,
        status TEXT DEFAULT "pending",
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(telegram_id)
    )''')
    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        # Kategoriyalar
        c.execute("INSERT INTO categories (name, emoji) VALUES (?, ?)", ("Kiyim", "👗"))
        c.execute("INSERT INTO categories (name, emoji) VALUES (?, ?)", ("Elektronika", "📱"))
        c.execute("INSERT INTO categories (name, emoji) VALUES (?, ?)", ("Oziq-ovqat", "🍎"))
        c.execute("INSERT INTO categories (name, emoji) VALUES (?, ?)", ("Uy-ro'zg'or", "🏠"))
        conn.commit()

        # Kiyim mahsulotlari (category_id=1)
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Erkaklar ko'ylagi", "Yuqori sifatli paxta ko'ylak. Rangi: oq, ko'k, qora. O'lchamlar: S, M, L, XL", 85000, 1))
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Ayollar ko'ylagi", "Zamonaviy stil, chiroyli naqshlar. O'lchamlar: XS, S, M, L", 95000, 1))
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Jinsi shim", "Premium denim material. Har xil ranglarda mavjud. O'lchamlar: 28-36", 150000, 1))
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Sport kiyim to'plami", "Yengil va qulay sport kiyim. Jacket + shim. O'lchamlar: S-XL", 220000, 1))
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Bolalar kiyimi", "Yumshoq va xavfsiz material. Yoshlar: 2-12. Har xil ranglar", 65000, 1))

        # Elektronika mahsulotlari (category_id=2)
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Simsiz quloqchin", "Bluetooth 5.0, 30 soat batareya. Bass sound texnologiyasi", 180000, 2))
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Power Bank 20000mAh", "Tez zaryadlash (Fast Charge). 2x USB + Type-C. Kompakt dizayn", 120000, 2))
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Smart soat", "Qadamlar, yurak urishi, uyqu monitoring. Su o'tkazmaydigan", 350000, 2))
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("USB-C kabel (2m)", "Tez zaryadlash kabelі. 2 metr uzunlik. Mustahkam material", 25000, 2))
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Mini speaker", "Portable Bluetooth speaker. 360° ovoz. Suv o'tkazmaydigan. 10 soat ishlaydi", 95000, 2))

        # Oziq-ovqat (category_id=3)
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Asal (1 kg)", "Tabiiy tog' asali. Sof va ekologik toza. Har xil o'ramlarda", 75000, 3))
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Quruq mevalar to'plami", "Aralash quruq mevalar: mayiz, o'rik, anjir, xurmo. 500g", 55000, 3))
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Yong'oq assortiment", "Yong'oq, bodom, keshyu, pista aralashmasi. 500g", 80000, 3))
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Zaytun moyi (500ml)", "Extra virgin zaytun moyi. Import, yuqori sifat", 65000, 3))

        # Uy-ro'zg'or (category_id=4)
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Dekorativ yostiq", "Yumshoq va chiroyli. 45x45 sm. Har xil dizaynlar", 45000, 4))
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Aromatik shamlar to'plami", "6 ta shamdan iborat to'plam. Har xil hidlar. Sovg'a uchun ideal", 60000, 4))
        c.execute("INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                  ("Termosli piyola", "500ml, ikki qavatli stainless steel. Sovuq/issiq ushlab turadi", 85000, 4))

        conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect('arzon_shop.db')

def is_registered(telegram_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE telegram_id=?", (telegram_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_user(telegram_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    result = c.fetchone()
    conn.close()
    return result

# ==================== KEYBOARDS ====================
def main_menu_keyboard():
    return ReplyKeyboardMarkup([
        ["🛍️ Katalog", "🛒 Buyurtmalarim"],
        ["👤 Profilim", "📞 Aloqa"]
    ], resize_keyboard=True)

def admin_menu_keyboard():
    return ReplyKeyboardMarkup([
        ["📦 Mahsulot qo'shish", "🗂️ Kategoriya qo'shish"],
        ["📋 Barcha buyurtmalar", "👥 Foydalanuvchilar"],
        ["🏠 Asosiy menyu"]
    ], resize_keyboard=True)

# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_registered(user_id):
        user = get_user(user_id)
        await update.message.reply_text(
            f"👋 Xush kelibsiz, *{user[2]}*!\n\n🏪 *Arzon Shop*'ga xush kelibsiz!\nQuyidagi menyudan foydalaning:",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "🏪 *Arzon Shop*'ga xush kelibsiz!\n\n"
            "Buyurtma berish uchun avval ro'yxatdan o'tishingiz kerak.\n\n"
            "📝 Ro'yxatdan o'tish uchun quyidagi tugmani bosing:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Ro'yxatdan o'tish", callback_data="register")]
            ])
        )

# ==================== RO'YXATDAN O'TISH ====================
async def register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📝 *Ro'yxatdan o'tish*\n\n👤 Ism va familiyangizni kiriting:",
        parse_mode="Markdown"
    )
    return REG_NAME

async def register_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_registered(update.effective_user.id):
        await update.message.reply_text("✅ Siz allaqachon ro'yxatdan o'tgansiz!", reply_markup=main_menu_keyboard())
        return ConversationHandler.END
    await update.message.reply_text(
        "📝 *Ro'yxatdan o'tish*\n\n👤 Ism va familiyangizni kiriting:",
        parse_mode="Markdown"
    )
    return REG_NAME

async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_name'] = update.message.text
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        f"✅ Ism: *{update.message.text}*\n\n📱 Telefon raqamingizni yuboring:",
        parse_mode="Markdown",
        reply_markup=kb
    )
    return REG_PHONE

async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text
    context.user_data['reg_phone'] = phone
    await update.message.reply_text(
        f"✅ Telefon: *{phone}*\n\n📍 Yetkazib berish manzilini kiriting:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True)
    )
    return REG_ADDRESS

async def reg_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text
    telegram_id = update.effective_user.id
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (telegram_id, name, phone, address) VALUES (?, ?, ?, ?)",
            (telegram_id, context.user_data['reg_name'], context.user_data['reg_phone'], address)
        )
        conn.commit()
    except Exception:
        pass
    conn.close()
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"🆕 *Yangi foydalanuvchi!*\n\n"
            f"👤 Ism: {context.user_data['reg_name']}\n"
            f"📱 Tel: {context.user_data['reg_phone']}\n"
            f"📍 Manzil: {address}\n"
            f"🆔 ID: {telegram_id}",
            parse_mode="Markdown"
        )
    except Exception:
        pass
    await update.message.reply_text(
        "✅ *Muvaffaqiyatli ro'yxatdan o'tdingiz!*\n\n🏪 Arzon Shop'ga xush kelibsiz!",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END

# ==================== KATALOG ====================
async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_registered(update.effective_user.id):
        await update.message.reply_text(
            "❌ Avval ro'yxatdan o'ting!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Ro'yxatdan o'tish", callback_data="register")]])
        )
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, emoji FROM categories")
    cats = c.fetchall()
    conn.close()
    if not cats:
        await update.message.reply_text("📭 Hozircha kategoriyalar yo'q.")
        return
    buttons = [[InlineKeyboardButton(f"{cat[2]} {cat[1]}", callback_data=f"cat_{cat[0]}")] for cat in cats]
    await update.message.reply_text(
        "🗂️ *Kategoriyani tanlang:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = int(query.data.split("_")[1])
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM categories WHERE id=?", (cat_id,))
    cat = c.fetchone()
    c.execute("SELECT id, name, price FROM products WHERE category_id=? AND available=1", (cat_id,))
    products = c.fetchall()
    conn.close()
    if not products:
        await query.message.edit_text(
            "📭 Bu kategoriyada mahsulotlar yo'q.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Ortga", callback_data="back_catalog")]])
        )
        return
    buttons = [[InlineKeyboardButton(f"🏷️ {p[1]} — {p[2]:,.0f} so'm", callback_data=f"prod_{p[0]}")] for p in products]
    buttons.append([InlineKeyboardButton("🔙 Ortga", callback_data="back_catalog")])
    await query.message.edit_text(
        f"📦 *{cat[0]}* kategoriyasi:\n\nMahsulotni tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    prod_id = int(query.data.split("_")[1])
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, description, price, image_id, category_id FROM products WHERE id=?", (prod_id,))
    p = c.fetchone()
    conn.close()
    if not p:
        await query.message.edit_text("❌ Mahsulot topilmadi.")
        return
    context.user_data['selected_product'] = p
    text = (f"🏷️ *{p[1]}*\n\n"
            f"📝 {p[2]}\n\n"
            f"💰 Narx: *{p[3]:,.0f} so'm*")
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Buyurtma berish", callback_data=f"order_{p[0]}")],
        [InlineKeyboardButton("🔙 Ortga", callback_data=f"cat_{p[5]}")]
    ])
    if p[4]:
        try:
            await query.message.delete()
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=p[4],
                caption=text,
                parse_mode="Markdown",
                reply_markup=buttons
            )
            return
        except Exception:
            pass
    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=buttons)

async def back_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, emoji FROM categories")
    cats = c.fetchall()
    conn.close()
    buttons = [[InlineKeyboardButton(f"{cat[2]} {cat[1]}", callback_data=f"cat_{cat[0]}")] for cat in cats]
    await query.message.edit_text(
        "🗂️ *Kategoriyani tanlang:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ==================== BUYURTMA ====================
async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    prod_id = int(query.data.split("_")[1])
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, price FROM products WHERE id=?", (prod_id,))
    p = c.fetchone()
    conn.close()
    context.user_data['order_product'] = p
    await query.message.reply_text(
        f"🛒 *{p[1]}* uchun buyurtma\n\n📦 Nechta dona kerak? (Raqam kiriting)",
        parse_mode="Markdown"
    )
    return ORDER_QTY

async def order_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        qty = int(update.message.text)
        if qty <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Iltimos, to'g'ri son kiriting (masalan: 1, 2, 3)!")
        return ORDER_QTY
    p = context.user_data['order_product']
    total = p[2] * qty
    context.user_data['order_qty'] = qty
    context.user_data['order_total'] = total
    user = get_user(update.effective_user.id)
    await update.message.reply_text(
        f"📋 *Buyurtma ma'lumotlari:*\n\n"
        f"🏷️ Mahsulot: *{p[1]}*\n"
        f"📦 Miqdor: *{qty} dona*\n"
        f"💰 Jami: *{total:,.0f} so'm*\n"
        f"📍 Manzil: *{user[4]}*\n\n"
        f"✅ Tasdiqlaysizmi?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_order"),
             InlineKeyboardButton("❌ Bekor", callback_data="cancel_order")]
        ])
    )
    return ORDER_CONFIRM

async def order_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel_order":
        await query.message.edit_text("❌ Buyurtma bekor qilindi.")
        return ConversationHandler.END
    user_id = update.effective_user.id
    p = context.user_data['order_product']
    qty = context.user_data['order_qty']
    total = context.user_data['order_total']
    user = get_user(user_id)
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO orders (user_id, product_id, product_name, quantity, total_price) VALUES (?, ?, ?, ?, ?)",
        (user_id, p[0], p[1], qty, total)
    )
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"🛒 *Yangi buyurtma #{order_id}!*\n\n"
            f"👤 Mijoz: {user[2]}\n"
            f"📱 Tel: {user[3]}\n"
            f"📍 Manzil: {user[4]}\n"
            f"🏷️ Mahsulot: {p[1]}\n"
            f"📦 Miqdor: {qty} dona\n"
            f"💰 Jami: {total:,.0f} so'm",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Qabul qilish", callback_data=f"adm_accept_{order_id}"),
                 InlineKeyboardButton("❌ Rad etish", callback_data=f"adm_reject_{order_id}")]
            ])
        )
    except Exception:
        pass
    await query.message.edit_text(
        f"✅ *Buyurtmangiz qabul qilindi!*\n\n"
        f"🔢 Buyurtma raqami: *#{order_id}*\n"
        f"💰 To'lov summasi: *{total:,.0f} so'm*\n\n"
        f"💳 *To'lov uchun admin bilan bog'laning:*\n{ADMIN_USERNAME}\n\n"
        f"⏳ Admin siz bilan tez orada bog'lanadi!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Admin bilan bog'lanish",
                                  url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")]
        ])
    )
    return ConversationHandler.END

# ==================== MENING BUYURTMALARIM ====================
async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text("❌ Avval ro'yxatdan o'ting!")
        return
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT id, product_name, quantity, total_price, status, created_at FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10",
        (user_id,)
    )
    orders = c.fetchall()
    conn.close()
    if not orders:
        await update.message.reply_text("📭 Sizda hali buyurtmalar yo'q.")
        return
    status_emoji = {"pending": "⏳", "accepted": "✅", "rejected": "❌", "delivered": "🚚"}
    text = "🛒 *Mening buyurtmalarim:*\n\n"
    for o in orders:
        emoji = status_emoji.get(o[4], "❓")
        text += (f"{emoji} *#{o[0]}* — {o[1]}\n"
                 f"   📦 {o[2]} dona | 💰 {o[3]:,.0f} so'm\n"
                 f"   📅 {o[5][:10]}\n\n")
    await update.message.reply_text(text, parse_mode="Markdown")

# ==================== PROFIL ====================
async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text("❌ Avval ro'yxatdan o'ting!")
        return
    user = get_user(user_id)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (user_id,))
    order_count = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(
        f"👤 *Profilim*\n\n"
        f"📛 Ism: *{user[2]}*\n"
        f"📱 Tel: *{user[3]}*\n"
        f"📍 Manzil: *{user[4]}*\n"
        f"🛒 Jami buyurtmalar: *{order_count}* ta",
        parse_mode="Markdown"
    )

# ==================== ALOQA ====================
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📞 *Aloqa*\n\n"
        f"👨‍💼 Admin: {ADMIN_USERNAME}\n"
        f"🕐 Ish vaqti: 9:00 - 22:00\n\n"
        f"Savol va takliflar uchun admin bilan bog'laning!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Admin bilan bog'lanish",
                                  url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")]
        ])
    )

# ==================== ADMIN ====================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return
    await update.message.reply_text("⚙️ *Admin panel*", parse_mode="Markdown", reply_markup=admin_menu_keyboard())

async def admin_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT o.id, u.name, u.phone, o.product_name, o.quantity, o.total_price, o.status, o.created_at
                 FROM orders o JOIN users u ON o.user_id=u.telegram_id
                 ORDER BY o.id DESC LIMIT 20""")
    orders = c.fetchall()
    conn.close()
    if not orders:
        await update.message.reply_text("📭 Buyurtmalar yo'q.")
        return
    status_emoji = {"pending": "⏳", "accepted": "✅", "rejected": "❌", "delivered": "🚚"}
    text = "📋 *Barcha buyurtmalar:*\n\n"
    for o in orders:
        emoji = status_emoji.get(o[6], "❓")
        text += (f"{emoji} *#{o[0]}* | {o[1]} | {o[3]}\n"
                 f"   📱 {o[2]} | {o[4]} dona | {o[5]:,.0f} so'm\n\n")
    await update.message.reply_text(text[:4000], parse_mode="Markdown")

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, phone, address, registered_at FROM users ORDER BY id DESC")
    users = c.fetchall()
    conn.close()
    text = f"👥 *Foydalanuvchilar ({len(users)} ta):*\n\n"
    for u in users:
        addr = u[2][:20] + "..." if len(u[2]) > 20 else u[2]
        text += f"👤 {u[0]} | 📱 {u[1]} | 📍 {addr}\n"
    await update.message.reply_text(text[:4000], parse_mode="Markdown")

async def admin_order_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    action = parts[1]
    order_id = int(parts[2])
    conn = get_db()
    c = conn.cursor()
    status = "accepted" if action == "accept" else "rejected"
    c.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    c.execute("SELECT user_id, product_name, total_price FROM orders WHERE id=?", (order_id,))
    order = c.fetchone()
    conn.commit()
    conn.close()
    emoji = "✅" if action == "accept" else "❌"
    try:
        await query.message.edit_text(
            query.message.text + f"\n\n{emoji} Holat: *{status.upper()}*",
            parse_mode="Markdown"
        )
    except Exception:
        pass
    try:
        if action == "accept":
            msg = (f"✅ *Buyurtmangiz qabul qilindi!*\n\n"
                   f"🏷️ {order[1]}\n"
                   f"💰 {order[2]:,.0f} so'm\n\n"
                   f"💳 To'lov uchun admin bilan bog'laning: {ADMIN_USERNAME}")
        else:
            msg = (f"❌ *#{order_id} buyurtmangiz rad etildi.*\n"
                   f"Batafsil ma'lumot uchun: {ADMIN_USERNAME}")
        await context.bot.send_message(order[0], msg, parse_mode="Markdown")
    except Exception:
        pass

# ==================== MAHSULOT QO'SHISH ====================
async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    await update.message.reply_text("📦 Yangi mahsulot nomi:")
    return ADMIN_PROD_NAME

async def add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['prod_name'] = update.message.text
    await update.message.reply_text("📝 Mahsulot tavsifi:")
    return ADMIN_PROD_DESC

async def add_product_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['prod_desc'] = update.message.text
    await update.message.reply_text("💰 Narxi (faqat raqam, so'mda. Masalan: 150000):")
    return ADMIN_PROD_PRICE

async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text.replace(" ", "").replace(",", ""))
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri narx! Faqat raqam kiriting:")
        return ADMIN_PROD_PRICE
    context.user_data['prod_price'] = price
    await update.message.reply_text(
        "🖼️ Mahsulot rasmini yuboring:\n(Rasmsiz qo'shish uchun /skip yozing)"
    )
    return ADMIN_PROD_IMG

async def add_product_img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['prod_img'] = update.message.photo[-1].file_id
    else:
        context.user_data['prod_img'] = None
    return await _ask_category(update, context)

async def add_product_skip_img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['prod_img'] = None
    return await _ask_category(update, context)

async def _ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name FROM categories")
    cats = c.fetchall()
    conn.close()
    buttons = [[InlineKeyboardButton(cat[1], callback_data=f"addcat_{cat[0]}")] for cat in cats]
    await update.message.reply_text("🗂️ Kategoriyani tanlang:", reply_markup=InlineKeyboardMarkup(buttons))
    return ADMIN_PROD_CAT

async def add_product_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = int(query.data.split("_")[1])
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO products (name, description, price, image_id, category_id) VALUES (?, ?, ?, ?, ?)",
        (context.user_data['prod_name'], context.user_data['prod_desc'],
         context.user_data['prod_price'], context.user_data['prod_img'], cat_id)
    )
    conn.commit()
    conn.close()
    await query.message.reply_text(
        f"✅ *{context.user_data['prod_name']}* mahsuloti qo'shildi!",
        parse_mode="Markdown",
        reply_markup=admin_menu_keyboard()
    )
    return ConversationHandler.END

# ==================== KATEGORIYA QO'SHISH ====================
async def add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    await update.message.reply_text("🗂️ Yangi kategoriya nomi:")
    return ADMIN_CAT_NAME

async def add_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        await update.message.reply_text(
            f"✅ *{name}* kategoriyasi qo'shildi!",
            parse_mode="Markdown",
            reply_markup=admin_menu_keyboard()
        )
    except Exception:
        await update.message.reply_text("❌ Bu kategoriya allaqachon mavjud!", reply_markup=admin_menu_keyboard())
    conn.close()
    return ConversationHandler.END

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏠 Asosiy menyu", reply_markup=main_menu_keyboard())

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

# ==================== MAIN ====================
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # Registration via callback
    reg_cb_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(register_callback, pattern="^register$")],
        states={
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), reg_phone)],
            REG_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_address)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Registration via command
    reg_cmd_conv = ConversationHandler(
        entry_points=[CommandHandler("register", register_cmd)],
        states={
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), reg_phone)],
            REG_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_address)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Order conversation
    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(order_start, pattern="^order_")],
        states={
            ORDER_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_qty)],
            ORDER_CONFIRM: [
                CallbackQueryHandler(order_confirm, pattern="^confirm_order$"),
                CallbackQueryHandler(order_confirm, pattern="^cancel_order$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Add product conversation
    add_prod_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📦 Mahsulot qo'shish$"), add_product_start)],
        states={
            ADMIN_PROD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_name)],
            ADMIN_PROD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_desc)],
            ADMIN_PROD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price)],
            ADMIN_PROD_IMG: [
                MessageHandler(filters.PHOTO, add_product_img),
                CommandHandler("skip", add_product_skip_img),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_img),
            ],
            ADMIN_PROD_CAT: [CallbackQueryHandler(add_product_cat, pattern="^addcat_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Add category conversation
    add_cat_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🗂️ Kategoriya qo'shish$"), add_category_start)],
        states={
            ADMIN_CAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    app.add_handler(reg_cb_conv)
    app.add_handler(reg_cmd_conv)
    app.add_handler(order_conv)
    app.add_handler(add_prod_conv)
    app.add_handler(add_cat_conv)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.Regex("^🛍️ Katalog$"), show_catalog))
    app.add_handler(MessageHandler(filters.Regex("^🛒 Buyurtmalarim$"), my_orders))
    app.add_handler(MessageHandler(filters.Regex("^👤 Profilim$"), my_profile))
    app.add_handler(MessageHandler(filters.Regex("^📞 Aloqa$"), contact))
    app.add_handler(MessageHandler(filters.Regex("^📋 Barcha buyurtmalar$"), admin_all_orders))
    app.add_handler(MessageHandler(filters.Regex("^👥 Foydalanuvchilar$"), admin_users))
    app.add_handler(MessageHandler(filters.Regex("^🏠 Asosiy menyu$"), back_main))
    app.add_handler(CallbackQueryHandler(show_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(show_product, pattern="^prod_"))
    app.add_handler(CallbackQueryHandler(back_catalog, pattern="^back_catalog$"))
    app.add_handler(CallbackQueryHandler(admin_order_action, pattern="^adm_(accept|reject)_"))

    print("🤖 Arzon Shop Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
