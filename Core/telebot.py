from telegram.ext import Updater
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler
from telegram.ext import Filters
from telegram.ext import CommandHandler
from Core.database import *
import logging
import Config.config as config
from Core.scroller import Scroller
import json
from Core.button_actions import *

# MySQL
db = Database()
db.bind(provider='mysql', host='37.46.132.57', user='telebot', passwd='Malinka2017', db='testbase')
db.generate_mapping(create_tables=True)

# Bots
updater = Updater(token=config.token)
dispatcher = updater.dispatcher

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# States for switching between handlers
NAME, FACULTY, PHONE_NUMBER, ADDRESS, END_OF_SIGNUP, BOOK_SEARCH, ARTICLE_SEARCH, AV_SEARCH = range(8)
NOT_FINISHED = range(1)

"""
search_functions(bot, update)

This is a query handler. Each time user sends inline button 
bot gets a callback query. This handler chooses the appropriate 
way to run further.
"""


@db_session
def search_functions(bot, update):
    query = update.callback_query.data
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
    else:
        parsed_query = json.loads(query)
        query_type = parsed_query['type']
        argument = parsed_query['argument']
        if query_type == 'deleteMedia':
            Media.get(mediaID=argument).delete()
            commit()
            bot.send_message(text="Media and its copies have been successfully deleted!",
                             chat_id=update.callback_query.from_user.id)
        elif query_type == 'cancelDeleteMedia':
            bot.send_message(text="Media hasn't been deleted!",
                             chat_id=update.callback_query.from_user.id)
        elif query_type == 'deleteCopy':
            MediaCopies.get(copyID=argument).delete()
            commit()
            bot.send_message(text="Copy has been successfully deleted!",
                             chat_id=update.callback_query.from_user.id)
        elif query_type == 'cancelDeleteCopy':
            bot.send_message(text="Copy hasn't been deleted!",
                             chat_id=update.callback_query.from_user.id)
        elif query_type == 'deleteUser':
            User.get(alias=argument).delete()
            RegistrySession[update.callback_query.from_user.id].delete()
            commit()
            bot.send_message(text="User has been successfully deleted!",
                             chat_id=update.callback_query.from_user.id)
        elif query_type == 'user_edit':
            edit_user(bot, update, argument)
        elif query_type == 'cancelDeleteUser':

            bot.send_message(text="User hasn't been deleted!",
                             chat_id=update.callback_query.from_user.id)
        elif query_type == 'inverseBestseller':
            media = Media.get(mediaID=argument)
            last_state = media.bestseller
            media.bestseller = not last_state
            bot.edit_message_text(
                text="Media's bestseller state has been changed from %s to %s" % (str(last_state), str(not last_state)),
                message_id=update.callback_query.message.message_id,
                chat_id=update.callback_query.from_user.id)
        elif query_type == 'inverseMediaAvailability':
            media = Media.get(mediaID=argument)
            last_state = media.availability
            media.availability = not last_state
            for elem in media.copies:
                elem.available = not last_state
            bot.edit_message_text(text="Media's availability state has been changed from %s to %s" % (
                str(last_state), str(not last_state)),
                                  message_id=update.callback_query.message.message_id,
                                  chat_id=update.callback_query.from_user.id)
        elif query_type == 'inverseFaculty':
            user = User[argument]
            user.faculty = not user.faculty
            commit()
            bot.edit_message_text(text="User's faculty state has been changed from %s to %s" % (
                str(not user.faculty), str(user.faculty)),
                                  message_id=update.callback_query.message.message_id,
                                  chat_id=update.callback_query.from_user.id)
        elif query_type == 'media_delete':
            delete_media(bot, update, argument)
        elif query_type == 'media_add_copy':
            add_copy(bot, update, argument)
        elif query_type == 'media_edit':
            edit_media(bot, update, argument)
        elif query_type == 'user_delete':
            delete_user(bot, update, list(str(argument)))
        elif query_type == 'my_medias':
            edit_my_medias_card(bot, update)
        elif query_type == 'returnMedia':
            make_return_request(bot, update, argument)
            session = RegistrySession[update.callback_query.from_user.id]
            session.my_medias_c = 0
        elif query_type == 'nextItem':
            if argument == 'my_medias':
                session = RegistrySession[update.callback_query.from_user.id]
                session.my_medias_c += 1
                commit()
                edit_my_medias_card(bot, update)
            elif argument == 'return_request':
                session = RegistrySession[update.callback_query.from_user.id]
                session.return_c += 1
                commit()
                edit_return_media(bot, update)

        elif query_type == 'prevItem':
            if argument == 'my_medias':
                session = RegistrySession[update.callback_query.from_user.id]
                session.my_medias_c -= 1
                commit()
                edit_my_medias_card(bot, update)
            elif argument == 'return_request':
                session = RegistrySession[update.callback_query.from_user.id]
                session.return_c -= 1
                commit()
                edit_return_media(bot, update)
        elif query_type == 'accept':
            if argument == 'return_request':
                accept_return(bot, update, parsed_query['id'])
        elif query_type == 'reject':
            if argument == 'return_request':
                (bot, update, parsed_query['id'])
        elif query_type == 'ask_for_return':
            ask_for_return(bot, update, argument, parsed_query['user'])


