from telegram.ext import Updater
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler
from telegram.ext import Filters
from telegram.ext import CommandHandler
from user import Patron
import logging
import pymysql
import config
from scroller import Scroller
from telegram.ext.dispatcher import run_async

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

temp_patron = Patron()  # Temporary user (used in registration process)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# States for switching between handlers
NAME, FACULTY, PHONE_NUMBER, ADDRESS, END_OF_SIGNUP, BOOK_SEARCH, ARTICLE_SEARCH, AV_SEARCH = range(8)

"""
search_functions(bot, update)

This is a query handler. Each time user sends inline button 
bot gets a callback query. This handler chooses the appropriate 
way to run further.
"""


def search_functions(bot, update):
    global temp_patron
    query = update.callback_query.data
    """
    if query == 'book_search':
        return book_search(bot, update)
    elif query == 'article_search':
        return article_search(bot, update)
    elif query == 'av_search':
        return av_search(bot, update)
    """
    if query == 'Faculty':
        temp_patron.set_faculty(1)
        end_of_registration(bot, update)
    elif query == 'NotFaculty':
        temp_patron.set_faculty(0)
        end_of_registration(bot, update)
    elif query == 'prevRequest':
        requestCard.decrease_cursor()
        edit_request_card(bot, update)
    elif query == 'nextRequest':
        requestCard.increase_cursor()
        edit_request_card(bot, update)
    elif query == 'prevItem':
        mediaCard.decrease_cursor()
        edit_media_card(bot, update)
    elif query == 'nextItem':
        mediaCard.increase_cursor()
        edit_media_card(bot, update)
    elif query == 'approveRequest':
        requestCard.approve_request(bot, update)
    elif query == 'rejectRequest':
        requestCard.reject_request(bot, update)
    elif query == 'book':
        mediaCard.book_media(bot, update)
    elif query == 'prevBookingRequest':
        temp.decrease_cursor()
        edit_issue_media(bot, update)
    elif query == 'nextBookingRequest':
        temp.increase_cursor()
        edit_issue_media(bot, update)
    elif query == 'approveBookingRequest':
        temp.accept_booking_request(bot, update)
    elif query == 'rejectBookingRequest':
        temp.reject_booking_request(bot, update)


# Filter for phone
def all_numbers(input_string):
    return all(char.isdigit() for char in input_string)


"""  Registration process   """

"""
def ask_name(bot, update)

This handler starts registration process. It handles from
/enroll button. Here user's profile is starting filling 
(into temp_patron)
"""


@run_async
def ask_name(bot, update):
    global temp_patron
    message = update.message
    temp_patron.set_telegram_id(message.chat_id)
    temp_patron.set_alias(message.chat.username)
    bot.send_message(chat_id=update.message.chat_id, text="""Let's start the enrolling process into Innopolis University Library!
Please, write your first and last name""")

    """
    This statement is required for transferring from one handler 
    to another using ConversationHandler
    """
    return PHONE_NUMBER


"""
def ask_phone(bot, update)

This is the second handler. It asks for phone.
We can't get the user's default phone number,
because of Telegram restrictions :(
"""


@run_async
def ask_phone(bot, update):
    global temp_patron
    temp_patron.set_name(update.message.text)
    bot.send_message(chat_id=update.message.chat_id, text="Please, write your phone number")
    return ADDRESS


"""
def ask_address(bot, update)

This is the third handler. It asks for address.
"""


@run_async
def ask_address(bot, update):
    global temp_patron
    message = update.message.text
    filtered_message = message.replace("+", "").replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
    if all_numbers(filtered_message):
        temp_patron.set_phone(message)
        bot.send_message(chat_id=update.message.chat_id, text="Please, write your address")
        return FACULTY
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Oops, this is not a phone number, try again")


"""
This is the fourth handler. It asks user's status
(faculty member or not)
"""


@run_async
def ask_faculty(bot, update):
    global temp_patron
    temp_patron.set_address(update.message.text)

    #   Buttons for answering Yes or No. callback_data is what bot gets as a query (see search_functions())
    reply = InlineKeyboardMarkup([[InlineKeyboardButton("Yes", callback_data="Faculty"),
                                   InlineKeyboardButton("No", callback_data="NotFaculty")]])
    bot.send_message(chat_id=update.message.chat_id, text="Are you a faculty member?", reply_markup=reply)
    return register_conversation.END


"""
This is the end of registration.
If everything is correct, send request to database.
"""


