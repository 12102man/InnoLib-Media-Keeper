from telegram.ext import Updater
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler
from telegram.ext import Filters
from telegram.ext import CommandHandler
from pony.orm import *
from user import User, Request, RegistrySession, Media, MediaRequest, Librarian, Log, MediaCopies
import logging
import pymysql
import config
from scroller import Scroller
import user
from button_actions import *
from telegram.ext.dispatcher import run_async

db = Database()
# MySQL
db.bind(provider='mysql', host='37.46.132.57', user='telebot', passwd='Malinka2017', db='testbase')

updater = Updater(token=config.token)

dispatcher = updater.dispatcher

""" MySQL connection """
connection = pymysql.connect(host=config.db_host,
                             user=config.db_username,
                             password=config.db_password,
                             db=config.db_name,
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)
cursor = connection.cursor()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# States for switching between handlers
NAME, FACULTY, PHONE_NUMBER, ADDRESS, END_OF_SIGNUP, BOOK_SEARCH, ARTICLE_SEARCH, AV_SEARCH = range(8)

db.generate_mapping(create_tables=True)

@db_session
def create_new_media(bot, update):
    """
    The same thing as with NEW PATRON but with media
    """
    print("something")
    session = RegistrySession.get(telegramID=update.message.chat_id)
    if session is not None:
        print("here")
        if session.title == "def":
            session.title = update.message.text
            print("title added")
            bot.send_message(text="What is the type of media: ", chat_id=update.message.chat_id)
            return NOT_FINISHED
        elif session.type == "def":
            print("type added")
            session.type = update.message.text
            bot.send_message(text="Who is the author?", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.author == "def":
            print("author added")
            session.author = update.message.text
            bot.send_message(text="What is the publisher?", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.publisher == "def":
            print("publisher added")
            session.publisher = update.message.text
            bot.send_message(text="What is the price?", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.price == 0:
            print("price added")
            session.price = update.message.text
            bot.send_message(text="What is the fine?", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.fine == 0:
            print("fine added")
            session.fine = update.message.text
            Media(mediaID=4, name=session.title, type=session.type, authors=session.author,
                  publisher=session.publisher, cost=session.price, fine=session.fine,
                  availability=True, bestseller=False)
            session.delete()
            commit()
            print("media added")
            return new_media_conversation.END
    else:
        print("new session added")
        RegistrySession(telegramID=update.message.chat_id)
        bot.send_message(text="Please, enter Title: ", chat_id=update.message.chat_id)
        return NOT_FINISHED


NOT_FINISHED = range(1)
new_media_conversation = ConversationHandler(entry_points=[CommandHandler("add_media", create_new_media)],
                                             states={
                                                 NOT_FINISHED: [MessageHandler(Filters.text, create_new_media)]
                                             },
                                             fallbacks=[])
dispatcher.add_handler(new_media_conversation)

updater.start_polling()  # Start asking for server about any incoming requests
