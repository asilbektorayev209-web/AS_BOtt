from bot.config import PRICES


def premium_info_text(card: str, name: str, channel_link: str) -> str:
    return (
        "🎬 <b>X-DUBBING PREMIUM HAQIDA MALUMOT!</b>\n\n"
        "Bu pullik kanal bo'lib faqat pul to'lab kirishingiz mumkin 💳\n\n"
        "<b>WERX PREMIUM NARXI:</b>\n"
        f"💎 1 Oylik = {PRICES['1m']}\n"
        f"💎 3 Oylik = {PRICES['3m']}\n"
        f"💎 6 Oylik = {PRICES['6m']}\n"
        f"💎 1 Yillik = {PRICES['12m']}\n\n"
        "<i>‼️ Chekni Yuborgach Biroz Kuting. Odatda 5-15 Daqiqada Javob olasiz. "
        "Ammo Hayot mamot masalalari bilan bo'lib qolgan paytlar 6-12 soatgacha "
        "kutishga to'g'ri kelishi mumkin. Albatta bunaqasi kam bo'ladi ‼️</i>\n\n"
        "<b>Premiumga qo'shilish uchun 2 amalni bajaring!</b>\n\n"
        "1. Kanalga o'tishni bosing\n"
        "2. Chek Tashlang! Shuketma-ketliksiz obuna ololmaysiz\n\n"
        "Pastdagi Havolaga bosing va Qo'shilish so'rovini yuboring! "
        "Keyin esa To'lov qilib rasm yuboring! 👇\n\n"
        f'🔗 <a href="{channel_link}">Kanalga O\'tish</a>\n\n'
        f"💳 <b>To'lov Karta Raqami:</b>\n"
        f"<code>{card}</code>\n"
        f"Shaxs: {name}\n\n"
        "📸 <b>Chekni Rasm Formatida Yuboring!</b>"
    )


def support_text(username: str, phone: str) -> str:
    return (
        f"<b>X-Dubbing Support</b> @{username}\n"
        f"{phone}\n\n"
        "Iltimos Aniq maqsad bilan murojaat qiling yordam beramiz!"
    )


def payment_admin_text(
    transaction_id: str,
    full_name: str,
    username: str | None,
    user_id: int,
    created_at: str,
) -> str:
    uname = f"@{username}" if username else "@—"
    return (
        "🧾 <b>YANGI TO'LOV CHEKI</b>\n\n"
        f"🆔 Tranzaksiya: <code>{transaction_id}</code>\n"
        f"👤 Foydalanuvchi: {full_name}\n"
        f"🌐 Username: {uname}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"🕐 Vaqt: {created_at}"
    )


def subscription_approved_text(plan_label: str) -> str:
    return (
        f"✅ <b>Muvaffaqiyatli!</b>\n\n"
        f"Sizning obunangiz tasdiqlandi: <b>{plan_label}</b>\n"
        "Yopiq guruhga qo'shildingiz. Marhamat!"
    )


def subscription_rejected_text() -> str:
    return (
        "❌ <b>Bekor qilingan Amal</b>\n\n"
        "Iltimos chekni qayta tekshiring va to'g'ri chekni yuboring."
    )
