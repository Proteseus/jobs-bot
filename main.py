import json
import os
import queue
import logging
import asyncio
from threading import Thread
import tracemalloc

import flask
from sqlalchemy.orm.base import ATTR_WAS_SET

from db import create_project_order, fetch_orders

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, BotCommand, BotCommandScopeChat
from telegram.ext import Application, CallbackContext, CommandHandler, ConversationHandler, filters, MessageHandler
from flask import Flask, jsonify
from aiohttp import web
from aiohttp.web_runner import AppRunner, TCPSite

# Create a Flask app
app = Flask(__name__)

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

queue_ = queue.Queue()

CHOICES, DESCRIPTION, BUDGET, TIMELINE, CONTACT = range(5)

# Define a route that returns a JSON greeting message
@app.route('/')
def hello():
    return jsonify(message="Hello, welcome to the Jobs-Bot by t.me/Leviticus_98!")

async def start(update: Update, context: CallbackContext):
    if str(update.effective_chat.id) == os.getenv('USERID'):
        await context.bot.set_my_commands(
            commands=[
                BotCommand('generate_report', 'See new requests'),
                BotCommand('generate_report_orders', 'Generate orders report'),
                BotCommand('generate_report_all_orders', 'Generate all orders report'),
            ],
            scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
        )
    else:
        await context.bot.set_my_commands(
            commands=[
                BotCommand("start", "New project request"),
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
            Unknown project if you have a vision
            Previous works to see previous works""",
            reply_markup=reply_markup
        )

        return CHOICES

async def choices(update: Update, context: CallbackContext) -> int:
    """Pick which section to move on to and ask for description of project"""
    choice = update.effective_message.text
    logger.info("user %s pick: %s", update.effective_chat.username, choice)

    if choice == "Known Project" or choice == "Unknown Project":
        await update.message.reply_text(
            text="Provide a brief description of the project you wish to undertake:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return DESCRIPTION

    elif choice == "Previous Works":
        return ConversationHandler.END

async def description(update: Update, context: CallbackContext) -> int:
    """Get the description and ask for budget of the project"""
    description = update.effective_message.text
    context.user_data['description'] = description
    logger.info("user %s description: %s", update.effective_chat.username, description)

    await update.message.reply_text(
        text="Now please, if you have an estimated budget for the project, if not just put in a '-' and proceed:",
        reply_markup=ReplyKeyboardRemove(),
    )
    
    return BUDGET

async def budget(update: Update, context: CallbackContext) -> int:
    """Get the budget and ask for an estimated time of the project"""
    budget_text = update.effective_message.text
    try:
        budget = float(budget_text)
        context.user_data['budget'] = budget
        logger.info("user %s budget: %s", update.effective_chat.username, budget)

        await update.message.reply_text(
            text="Now please, if you have an estimated time for the project, if not just put in a '-' and proceed:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return TIMELINE
    except ValueError:
        await update.message.reply_text(
            text="Please enter a valid number for the budget:",
            reply_markup=ReplyKeyboardRemove()
        )
        return BUDGET

async def timeline(update: Update, context: CallbackContext) -> int:
    """Get the estimated time and ask for a contact of the client"""
    timeline = update.effective_message.text
    context.user_data['timeline'] = timeline
    logger.info("user %s timeline: %s", update.effective_chat.username, timeline)

    await update.message.reply_text(
        text="You will now be prompted to share your contact info:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="Share Contact", request_contact=True)]], resize_keyboard=True)
    )
    
    return CONTACT

async def contact(update: Update, context: CallbackContext) -> int:
    """Get client contact and log project"""
    contact = update.message.contact
    context.user_data['contact'] = contact
    logger.info("user %s contact: %s, %s", update.effective_chat.username, contact.first_name, contact.phone_number)

    project_tracker = create_project_order(context.user_data['contact'].user_id, update.effective_chat.username, context.user_data['contact'].first_name, context.user_data['contact'].phone_number, context.user_data['description'], context.user_data['timeline'], context.user_data['budget'])
    
    await update.message.reply_text(
        text=f"Thank you, your project request has been logged with number `{project_tracker}`. The developer will contact you shortly.\n Thank you for your patience",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='markdown'
    )
    
    message = "Order: #`{}`\nName: {}\nUser: `@{}`\nPhone: {}\nDetails: {}\nBudget: {}\nTimeline: {}".format(
    project_tracker,
    context.user_data['contact'].first_name,
    update.effective_chat.username,
    context.user_data['contact'].phone_number,
    context.user_data['description'],
    context.user_data['budget'],
    context.user_data['timeline']
    )

    chat_id = os.getenv('USERID')

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='markdown'
    )
    logger.info("Order recieved and transmitted to %s.", chat_id)
        
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    if str(update.effective_user.id) == os.getenv('USERID'):
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

async def admin_fetch_orders(update: Update, context: CallbackContext):
    """Get orders"""
    logger.info("Orders fetched...")
    if str(update.effective_user.id) == os.getenv('USERID'):
        orders = fetch_orders()
        orders_list = json.loads(orders)
        formatted_orders = json.dumps(orders_list, indent=4)
        await update.message.reply_text(
            text=f"<pre>{formatted_orders}</pre>",
            parse_mode="HTML"
        )


async def error_handler(update: Update, context: CallbackContext):
    """Log the error and handle it gracefully"""
    logger.error(msg="Exception occurred", exc_info=context.error)
    await update.message.reply_text('Sorry, an error occurred. Please try again.')

########################################################
async def run_flask():
    runner = AppRunner(web.Application())
    await runner.setup()
    site = TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    while True:
        await asyncio.sleep(3600)

async def run_bot():
    # bot runner
    application = Application.builder().token(TOKEN).build()

    # Commands
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^(Unknown Project|Known Project|Previous Works)') & ~filters.COMMAND, choices)],
        states={
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget)],
            TIMELINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, timeline)],
            CONTACT: [MessageHandler(filters.CONTACT & ~filters.COMMAND, contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handlers([conv_handler])
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('generate_report', admin_fetch_orders))

    # Run bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    # await application.shutdown()
    # await application.stop()

    # application.run_polling(allowed_updates=Update.ALL_TYPES, poll_interval=1.0)

async def main():
    bot_task = asyncio.create_task(run_bot())
    flask_task = asyncio.create_task(run_flask())

    await asyncio.gather(bot_task, flask_task)

if __name__ == '__main__':
    tracemalloc.start()

    asyncio.run(main())

    tracemalloc.stop()
    print(tracemalloc.get_object_traceback())

