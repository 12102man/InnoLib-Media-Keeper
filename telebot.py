from telegram.ext import Updater
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler
from telegram.ext import Filters
from telegram.ext import CommandHandler
from pony.orm import *
from new_user import User, Request, RegistrySession, Media, MediaRequest, Librarian, Log, MediaCopies
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

"""
search_functions(bot, update)

This is a query handler. Each time user sends inline button 
bot gets a callback query. This handler chooses the appropriate 
way to run further.
"""


@db_session
def search_functions(bot, update):
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
        session_user = RegistrySession[update.callback_query.from_user.id]
        session_user.faculty = True
        commit()
        end_of_registration(bot, update)
    elif query == 'NotFaculty':
        session_user = RegistrySession[update.callback_query.from_user.id]
        session_user.faculty = False
        commit()
        end_of_registration(bot, update)
    elif query == 'prevRequest':
        session = RegistrySession[update.callback_query.from_user.id]
        session.request_c -= 1
        commit()
        edit_request_card(bot, update)
    elif query == 'nextRequest':
        session = RegistrySession[update.callback_query.from_user.id]
        session.request_c += 1
        commit()
        edit_request_card(bot, update)
    elif query == 'prevItem':
        session = RegistrySession[update.callback_query.from_user.id]
        session.media_c -= 1
        commit()
        edit_media_card(bot, update)
    elif query == 'nextItem':
        session = RegistrySession[update.callback_query.from_user.id]
        session.media_c += 1
        commit()
        edit_media_card(bot, update)
    elif query == 'approveRequest':
        approve_request(bot, update)
    elif query == 'rejectRequest':
        reject_request(bot, update)
    elif query == 'book':
        book_media(bot, update)
    elif query == 'prevBookingRequest':
        session = RegistrySession[update.callback_query.from_user.id]
        session.book_r_c -= 1
        commit()
        edit_issue_media(bot, update)
    elif query == 'nextBookingRequest':
        session = RegistrySession[update.callback_query.from_user.id]
        session.book_r_c += 1
        commit()
        edit_issue_media(bot, update)
    elif query == 'approveBookingRequest':
        accept_booking_request(bot, update)
    elif query == 'rejectBookingRequest':
        reject_booking_request(bot, update)
    elif query == 'prevLogItem':
        session = RegistrySession[update.callback_query.from_user.id]
        session.log_c -= 1
        commit()
        edit_log_card(bot, update)
    elif query == 'nextLogItem':
        session = RegistrySession[update.callback_query.from_user.id]
        session.log_c += 1
        commit()
        edit_log_card(bot, update)


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


@db_session
def ask_name(bot, update):
    message = update.message
    user = User.get(telegramID=message.chat_id)
    session = RegistrySession.get(telegramID=message.chat_id)
    if user is not None:
        bot.send_message(text="🎓 Sorry, you have already been registered", chat_id=message.chat_id)
        return register_conversation.END
    elif session is not None:
        if session.phone is None:
            ask_phone(bot, update)
        elif session.address is None:
            ask_address(bot, update)
        elif session.faculty is None:
            ask_faculty(bot, update)
    else:
        session_user = RegistrySession(telegramID=message.chat_id, alias=message.chat.username)
        bot.send_message(chat_id=update.message.chat_id, text="""Let's start the enrolling process into Innopolis University Library!
Please, write your first and last name""")

        """
        This statement is required for transferring from one handler 
        to another using ConversationHandler
        """
        commit()
        return PHONE_NUMBER


"""
def ask_phone(bot, update)

This is the second handler. It asks for phone.
We can't get the user's default phone number,
because of Telegram restrictions :(
"""


@db_session
def ask_phone(bot, update):
    session_user = RegistrySession[update.message.chat_id]
    session_user.name = update.message.text
    bot.send_message(chat_id=update.message.chat_id, text="Please, write your phone number")
    commit()
    return ADDRESS


