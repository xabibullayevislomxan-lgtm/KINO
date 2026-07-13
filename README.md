# 🎬 Kino Bot

Telegram kino bot: foydalanuvchi kod yuboradi → bot kinoni yuboradi.
5 ta kanalga majburiy obuna talab qilinadi. Admin panel orqali kino
qo'shish va statistika ko'rish mumkin.

## 📁 Fayllar

- `bot.py` — botning asosiy logikasi
- `database.py` — SQLite baza bilan ishlash
- `config.py` — sozlamalar (`.env` dan o'qiydi)
- `requirements.txt` — kerakli kutubxonalar
- `Procfile` — Railway uchun ishga tushirish buyrug'i
- `.env` — sizning tokeningiz va sozlamalaringiz (⚠️ GitHub'ga hech qachon yuklamang!)

---

## 1-qadam: ADMIN_ID ni olish

1. Telegramda **@userinfobot** ga kiring va `/start` bosing
2. U sizga ID raqamingizni beradi (masalan: `123456789`)
3. Shu raqamni `.env` faylidagi `ADMIN_ID=` qatoriga yozing

## 2-qadam: Yopiq kanallarning raqamli ID sini olish

Sizning 3 ta kanalingiz **yopiq** (invite-link, `+` bilan boshlanadi):
- https://t.me/+DK-59zvtQ-5lYmUy
- https://t.me/+4MqyHPn_QDYxMTFi
- https://t.me/+LB8c33Lp9DBkYzAy

Botning obunani tekshirishi uchun bu kanallarning **raqamli ID**si kerak
(masalan `-1001234567890`). Buni olish uchun:

1. Har bir kanalga kiring → **Administratorlar** → botingizni (masalan
   `@sizning_bot_username`) **admin** qilib qo'shing (kamida "Foydalanuvchilarni
   ko'rish/taklif qilish" huquqi kifoya)
2. Kanalga istalgan xabar yozing (yoki eski xabarni) → o'sha xabarni
   **@userinfobot** ga forward qiling — bot sizga kanal ID sini ko'rsatadi
   (`-100...` bilan boshlanadi)
3. Shu ID ni `.env` faylida mos qatorga yozing:
   ```
   CHANNEL_1_ID=-1001234567890
   CHANNEL_2_ID=-1009876543210
   CHANNEL_3_ID=-1005556667778
   ```

Ochiq kanallar (`@kinoolamiuzbe`, `@sunniyintellekt_darslar`) uchun ID
allaqachon `.env` da to'g'ri turibdi — ularga ham botni admin qilib
qo'shishni unutmang, aks holda obuna tekshiruvi ishlamaydi.

## 3-qadam: Botni lokal sinab ko'rish (ixtiyoriy)

```bash
pip install -r requirements.txt
python bot.py
```

Keyin Telegramda botingizga `/start` yozing.

---

## 4-qadam: GitHub'ga yuklash

```bash
cd kino_bot
git init
git add .
git commit -m "Kino bot"
git branch -M main
git remote add origin https://github.com/FOYDALANUVCHI_NOMI/kino-bot.git
git push -u origin main
```

⚠️ `.env` fayli `.gitignore` tufayli GitHub'ga yuklanmaydi — bu xavfsizlik
uchun to'g'ri. Railway'da tokenni alohida kiritasiz (quyida).

## 5-qadam: Railway orqali joylashtirish

1. https://railway.app ga kiring, GitHub hisobingiz bilan ro'yxatdan o'ting
2. **New Project** → **Deploy from GitHub repo** → `kino-bot` repongizni tanlang
3. Loyiha ochilgach, **Variables** bo'limiga o'ting va quyidagi
   o'zgaruvchilarni qo'shing (`.env` faylingizdagi barcha qatorlar):
   - `BOT_TOKEN`
   - `ADMIN_ID`
   - `CHANNEL_1_URL`, `CHANNEL_1_ID`
   - `CHANNEL_2_URL`, `CHANNEL_2_ID`
   - `CHANNEL_3_URL`, `CHANNEL_3_ID`
   - `CHANNEL_4_URL`, `CHANNEL_4_ID`
   - `CHANNEL_5_URL`, `CHANNEL_5_ID`
4. Railway avtomatik `Procfile` ni o'qib botni **worker** sifatida ishga
   tushiradi. Agar tushirmasa, **Settings → Deploy → Start Command** ga
   `python bot.py` deb yozing
5. **Deploy** tugmasini bosing — tayyor, bot 24/7 ishlaydi!

---

## Qanday ishlaydi

- **Oddiy foydalanuvchi:** `/start` → 5 kanalga obuna tugmalari (2 tadan
  yonma-yon) chiqadi → "✅ Obunani tekshirish" bossa, obuna tekshiriladi →
  obuna bo'lsa "kino kodini yuboring" deyiladi → kod yuborsa, mos kino
  keladi
- **Siz (admin):** `/start` bossangiz obuna talab qilinmaydi, o'rniga
  **📊 Statistika** va **🎬 Kino joylash** tugmalari chiqadi
  - **🎬 Kino joylash** → video yuboring → kod kiriting → saqlanadi
  - **📊 Statistika** → foydalanuvchilar va kinolar sonini ko'rsatadi
- Har safar **yangi** foydalanuvchi `/start` bosganda, sizga avtomatik
  xabar keladi (ism, username, ID)

## Eslatma

- Kino kodlari raqam yoki matn bo'lishi mumkin (masalan `101`, `kino1`)
- Bir xil kodni qayta yuborsangiz, eski kino ustidan yangilanadi
- Agar `CHANNEL_X_ID` bo'sh qoldirilsa, o'sha kanal uchun obuna tekshiruvi
  o'tkazib yuboriladi — shuning uchun barcha ID larni to'ldirish muhim
