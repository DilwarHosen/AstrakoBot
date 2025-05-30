import html
from typing import Optional

from AstrakoBot import LOGGER, dispatcher
from AstrakoBot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    connection_status,
    user_admin,
    user_can_ban,
    can_delete,
    is_user_ban_protected,
)
from AstrakoBot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from AstrakoBot.modules.helper_funcs.string_handling import extract_time
from AstrakoBot.modules.log_channel import loggable
from AstrakoBot.modules.helper_funcs.admin_status import get_bot_member, user_is_admin

from telegram import Bot, Chat, ChatPermissions, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram.utils.helpers import mention_html


def check_user(user_id: int, bot: Bot, chat: Chat) -> Optional[str]:
    if not user_id:
        reply = "You don't seem to be referring to a user or the ID specified is incorrect.."
        return reply

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            reply = "I can't seem to find this user"
            return reply
        else:
            raise

    if user_id == bot.id:
        reply = "I'm not gonna MUTE myself, How high are you?"
        return reply

    if is_user_ban_protected(chat, user_id):
        reply = "Can't. Find someone else to mute but not this one."
        return reply

    if user_id in [777000, 1087968824]:
        reply = "Fool! You can't attack Telegram's native tech!"
        return reply

    return None


@connection_status
@bot_admin
@user_admin
@user_can_ban
@can_restrict
@loggable
def mute(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)

    silent = False
    if message.text.startswith("/s") or message.text.startswith("!s"):
        silent = True
        if not can_delete(chat, context.bot.id):
            return ""

    if reply:
        message.reply_text(reply)
        return ""

    member = chat.get_member(user_id)

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#MUTE\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    if member.can_send_messages is None or member.can_send_messages:
        chat_permissions = ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(chat.id, user_id, chat_permissions)
        if not silent:
            reply = (
                f"<code>❕</code><b>Mute Event</b>\n"
                f"<code> </code><b>•  User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
                f"<code> </code><b>•  Time: no expiration date</b>"
            )
            if reason:
                reply += f"\n<code> </code><b>•  Reason:</b> {html.escape(reason)}"
            bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML)
        else:
            message.delete()
        return log

    else:
        if not silent:
            message.reply_text("This user is already muted!")
        else:
            message.delete()

    return ""


@connection_status
@bot_admin
@user_admin
@user_can_ban
@can_restrict
@loggable
def unmute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    silent = False
    if message.text.startswith("/s") or message.text.startswith("!s"):
        silent = True
        if not can_delete(chat, context.bot.id):
            return ""

    user_id = extract_user(message, args)
    if not user_id:
        if silent:
            message.delete()
        else:
            message.reply_text(
                "You'll need to either give me a username to unmute, or reply to someone to be unmuted."
            )
        return ""

    member = chat.get_member(int(user_id))

    if member.status != "kicked" and member.status != "left":
        if (
            member.can_send_messages is not False
            and member.can_send_media_messages is not False
            and member.can_send_other_messages is not False
            and member.can_add_web_page_previews is not False
        ):
            if not silent:
                message.reply_text("This user already has the right to speak.")
        else:
            chat_permissions = ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
            try:
                bot.restrict_chat_member(chat.id, int(user_id), chat_permissions)
            except BadRequest:
                pass
            if not silent:
                bot.sendMessage(
                    chat.id,
                    f"I shall allow <b>{html.escape(member.user.first_name)}</b> to text!",
                    parse_mode=ParseMode.HTML,
                )
            else:
                message.delete()
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNMUTE\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
            )
    else:
        if not silent:
            message.reply_text(
                "This user isn't even in the chat, unmuting them won't make them talk more than they "
                "already do!"
            )

    if silent:
        message.delete()
    return ""


@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def temp_mute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)

    silent = False
    if message.text.startswith("/s") or message.text.startswith("!s"):
        silent = True
        if not can_delete(chat, context.bot.id):
            return ""

    if reply:
        message.reply_text(reply)
        return ""

    member = chat.get_member(user_id)

    if not reason:
        if not silent:
            message.reply_text("You haven't specified a time to mute this user for!")
        else:
            message.delete()
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#TEMP MUTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>Time:</b> {time_val}"
    )
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    try:
        chat_permissions = ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(
            chat.id, user_id, chat_permissions, until_date=mutetime
        )
        if not silent:
            reply = (
                f"<code>❕</code><b>Mute Event</b>\n"
                f"<code> </code><b>•  User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
                f"<code> </code><b>•  Time: {time_val}</b>"
            )
            if reason:
                reply += f"\n<code> </code><b>•  Reason:</b> {html.escape(reason)}"
            bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML)
        else:
            message.delete()
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            if not silent:
                message.reply_text(f"Muted for {time_val}!", quote=False)
            else:
                message.delete()
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR muting user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            if not silent:
                message.reply_text("Well damn, I can't mute that user.")
            else:
                message.delete()

    return ""


__help__ = """
*Admins only:*
 • `/mute <userhandle> <reason>(optional)`*:* silences a user. Can also be used as a reply, muting the replied to user.
 • `/tmute <userhandle> x(m/h/d) <reason>(optional)`*:* mutes a user for x time. (via handle, or reply). `m` = `minutes`, `h` = `hours`, `d` = `days`.
 • `/unmute <userhandle>`*:* unmutes a user. Can also be used as a reply, muting the replied to user.
"""

MUTE_HANDLER = CommandHandler(["mute", "smute"], mute, run_async=True)
UNMUTE_HANDLER = CommandHandler(["unmute", "sunmute"], unmute, run_async=True)
TEMPMUTE_HANDLER = CommandHandler(["tmute", "tempmute", "stmute", "stempmute"], temp_mute, run_async=True)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)

__mod_name__ = "Muting"
__handlers__ = [MUTE_HANDLER, UNMUTE_HANDLER, TEMPMUTE_HANDLER]
