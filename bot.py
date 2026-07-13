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

# ---------- Tugma matnlari ----------
BTN_STATS = "📊 Statistika"
BTN_ADD_MOVIE = "🎬 Kino joylash"
BTN_ADD_SERIES = "📺 Serial joylash"
BTN_FIND_CODES = "🔍 Kino kodlarini topish"

# Admin uchun 2x2 klaviatura
ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    [[BTN_STATS, BTN_ADD_MOVIE], [BTN_ADD_SERIES, BTN_FIND_CODES]],
    resize_keyboard=True,
)

# Oddiy foydalanuvchi uchun klaviatura
USER_KEYBOARD = ReplyKeyboardMarkup([[BTN_FIND_CODES]], resize_keyboard=True)

# Kino qo'shish suhbati holatlari
WAITING_VIDEO, WAITING_CODE = range(2)

# Serial qo'shish suhbati holatlari
SERIES_CODE, SERIES_TITLE, SERIES_EP_NUM, SERIES_EP_VIDEO, SERIES_CONTINUE = range(2, 7)


# ---------- Obuna tekshirish ----------

def build_channels_keyboard() -> InlineKeyboardMarkup:
    """Kanal tugmalarini 2 tadan yonma-yon joylaydi."""
    buttons = [InlineKeyboardButton(ch["name"], url=ch["url"]) for ch in CHANNELS]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(rows)


async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    for ch in CHANNELS:
        chat_id = ch["id"]
        if not chat_id:
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
            f"Assalomu alaykum, <b>{user.first_name}</b>! 🎬\n\n"
            f"Kino kodini yuboring.",
            parse_mode=ParseMode.HTML,
            reply_markup=USER_KEYBOARD,
        )
    else:
        await send_subscribe_prompt(update)


async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    if await is_subscribed(user.id, context):
        await query.edit_message_text("✅ Obuna tasdiqlandi!")
        await query.message.reply_text(
            f"Assalomu alaykum, <b>{user.first_name}</b>! 🎬\n\n"
            f"Kino kodini yuboring.",
            parse_mode=ParseMode.HTML,
            reply_markup=USER_KEYBOARD,
        )
    else:
        await query.answer(
            "❌ Siz hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True
        )


# ---------- Serial qismlarini tanlash (foydalanuvchi tomonidan) ----------

def build_episodes_keyboard(series_code: str, numbers: list) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(f"{n}-qism", callback_data=f"ep:{series_code}:{n}")
        for n in numbers
    ]
    rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
    return InlineKeyboardMarkup(rows)


async def send_episode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, series_code, ep_num = query.data.split(":")
    file_id = db.get_episode(series_code, int(ep_num))
    if file_id:
        await query.message.reply_video(video=file_id, caption=f"{ep_num}-qism")
    else:
        await query.answer("Qism topilmadi.", show_alert=True)


# ---------- Kino kodlarini topish (hammaga) ----------

CODES_CHANNEL_URL = "https://t.me/shoxona_kinolar"


async def show_codes(update: Update):
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📂 Kino kodlari kanaliga o'tish", url=CODES_CHANNEL_URL)]]
    )
    await update.message.reply_text(
        "Barcha kino kodlarini shu kanaldan topishingiz mumkin 👇",
        reply_markup=keyboard,
    )


# ---------- Kino/serial kodini qabul qilish ----------

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

    if text == BTN_FIND_CODES:
        await show_codes(update)
        return

    if not await is_subscribed(user.id, context):
        await send_subscribe_prompt(update)
        return

    movie = db.get_movie(text)
    if movie:
        file_id, caption = movie
        await update.message.reply_video(video=file_id, caption=caption or None)
        return

    series_title = db.get_series(text)
    if series_title:
        numbers = db.get_episode_numbers(text)
        if numbers:
            await update.message.reply_text(
                f"📺 <b>{series_title}</b>\nQaysi qismni ko'rmoqchisiz?",
                parse_mode=ParseMode.HTML,
                reply_markup=build_episodes_keyboard(text, numbers),
            )
        else:
            await update.message.reply_text("Bu serialga hali qism qo'shilmagan.")
        return

    await update.message.reply_text(
        "❌ Bunday kodli kino yoki serial topilmadi. Kodni tekshirib qayta yuboring."
    )


# ---------- Admin: statistika ----------

async def show_stats(update: Update):
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar soni: {db.count_users()}\n"
        f"🎬 Kinolar soni: {db.count_movies()}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=ADMIN_KEYBOARD)


# ---------- Admin: kino qo'shish ----------

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


# ---------- Admin: serial qo'shish ----------

async def start_add_series(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📺 Serial kodini kiriting (masalan: 5):", reply_markup=ReplyKeyboardRemove()
    )
    return SERIES_CODE


async def receive_series_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["series_code"] = update.message.text.strip()
    await update.message.reply_text("Serial nomini kiriting (masalan: Ertak podshosi):")
    return SERIES_TITLE


async def receive_series_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = context.user_data["series_code"]
    title = update.message.text.strip()
    db.add_series(code, title)
    await update.message.reply_text("Nechinchi qism ekanini kiriting (masalan: 1):")
    return SERIES_EP_NUM


async def receive_episode_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Iltimos, faqat raqam kiriting (masalan: 1).")
        return SERIES_EP_NUM
    context.user_data["episode_number"] = int(text)
    await update.message.reply_text(f"{text}-qism videosini yuboring:")
    return SERIES_EP_VIDEO


async def receive_episode_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.video:
        await update.message.reply_text("Iltimos, video fayl yuboring.")
        return SERIES_EP_VIDEO

    code = context.user_data["series_code"]
    ep_num = context.user_data["episode_number"]
    db.add_episode(code, ep_num, update.message.video.file_id)

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("➕ Yana qism qo'shish", callback_data="series_continue"),
                InlineKeyboardButton("✅ Tugatish", callback_data="series_finish"),
            ]
        ]
    )
    await update.message.reply_text(f"✅ {ep_num}-qism saqlandi!", reply_markup=keyboard)
    return SERIES_CONTINUE


async def handle_series_continue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "series_continue":
        await query.edit_message_text("Nechinchi qism ekanini kiriting (masalan: 2):")
        return SERIES_EP_NUM

    await query.edit_message_text("✅ Serial saqlandi!")
    await query.message.reply_text("Admin panel:", reply_markup=ADMIN_KEYBOARD)
    context.user_data.pop("series_code", None)
    context.user_data.pop("episode_number", None)
    return ConversationHandler.END


async def cancel_add_series(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("series_code", None)
    context.user_data.pop("episode_number", None)
    await update.message.reply_text("Bekor qilindi.", reply_markup=ADMIN_KEYBOARD)
    return ConversationHandler.END


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN sozlanmagan!")

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

    add_series_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{BTN_ADD_SERIES}$"), start_add_series)],
        states={
            SERIES_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_series_code)],
            SERIES_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_series_title)],
            SERIES_EP_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_episode_number)],
            SERIES_EP_VIDEO: [MessageHandler(filters.VIDEO, receive_episode_video)],
            SERIES_CONTINUE: [CallbackQueryHandler(handle_series_continue, pattern="^series_(continue|finish)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_series)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(add_movie_conv)
    app.add_handler(add_series_conv)
    app.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(send_episode_callback, pattern="^ep:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
