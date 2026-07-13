import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import database as db
from config import ADMIN_ID, BOT_TOKEN, CHANNELS

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Admin panel tugmalari
BTN_STATS = "📊 Statistika"
BTN_ADD_MOVIE = "🎬 Kino joylash"
ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    [[BTN_STATS, BTN_ADD_MOVIE]], resize_keyboard=True
)

# Kino qo'shish suhbati uchun holatlar
WAITING_VIDEO, WAITING_CODE = range(2)


# ---------- Obuna tekshirish ----------

def build_channels_keyboard() -> InlineKeyboardMarkup:
    """Kanal tugmalarini 2 tadan yonma-yon joylaydi."""
    buttons = [
        InlineKeyboardButton(ch["name"], url=ch["url"]) for ch in CHANNELS
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(rows)


async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    for ch in CHANNELS:
        chat_id = ch["id"]
        if not chat_id:
            # ID sozlanmagan bo'lsa, tekshirib bo'lmaydi — o'tkazib yuboramiz
            continue
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            if member.status in ("left", "kicked"):
                return False
        except TelegramError as e:
            logger.warning("Obunani tekshirishda xatolik (%s): %s", chat_id, e)
            return False
    return True


async def send_subscribe_prompt(update: Update):
    text = (
        "🎬 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling, "
        "so'ng \"✅ Obunani tekshirish\" tugmasini bosing:"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=build_channels_keyboard()
        )
    else:
        await update.message.reply_text(text, reply_markup=build_channels_keyboard())


# ---------- /start ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    is_new = db.add_user(user.id, user.username or "", user.full_name or "")
    if is_new and user.id != ADMIN_ID:
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"🆕 Yangi foydalanuvchi:\n"
                f"Ism: {user.full_name}\n"
                f"Username: @{user.username if user.username else '—'}\n"
                f"ID: {user.id}",
            )
        except TelegramError:
            pass

    if user.id == ADMIN_ID:
        await update.message.reply_text(
            "👑 Admin panelga xush kelibsiz!", reply_markup=ADMIN_KEYBOARD
        )
        return

    if await is_subscribed(user.id, context):
        await update.message.reply_text(
            "✅ Xush kelibsiz! Endi tayyorsiz, kino kodini yuboring."
        )
    else:
        await send_subscribe_prompt(update)


async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    if await is_subscribed(user.id, context):
        await query.edit_message_text(
            "✅ Obuna tasdiqlandi! Endi tayyorsiz, kino kodini yuboring."
        )
    else:
        await query.answer(
            "❌ Siz hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True
        )


# ---------- Kino kodini qabul qilish (oddiy foydalanuvchi) ----------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()

    if user.id == ADMIN_ID:
        if text == BTN_STATS:
            await show_stats(update)
            return
        if text == BTN_ADD_MOVIE:
            await update.message.reply_text(
                "🎬 Kino videosini yuboring.", reply_markup=ReplyKeyboardRemove()
            )
            return WAITING_VIDEO

    if not await is_subscribed(user.id, context):
        await send_subscribe_prompt(update)
        return

    movie = db.get_movie(text)
    if movie:
        file_id, caption = movie
        await update.message.reply_video(video=file_id, caption=caption or None)
    else:
        await update.message.reply_text(
            "❌ Bunday kodli kino topilmadi. Kodni tekshirib qayta yuboring."
        )


# ---------- Admin: statistika ----------

async def show_stats(update: Update):
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar soni: {db.count_users()}\n"
        f"🎬 Kinolar soni: {db.count_movies()}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=ADMIN_KEYBOARD)


# ---------- Admin: kino qo'shish (ConversationHandler) ----------

async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.video:
        await update.message.reply_text("Iltimos, video fayl yuboring.")
        return WAITING_VIDEO

    context.user_data["pending_file_id"] = update.message.video.file_id
    await update.message.reply_text("Endi shu kino uchun kod kiriting (masalan: 101):")
    return WAITING_CODE


async def receive_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    file_id = context.user_data.get("pending_file_id")

    if not file_id:
        await update.message.reply_text("Xatolik yuz berdi, qaytadan boshlang.", reply_markup=ADMIN_KEYBOARD)
        return ConversationHandler.END

    db.add_movie(code, file_id, caption=f"Kino kodi: {code}")
    context.user_data.pop("pending_file_id", None)

    await update.message.reply_text(
        f"✅ Kino saqlandi! Kod: {code}", reply_markup=ADMIN_KEYBOARD
    )
    return ConversationHandler.END


async def cancel_add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("pending_file_id", None)
    await update.message.reply_text("Bekor qilindi.", reply_markup=ADMIN_KEYBOARD)
    return ConversationHandler.END


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN sozlanmagan! .env faylini tekshiring.")

    db.init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    add_movie_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{BTN_ADD_MOVIE}$"), handle_text)],
        states={
            WAITING_VIDEO: [MessageHandler(filters.VIDEO, receive_video)],
            WAITING_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_movie)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(add_movie_conv)
    app.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_sub$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
