import os
import logging
from telegram import ChatPermissions, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext.callbackcontext import CallbackContext
from telegram.error import BadRequest, TelegramError
from telegram.utils.helpers import mention_html

# ====== Config ======
# Токен читаем из переменной окружения TOKEN (Railway → Variables)
TOKEN = os.getenv("TOKEN")

# Логирование (видно в Railway logs)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Ограниченные права (новичок = mute)
restricted_permissions = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_invite_users=False,
)

# Полные права (размут)
full_permissions = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_invite_users=True,
)

def is_user_admin(context: CallbackContext, chat_id: int, user_id: int) -> bool:
    try:
        member = context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except TelegramError as e:
        logger.warning("Не удалось проверить права администратора: %s", e)
        return False

# Когда новый юзер заходит → мутим
def welcome(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    for member in update.message.new_chat_members:
        try:
            context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=member.id,
                permissions=restricted_permissions,
            )
            update.message.reply_text(
                f"👋 Привет, {mention_html(member.id, member.full_name)}! Ожидай подтверждения от админа.",
                parse_mode="HTML",
            )
            logger.info("Замутили нового участника %s (%s) в чате %s", member.full_name, member.id, chat_id)
        except BadRequest as e:
            logger.error("Не удалось ограничить пользователя %s: %s", member.id, e)
        except TelegramError as e:
            logger.exception("Ошибка Telegram при ограничении пользователя: %s", e)

# Команда /approve → размут (только для админов, запускать в ответ на сообщение)
def approve(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    from_id = update.effective_user.id

    # Только админы
    if not is_user_admin(context, chat_id, from_id):
        update.message.reply_text("❌ Только администратор может подтверждать доступ.")
        return

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        user_id = target_user.id
        username_html = mention_html(target_user.id, target_user.full_name)
    else:
        update.message.reply_text("❌ Используй /approve в ответ на сообщение пользователя, которого хочешь размутить.")
        return

    try:
        context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=full_permissions,
        )
        update.message.reply_text(f"✅ {username_html} получил доступ!", parse_mode="HTML")
        logger.info("Размутил пользователя %s (%s) в чате %s", target_user.full_name, user_id, chat_id)
    except BadRequest as e:
        update.message.reply_text(f"⚠️ Не удалось выдать доступ: {e}")
        logger.error("Ошибка при выдаче прав пользователю %s: %s", user_id, e)
    except TelegramError as e:
        logger.exception("Ошибка Telegram при выдаче прав: %s", e)

def error_handler(update: object, context: CallbackContext):
    logger.exception("Исключение при обработке апдейта: %s", context.error)

def main():
    if not TOKEN:
        raise RuntimeError("Не задан TOKEN в переменных окружения. В Railway добавь Variable: TOKEN=<твой_токен>.")

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
    dp.add_handler(CommandHandler("approve", approve))
    dp.add_error_handler(error_handler)

    logger.info("Бот запущен. Ожидаю события…")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