"""  Registration process   """


# Filter for phone
def all_numbers(input_string):
    return all(char.isdigit() for char in input_string)


"""
def ask_name(bot, update)

This handler starts registration process. It handles from
/enroll button. Here user's profile is starting filling 
(into temp_patron)
"""


@db_session
def ask_name(bot, update):
    message = update.message
    user = User.get(telegram_ID=message.chat_id)
    session = RegistrySession.get(telegram_ID=message.chat_id)
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
        RegistrySession(telegram_ID=message.chat_id, alias=message.chat.username)
        bot.send_message(chat_id=update.message.chat_id, text="""Let's start the enrolling process into Innopolis University Library!
Please, write your first and last name""")
        commit()

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


@db_session
def end_of_registration(bot, update):
    session_user = RegistrySession[update.callback_query.from_user.id]
    Request(
        telegram_ID=session_user.telegram_ID,
        name=session_user.name,
        phone=session_user.phone,
        address=session_user.address,
        alias=session_user.alias,
        faculty=session_user.faculty)
    commit()
    bot.send_message(chat_id=update.callback_query.from_user.id, text="Application was sent to library!")
    return register_conversation.END


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

    request_card = Scroller('request', registry, update.message.chat_id)
    try:
        bot.send_message(text=request_card.create_message(), chat_id=update.message.chat_id,
                         reply_markup=request_card.create_keyboard())
    except FileNotFoundError as e:
        bot.send_message(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


@db_session
def create_media_card(bot, update):
    registry = list(Media.select())
    media_card = Scroller('media', registry, update.message.chat_id)

    try:
        bot.send_message(text=media_card.create_message(), chat_id=update.message.chat_id,
                         reply_markup=media_card.create_keyboard())
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


@db_session
def return_media(bot, update):
    registry = list(ReturnRequest.select())
    log = Scroller('return_request', registry, update.message.chat_id)
    try:
        bot.send_message(text=log.create_message(), chat_id=update.message.chat_id,
                         reply_markup=log.create_keyboard())
    except FileNotFoundError as e:
        bot.send_message(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


@db_session
def edit_return_media(bot, update):
    registry = list(ReturnRequest.select())
    query = update.callback_query
    log = Scroller('return_request', registry, update.callback_query.message.chat_id)
    try:
        bot.edit_message_text(text=log.create_message(), chat_id=query.message.chat_id,
                              message_id=query.message.message_id, reply_markup=log.create_keyboard())
    except FileNotFoundError as e:
        bot.edit_message_text(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


"""
Following three functions are called from queries from buttons.
When user presses button, message gets changed for the next/previous
record.
"""


def edit_request_card(bot, update):
    query = update.callback_query
    try:
        registry = list(Request.select(lambda c: c.status == 0))

        request_card = Scroller('request', registry, update.callback_query.from_user.id)
        bot.edit_message_text(text=request_card.create_message(), chat_id=query.message.chat_id,
                              message_id=query.message.message_id, reply_markup=request_card.create_keyboard())
    except UnboundLocalError as e:
        logging.error("Error occured: " + e.args[0])
        bot.edit_message_text(text="Error occured: " + e.args[0], chat_id=query.message.chat_id,
                              message_id=query.message.message_id)


def edit_media_card(bot, update):
    query = update.callback_query
    try:
        registry = list(Media.select())
        media_card = Scroller('media', registry, query.message.chat_id)
        bot.edit_message_text(text=media_card.create_message(), chat_id=query.message.chat_id,
                              message_id=query.message.message_id, reply_markup=media_card.create_keyboard())
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


def edit_my_medias_card(bot, update):
    query = update.callback_query
    try:
        medias = list(Log.select(lambda c: c.libID == update.callback_query.message.chat_id and not c.returned))
        media_container = Scroller('user_medias', medias, query.message.chat_id)
        bot.edit_message_text(text=media_container.create_message(), chat_id=query.message.chat_id,
                              message_id=query.message.message_id, reply_markup=media_container.create_keyboard())
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
    telegram_id = update.message.chat_id
    librarian = Librarian.get(telegramID=telegram_id)
    if not librarian_authentication(telegram_id):
        print("Unauthorized logging")
        return 0

    bot.send_message(text="""Hello, %s!
Here's a list of useful commands, which are only allowed to librarians:
/requests - see registry requests    
/log - see log of librarian
/return - return a book
/users - list of users
""" % librarian.name, chat_id=telegram_id)


@db_session
def users(bot, update):
    telegram_id = update.message.chat_id
    if not librarian_authentication(telegram_id):
        return 0
    list_of_all_users = User.select()
    string = ""
    for user in list_of_all_users:
        string += "Telegram ID: " + str(user.telegram_ID) + "\n" + \
                  "Name: " + user.name + "\n" + \
                  "Address: " + user.address + "\n" + \
                  "Phone: " + user.phone + "\n" + \
                  "Faculty? " + str(user.faculty) + "\n" + \
                  "Medias: " + "\n"
        list_of_user_medias = Log.select(lambda c: c.libID == user.telegram_ID and not c.returned)
        for item in list_of_user_medias:
            abstract_media = MediaCopies.get(copyID=item.mediaID).mediaID
            string += "     ID: " + item.mediaID + "\n" + \
                      "         " + abstract_media.name + " by " + abstract_media.authors + "\n" + \
                      "     Issued: " + item.issue_date.strftime("%H:%M %d %h %Y") + "\n" + \
                      "     Expiry: " + item.expiry_date.strftime("%H:%M %d %h %Y") + "\n"
        string += "\n"
    bot.send_message(text=string, chat_id=update.message.chat_id)


@db_session
def delete_media(bot, update, media_id):
    telegram_id = update.callback_query.message.chat_id
    deleted_media = Media.get(mediaID=media_id)
    if deleted_media is None:
        bot.send_message(text="Sorry, media with this ID doesn't exist", chat_id=update.message.chat_id)
        return 0
    message = "Are you sure you want to delete \"" + deleted_media.name + "\" by " + \
              deleted_media.authors + " and all its copies?"
    delete_query = json.dumps({'type': 'deleteMedia', 'argument': media_id})
    stay_query = json.dumps({'type': 'cancelDeleteMedia', 'argument': media_id})
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅", callback_data=delete_query),
                                      InlineKeyboardButton("🚫", callback_data=stay_query)]])
    bot.send_message(text=message, chat_id=telegram_id, reply_markup=keyboard)


