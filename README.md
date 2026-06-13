# X-Dubbing Premium Telegram Bot

Premium obuna, to'lov cheklari, admin panel va kanalga post yuborish boti.

## Imkoniyatlar

### Foydalanuvchilar uchun
- Premium obuna ma'lumoti (karta raqami monospace — copy qilish oson)
- Chek yuborish (rasm)
- Aloqa ma'lumotlari

### Adminlar uchun
- To'lov cheklarini tasdiqlash (1/3/6/12 oy) yoki rad etish
- Statistika, foydalanuvchilar ro'yxati
- Kanal/guruh/foydalanuvchiga xabar yuborish
- Professional post yaratish (rasm, video, matn, inline tugmalar)
- Admin qo'shish/o'chirish
- Obuna muddati tugaganda avtomatik guruhdan chiqarish (bloklamasdan)

## Render.com da ishga tushirish (tavsiya)

> **Muhim:** Bu bot **Web Service emas**, **Background Worker** sifatida ishlaydi.  
> HTTP port kerak emas — faqat `python -m bot.main` ishga tushadi.

### 1. GitHub ga yuklang
```bash
git init
git add .
git commit -m "X-Dubbing bot"
git remote add origin YOUR_REPO_URL
git push -u origin main
```

### 2. Render
1. [render.com](https://render.com) → **New** → **Blueprint** (yoki Worker qo'lda)
2. GitHub repozitoriyani ulang
3. `render.yaml` avtomatik o'qiladi

**Yoki qo'lda:**
- **New → Background Worker**
- Build Command: `pip install -r requirements.txt`
- Start Command: `python -m bot.main`

### 3. Environment Variables

| O'zgaruvchi | Qiymat |
|---|---|
| `BOT_TOKEN` | @BotFather dan token |
| `MAIN_ADMIN_ID` | `6857570089` |
| `PRIVATE_GROUP_ID` | Yopiq guruh ID (`-100...`) |
| `CHANNEL_LINK` | `https://t.me/+bUQj_WkfOAphNzMy` |
| `CHANNEL_USERNAME` | `FxDubbing` |
| `DATABASE_PATH` | `/var/data/bot.db` |

### 4. Disk (ma'lumotlar saqlanishi uchun)
Render Dashboard → Worker → **Disks** → Add Disk:
- Mount Path: `/var/data`
- Size: 1 GB

Disk bo'lmasa, har restartda SQLite bazasi tozalanadi (adminlar, obunalar yo'qoladi).

### 5. Guruh ID ni olish
1. Botni yopiq guruhga admin qiling (aqlli cheklovlar + a'zolarni qo'shish)
2. Guruhga xabar yuboring
3. `https://api.telegram.org/bot<TOKEN>/getUpdates` oching
4. `chat.id` ni `PRIVATE_GROUP_ID` ga qo'ying

### 6. Bot sozlash
- @X_Dubbing_Bot — Privacy Mode **OFF** (Group Privacy disabled)
- Guruhda bot admin bo'lishi kerak
- Kanalda post yuborish uchun bot kanal admini bo'lishi kerak

## Lokal ishga tushirish

```bash
cd x-dubbing-bot
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env       # token va ID larni to'ldiring
python -m bot.main
```

## Inline tugmalar formati

```
Kanalga o'tish | https://t.me/FxDubbing
Buyurtma | callback_data
```

Har qator — bitta tugma. URL `http` bilan boshlansa link tugma bo'ladi.
