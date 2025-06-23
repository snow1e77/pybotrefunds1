import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# -------------------------------------------------
# INITIAL CONFIGURATION
# -------------------------------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Secrets are supplied via environment variables -> Render Dashboard ➜ Environment
TOKEN = os.environ["BOT_TOKEN"]                       # Telegram bot token
OPERATOR_CHAT_ID = int(os.environ.get("OPERATOR_CHAT_ID", "1138693316"))

# For webhook hosting on Render
WEBHOOK_HOST = os.environ["WEBHOOK_HOST"]             # e.g. https://refunds-bot.onrender.com
PORT = int(os.environ.get("PORT", 10000))             # Render passes chosen port here
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# -------------------------------------------------
# STATE CONSTANTS
# -------------------------------------------------
ASK_QUESTION = 1
ADMIN_REPLY = 11
USER_REPLY = 12

# -------------------------------------------------
# STATIC TEXT & IMAGES
# -------------------------------------------------
MAIN_MENU_PHOTO_URL = "https://i.imgur.com/451wLeS.png"
MAIN_MENU_TEXT = (
    "Ниже расположено меню с типовыми ситуациями.\n"
    "Пожалуйста ознакомьтесь, нажав на соответствующую кнопку.\n\n"
    "Если мы решили Ваш вопрос, просим поставить ★★★★★ или скорректировать оценку, "
    "либо дополнить отзыв.\n"
    "С Уважением, TITAN STYLE!"
)

CONTACT_TEXT = (
    "Если вы не нашли ответа на свой вопрос:\n"
    "Опишите, пожалуйста, проблему текстом ниже и прикрепите фото или видео товара, если это необходимо "
    "[ОБЯЗАТЕЛЬНО вместе с текстом].\n"
    "(Также желательно указать время оформления заявки на возврат или заказа товара, а также номер Заказа.)\n\n"
    "Вскоре с вами свяжется специалист гарантийной службы."
)

# -------------------------------------------------
# KEYBOARDS
# -------------------------------------------------

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("✅ Сможем помочь +", callback_data="approve")],
        [InlineKeyboardButton("❌ НЕ Сможем помочь -", callback_data="reject")],
        [InlineKeyboardButton("❓ Не нашел ответа", callback_data="contact")],
        [InlineKeyboardButton("🛍 МЫ НА ОЗОН", url="https://www.ozon.ru/seller/titan-style-1468753/products/?miniapp=seller_1468753")],
        [InlineKeyboardButton("🛍 МЫ НА ВБ", url="https://www.wildberries.ru/brands/310806956-titan-style/galstuki")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_nav_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Назад", callback_data="back"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_continue_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("✏️ Дополнить обращение", callback_data="add_more"),
            InlineKeyboardButton("✅ Завершить", callback_data="done"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_reply_button(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Ответить", callback_data=f"admin_reply_{user_id}")]]
    )

def user_reply_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Ответить админу", callback_data="user_reply")]]
    )

# -------------------------------------------------
# HANDLERS
# -------------------------------------------------

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_photo(
        photo=MAIN_MENU_PHOTO_URL,
        caption=MAIN_MENU_TEXT,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(),
    )

# ---------- Common button dispatcher ----------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    # Удаляем сообщение с кнопкой (если можно)
    try:
        await query.message.delete()
    except Exception as e:
        logger.warning("Не удалось удалить сообщение: %s", e)

    if data == "approve":
        await query.message.chat.send_photo(
            photo="https://i.imgur.com/ZLQxRGb.png",
            reply_markup=get_nav_keyboard(),
        )
        return ASK_QUESTION

    elif data == "reject":
        await query.message.chat.send_photo(
            photo="https://i.imgur.com/IxAb3Pu.png",
            reply_markup=get_nav_keyboard(),
        )
        return ConversationHandler.END

    elif data == "contact":
        await query.message.chat.send_message(
            text=CONTACT_TEXT,
            parse_mode="HTML",
            reply_markup=get_nav_keyboard(),
        )
        return ASK_QUESTION

    elif data in ("back", "main_menu"):
        await query.message.chat.send_photo(
            photo=MAIN_MENU_PHOTO_URL,
            caption=MAIN_MENU_TEXT,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    elif data == "add_more":
        await query.message.chat.send_message(
            text="Опишите вашу проблему дополнительно или прикрепите новые файлы.",
            parse_mode="HTML",
            reply_markup=get_nav_keyboard(),
        )
        return ASK_QUESTION

    elif data == "done":
        await query.message.chat.send_photo(
            photo=MAIN_MENU_PHOTO_URL,
            caption=MAIN_MENU_TEXT,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    # -------------- mini dialogs --------------
    elif data.startswith("admin_reply_"):
        return await admin_reply_start(update, context)

    elif data == "user_reply":
        return await user_reply_start(update, context)

    return ConversationHandler.END

# ---------- ASK_QUESTION state handlers ----------

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_text = update.message.text

    message_text = (
        f"Обращение от: {user.first_name} {user.last_name or ''} "
        f"(@{user.username or 'нет'})\n"
        f"User ID: {user.id}\n\n"
        f"Сообщение: {user_text}"
    )

    await context.bot.send_message(
        chat_id=OPERATOR_CHAT_ID,
        text=message_text,
        parse_mode="HTML",
        reply_markup=admin_reply_button(user.id),
    )

    await update.message.reply_text(
        "Сообщение получено.\nХотите что-то дополнить?",
        parse_mode="HTML",
        reply_markup=get_continue_keyboard(),
    )
    return ASK_QUESTION

async def attachment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Документы / фото / видео в ASK_QUESTION."""
    user = update.message.from_user
    user_info = (
        f"Обращение от: {user.first_name} {user.last_name or ''} "
        f"(@{user.username or 'нет'})\n"
        f"User ID: {user.id}\n"
    )

    # Пересылаем в зависимости от типа
    if update.message.document:
        await context.bot.forward_message(
            chat_id=OPERATOR_CHAT_ID,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id,
        )
        await context.bot.send_message(
            chat_id=OPERATOR_CHAT_ID,
            text=user_info + "Пользователь отправил документ.",
            parse_mode="HTML",
            reply_markup=admin_reply_button(user.id),
        )

    elif update.message.photo:
        await context.bot.forward_message(
            chat_id=OPERATOR_CHAT_ID,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id,
        )
        await context.bot.send_message(
            chat_id=OPERATOR_CHAT_ID,
            text=user_info + "Пользователь отправил фото.",
            parse_mode="HTML",
            reply_markup=admin_reply_button(user.id),
        )

    elif update.message.video:
        await context.bot.forward_message(
            chat_id=OPERATOR_CHAT_ID,
            from_chat