@db_session
def delete_copy(bot, update, args):
    media_id = "".join(args).strip()
    deleted_media = MediaCopies.get(copyID=media_id)
    if deleted_media is None:
        bot.send_message(text="Sorry, copy with this ID doesn't exist", chat_id=update.message.chat_id)
        return 0
    message = "Are you sure you want to delete \"" + deleted_media.mediaID.name + "\" by " + \
              deleted_media.mediaID.authors + " (" + deleted_media.copyID + ")?"
    delete_query = json.dumps({'type': 'deleteCopy', 'argument': media_id})
    stay_query = json.dumps({'type': 'cancelDeleteCopy', 'argument': media_id})
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅", callback_data=delete_query),
                                      InlineKeyboardButton("🚫", callback_data=stay_query)]])
    bot.send_message(text=message, chat_id=update.message.chat_id, reply_markup=keyboard)


@db_session
def delete_user(bot, update, args):
    alias = "".join(args).replace("@", "")
    deleted_user = User.get(alias=alias)
    if deleted_user is None:
        bot.send_message(text="Sorry, copy with this alias doesn't exist", chat_id=update.message.chat_id)
        return 0
    message = "Are you sure you want to delete " + deleted_user.name + " from the ILMK?"
    delete_query = json.dumps({'type': 'deleteUser', 'argument': alias})
    stay_query = json.dumps({'type': 'cancelDeleteUser', 'argument': alias})
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅", callback_data=delete_query),
                                      InlineKeyboardButton("🚫", callback_data=stay_query)]])
    try:
        bot.send_message(text=message, chat_id=update.message.chat_id, reply_markup=keyboard)
    except AttributeError:
        bot.send_message(text=message, chat_id=update.callback_query.message.chat_id, reply_markup=keyboard)


