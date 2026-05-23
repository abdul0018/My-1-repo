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
BOT_TOKEN = "8790387724:AAE_yu0FTWkZf7oB1KLYyOorzfVoihGPHiY"   # <-- YANGI TOKEN QOYING
ADMIN_ID = 1799129203                # <-- O'zingizning Telegram ID (@userinfobot dan oling)
ADMIN_USERNAME = "@positive_prog"   # <-- O'zingizning @username

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
        categories = [
            ("Kiyim", "👗"),
            ("Elektronika", "📱"),
            ("Oziq-ovqat", "🍎"),
            ("Uy-ro'zg'or", "🏠"),
        ]
        c.executemany("INSERT INTO categories (name, emoji) VALUES (?, ?)", categories)
        conn.commit()

        products = [
            # Kiyim (cat 1)
            ("Erkaklar ko'ylagi", "Yuqori sifatli paxta ko'ylak. Rangi: oq, ko'k, qora. O'lchamlar: S, M, L, XL", 85000, None, 1),
            ("Ayollar ko'ylagi", "Zamonaviy stil, chiroyli naqshlar. O'lchamlar: XS, S, M, L", 95000, None, 1),
            ("Jinsi shim", "Premium denim material. Har xil ranglarda mavjud. O'lchamlar: 28-36", 150000, None, 1),
            ("Sport kiyim to'plami", "Yengil va qulay sport kiyim. Jacket + shim. O'lchamlar: S-XL", 220000, None, 1),
            ("Bolalar kiyimi", "Yumshoq va xavfsiz material. Yoshlar: 2-12. Har xil ranglar", 65000, None, 1),
            # Elektronika (cat 2)
            ("Simsiz quloqchin", "Bluetooth 5.0, 30 soat batareya. Bass sound texnologiyasi", 180000, None, 2),
            ("Power Bank 20000mAh", "Tez zaryadlash (Fast Charge). 2x USB + Type-C. Kompakt dizayn", 120000, None, 2),
            ("Smart soat", "Qadamlar, yurak urishi, uyqu monitoring. Su o'tkazmaydigan", 350000, None, 2),
            ("USB-C kabel (2m)", "Tez zaryadlash kabeli. 2 metr uzunlik. Mustahkam material", 25000, None, 2),
            ("Mini speaker", "Portable Bluetooth speaker. 360° ovoz. Suv o'tkazmaydigan. 10 soat ishlaydi", 95000, None, 2),
            # Oziq-ovqat (cat 3)
            ("Asal (1 kg)", "Tabiiy tog' asali. Sof va ekologik toza. Har xil o'ramlarda", 75000, None, 3),
            ("Quruq mevalar to'plami", "Aralash quruq mevalar: mayiz, o'rik, anjir, xurmo. 500g", 55000, None, 3),
            ("Yong'oq assortiment", "Yong'oq, bodom, keshyu, pista aralashmasi. 500g", 80000, None, 3),
            ("Zaytun moyi (500ml)", "Extra virgin zaytun moyi. Import, yuqori sifat", 65000, None, 3),
            # Uy-ro'zg'or (cat 4)
            ("Dekorativ yostiq", "Yumshoq va chiroyli. 45x45 sm. Har xil dizaynlar", 45000, None, 4),
            ("Aromatik shamlar to'plami", "6 ta shamdan iborat to'plam. Har xil hidlar. Sovg'a uchun ideal", 60000, None, 4),
            ("Termosli piyola", "500ml, ikki qavatli stainless steel. Sovuq/issiq ushlab turadi", 85000, None, 4),
        ]
        c.executemany(
            "INSERT INTO products (name, description, price, image_id, category_id) VALUES (?, ?, ?, ?, ?)",
            products
        )
        conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('arzon_shop.db')
    conn.row_factory = sqlite3.Row  # FIX: allows dict-style column access
    return conn

