import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatPermissions, Update
from telegram.ext.callbackcontext import CallbackContext

# Токен берём из переменных окружения Railway
TOKEN = os.getenv("8407685621:AAGCRfidEQ_oE5jZfabFufCaKyxJkhVgSBA")

# Ограниченные права (новичок = mute)
restricted_permissions = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_invite_users=False,
    can_pin_messages=False,
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

# Когда новый юзер заходит → мутим
def welcome(update: Update, context: CallbackContext):
    for member in update.message.new_chat_members:
        context.bot.restrict_chat_member(
            chat_id=update.message.chat.id,
            user_id=member.id,
            permissions=restricted_permissions,
        )
        update.message.reply_text(
            f"👋 Привет, {member.mention_html()}! Ожидай подтверждения от админа.",
            parse_mode="HTML"
        )

# Команда /approve → размут
def approve(update: Update, context: CallbackContext):
    if update.message.reply_to_message:  
        user_id = update.message.reply_to_message.from_user.id
        username = update.message.reply_to_message.from_user.mention_html()
    else:
        update.message.reply_text("❌ Используй /approve в ответ на сообщение пользователя")
        return

    context.bot.restrict_chat_member(
        chat_id=update.message.chat.id,
        user_id=user_id,
        permissions=full_permissions,
    )
    update.message.reply_text(f"✅ {username} получил доступ!", parse_mode="HTML")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
    dp.add_handler(CommandHandler("approve", approve))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