@db_session
def add_copy(bot, update, media_id):
    abstract_media = Media.get(mediaID=media_id)
    copies = list(abstract_media.copies)
    copy_to_add = MediaCopies(mediaID=media_id, copyID=str(media_id) + "-" + str(len(copies) + 1), available=1)
    copies.append(copy_to_add)
    abstract_media.copies = copies
    commit()
    bot.send_message(text="New copy has been added!", chat_id=update.callback_query.message.chat_id)


@db_session
def edit_media(bot, update, media_id):
    author = InlineKeyboardButton("Author",
                                  callback_data=json.dumps(
                                      {'type': 'editMediaAuthor', 'argument': media_id, 'field': 'author'}))
    title = InlineKeyboardButton("Title",
                                 callback_data=json.dumps(
                                     {'type': 'editMediaTitle', 'argument': media_id, 'field': 'title'}))
    availability = InlineKeyboardButton("Availability",
                                        callback_data=json.dumps(
                                            {'type': 'inverseMediaAvailability', 'argument': media_id}))
    fine = InlineKeyboardButton("Fine",
                                callback_data=json.dumps(
                                    {'type': 'editMediaFine', 'argument': media_id, 'field': 'fine'}))
    price = InlineKeyboardButton("Price",
                                 callback_data=json.dumps(
                                     {'type': 'editMediaPrice', 'argument': media_id, 'field': 'price'}))
    bestseller = InlineKeyboardButton("Bestseller",
                                      callback_data=json.dumps({'type': 'inverseBestseller', 'argument': media_id}))
    up_row = [author, title, bestseller]
    low_row = [availability, fine, price]
    keyboard = InlineKeyboardMarkup([up_row, low_row])

    bot.send_message(text="What do you want to change?", chat_id=update.callback_query.message.chat_id,
                     reply_markup=keyboard)


ENTER_VALUE = range(1)


@db_session
def edit_field(bot, update):
    query = json.loads(update.callback_query.data)
    telegram_id = update.callback_query.message.chat_id
    media_id = query['argument']
    field = query['field']
    media, user = [], []
    last_value = ""
    try:
        user = User[id]
    except UnboundLocalError:
        media = Media.get(mediaID=media_id)
    if field == 'title':
        last_value = media.name
    elif field == 'author':
        last_value = media.authors
    elif field == 'fine':
        last_value = str(media.fine)
    elif field == 'price':
        last_value = str(media.cost)
    elif field == 'name':
        last_value = user.name
    elif field == 'addr':
        last_value = user.address
    elif field == 'phone':
        last_value = str(user.phone)

    session = RegistrySession[telegram_id]
    session.edit_media_cursor = media_id
    session.edit_media_state = field
    commit()

    bot.edit_message_text(text="Last value: %s \nPlease, enter new value:" % last_value,
                          message_id=update.callback_query.message.message_id,
                          chat_id=update.callback_query.message.chat_id)

    return ENTER_VALUE


@db_session
def change_value(bot, update):
    telegram_id = update.message.chat_id
    text = update.message.text
    session = RegistrySession[telegram_id]
    field = session.edit_media_state
    media, user = [], []
    try:
        user = User[session.edit_media_cursor]

    except UnboundLocalError:
        media = Media.get(mediaID=session.edit_media_cursor)
    if field == 'title':
        media.name = text
    elif field == 'author':
        media.authors = text
    elif field == 'fine':
        media.fine = int(text)
    elif field == 'price':
        media.cost = int(text)
    elif field == 'name':
        user.name = text
    elif field == 'addr':
        user.address = text
    elif field == 'phone':
        user.phone = text

    commit()

    bot.send_message(text="Everything has been saved!",
                     chat_id=update.message.chat_id)
    return edit_conv.END