def is_registered(telegram_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute("SELECT id FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
    return row is not None

def get_user(telegram_id: int):
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()

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

# ==================== HELPERS ====================
STATUS_EMOJI = {"pending": "⏳", "accepted": "✅", "rejected": "❌", "delivered": "🚚"}

def format_price(price: float) -> str:
    return f"{price:,.0f} so'm"

async def notify_admin(context, text: str, reply_markup=None):
    """Send a message to admin, silently ignore errors."""
    try:
        await context.bot.send_message(
            ADMIN_ID, text, parse_mode="Markdown", reply_markup=reply_markup
        )
    except Exception as e:
        logger.warning(f"Admin notification failed: {e}")

async def notify_user(context, user_id: int, text: str):
    """Send a message to a user, silently ignore errors."""
    try:
        await context.bot.send_message(user_id, text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"User notification failed (id={user_id}): {e}")

# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_registered(user_id):
        user = get_user(user_id)
        await update.message.reply_text(
            f"👋 Xush kelibsiz, *{user['name']}*!\n\n🏪 *Arzon Shop*'ga xush kelibsiz!\nQuyidagi menyudan foydalaning:",
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
    if is_registered(query.from_user.id):
        await query.message.reply_text(
            "✅ Siz allaqachon ro'yxatdan o'tgansiz!",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    await query.message.reply_text(
        "📝 *Ro'yxatdan o'tish*\n\n👤 Ism va familiyangizni kiriting:",
        parse_mode="Markdown"
    )
    return REG_NAME

async def register_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_registered(update.effective_user.id):
        await update.message.reply_text(
            "✅ Siz allaqachon ro'yxatdan o'tgansiz!",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    await update.message.reply_text(
        "📝 *Ro'yxatdan o'tish*\n\n👤 Ism va familiyangizni kiriting:",
        parse_mode="Markdown"
    )
    return REG_NAME

async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❌ Ism juda qisqa. Iltimos, to'liq ismingizni kiriting:")
        return REG_NAME
    context.user_data['reg_name'] = name
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        f"✅ Ism: *{name}*\n\n📱 Telefon raqamingizni yuboring:",
        parse_mode="Markdown",
        reply_markup=kb
    )
    return REG_PHONE

async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()
        # Basic phone validation
        digits = phone.replace("+", "").replace(" ", "").replace("-", "")
        if not digits.isdigit() or len(digits) < 9:
            await update.message.reply_text(
                "❌ Noto'g'ri telefon raqam. Iltimos, to'g'ri raqam kiriting yoki tugmani bosing:"
            )
            return REG_PHONE
    context.user_data['reg_phone'] = phone
    await update.message.reply_text(
        f"✅ Telefon: *{phone}*\n\n📍 Yetkazib berish manzilini kiriting:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True)
    )
    return REG_ADDRESS

async def reg_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    if len(address) < 5:
        await update.message.reply_text("❌ Manzil juda qisqa. Iltimos, to'liq manzil kiriting:")
        return REG_ADDRESS
    telegram_id = update.effective_user.id
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (telegram_id, name, phone, address) VALUES (?, ?, ?, ?)",
                (telegram_id, context.user_data['reg_name'], context.user_data['reg_phone'], address)
            )
    except Exception as e:
        logger.error(f"Registration DB error: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        return ConversationHandler.END

    await notify_admin(
        context,
        f"🆕 *Yangi foydalanuvchi!*\n\n"
        f"👤 Ism: {context.user_data['reg_name']}\n"
        f"📱 Tel: {context.user_data['reg_phone']}\n"
        f"📍 Manzil: {address}\n"
        f"🆔 ID: `{telegram_id}`"
    )
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
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Ro'yxatdan o'tish", callback_data="register")]
            ])
        )
        return
    with get_db() as conn:
        cats = conn.execute("SELECT id, name, emoji FROM categories").fetchall()
    if not cats:
        await update.message.reply_text("📭 Hozircha kategoriyalar yo'q.")
        return
    buttons = [
        [InlineKeyboardButton(f"{cat['emoji']} {cat['name']}", callback_data=f"cat_{cat['id']}")]
        for cat in cats
    ]
    await update.message.reply_text(
        "🗂️ *Kategoriyani tanlang:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = int(query.data.split("_")[1])
    with get_db() as conn:
        cat = conn.execute("SELECT name FROM categories WHERE id=?", (cat_id,)).fetchone()
        products = conn.execute(
            "SELECT id, name, price FROM products WHERE category_id=? AND available=1", (cat_id,)
        ).fetchall()
    if not products:
        await query.message.edit_text(
            "📭 Bu kategoriyada mahsulotlar yo'q.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Ortga", callback_data="back_catalog")]
            ])
        )
        return
    buttons = [
        [InlineKeyboardButton(f"🏷️ {p['name']} — {format_price(p['price'])}", callback_data=f"prod_{p['id']}")]
        for p in products
    ]
    buttons.append([InlineKeyboardButton("🔙 Ortga", callback_data="back_catalog")])
    await query.message.edit_text(
        f"📦 *{cat['name']}* kategoriyasi:\n\nMahsulotni tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    prod_id = int(query.data.split("_")[1])
    with get_db() as conn:
        p = conn.execute(
            "SELECT id, name, description, price, image_id, category_id FROM products WHERE id=?", (prod_id,)
        ).fetchone()
    if not p:
        await query.message.edit_text("❌ Mahsulot topilmadi.")
        return
    context.user_data['selected_product'] = dict(p)
    text = (
        f"🏷️ *{p['name']}*\n\n"
        f"📝 {p['description']}\n\n"
        f"💰 Narx: *{format_price(p['price'])}*"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Buyurtma berish", callback_data=f"order_{p['id']}")],
        [InlineKeyboardButton("🔙 Ortga", callback_data=f"cat_{p['category_id']}")]
    ])
    if p['image_id']:
        try:
            await query.message.delete()
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=p['image_id'],
                caption=text,
                parse_mode="Markdown",
                reply_markup=buttons
            )
            return
        except Exception as e:
            logger.warning(f"Failed to send product photo: {e}")
    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=buttons)