"""
def ask_address(bot, update)

This is the third handler. It asks for address.
"""


@db_session
def ask_address(bot, update):
    session_user = RegistrySession[update.message.chat_id]
    message = update.message.text
    filtered_message = message.replace("+", "").replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
    if all_numbers(filtered_message):
        session_user.phone = update.message.text
        bot.send_message(chat_id=update.message.chat_id, text="Please, write your address")
        commit()
        return FACULTY
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Oops, this is not a phone number, try again")


"""
This is the fourth handler. It asks user's status
(faculty member or not)
"""


@db_session
def ask_faculty(bot, update):
    session_user = RegistrySession[update.message.chat_id]
    session_user.address = update.message.text
    commit()

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
@db_session
def end_of_registration(bot, update):
    session_user = RegistrySession[update.callback_query.from_user.id]
    user_request = Request(
        telegramID=session_user.telegramID,
        name=session_user.name,
        phone=session_user.phone,
        address=session_user.address,
        alias=session_user.alias,
        faculty=session_user.faculty)
    commit()
    bot.send_message(chat_id=update.callback_query.from_user.id, text="Application was sent to library!")
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

"""
These three functions are called when commands 
are getting called at first time.
"""


@db_session
def create_request_card(bot, update):
    registry = list(Request.select(lambda c: c.status == 0))

    requestCard = Scroller('request', registry, update.message.chat_id)
    try:
        bot.send_message(text=requestCard.create_message(), chat_id=update.message.chat_id,
                         reply_markup=requestCard.create_keyboard())
    except FileNotFoundError as e:
        bot.send_message(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


@db_session
def create_media_card(bot, update):
    registry = list(Media.select())
    mediaCard = Scroller('media', registry, update.message.chat_id)

    try:
        bot.send_message(text=mediaCard.create_message(), chat_id=update.message.chat_id,
                         reply_markup=mediaCard.create_keyboard())
    except FileNotFoundError as e:
        bot.send_message(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


@db_session
def issue_media(bot, update):
    registry = list(MediaRequest.select())
    issue_card = Scroller('bookingRequest', registry, update.message.chat_id)
    try:
        bot.send_message(text=issue_card.create_message(), chat_id=update.message.chat_id,
                         reply_markup=issue_card.create_keyboard())
    except FileNotFoundError as e:
        bot.send_message(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


@db_session
def create_log_card(bot, update):
    registry = list(Log.select())
    log = Scroller('log', registry, update.message.chat_id)
    try:
        bot.send_message(text=log.create_message(), chat_id=update.message.chat_id,
                         reply_markup=log.create_keyboard())
    except FileNotFoundError as e:
        bot.send_message(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


"""
Following three functions are called from queries from buttons.
When user presses button, message gets changed for the next/previous
record.
"""


def edit_request_card(bot, update):
    query = update.callback_query
    try:
        registry = list(Request.select(lambda c: c.status == 0))

        requestCard = Scroller('request', registry, update.callback_query.from_user.id)
        bot.edit_message_text(text=requestCard.create_message(), chat_id=query.message.chat_id,
                              message_id=query.message.message_id, reply_markup=requestCard.create_keyboard())
    except UnboundLocalError as e:
        logging.error("Error occured: " + e.args[0])
        bot.edit_message_text(text="Error occured: " + e.args[0], chat_id=query.message.chat_id,
                              message_id=query.message.message_id)


def edit_media_card(bot, update):
    query = update.callback_query
    try:
        registry = list(Media.select())
        mediaCard = Scroller('media', registry, query.message.chat_id)
        bot.edit_message_text(text=mediaCard.create_message(), chat_id=query.message.chat_id,
                              message_id=query.message.message_id, reply_markup=mediaCard.create_keyboard())
    except UnboundLocalError as e:
        logging.error("Error occured: " + e.args[0])
        bot.edit_message_text(text="Error occured: " + e.args[0], chat_id=query.message.chat_id,
                              message_id=query.message.message_id)


def edit_issue_media(bot, update):
    query = update.callback_query
    try:
        registry = list(MediaRequest.select())
        issue_card = Scroller('bookingRequest', registry, query.message.chat_id)
        bot.edit_message_text(text=issue_card.create_message(), chat_id=query.message.chat_id,
                              message_id=query.message.message_id, reply_markup=issue_card.create_keyboard())
    except UnboundLocalError as e:
        logging.error("Error occured: " + e.args[0])
        bot.edit_message_text(text="Error occured: " + e.args[0], chat_id=query.message.chat_id,
                              message_id=query.message.message_id)


def edit_log_card(bot, update):
    query = update.callback_query
    try:
        registry = list(Log.select())
        log = Scroller('log', registry, query.message.chat_id)
        bot.edit_message_text(text=log.create_message(), chat_id=query.message.chat_id,
                              message_id=query.message.message_id, reply_markup=log.create_keyboard())
    except UnboundLocalError as e:
        logging.error("Error occured: " + e.args[0])
        bot.edit_message_text(text="Error occured: " + e.args[0], chat_id=query.message.chat_id,
                              message_id=query.message.message_id)


"""
librarian_authentication(user_id)

This function is responsible for checking if 
user is a librarian or not. If not - return false,
if yes - return true.
"""


@db_session
def librarian_authentication(user_id):
    librarian = Librarian.get(telegramID=user_id)
    if librarian is not None:
        return True
    else:
        return False


@db_session
def librarian_interface(bot, update):
    telegramID = update.message.chat_id
    librarian = Librarian.get(telegramID=telegramID)
    if not librarian_authentication(telegramID):
        print("Unauthorized logging")
        return 0

    bot.send_message(text="""Hello, %s!
Here's a list of useful commands, which are only allowed to librarians:
/requests - see registry requests    
/log - see log of librarian
/return - return a book
/users - list of users
""" % librarian.name, chat_id=telegramID)


@db_session
def my_medias(bot, update):
    list_of_user_medias = Log.select(lambda c: c.libID == update.message.chat_id)
    string = ""
    for item in list_of_user_medias:
        abstract_media = MediaCopies.get(copyID=item.mediaID).mediaID
        string += "ID: " + item.mediaID + "\n" + \
                  abstract_media.name + " by " + abstract_media.authors + "\n" + \
                  "Issued: " + item.issue_date.strftime("%H:%M %d %h %Y") + "\n" + \
                  "Expiry: " + item.expiry_date.strftime("%H:%M %d %h %Y") + "\n" + "\n"

    bot.send_message(text=string, chat_id=update.message.chat_id)


@db_session
def users(bot, update):
    telegramID = update.message.chat_id
    if not librarian_authentication(telegramID):
        return 0
    list_of_all_users = User.select()
    string = ""
    for user in list_of_all_users:
        string += "Telegram ID: " + str(user.telegramID) + "\n" + \
                  "Name: " + user.name + "\n" + \
                  "Address: " + user.address + "\n" + \
                  "Phone: " + user.phone + "\n" + \
                  "Faculty? " + str(user.faculty) + "\n" + \
                  "Medias: " + "\n"
        list_of_user_medias = Log.select(lambda c: c.libID == user.telegramID)
        for item in list_of_user_medias:
            abstract_media = MediaCopies.get(copyID=item.mediaID).mediaID
            string += "     ID: " + item.mediaID + "\n" + \
                      "         " + abstract_media.name + " by " + abstract_media.authors + "\n" + \
                      "     Issued: " + item.issue_date.strftime("%H:%M %d %h %Y") + "\n" + \
                      "     Expiry: " + item.expiry_date.strftime("%H:%M %d %h %Y") + "\n"
        string += "\n"
    bot.send_message(text=string, chat_id=update.message.chat_id)


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

TYPE, TITLE, PUBLISHER, MEDIA_ID, DELETE, FIND, TELEGRAM_ID, AUTHORS, COPY, FINE, PRICE = range(11)


def create_new_patron(bot, update, state):
    """
    We need to create new record in database with filled TelegramID and then
    put there new data from message of librarian
    Ask required field to user and put it new entity
    Then commit it
    ATTENTION: registration is being done by LIBRARIAN, not PATRON by himself
    """
    # new_user = User.get(telegramID=update.message.chat_id)
    session = RegistrySession.get(telegramID=update.message.chat_id)
    if session is not None:
        if session.name is None:
            """Тут ещё не понятно, сможет ли библиотекарь писать сразу ИД
            или бот сможет находить по алиасу ИД """
            session.request_c = update.message.text
            bot.send_message("write his full name")
            commit()
            return NAME
        elif session.name is None:
            session.name = update.message.text
            bot.send_message("write his full name")
            commit()
            return PHONE_NUMBER
        elif session.phone is None:
            session.phone = update.message.text
            bot.send_message("write his address")
            commit()
            return ADDRESS
        elif session.address is None:
            session.address = update.message.text
            bot.send_message("write is he a faculty member")
            commit()
            return FACULTY
        elif session.faculty is None:
            session.faculty = update.message.text
            bot.send_message("write is he a faculty member")
            new_user = User(telegramID=session.request_c, name=session.name,
                            phone=session.phone, address=session.address,
                            faculty=session.faculty)
            commit()
            return new_patron_conversation.END
    else:
        session_lib = RegistrySession(telegramID=update.message.chat_id)
        bot.send("start reg new patron, write his tgID/alias")
        commit()
        return TELEGRAM_ID


NOT_FINISHED = range(1)


@db_session
def create_new_media(bot, update):
    """
    The same thing as with NEW PATRON but with media
    """

    session = RegistrySession.get(telegramID=update.message.chat_id)
    if session is not None:
        if session.title is None:
            bot.send_message(text="Please, enter Title: ", chat_id=update.message.chat_id)
            return NOT_FINISHED
        elif session.type is None:
            session.title = update.message.text
            bot.send_message(text="What is the type of media: ", chat_id=update.message.chat_id)
            # commit()
            return TYPE
        elif session.author is None:
            session.type = update.message.text
            bot.send_message(text="Who is the author?", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.publisher is None:
            session.author = update.message.text
            bot.send_message(text="What is the publisher?", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.price is None:
            session.publisher = update.message.text
            bot.send_message(text="What is the price?", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.fine is None:
            session.price = update.message.text
            bot.send_message(text="What is the fine?", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        else:
            session.price = update.message.text
            bot.send_message(text="What is the fine?", chat_id=update.message.chat_id)

            new_media = Media(mediaID=2, name=session.title, type=session.type, authors=session.author,
                              publisher=session.publisher, price=session.price, fine=session.fine)
            commit()
            return new_media_conversation.END



"""def modify_user():
def modify_media():"""

new_media_handler = CommandHandler("add_media", create_new_media)
new_media_conversation = ConversationHandler(entry_points=[CommandHandler("add_media", create_new_media)],
                                             states={
                                                 TYPE: [MessageHandler(Filters.text, ask_address)],
                                                 TITLE: [MessageHandler(Filters.text, ask_address)],
                                                 NOT_FINISHED: [MessageHandler(Filters.text, create_new_media)]
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
dispatcher.add_handler(CommandHandler('log', create_log_card))
dispatcher.add_handler(CommandHandler('my', my_medias))
dispatcher.add_handler(CommandHandler('users', users))
dispatcher.add_handler(CommandHandler('librarian', librarian_interface))
dispatcher.add_handler(search_query_handler)
dispatcher.add_handler(register_conversation)
dispatcher.add_handler(new_media_handler)
dispatcher.add_handler(new_media_conversation)

updater.start_polling()  # Start asking for server about any incoming requests

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