@run_async
def end_of_registration(bot, update):
    global temp_patron
    bot.send_message(chat_id=update.callback_query.from_user.id, text="Application was sent to library!")
    temp_patron.add_request()
    return register_conversation.END


""" Getting list of users and listing the requests"""

""" get_list(cursor, table)
    Updates the list of all records from the table
    Needs:      name of table to search in
    Returns:    list with all the records from the table
"""


def get_list(table):
    connection.connect()
    sql = "SELECT * FROM %s;" % table
    cursor.execute(sql)
    res = cursor.fetchall()
    return res


"""
These objects are from Scroller class (see scroller.py)
They perform menus for viewing menu, registry requests
and booking requests.
"""
requestCard = Scroller('request', get_list('request'))
mediaCard = Scroller('media', get_list('media'))
temp = Scroller('bookingRequest', get_list('mediarequest'))


"""
These three functions are called when commands 
are getting called at first time.
"""


def create_request_card(bot, update):
    requestCard.update(get_list('request'))     # Updating table
    bot.send_message(text=requestCard.create_message(), chat_id=update.message.chat_id,
                     reply_markup=requestCard.create_keyboard())


def create_media_card(bot, update):
    mediaCard.update(get_list('media'))         # Updating table
    bot.send_message(text=mediaCard.create_message(), chat_id=update.message.chat_id,
                     reply_markup=mediaCard.create_keyboard())


def issue_media(bot, update):
    temp.update(get_list('mediarequest'))       # Updating table
    bot.send_message(text=temp.create_message(), chat_id=update.message.chat_id, reply_markup=temp.create_keyboard())


"""
Following three functions are called from queries from buttons.
When user presses button, message gets changed for the next/previous
record.
"""


def edit_request_card(bot, update):
    requestCard.update(get_list('request'))
    query = update.callback_query
    bot.edit_message_text(text=requestCard.create_message(), chat_id=query.message.chat_id,
                          message_id=query.message.message_id, reply_markup=requestCard.create_keyboard())


def edit_media_card(bot, update):
    mediaCard.update(get_list('media'))
    query = update.callback_query
    bot.edit_message_text(text=mediaCard.create_message(), chat_id=query.message.chat_id,
                          message_id=query.message.message_id, reply_markup=mediaCard.create_keyboard())


def edit_issue_media(bot, update):
    query = update.callback_query
    bot.edit_message_text(text=temp.create_message(), chat_id=query.message.chat_id,
                          message_id=query.message.message_id, reply_markup=temp.create_keyboard())


"""
librarian_authentication(user_id)

This function is responsible for checking if 
user is a librarian or not. If not - return false,
if yes - return true.
"""


def librarian_authentication(user_id):
    connection.connect()
    sql = "SELECT telegramID FROM librarian WHERE telegramID = %s;" % user_id
    cursor.execute(sql)
    if len(cursor.fetchall()) == 0:
        return False
    else:
        return True


"""
This is a conversation handler. It helps smoothly iterating 
from one command to another. Entry point is /enroll command.

Using states handler switches from one function to another.
"""
register_conversation = ConversationHandler(entry_points=[CommandHandler('enroll', ask_name)],
                                            states={
                                                PHONE_NUMBER: [MessageHandler(Filters.text, ask_phone)],
                                                ADDRESS: [MessageHandler(Filters.text, ask_address)],
                                                FACULTY: [MessageHandler(Filters.text, ask_faculty)]
                                            },
                                            fallbacks=[])

"""
This part connects commands, queries and any other input information to features
in code. These are handlers.
"""
search_query_handler = CallbackQueryHandler(search_functions, pass_groups=True)
dispatcher.add_handler(CommandHandler('requests', create_request_card))
dispatcher.add_handler(CommandHandler('medias', create_media_card))
dispatcher.add_handler(CommandHandler('issue', issue_media))
dispatcher.add_handler(search_query_handler)
dispatcher.add_handler(register_conversation)

updater.start_polling()     # Start asking for server about any incoming requests


"""
-------------   Menu for ordering (for later implementation)

#   search_handler = CommandHandler('search', start)
#   dispatcher.add_handler(search_handler)
#   dispatcher.add_handler(search_conversation)
search_conversation = ConversationHandler(entry_points=[search_query_handler],
                                          states={
                                              BOOK_SEARCH: [MessageHandler(Filters.text, book_name)],
                                              ARTICLE_SEARCH: [MessageHandler(Filters.text, article_name)],
                                              AV_SEARCH: [MessageHandler(Filters.text, av_name)]
                                          },
                                          fallbacks=[])



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



"""