async def back_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    with get_db() as conn:
        cats = conn.execute("SELECT id, name, emoji FROM categories").fetchall()
    buttons = [
        [InlineKeyboardButton(f"{cat['emoji']} {cat['name']}", callback_data=f"cat_{cat['id']}")]
        for cat in cats
    ]
    await query.message.edit_text(
        "🗂️ *Kategoriyani tanlang:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ==================== BUYURTMA ====================
async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # FIX: check registration before ordering
    if not is_registered(query.from_user.id):
        await query.message.reply_text("❌ Avval ro'yxatdan o'ting!")
        return ConversationHandler.END
    prod_id = int(query.data.split("_")[1])
    with get_db() as conn:
        p = conn.execute("SELECT id, name, price FROM products WHERE id=?", (prod_id,)).fetchone()
    if not p:
        await query.message.reply_text("❌ Mahsulot topilmadi.")
        return ConversationHandler.END
    context.user_data['order_product'] = dict(p)
    await query.message.reply_text(
        f"🛒 *{p['name']}* uchun buyurtma\n\n📦 Nechta dona kerak? (Raqam kiriting)",
        parse_mode="Markdown"
    )
    return ORDER_QTY

async def order_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        qty = int(update.message.text.strip())
        if qty <= 0 or qty > 1000:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ Iltimos, to'g'ri son kiriting (1 dan 1000 gacha, masalan: 1, 2, 3)!"
        )
        return ORDER_QTY
    p = context.user_data['order_product']
    total = p['price'] * qty
    context.user_data['order_qty'] = qty
    context.user_data['order_total'] = total
    user = get_user(update.effective_user.id)
    await update.message.reply_text(
        f"📋 *Buyurtma ma'lumotlari:*\n\n"
        f"🏷️ Mahsulot: *{p['name']}*\n"
        f"📦 Miqdor: *{qty} dona*\n"
        f"💰 Jami: *{format_price(total)}*\n"
        f"📍 Manzil: *{user['address']}*\n\n"
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
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO orders (user_id, product_id, product_name, quantity, total_price) VALUES (?, ?, ?, ?, ?)",
                (user_id, p['id'], p['name'], qty, total)
            )
            order_id = cursor.lastrowid
    except Exception as e:
        logger.error(f"Order insert error: {e}")
        await query.message.edit_text("❌ Buyurtma saqlashda xatolik. Iltimos, qayta urinib ko'ring.")
        return ConversationHandler.END

    await notify_admin(
        context,
        f"🛒 *Yangi buyurtma #{order_id}!*\n\n"
        f"👤 Mijoz: {user['name']}\n"
        f"📱 Tel: {user['phone']}\n"
        f"📍 Manzil: {user['address']}\n"
        f"🏷️ Mahsulot: {p['name']}\n"
        f"📦 Miqdor: {qty} dona\n"
        f"💰 Jami: {format_price(total)}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Qabul qilish", callback_data=f"adm_accept_{order_id}"),
             InlineKeyboardButton("❌ Rad etish", callback_data=f"adm_reject_{order_id}")]
        ])
    )
    admin_url = f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"
    await query.message.edit_text(
        f"✅ *Buyurtmangiz qabul qilindi!*\n\n"
        f"🔢 Buyurtma raqami: *#{order_id}*\n"
        f"💰 To'lov summasi: *{format_price(total)}*\n\n"
        f"💳 *To'lov uchun admin bilan bog'laning:*\n{ADMIN_USERNAME}\n\n"
        f"⏳ Admin siz bilan tez orada bog'lanadi!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Admin bilan bog'lanish", url=admin_url)]
        ])
    )
    return ConversationHandler.END