@db_session
def edit_user(bot, update, telegram_id):
    name = InlineKeyboardButton("Name",
                                callback_data=json.dumps(
                                    {'type': 'editUserName', 'argument': telegram_id, 'field': 'name'}))
    address = InlineKeyboardButton("Address",
                                   callback_data=json.dumps(
                                       {'type': 'editAddress', 'argument': telegram_id, 'field': 'addr'}))
    phone = InlineKeyboardButton("Phone",
                                 callback_data=json.dumps(
                                     {'type': 'editPhone', 'argument': telegram_id, 'field': 'phone'}))
    faculty = InlineKeyboardButton("Faculty",
                                   callback_data=json.dumps({'type': 'inverseFaculty', 'argument': telegram_id}))

    up_row = [name, address]
    low_row = [phone, faculty]
    keyboard = InlineKeyboardMarkup([up_row, low_row])

    bot.send_message(text="What do you want to change?", chat_id=update.callback_query.message.chat_id,
                     reply_markup=keyboard)


@db_session
def me(bot, update):
    telegram_id = update.message.chat_id
    my_user = User.get(telegram_ID=telegram_id)
    if my_user is None:
        bot.send_message(text="Sorry, you're not a user. /enroll now!", chat_id=telegram_id)
        return 0

    edit_button = InlineKeyboardButton("Edit",
                                       callback_data=json.dumps({'type': 'user_edit', 'argument': my_user.telegram_ID}))
    delete_button = InlineKeyboardButton("Delete",
                                         callback_data=json.dumps({'type': 'user_delete', 'argument': my_user.alias}))
    my_medias_button = InlineKeyboardButton("My medias",
                                            callback_data=json.dumps({'type': 'my_medias', 'argument': 0}))

    keyboard = [[edit_button, delete_button], [my_medias_button]]
    keyboard = InlineKeyboardMarkup(keyboard)
    message = "Hello, %s! \nHere is information about you: \n👨‍🎓: %s (@%s) \n🏠: %s \n☎️: %s \n🎓: %s" % (
        my_user.name, my_user.name, my_user.alias, my_user.address, my_user.phone, convert_to_emoji(my_user.faculty))
    bot.send_message(text=message, chat_id=telegram_id, reply_markup=keyboard)


