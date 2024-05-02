import os
import queue
import logging
import tracemalloc

from db import create_project_order

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, BotCommand, BotCommandScopeChat
from telegram.ext import Application, CallbackContext, CommandHandler, ConversationHandler, filters, MessageHandler

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

queue_ = queue.Queue()

CHOICES, DESCRIPTION, BUDGET, TIMELINE, CONTACT = range(5)

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
    """Pick which section to move on to and ask for description of project"""
    choice = update.effective_message.text
    logger.info("user pick: %s", choice)

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
    logger.info("user description: %s", description)

    await update.message.reply_text(
        text="Now please, if you have an estimated budget for the project, if not just put in a '-' and proceed:",
        reply_markup=ReplyKeyboardRemove(),
    )
    
    return BUDGET

async def budget(update: Update, context: CallbackContext) -> int:
    """Get the budget and ask for an estimated time of the project"""
    budget = update.effective_message.text
    context.user_data['budget'] = budget
    logger.info("user budget: %s", budget)

    await update.message.reply_text(
        text="Now please, if you have an estimated time for the project, if not just put in a '-' and proceed:",
        reply_markup=ReplyKeyboardRemove(),
    )
    
    return TIMELINE

async def timeline(update: Update, context: CallbackContext) -> int:
    """Get the estimated time and ask for a contact of the client"""
    timeline = update.effective_message.text
    context.user_data['timeline'] = timeline
    logger.info("user timeline: %s", timeline)

    await update.message.reply_text(
        text="You will now be prompted to share your contact info:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="Share Contact", request_contact=True)]], resize_keyboard=True)
    )
    
    return CONTACT

async def contact(update: Update, context: CallbackContext) -> int:
    """Get client contact and log project"""
    contact = update.message.contact
    context.user_data['contact'] = contact
    logger.info("user contact: %s, %s", contact.first_name, contact.phone_number)

    project_tracker = create_project_order(context.user_data['contact'].user_id, context.user_data['contact'].first_name, context.user_data['contact'].phone_number, context.user_data['description'], context.user_data['timeline'], context.user_data['budget'])
    
    await update.message.reply_text(
        text=f"Thank you, your project request has been logged with number `{project_tracker}`. The developer will contact you shortly.\n Thank you for your patience",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='markdown'
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
        entry_points=[MessageHandler(filters.Regex(r'^(Unknown Project|Known Project|Previous Works)'), choices)],
        states={
            DESCRIPTION: [MessageHandler(filters.TEXT, description)],
            BUDGET: [MessageHandler(filters.TEXT, budget)],
            TIMELINE: [MessageHandler(filters.TEXT, timeline)],
            CONTACT: [MessageHandler(filters.CONTACT, contact)],
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