# ==================== MENING BUYURTMALARIM ====================
async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text("❌ Avval ro'yxatdan o'ting!")
        return
    with get_db() as conn:
        orders = conn.execute(
            "SELECT id, product_name, quantity, total_price, status, created_at "
            "FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10",
            (user_id,)
        ).fetchall()
    if not orders:
        await update.message.reply_text("📭 Sizda hali buyurtmalar yo'q.")
        return
    text = "🛒 *Mening buyurtmalarim:*\n\n"
    for o in orders:
        emoji = STATUS_EMOJI.get(o['status'], "❓")
        text += (
            f"{emoji} *#{o['id']}* — {o['product_name']}\n"
            f"   📦 {o['quantity']} dona | 💰 {format_price(o['total_price'])}\n"
            f"   📅 {o['created_at'][:10]}\n\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

# ==================== PROFIL ====================
async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text("❌ Avval ro'yxatdan o'ting!")
        return
    user = get_user(user_id)
    with get_db() as conn:
        order_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM orders WHERE user_id=?", (user_id,)
        ).fetchone()['cnt']
    await update.message.reply_text(
        f"👤 *Profilim*\n\n"
        f"📛 Ism: *{user['name']}*\n"
        f"📱 Tel: *{user['phone']}*\n"
        f"📍 Manzil: *{user['address']}*\n"
        f"🛒 Jami buyurtmalar: *{order_count}* ta",
        parse_mode="Markdown"
    )

# ==================== ALOQA ====================
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_url = f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"
    await update.message.reply_text(
        f"📞 *Aloqa*\n\n"
        f"👨‍💼 Admin: {ADMIN_USERNAME}\n"
        f"🕐 Ish vaqti: 9:00 - 22:00\n\n"
        f"Savol va takliflar uchun admin bilan bog'laning!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Admin bilan bog'lanish", url=admin_url)]
        ])
    )

# ==================== ADMIN ====================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return
    with get_db() as conn:
        user_count = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()['cnt']
        order_count = conn.execute("SELECT COUNT(*) as cnt FROM orders WHERE status='pending'").fetchone()['cnt']
    await update.message.reply_text(
        f"⚙️ *Admin panel*\n\n"
        f"👥 Foydalanuvchilar: *{user_count}* ta\n"
        f"⏳ Kutilayotgan buyurtmalar: *{order_count}* ta",
        parse_mode="Markdown",
        reply_markup=admin_menu_keyboard()
    )

async def admin_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    with get_db() as conn:
        orders = conn.execute(
            "SELECT o.id, u.name, u.phone, o.product_name, o.quantity, o.total_price, o.status, o.created_at "
            "FROM orders o JOIN users u ON o.user_id=u.telegram_id "
            "ORDER BY o.id DESC LIMIT 20"
        ).fetchall()
    if not orders:
        await update.message.reply_text("📭 Buyurtmalar yo'q.")
        return
    text = "📋 *Barcha buyurtmalar:*\n\n"
    for o in orders:
        emoji = STATUS_EMOJI.get(o['status'], "❓")
        text += (
            f"{emoji} *#{o['id']}* | {o['name']} | {o['product_name']}\n"
            f"   📱 {o['phone']} | {o['quantity']} dona | {format_price(o['total_price'])}\n\n"
        )
    # Telegram max message length is 4096 chars
    await update.message.reply_text(text[:4096], parse_mode="Markdown")

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    with get_db() as conn:
        users = conn.execute(
            "SELECT name, phone, address, registered_at FROM users ORDER BY id DESC"
        ).fetchall()
    text = f"👥 *Foydalanuvchilar ({len(users)} ta):*\n\n"
    for u in users:
        addr = (u['address'][:20] + "...") if len(u['address']) > 20 else u['address']
        text += f"👤 {u['name']} | 📱 {u['phone']} | 📍 {addr}\n"
    await update.message.reply_text(text[:4096], parse_mode="Markdown")

async def admin_order_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # FIX: only admin can use these buttons
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    parts = query.data.split("_")
    action = parts[1]        # "accept" or "reject"
    order_id = int(parts[2])
    status = "accepted" if action == "accept" else "rejected"
    try:
        with get_db() as conn:
            conn.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
            order = conn.execute(
                "SELECT user_id, product_name, total_price FROM orders WHERE id=?", (order_id,)
            ).fetchone()
    except Exception as e:
        logger.error(f"Order action DB error: {e}")
        return
    emoji = "✅" if action == "accept" else "❌"
    try:
        await query.message.edit_text(
            query.message.text + f"\n\n{emoji} Holat: *{status.upper()}*",
            parse_mode="Markdown"
        )
    except Exception:
        pass  # Message may already be edited

    if order:
        if action == "accept":
            msg = (
                f"✅ *Buyurtmangiz qabul qilindi!*\n\n"
                f"🏷️ {order['product_name']}\n"
                f"💰 {format_price(order['total_price'])}\n\n"
                f"💳 To'lov uchun admin bilan bog'laning: {ADMIN_USERNAME}"
            )
        else:
            msg = (
                f"❌ *#{order_id} buyurtmangiz rad etildi.*\n"
                f"Batafsil ma'lumot uchun: {ADMIN_USERNAME}"
            )
        await notify_user(context, order['user_id'], msg)

