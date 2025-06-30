import logging
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# ---------------------------------------------
# SETTINGS
# ---------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

OPERATOR_CHAT_ID = 1138693316  # ID администратора (куда пересылаются сообщения)

# Состояния для ConversationHandler:
ASK_QUESTION = 1     # Основное состояние для сообщений пользователей ("Не нашел ответа")
ADMIN_REPLY = 11     # Мини-диалог: админ отвечает пользователю
USER_REPLY = 12      # Мини-диалог: пользователь отвечает админу

MAIN_MENU_PHOTO_URL = "https://i.imgur.com/451wLeS.png"
MAIN_MENU_TEXT = (
    "Ниже расположено меню с типовыми ситуациями. Пожалуйста ознакомьтесь, "
    "нажав на соответствующую кнопку.\n\n"
    "Если мы решили Ваш вопрос, просим поставить ★★★★★ или скорректировать оценку, "
    "либо дополнить отзыв.\n"
    "С Уважением, TITAN STYLE!"
)

CONTACT_TEXT = (
    "<b>Если вы не нашли ответа на свой вопрос:</b>\n"
    "Опишите, пожалуйста, проблему текстом ниже и прикрепите фото или видео товара, если это необходимо "
    "[<b>ОБЯЗАТЕЛЬНО вместе с текстом</b>].\n"
    "(Также желательно указать время оформления заявки на возврат или заказа товара, а также номер Заказа.)\n\n"
    "Вскоре с вами свяжется <b>специалист гарантийной службы</b>."
)