@db_session
def create_new_media(bot, update):
    """
    The same thing as with NEW PATRON but with media
    """
    session = RegistrySession.get(telegram_ID=update.message.chat_id)
    if session is not None:
        if session.type == "":
            if update.message.text == "/add_media":
                bot.send_message(text="Let's add a new media! What is the type of media?",
                                 chat_id=update.message.chat_id)
                return NOT_FINISHED
            session.type = update.message.text
            bot.send_message(text="What is the title of media?", chat_id=update.message.chat_id)
            return NOT_FINISHED
        elif session.title == "":
            session.title = update.message.text
            bot.send_message(text="Who is the author?", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.author == "":
            session.author = update.message.text
            bot.send_message(text="What is the publisher?", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.publisher == "":
            session.publisher = update.message.text
            bot.send_message(text="What is the price?", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.price == -1:
            session.price = update.message.text
            bot.send_message(text="What is the fine?", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.fine == -1:
            session.fine = update.message.text
            bot.send_message(text="How many copies do you want to add?", chat_id=update.message.chat_id)
            commit()
        elif session.no_of_copies == -1:
            no_of_copies = int(update.message.text)
            session.no_of_copies = no_of_copies
            Media(name=session.title, type=session.type, authors=session.author,
                  publisher=session.publisher, cost=session.price, fine=session.fine,
                  availability=True, bestseller=False)
            media_id = Media.get(name=session.title).mediaID
            for i in range(1, no_of_copies + 1):
                MediaCopies(mediaID=media_id, copyID="%s-%s" % (str(media_id), str(i)), available=1)
            session.title = ""
            session.type = ""
            session.author = ""
            session.fine = -1
            session.price = -1
            session.no_of_copies = -1
            session.publisher = ""
            commit()
            bot.send_message(text="Media and %s its copies had been added" % str(no_of_copies),
                             chat_id=update.message.chat_id)
            return new_media_conversation.END
    else:
        RegistrySession(telegram_ID=update.message.chat_id)
        bot.send_message(text="Please, enter Title: ", chat_id=update.message.chat_id)
        return NOT_FINISHED


@db_session
def create_new_user(bot, update):
    session = RegistrySession.get(telegramID=update.message.chat_id)
    if session is not None:
        if session.user_telegramID == -1:
            if update.message.text == "/add_user":
                bot.send_message(text="Let's add a new User! Please, enter new user's Telegram ID",
                                 chat_id=update.message.chat_id)
                return NOT_FINISHED
            session.user_telegramID = update.message.text
            bot.send_message(text="Please, enter new user's alias", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.alias == "":
            session.alias = update.message.text
            bot.send_message(text="Please, enter new user's name", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.name == "":
            session.name = update.message.text
            bot.send_message(text="Please, enter new user's phone", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.phone == "":
            session.phone = update.message.text
            bot.send_message(text="Please, enter new user's address", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.address == "":
            session.address = update.message.text
            bot.send_message(text="Is he/she a faculty member?", chat_id=update.message.chat_id)
            commit()
            return NOT_FINISHED
        elif session.faculty is None:
            session.faculty = update.message.text
            bot.send_message(text="User was added", chat_id=update.message.chat_id)
            User(telegramID=session.user_telegramID, name=session.name, phone=session.phone,
                 address=session.address, faculty=session.faculty, alias=session.alias)
            session.delete()
            commit()
            return new_user_conversation.END


def cancel_process(bot, update):
    bot.send_message(text="Process has been cancelled.", chat_id=update.message.chat_id)


"""
This is a conversation handler. It helps smoothly iterating 
from one command to another. Entry point is /enroll command.

Using states handler switches from one function to another.
"""
register_conversation = ConversationHandler(entry_points=[CommandHandler("enroll", ask_name)],
                                            states={
                                                PHONE_NUMBER: [MessageHandler(Filters.text, ask_phone)],
                                                ADDRESS: [MessageHandler(Filters.text, ask_address)],
                                                FACULTY: [MessageHandler(Filters.text, ask_faculty)]
                                            },
                                            fallbacks=[])
new_media_conversation = ConversationHandler(entry_points=[CommandHandler("add_media", create_new_media)],
                                             states={
                                                 NOT_FINISHED: [MessageHandler(Filters.text, create_new_media)]
                                             },
                                             fallbacks=[CommandHandler('cancel', cancel_process)])
new_user_conversation = ConversationHandler(entry_points=[CommandHandler("add_user", create_new_user)],
                                            states={
                                                NOT_FINISHED: [MessageHandler(Filters.text, create_new_user)]
                                            },
                                            fallbacks=[])
edit_conv = ConversationHandler(entry_points=[CallbackQueryHandler(edit_field, pattern="^{\"type\": \"edit")],
                                states={
                                    ENTER_VALUE: [MessageHandler(Filters.text, change_value)]
                                },
                                fallbacks=[])

"""
This part connects commands, queries and any other input information to features
in code. These are handlers.
"""
dispatcher.add_handler(register_conversation)
dispatcher.add_handler(new_media_conversation)
dispatcher.add_handler(new_user_conversation)
dispatcher.add_handler(edit_conv)

search_query_handler = CallbackQueryHandler(search_functions)
dispatcher.add_handler(CommandHandler('requests', create_request_card))
dispatcher.add_handler(CommandHandler('return', return_media))
dispatcher.add_handler(CommandHandler('medias', create_media_card))
dispatcher.add_handler(CommandHandler('issue', issue_media))
dispatcher.add_handler(CommandHandler('log', create_log_card))
dispatcher.add_handler(CommandHandler('me', me))
dispatcher.add_handler(CommandHandler('edit_user', edit_user, pass_args=True))
dispatcher.add_handler(CommandHandler('delete_copy', delete_copy, pass_args=True))
dispatcher.add_handler(CommandHandler('delete_user', delete_user, pass_args=True))
dispatcher.add_handler(CommandHandler('users', users))
dispatcher.add_handler(CommandHandler('librarian', librarian_interface))
dispatcher.add_handler(search_query_handler)

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