# ==================== MAHSULOT QO'SHISH ====================
async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    await update.message.reply_text("📦 Yangi mahsulot nomi:")
    return ADMIN_PROD_NAME

async def add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['prod_name'] = update.message.text.strip()
    await update.message.reply_text("📝 Mahsulot tavsifi:")
    return ADMIN_PROD_DESC

async def add_product_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['prod_desc'] = update.message.text.strip()
    await update.message.reply_text("💰 Narxi (faqat raqam, so'mda. Masalan: 150000):")
    return ADMIN_PROD_PRICE

async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text.replace(" ", "").replace(",", ""))
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri narx! Faqat musbat raqam kiriting:")
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
    with get_db() as conn:
        cats = conn.execute("SELECT id, name FROM categories").fetchall()
    buttons = [
        [InlineKeyboardButton(cat['name'], callback_data=f"addcat_{cat['id']}")]
        for cat in cats
    ]
    await update.message.reply_text("🗂️ Kategoriyani tanlang:", reply_markup=InlineKeyboardMarkup(buttons))
    return ADMIN_PROD_CAT

async def add_product_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = int(query.data.split("_")[1])
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO products (name, description, price, image_id, category_id) VALUES (?, ?, ?, ?, ?)",
                (context.user_data['prod_name'], context.user_data['prod_desc'],
                 context.user_data['prod_price'], context.user_data.get('prod_img'), cat_id)
            )
    except Exception as e:
        logger.error(f"Add product DB error: {e}")
        await query.message.reply_text("❌ Mahsulot qo'shishda xatolik!")
        return ConversationHandler.END
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
    name = update.message.text.strip()
    try:
        with get_db() as conn:
            conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        await update.message.reply_text(
            f"✅ *{name}* kategoriyasi qo'shildi!",
            parse_mode="Markdown",
            reply_markup=admin_menu_keyboard()
        )
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "❌ Bu kategoriya allaqachon mavjud!",
            reply_markup=admin_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Add category error: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.", reply_markup=admin_menu_keyboard())
    return ConversationHandler.END

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏠 Asosiy menyu", reply_markup=main_menu_keyboard())

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

# ==================== ERROR HANDLER ====================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)

# ==================== MAIN ====================
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # Registration via callback (inline button)
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

    # Registration via /register command
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

    # Add product conversation (admin only)
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

    # Add category conversation (admin only)
    add_cat_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🗂️ Kategoriya qo'shish$"), add_category_start)],
        states={
            ADMIN_CAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Conversation handlers must be added BEFORE plain message handlers
    app.add_handler(reg_cb_conv)
    app.add_handler(reg_cmd_conv)
    app.add_handler(order_conv)
    app.add_handler(add_prod_conv)
    app.add_handler(add_cat_conv)

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))

    # Reply keyboard buttons
    app.add_handler(MessageHandler(filters.Regex("^🛍️ Katalog$"), show_catalog))
    app.add_handler(MessageHandler(filters.Regex("^🛒 Buyurtmalarim$"), my_orders))
    app.add_handler(MessageHandler(filters.Regex("^👤 Profilim$"), my_profile))
    app.add_handler(MessageHandler(filters.Regex("^📞 Aloqa$"), contact))
    app.add_handler(MessageHandler(filters.Regex("^📋 Barcha buyurtmalar$"), admin_all_orders))
    app.add_handler(MessageHandler(filters.Regex("^👥 Foydalanuvchilar$"), admin_users))
    app.add_handler(MessageHandler(filters.Regex("^🏠 Asosiy menyu$"), back_main))

    # Inline button callbacks
    app.add_handler(CallbackQueryHandler(show_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(show_product, pattern="^prod_"))
    app.add_handler(CallbackQueryHandler(back_catalog, pattern="^back_catalog$"))
    app.add_handler(CallbackQueryHandler(admin_order_action, pattern="^adm_(accept|reject)_"))

    # Global error handler
    app.add_error_handler(error_handler)

    print("🤖 Arzon Shop Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
