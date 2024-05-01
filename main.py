import os
import queue
import asyncio
import logging
import tracemalloc
from pprint import pprint
from threading import Thread
import subprocess

#from db import create_user_order, add_order, delete_order, change_lang, track, session
#from model import Order, Base

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, Bot, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeChat
from telegram.ext import Application, CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler, filters, MessageHandler, Updater

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

queue_ = queue.Queue()

CHOICES = range(1)

async def start(update: Update, context: CallbackContext):
    if str(update.effective_chat.id) == os.getenv('USERNAME'):
        await context.bot.set_my_commands(
            commands=[
                BotCommand('generate_report_subs', 'See new requests'),
                BotCommand('generate_report_orders', 'Generate orders report'),
                BotCommand('generate_report_all_orders', 'Generate all orders report'),
            ],
            scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
        )
    else:
        await context.bot.set_my_commands(
            commands=[
                BotCommand("cancel", "end conversation"),
                BotCommand("contact_us", "contact us"),
                BotCommand("about","info")
            ],
            scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Welcome to my job request bot, please fill in the information as you see fit.",
            reply_markup=ReplyKeyboardRemove()
        )

        known = KeyboardButton(text="Known Project")
        unknown = KeyboardButton(text="Unknown Project")
        portfolio = KeyboardButton(text="Previous Works")

        custom_keyboard = [[ known, unknown ]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        await update.message.reply_text(
            text="""Pick where to proceed:
            Known project if you have a set of requirements
            Unkown project if you have a vision
            Previous works to see previous works""",
            reply_markup=reply_markup
        )

        return CHOICES

async def choices(update: Update, context: CallbackContext) -> int:
    """Pick which section to move on to"""
    choice = update.effective_message.text
    logger.info("user pick: %s", choice)

    if choice == "Known Project":
        await update.message.reply_text(
            text="""""",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="html"
        )

    elif choice == "Unknown Project":
        await update.message.reply_text(
            text="""""",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="html"
        )

    custom_keyboard = [[ order_laundry ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )

    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    if str(update.effective_user.id) == os.getenv('USERNAME'):
        await update.message.reply_text(
            "ADMIN\n/generate_report\n/delete_subscriber",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: CallbackContext):
    """Log the error and handle it gracefully"""
    logger.error(msg="Exception occurred", exc_info=context.error)
    await update.message.reply_text('Sorry, an error occurred. Please try again.')

########################################################
def main():
    # bot runner
    application = Application.builder().token(TOKEN).build()

    # Commands
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('choices', choices)],
        states={
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handlers([conv_handler])
    application.add_handler(CommandHandler('start', start))

    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES, poll_interval=1.0)


if __name__ == '__main__':
    tracemalloc.start()

    main()

    tracemalloc.stop()
    print(tracemalloc.get_object_traceback())
