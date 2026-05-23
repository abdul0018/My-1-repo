# 🏪 Arzon Shop Telegram Bot

## ⚙️ O'rnatish

### 1. Talablar
- Python 3.10+
- pip

### 2. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 3. bot.py ni sozlash
`bot.py` faylini oching va quyidagilarni o'zgartiring:

```python
BOT_TOKEN = "SIZNING_TOKENINGIZ"   # BotFather dan olingan token
ADMIN_ID = 123456789               # Sizning Telegram ID ingiz
ADMIN_USERNAME = "@sizning_username" # Sizning @username ingiz
```

> 📌 Telegram ID ni bilish uchun: @userinfobot ga /start yuboring

### 4. Ishga tushirish
```bash
python bot.py
```

---

## 🚀 Bepul Hosting (Railway)

1. [railway.app](https://railway.app) ga kiring
2. GitHub account bilan login qiling
3. "New Project" → "Deploy from GitHub repo"
4. Fayllarni GitHub ga yuklang va deploy qiling
5. Bot 24/7 ishlaydi!

---

## ✨ Bot imkoniyatlari

### Mijozlar uchun:
- 📝 Ro'yxatdan o'tish (ism, telefon, manzil)
- 🗂️ Kategoriyalar bo'yicha mahsulotlar
- 🖼️ Mahsulot rasmlari va tavsiflari
- 🛒 Buyurtma berish
- 📋 Buyurtmalar tarixi
- 👤 Shaxsiy profil

### Admin uchun (/admin):
- 📦 Mahsulot qo'shish (rasm bilan)
- 🗂️ Kategoriya qo'shish
- 📋 Barcha buyurtmalarni ko'rish
- ✅/❌ Buyurtmalarni qabul/rad qilish
- 👥 Foydalanuvchilar ro'yxati

---

## 📁 Fayl tuzilmasi
```
arzon_shop_bot/
├── bot.py           # Asosiy bot kodi
├── requirements.txt # Kutubxonalar
├── Procfile         # Hosting uchun
├── README.md        # Qo'llanma
└── arzon_shop.db    # Ma'lumotlar bazasi (avtomatik yaratiladi)
```
