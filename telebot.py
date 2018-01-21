from telegram.ext import Updater
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler
from telegram.ext import Filters
from telegram.ext import CommandHandler
from user import Patron
import logging
import pymysql
import config

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

temp_patron = Patron()


##Menu for ordering
def build_menu():
    button_list = [
        [
            InlineKeyboardButton("Book", callback_data='book_search'),
            InlineKeyboardButton("Article", callback_data='article_search')
        ],
        [
            InlineKeyboardButton("A/V", callback_data='av_search')
        ]]

    reply = InlineKeyboardMarkup(button_list)
    return reply


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="You have a patron access. What do you want to find?",
                     reply_markup=build_menu())


NAME, FACULTY, PHONE_NUMBER, ADDRESS, END_OF_SIGNUP, BOOK_SEARCH, ARTICLE_SEARCH, AV_SEARCH = range(8)

##Elements of search conversation
def book_search(bot, update):
    query = update.callback_query
    bot.send_message(chat_id=query.message.chat_id, text="Send me name of the book")
    return BOOK_SEARCH


def article_search(bot, update):
    query = update.callback_query
    bot.send_message(chat_id=query.message.chat_id, text="Send me name of the article")
    return ARTICLE_SEARCH


def av_search(bot, update):
    query = update.callback_query
    bot.send_message(chat_id=query.message.chat_id, text="Send me name of the av")
    return AV_SEARCH


def book_name(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)
    return search_conversation.END


def article_name(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)
    return search_conversation.END


def av_name(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)
    return search_conversation.END


##Choosing right type of material
def search_functions(bot, update, user_data):
    global temp_patron
    query = update.callback_query.data
    if query == 'book_search':
        return book_search(bot, update)
    elif query == 'article_search':
        return article_search(bot, update)
    elif query == 'av_search':
        return av_search(bot, update)
    elif query == 'Faculty':
        temp_patron.setFaculty(1)
        end_of_registration(bot,update)
    elif query == 'NotFaculty':
        temp_patron.setFaculty(0)
        end_of_registration(bot, update)

# Filter for phone
def allNumbers(inputString):
    return all(char.isdigit() for char in inputString)


def ask_name(bot, update):
    global temp_patron
    message = update.message
    temp_patron.setTelegramID(message.chat_id)
    temp_patron.setAlias(message.chat.username)
    temp_patron.initialize()
    bot.send_message(chat_id=update.message.chat_id, text="""Let's start the enrolling process into Innopolis University Library!
Please, write your first and last name""")
    return PHONE_NUMBER


def ask_phone(bot, update):
    global temp_patron
    temp_patron.setName(update.message.text)
    bot.send_message(chat_id=update.message.chat_id, text="Please, write your phone number")
    return ADDRESS


def ask_address(bot, update):
    global temp_patron
    message = update.message.text
    filteredMessage = message.replace("+","").replace("(","").replace(")","").replace("-","").replace(" ","")
    if (allNumbers(filteredMessage)):
        temp_patron.setPhone(message)
        bot.send_message(chat_id=update.message.chat_id, text="Please, write your address")
        return FACULTY
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Oops, this is not a phone number, try again")

def ask_faculty(bot, update):
    global temp_patron

    temp_patron.setAddress(update.message.text)
    reply = InlineKeyboardMarkup([[InlineKeyboardButton("Yes", callback_data="Faculty"), InlineKeyboardButton("No", callback_data="NotFaculty")]])
    bot.send_message(chat_id=update.message.chat_id, text="Are you a faculty member?", reply_markup=reply)
    return register_conversation.END
def end_of_registration(bot, update):
    global temp_patron
    bot.send_message(chat_id=update.callback_query.from_user.id, text="Application was sent to library!")
    print(temp_patron.addRequest())
    cursor.execute(temp_patron.addRequest())
    connection.commit()
    print("test")
    return register_conversation.END


register_conversation = ConversationHandler(entry_points=[CommandHandler('enroll', ask_name)],
                                            states={
                                                PHONE_NUMBER: [MessageHandler(Filters.text, ask_phone)],
                                                ADDRESS: [MessageHandler(Filters.text, ask_address)],
                                                FACULTY: [MessageHandler(Filters.text, ask_faculty)]
                                            },
                                            fallbacks=[])

search_handler = CommandHandler('search', start)
search_query_handler = CallbackQueryHandler(search_functions, pass_groups=True, pass_user_data=True)
search_conversation = ConversationHandler(entry_points=[search_query_handler],
                                          states={
                                              BOOK_SEARCH: [MessageHandler(Filters.text, book_name)],
                                              ARTICLE_SEARCH: [MessageHandler(Filters.text, article_name)],
                                              AV_SEARCH: [MessageHandler(Filters.text, av_name)]
                                          },
                                          fallbacks=[])

dispatcher.add_handler(search_handler)
dispatcher.add_handler(search_conversation)
dispatcher.add_handler(search_query_handler)
dispatcher.add_handler(register_conversation)

updater.start_polling()