# ---------------------------------------------
# KEYBOARD FUNCTIONS
# ---------------------------------------------
def get_main_menu_keyboard():
    """Главное меню: кнопки расположены столбиком."""
    keyboard = [
        [InlineKeyboardButton("✅ Сможем помочь +", callback_data="approve")],
        [InlineKeyboardButton("❌ НЕ Сможем помочь -", callback_data="reject")],
        [InlineKeyboardButton("💬 Не нашел ответа", callback_data="contact")],
        [InlineKeyboardButton("МЫ НА ОЗОН", url="https://www.ozon.ru/seller/titan-style-1468753/products/?miniapp=seller_1468753")],
        [InlineKeyboardButton("МЫ НА ВБ", url="https://www.wildberries.ru/brands/310806956-titan-style/galstuki")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_nav_keyboard():
    """Навигация: кнопки 'Назад' и 'Главное меню'."""
    keyboard = [
        [
            InlineKeyboardButton("🔙 Назад", callback_data="back"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_continue_keyboard():
    """Клавиатура: 'Дополнить обращение' и 'Завершить'."""
    keyboard = [
        [
            InlineKeyboardButton("Дополнить обращение", callback_data="add_more"),
            InlineKeyboardButton("Завершить", callback_data="done")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_reply_button(user_id: int):
    """Кнопка 'Ответить' для администратора, callback_data = "admin_reply_<user_id>"."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Ответить", callback_data=f"admin_reply_{user_id}")]
    ])

def user_reply_button():
    """Кнопка 'Ответить админу' для пользователя."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Ответить админу", callback_data="user_reply")]
    ])

# ---------------------------------------------
# HANDLERS
# ---------------------------------------------
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start: отправляет фото главного меню с подписью и клавиатурой."""
    await update.message.reply_photo(
        photo=MAIN_MENU_PHOTO_URL,
        caption=MAIN_MENU_TEXT,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка основных кнопок меню:
      - "approve": отправляем фото https://i.imgur.com/ZLQxRGb.png;
      - "reject": отправляем фото https://i.imgur.com/IxAb3Pu.png;
      - "contact": отправляем инструкцию CONTACT_TEXT и переходим в состояние ASK_QUESTION;
      - "back"/"main_menu": отправляем фото главного меню;
      - "add_more": оставляем диалог открытым;
      - "done": завершаем диалог и возвращаем фото главного меню;
      - Если callback_data начинается с "admin_reply_" или равна "user_reply", передаём в мини-диалоги.
    """
    query = update.callback_query
    data = query.data
    await query.answer()
    try:
        await query.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения: {e}")

    if data == "approve":
        await query.message.chat.send_photo(
            photo="https://i.imgur.com/ZLQxRGb.png",
            reply_markup=get_nav_keyboard()
        )
        return ASK_QUESTION

    elif data == "reject":
        await query.message.chat.send_photo(
            photo="https://i.imgur.com/IxAb3Pu.png",
            reply_markup=get_nav_keyboard()
        )
        return ConversationHandler.END

    elif data == "contact":
        await query.message.chat.send_message(
            text=CONTACT_TEXT,
            parse_mode="HTML",
            reply_markup=get_nav_keyboard()
        )
        return ASK_QUESTION

    elif data in ["back", "main_menu"]:
        await query.message.chat.send_photo(
            photo=MAIN_MENU_PHOTO_URL,
            caption=MAIN_MENU_TEXT,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END

    elif data == "add_more":
        await query.message.chat.send_message(
            text="Опишите вашу проблему дополнительно или прикрепите новые файлы.",
            parse_mode="HTML",
            reply_markup=get_nav_keyboard()
        )
        return ASK_QUESTION

    elif data == "done":
        await query.message.chat.send_photo(
            photo=MAIN_MENU_PHOTO_URL,
            caption=MAIN_MENU_TEXT,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END

    elif data.startswith("admin_reply_"):
        return await admin_reply_start(update, context)

    elif data == "user_reply":
        return await user_reply_start(update, context)

    return ConversationHandler.END

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка текстового сообщения в состоянии ASK_QUESTION.
    Пересылаем сообщение администратору с кнопкой "Ответить" и предлагаем дополнить обращение.
    """
    user_text = update.message.text
    message_text = (
        f"<b>Обращение от:</b> {update.message.from_user.first_name} "
        f"{update.message.from_user.last_name or ''} (@{update.message.from_user.username or 'нет'})\n"
        f"<b>User ID:</b> {update.message.from_user.id}\n\n"
        f"<b>Сообщение:</b> {user_text}"
    )
    await context.bot.send_message(
        chat_id=OPERATOR_CHAT_ID,
        text=message_text,
        parse_mode="HTML",
        reply_markup=admin_reply_button(update.message.from_user.id)
    )
    await update.message.reply_text(
        "Сообщение получено. Хотите что-то дополнить?",
        parse_mode="HTML",
        reply_markup=get_continue_keyboard()
    )
    return ASK_QUESTION

async def attachment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка вложений (документы, фото, видео) в состоянии ASK_QUESTION.
    Пересылаем сообщение администратору с кнопкой "Ответить" и предлагаем дополнить обращение.
    """
    user_info = (
        f"<b>Обращение от:</b> {update.message.from_user.first_name} "
        f"{update.message.from_user.last_name or ''} (@{update.message.from_user.username or 'нет'})\n"
        f"<b>User ID:</b> {update.message.from_user.id}\n"
    )
    if update.message.document:
        doc = update.message.document
        file = await doc.get_file()
        file_path = f"user_doc_{update.message.from_user.id}_{doc.file_unique_id}"
        await file.download_to_drive(file_path)
        caption = user_info + "<i>Пользователь отправил документ.</i>"
        with open(file_path, "rb") as f:
            await context.bot.send_document(
                chat_id=OPERATOR_CHAT_ID,
                document=f,
                caption=caption,
                parse_mode="HTML",
                reply_markup=admin_reply_button(update.message.from_user.id)
            )
    elif update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = f"user_photo_{update.message.from_user.id}_{photo.file_unique_id}.jpg"
        await file.download_to_drive(file_path)
        caption = user_info + "<i>Пользователь отправил фото.</i>"
        with open(file_path, "rb") as f:
            await context.bot.send_photo(
                chat_id=OPERATOR_CHAT_ID,
                photo=f,
                caption=caption,
                parse_mode="HTML",
                reply_markup=admin_reply_button(update.message.from_user.id)
            )
    elif update.message.video:
        video = update.message.video
        file = await video.get_file()
        file_path = f"user_video_{update.message.from_user.id}_{video.file_unique_id}.mp4"
        await file.download_to_drive(file_path)
        caption = user_info + "<i>Пользователь отправил видео.</i>"
        with open(file_path, "rb") as f:
            await context.bot.send_video(
                chat_id=OPERATOR_CHAT_ID,
                video=f,
                caption=caption,
                parse_mode="HTML",
                reply_markup=admin_reply_button(update.message.from_user.id)
            )
    await update.message.reply_text(
        "Файл получен. Хотите что-то дополнить?",
        parse_mode="HTML",
        reply_markup=get_continue_keyboard()
    )
    return ASK_QUESTION

async def not_in_conversation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Если сообщение приходит вне диалога, предлагаем вернуться в главное меню.
    """
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Чтобы отправить сообщение, пожалуйста, нажмите кнопку «💬 Не нашел ответа» в главном меню.",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /cancel — завершает текущий диалог."""
    await update.message.reply_text("Операция отменена.", parse_mode="HTML")
    return ConversationHandler.END

# ---------------------------------------------
# MINI DIALOG: ADMIN -> USER
# ---------------------------------------------
async def admin_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Старт мини-диалога: админ нажал кнопку "Ответить" (callback_data вида "admin_reply_<user_id>").
    Извлекаем user_id и переводим админа в состояние ADMIN_REPLY.
    """
    query = update.callback_query
    await query.answer()
    try:
        user_id = int(query.data.split("_")[-1])
    except ValueError:
        await query.message.reply_text("Ошибка: не удалось извлечь ID пользователя.")
        return ConversationHandler.END
    context.user_data["reply_to_user_id"] = user_id
    try:
        await query.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения: {e}")
    await query.message.chat.send_message(
        text=f"Введите текст ответа пользователю {user_id} или пришлите фото/документ/видео.",
        parse_mode="HTML"
    )
    return ADMIN_REPLY

async def admin_reply_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстового ответа администратора в состоянии ADMIN_REPLY."""
    if "reply_to_user_id" not in context.user_data:
        await update.message.reply_text("Неизвестен пользователь для ответа.", parse_mode="HTML")
        return ConversationHandler.END
    user_id = context.user_data["reply_to_user_id"]
    answer_text = update.message.text
    message = f"<b>Сообщение от администратора:</b>\n{answer_text}"
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="HTML",
            reply_markup=user_reply_button()
        )
        await update.message.reply_text(
            f"Ваш ответ отправлен пользователю {user_id}.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения пользователю: {e}")
        await update.message.reply_text("Ошибка при отправке ответа пользователю.", parse_mode="HTML")
    context.user_data.pop("reply_to_user_id", None)
    return ConversationHandler.END

async def admin_reply_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка вложения от администратора в состоянии ADMIN_REPLY."""
    if "reply_to_user_id" not in context.user_data:
        await update.message.reply_text("Неизвестен пользователь для ответа.", parse_mode="HTML")
        return ConversationHandler.END
    user_id = context.user_data["reply_to_user_id"]

    if update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = f"admin_reply_photo_{update.message.from_user.id}_{photo.file_unique_id}.jpg"
        await file.download_to_drive(file_path)
        caption = "<b>Сообщение от администратора:</b>"
        try:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=open(file_path, "rb"),
                caption=caption,
                parse_mode="HTML",
                reply_markup=user_reply_button()
            )
            await update.message.reply_text(f"Ваш ответ (фото) отправлен пользователю {user_id}.", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при отправке фото: {e}")
            await update.message.reply_text("Ошибка при отправке фото пользователю.", parse_mode="HTML")
    elif update.message.document:
        doc = update.message.document
        file = await doc.get_file()
        file_path = f"admin_reply_doc_{update.message.from_user.id}_{doc.file_unique_id}"
        await file.download_to_drive(file_path)
        caption = "<b>Сообщение от администратора:</b>"
        try:
            await context.bot.send_document(
                chat_id=user_id,
                document=open(file_path, "rb"),
                caption=caption,
                parse_mode="HTML",
                reply_markup=user_reply_button()
            )
            await update.message.reply_text(f"Ваш ответ (документ) отправлен пользователю {user_id}.", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при отправке документа: {e}")
            await update.message.reply_text("Ошибка при отправке документа пользователю.", parse_mode="HTML")
    elif update.message.video:
        video = update.message.video
        file = await video.get_file()
        file_path = f"admin_reply_video_{update.message.from_user.id}_{video.file_unique_id}.mp4"
        await file.download_to_drive(file_path)
        caption = "<b>Сообщение от администратора:</b>"
        try:
            await context.bot.send_video(
                chat_id=user_id,
                video=open(file_path, "rb"),
                caption=caption,
                parse_mode="HTML",
                reply_markup=user_reply_button()
            )
            await update.message.reply_text(f"Ваш ответ (видео) отправлен пользователю {user_id}.", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при отправке видео: {e}")
            await update.message.reply_text("Ошибка при отправке видео пользователю.", parse_mode="HTML")
    context.user_data.pop("reply_to_user_id", None)
    return ConversationHandler.END

# ---------------------------------------------
# MINI DIALOG: USER -> ADMIN
# ---------------------------------------------
async def user_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт мини-диалога: пользователь нажал кнопку "Ответить админу"."""
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения: {e}")
    context.user_data["reply_to_admin"] = True
    await query.message.chat.send_message(
        text="Введите текст ответа администратору или прикрепите фото/документ/видео.",
        parse_mode="HTML"
    )
    return USER_REPLY

async def user_reply_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь прислал текст ответа в состоянии USER_REPLY."""
    if "reply_to_admin" not in context.user_data:
        await update.message.reply_text("Невозможно определить, кому вы отвечаете.", parse_mode="HTML")
        return ConversationHandler.END
    user_text = update.message.text
    message = (
        f"<b>Ответ от пользователя:</b> {update.message.from_user.first_name}\n"
        f"<b>User ID:</b> {update.message.from_user.id}\n\n"
        f"{user_text}"
    )
    try:
        await context.bot.send_message(
            chat_id=OPERATOR_CHAT_ID,
            text=message,
            parse_mode="HTML",
            reply_markup=admin_reply_button(update.message.from_user.id)
        )
        await update.message.reply_text("Ваш ответ отправлен администратору.", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа админу: {e}")
        await update.message.reply_text("Ошибка при отправке ответа админу.", parse_mode="HTML")
    context.user_data.pop("reply_to_admin", None)
    return ConversationHandler.END

async def user_reply_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь прислал вложение в состоянии USER_REPLY."""
    if "reply_to_admin" not in context.user_data:
        await update.message.reply_text("Невозможно определить, кому вы отвечаете.", parse_mode="HTML")
        return ConversationHandler.END
    admin_id = OPERATOR_CHAT_ID
    if update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = f"user_reply_photo_{update.message.from_user.id}_{photo.file_unique_id}.jpg"
        await file.download_to_drive(file_path)
        caption = f"<b>Ответ от пользователя:</b> {update.message.from_user.first_name}"
        try:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=open(file_path, "rb"),
                caption=caption,
                parse_mode="HTML",
                reply_markup=admin_reply_button(update.message.from_user.id)
            )
            await update.message.reply_text("Ваш ответ (фото) отправлен администратору.", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при отправке фото админу: {e}")
            await update.message.reply_text("Ошибка при отправке фото администратору.", parse_mode="HTML")
    elif update.message.document:
        doc = update.message.document
        file = await doc.get_file()
        file_path = f"user_reply_doc_{update.message.from_user.id}_{doc.file_unique_id}"
        await file.download_to_drive(file_path)
        caption = f"<b>Ответ от пользователя:</b> {update.message.from_user.first_name}"
        try:
            await context.bot.send_document(
                chat_id=admin_id,
                document=open(file_path, "rb"),
                caption=caption,
                parse_mode="HTML",
                reply_markup=admin_reply_button(update.message.from_user.id)
            )
            await update.message.reply_text("Ваш ответ (документ) отправлен администратору.", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при отправке документа админу: {e}")
            await update.message.reply_text("Ошибка при отправке документа администратору.", parse_mode="HTML")
    elif update.message.video:
        video = update.message.video
        file = await video.get_file()
        file_path = f"user_reply_video_{update.message.from_user.id}_{video.file_unique_id}.mp4"
        await file.download_to_drive(file_path)
        caption = f"<b>Ответ от пользователя:</b> {update.message.from_user.first_name}"
        try:
            await context.bot.send_video(
                chat_id=admin_id,
                video=open(file_path, "rb"),
                caption=caption,
                parse_mode="HTML",
                reply_markup=admin_reply_button(update.message.from_user.id)
            )
            await update.message.reply_text("Ваш ответ (видео) отправлен администратору.", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при отправке видео админу: {e}")
            await update.message.reply_text("Ошибка при отправке видео администратору.", parse_mode="HTML")
    context.user_data.pop("reply_to_admin", None)
    return ConversationHandler.END

# ---------------------------------------------
# MAIN HANDLERS
# ---------------------------------------------
async def not_in_conversation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Если сообщение приходит вне диалога, предлагаем вернуться в главное меню."""
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Чтобы отправить сообщение, пожалуйста, нажмите кнопку «💬 Не нашел ответа» в главном меню.",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /cancel — завершает текущий диалог."""
    await update.message.reply_text("Операция отменена.", parse_mode="HTML")
    return ConversationHandler.END

# ---------------------------------------------
# MAIN
# ---------------------------------------------
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_main = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^(contact)$")],
        states={
            ASK_QUESTION: [
                MessageHandler(filters.Document.ALL | filters.VIDEO | filters.PHOTO, attachment_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler),
                CallbackQueryHandler(button_handler, pattern="^(add_more|done|back|main_menu)$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        allow_reentry=True
    )

    conv_reply = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_reply_start, pattern=r"^admin_reply_\d+$"),
            CallbackQueryHandler(user_reply_start, pattern="^user_reply$")
        ],
        states={
            ADMIN_REPLY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reply_text),
                MessageHandler(filters.Document.ALL | filters.VIDEO | filters.PHOTO, admin_reply_attachment)
            ],
            USER_REPLY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, user_reply_text),
                MessageHandler(filters.Document.ALL | filters.VIDEO | filters.PHOTO, user_reply_attachment)
            ]
        },
        fallbacks=[],
        allow_reentry=True
    )

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(conv_main)
    application.add_handler(conv_reply)
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(approve|reject|back|main_menu)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, not_in_conversation_handler))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO | filters.PHOTO, not_in_conversation_handler))

    application.run_polling()

if __name__ == '__main__':
    main()
