from telegram.ext import Updater
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler
from telegram.ext import Filters
from telegram.ext import CommandHandler
from database import *
import logging
import config as config
from scroller import Scroller
import json
from button_actions import *
from key_generator import generate_key
from telegram.ext import jobqueue
from datetime import datetime, date, time
import datetime as dt

import os

# MySQL
db = Database()

db.bind(provider='mysql', host=config.db_host, user=config.db_username, passwd=config.db_password, db=config.db_name)
db.generate_mapping(create_tables=True)

updater = Updater(token=config.token)
dispatcher = updater.dispatcher

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# States for switching between handlers


NAME, PRIORITY, PHONE_NUMBER, ADDRESS, END_OF_SIGNUP, BOOK_SEARCH, ARTICLE_SEARCH, AV_SEARCH, NOT_FINISHED, ENTER_VALUE = range(
    10)


@db_session  # Means that this function is using database
def callback_query_selector(bot, update):
    """
    This is a query handler. Each time user sends inline button
    bot gets a callback query. This handler chooses the appropriate
    way to run further.
    :param bot:     bot object
    :param update:  update object
    :return:        none
    """
    query = update.callback_query.data
    parsed_query = json.loads(query)

    #   'type' and 'argument' values are in each button
    query_type = parsed_query['type']
    argument = parsed_query['argument']

    #
    if query_type == 'priority':

        session_user = RegistrySession[update.callback_query.from_user.id]
        session_user.faculty = argument
        commit()
        end_of_registration(bot, update)

    elif query_type == 'approveRequest':
        approve_request(bot, update)
    elif query_type == 'rejectRequest':
        reject_request(bot, update)
    elif query_type == 'book':
        book_media(bot, update)
    elif query_type == 'get_in_line':
        add_in_line(bot, update)
    elif query_type == 'get_out_of_line':
        query = update.callback_query
        telegram_id = query.message.chat_id
        session = database.RegistrySession[telegram_id]
        media = list(database.Media.select())[session.media_c]
        MediaQueue.select(lambda c: c.user == User[telegram_id] and c.mediaID == media).delete()
        database.Actions(implementer=str(telegram_id),
                         action="got out of line for media #",
                         implementee=str(media.mediaID))
        bot.edit_message_text(text="You got out of the line!",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)

    # 'Delete' states

    #   Requests for deleting
    elif query_type == 'media_delete':
        delete_media(bot, update, argument)
    elif query_type == 'user_delete':
        delete_user(bot, update, argument)

    # Actions with librarians
    elif query_type == 'lib_delete':
        yes_json = json.dumps({'type': 'lib_delete_y', 'argument': argument})
        no_json = json.dumps({'type': 'lib_delete_n', 'argument': argument})
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Yes", callback_data=yes_json),
            InlineKeyboardButton("No", callback_data=no_json)
        ]])
        bot.edit_message_text(text="Do you really want to remove librarian rights?",
                              chat_id=update.callback_query.message.chat_id,
                              message_id=update.callback_query.message.message_id,
                              reply_markup=keyboard)
    elif query_type == 'lib_delete_y':
        admin = Admin.get(telegram_id=update.callback_query.message.chat_id)
        admin.delete_librarian(argument)
        database.Actions(implementer=str(update.callback_query.message.chat_id),
                         action="has deleted rights for librarian #",
                         implementee=str(argument))
        bot.edit_message_text(text="Rights was removed!",
                              chat_id=update.callback_query.message.chat_id,
                              message_id=update.callback_query.message.message_id)
    elif query_type == 'lib_delete_n':
        bot.edit_message_text(text="Process was cancelled.",
                              chat_id=update.callback_query.message.chat_id,
                              message_id=update.callback_query.message.message_id)
    elif query_type == 'priv_edit':
        admin = Admin.get(telegram_id=update.callback_query.message.chat_id)
        admin.new_lib_id = argument
        see_edit = json.dumps({'type': 'adm_s_pr', 'argument': 'edit'})
        add = json.dumps({'type': 'adm_s_pr', 'argument': 'add'})
        deletion = json.dumps({'type': 'adm_s_pr', 'argument': 'delete'})
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("See/Edit", callback_data=see_edit),
                                          InlineKeyboardButton(" + Addition", callback_data=add),
                                          InlineKeyboardButton(" + Deletion", callback_data=deletion)]])
        bot.edit_message_text(text="Choose librarian's new privileges:",
                              message_id=update.callback_query.message.message_id,
                              chat_id=update.callback_query.from_user.id,
                              reply_markup=keyboard)

    # Confirmed deletes
    elif query_type == 'deleteMedia':
        Media.get(mediaID=argument).delete()
        commit()
        database.Actions(implementer=str(update.callback_query.message.chat_id),
                         action="has deleted media #",
                         implementee=str(argument))
        bot.send_message(text="Media and its copies have been successfully deleted!",
                         chat_id=update.callback_query.from_user.id)
    elif query_type == 'cancelDeleteMedia':
        bot.send_message(text="Media hasn't been deleted!",
                         chat_id=update.callback_query.from_user.id)
    elif query_type == 'deleteCopy':
        MediaCopies.get(copyID=argument).delete()
        commit()
        database.Actions(implementer=str(update.callback_query.message.chat_id),
                         action="has deleted media copy #",
                         implementee=str(argument))
        bot.send_message(text="Copy has been successfully deleted!",
                         chat_id=update.callback_query.from_user.id)
    elif query_type == 'cancelDeleteCopy':
        bot.send_message(text="Copy hasn't been deleted!",
                         chat_id=update.callback_query.from_user.id)
    elif query_type == 'deleteUser':
        User.get(telegramID=argument).delete()
        commit()
        database.Actions(implementer=str(update.callback_query.message.chat_id),
                         action="has deleted user #",
                         implementee=str(argument))
        bot.send_message(text="User has been successfully deleted!",
                         chat_id=update.callback_query.from_user.id)
        session = RegistrySession[update.callback_query.from_user.id]
        session.users_c = 0
        commit()
    elif query_type == 'cancelDeleteUser':
        bot.send_message(text="User hasn't been deleted!",
                         chat_id=update.callback_query.from_user.id)

    # 'Edit' states

    #   Inverse states
    elif query_type == 'inverseBestseller':
        media = Media.get(mediaID=argument)
        last_state = media.bestseller
        media.bestseller = not last_state
        database.Actions(implementer=str(update.callback_query.message.chat_id),
                         action="has inversed media bestseller from %s to %s" % (str(last_state), str(not last_state)),
                         implementee=str(argument))
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
        database.Actions(implementer=str(update.callback_query.message.chat_id),
                         action="has inversed media availability from %s to %s" % (
                             str(last_state), str(not last_state)),
                         implementee=str(argument))
        bot.edit_message_text(text="Media's availability state has been changed from %s to %s" % (
            str(last_state), str(not last_state)),
                              message_id=update.callback_query.message.message_id,
                              chat_id=update.callback_query.from_user.id)

    elif query_type == 'priorityEdited':
        user = User.get(telegramID=update.callback_query.from_user.id)
        user.priority = argument
        commit()

        bot.edit_message_text(text="Status was successfully changed!",

                              message_id=update.callback_query.message.message_id,
                              chat_id=update.callback_query.from_user.id)

    # Editing menu calls and fixes
    elif query_type == 'user_edit':
        edit_user(bot, update, argument)
    elif query_type == 'media_add_copy':
        add_copy(bot, update, argument)
    elif query_type == 'media_edit':
        edit_media(bot, update, argument)
    elif query_type == 'my_medias':
        edit_my_medias_card(bot, update)

    # Return media
    elif query_type == 'returnMedia':
        make_return_request(bot, update, argument)
        session = RegistrySession[update.callback_query.from_user.id]
        session.my_medias_c = 0
        commit()
    elif query_type == 'accept':
        if argument == 'return_request':
            accept_return(bot, update, parsed_query['id'])
            session = RegistrySession[update.callback_query.from_user.id]
            session.return_c = 0
    elif query_type == 'reject':
        if argument == 'return_request':
            reject_return(bot, update, parsed_query['id'])
            session = RegistrySession[update.callback_query.from_user.id]
            session.return_c = 0
    elif query_type == 'ask_for_return':
        ask_for_return(bot, update, argument, parsed_query['user'])

    # Renew media
    elif query_type == 'renewMedia':
        renew_media(bot, update, argument)

    elif query_type == 'my_balance':
        print_balance(bot, update, argument)

    elif query_type == 'pay':
        pay_for_media(bot, update, argument, parsed_query['media'])


    # Arrows for switching between cards
    # Selectors for 'next' arrows
    elif query_type == 'nextItem':
        if argument == 'request':
            session = RegistrySession[update.callback_query.from_user.id]
            session.request_c += 1
            commit()
            edit_request_card(bot, update)
        elif argument == 'media':
            session = RegistrySession[update.callback_query.from_user.id]
            session.media_c += 1
            commit()
            edit_media_card(bot, update)
        elif argument == 'my_medias':
            session = RegistrySession[update.callback_query.from_user.id]
            session.my_medias_c += 1
            commit()
            edit_my_medias_card(bot, update)
        elif argument == 'log':
            session = RegistrySession[update.callback_query.from_user.id]
            session.log_c += 1
            commit()
            edit_log_card(bot, update)
        elif argument == 'return_request':
            session = RegistrySession[update.callback_query.from_user.id]
            session.return_c += 1
            commit()
            edit_return_media(bot, update)
        elif argument == 'users':
            session = RegistrySession[update.callback_query.from_user.id]
            session.users_c += 1
            commit()
            edit_users_card(bot, update)
        elif argument == 'users':
            session = RegistrySession[update.callback_query.from_user.id]
            session.users_c += 1
            commit()
            edit_users_card(bot, update)
        elif argument == 'librs':
            session = RegistrySession[update.callback_query.from_user.id]
            session.users_c += 1
            edit_librarians_card(bot, update)
        elif argument == 'debtors':  # воть тут
            session = RegistrySession[update.callback_query.from_user.id]
            session.debtors_c += 1
            commit()
            edit_debt_card(bot, update)

    # Selectors for 'prev' arrows
    elif query_type == 'prevItem':
        if argument == 'request':
            session = RegistrySession[update.callback_query.from_user.id]
            session.request_c -= 1
            commit()
            edit_request_card(bot, update)
        elif argument == 'media':
            session = RegistrySession[update.callback_query.from_user.id]
            session.media_c -= 1
            commit()
            edit_media_card(bot, update)
        elif argument == 'my_medias':
            session = RegistrySession[update.callback_query.from_user.id]
            session.my_medias_c -= 1
            commit()
            edit_my_medias_card(bot, update)
        elif argument == 'log':
            session = RegistrySession[update.callback_query.from_user.id]
            session.log_c -= 1
            commit()
            edit_log_card(bot, update)
        elif argument == 'return_request':
            session = RegistrySession[update.callback_query.from_user.id]
            session.return_c -= 1
            commit()
            edit_return_media(bot, update)
        elif argument == 'users':
            session = RegistrySession[update.callback_query.from_user.id]
            session.users_c -= 1
            commit()
            edit_users_card(bot, update)
        elif argument == 'librs':
            session = RegistrySession[update.callback_query.from_user.id]
            session.users_c -= 1
            edit_librarians_card(bot, update)
        elif argument == 'debtors':  # воть тут
            session = RegistrySession[update.callback_query.from_user.id]
            session.debtors_c -= 1
            commit()
            edit_debt_card(bot, update)
    elif query_type == 'outstanding_request':
        librarian = Librarian.get(telegramID=update.callback_query.from_user.id)
        status = librarian.outstanding_request(argument, datetime.datetime.now())
        if status[0] == 1:
            database.Actions(implementer=str(update.callback_query.message.chat_id),
                             action="has placed an outstanding request for media #",
                             implementee=str(argument))
            bot.edit_message_text(text="Request completed!",
                                  message_id=update.callback_query.message.message_id,
                                  chat_id=update.callback_query.message.chat_id)
            title = Media[argument].name
            queue = status[1]
            for element in queue:
                bot.send_message(text="Sorry, you have been deleted from "
                                      "the queue for the following media: "
                                      "%s because of an outstanding "
                                      "request" % title,
                                 chat_id=element.telegramID)
            holders = status[2]
            for element in holders:
                ask_for_return(bot, update, element[1], element[0])

    # Features of ADMIN
    # 'acpt_nl' is 'accept new librarian'
    # 'adm_s_pr' is 'admin sets privilege'
    elif query_type == 'acpt_nl':
        if argument == 'Yes':
            admin = Admin.get(telegram_id=update.callback_query.message.chat_id)
            see_edit = json.dumps({'type': 'adm_s_pr', 'argument': 'edit'})
            add = json.dumps({'type': 'adm_s_pr', 'argument': 'add'})
            deletion = json.dumps({'type': 'adm_s_pr', 'argument': 'delete'})
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("See/Edit", callback_data=see_edit),
                                              InlineKeyboardButton(" + Addition", callback_data=add),
                                              InlineKeyboardButton(" + Deletion", callback_data=deletion)]])
            admin.add_new_librarian()
            bot.edit_message_text(text="Choose new librarian's privilege:",
                                  message_id=update.callback_query.message.message_id,
                                  chat_id=update.callback_query.from_user.id,
                                  reply_markup=keyboard)
        if argument == 'No':
            bot.edit_message_text(text="Process was cancelled!",
                                  message_id=update.callback_query.message.message_id,
                                  chat_id=update.callback_query.from_user.id)

    elif query_type == 'adm_s_pr':
        admin = Admin[update.callback_query.message.chat_id]
        action = admin.set_privilege(argument)
        bot.edit_message_text(text=action,
                              message_id=update.callback_query.message.message_id,
                              chat_id=update.callback_query.from_user.id)


"""  Registration process   """


# Filter for phone
def all_numbers(input_string):
    return all(char.isdigit() for char in input_string)


@db_session
def ask_name(bot, update):
    """
    This handler starts registration process. It handles from
    /enroll button. Here user's profile is starting filling
    :param bot: bot object
    :param update: update object
    :return: PHONE_NUMBER statement
    """
    message = update.message
    user = User.get(telegramID=message.chat_id)
    session = RegistrySession.get(telegramID=message.chat_id)
    if user is not None:
        bot.send_message(text="🎓 Sorry, you have already been registered", chat_id=message.chat_id)
        return register_conversation.END
    elif session is not None:
        if session.name == "":
            bot.send_message(chat_id=update.message.chat_id, text="""Let's start the enrolling process into Innopolis University Library!
Please, write your first and last name""")
            return PHONE_NUMBER
        if session.phone == "":
            ask_phone(bot, update)
        elif session.address == "":
            ask_address(bot, update)
        elif session.faculty == "":
            ask_priority(bot, update)
    else:
        RegistrySession(telegramID=message.chat_id, alias=message.chat.username)
        bot.send_message(chat_id=update.message.chat_id, text="""Let's start the enrolling process into Innopolis University Library!
Please, write your first and last name""")
        commit()

        """
        This statement is required for transferring from one handler 
        to another using ConversationHandler
        """

        return PHONE_NUMBER


@db_session
def ask_phone(bot, update):
    """
    This is the second handler. It asks for phone.
    We can't get the user's default phone number,
    because of Telegram restrictions :(
    :param bot: bot object
    :param update: update object
    :return: ADDRESS statement
    """

    session_user = RegistrySession[update.message.chat_id]
    session_user.name = update.message.text
    bot.send_message(chat_id=update.message.chat_id, text="Please, write your phone number")
    commit()
    return ADDRESS


@db_session
def ask_address(bot, update):
    """
    This is the third handler. It asks for address.
    :param bot: bot object
    :param update: update object
    :return: PRIORITY statement
    """
    session_user = RegistrySession[update.message.chat_id]
    message = update.message.text
    filtered_message = message.replace("+", "").replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
    if all_numbers(filtered_message):
        session_user.phone = update.message.text
        bot.send_message(chat_id=update.message.chat_id, text="Please, write your address")
        commit()
        return PRIORITY
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Oops, this is not a phone number, try again")


@db_session
def ask_priority(bot, update):
    """
    This is the fourth handler. It asks user's status
    (who is this user)
    :param bot: bot object
    :param update: update object
    :return: end register_conversation
    """

    session_user = RegistrySession[update.message.chat_id]
    session_user.address = update.message.text
    commit()

    # Buttons for choosing user's status, callback_data is what bot gets as a query (see callback_query_selector())
    reply = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Student", callback_data=json.dumps({'type': 'priority', 'argument': 5})),
          InlineKeyboardButton("Instructor", callback_data=json.dumps({'type': 'priority', 'argument': 4}))],
         [InlineKeyboardButton("TA", callback_data=json.dumps({'type': 'priority', 'argument': 3})),
          InlineKeyboardButton("Professor", callback_data=json.dumps({'type': 'priority', 'argument': 1}))],
         [InlineKeyboardButton("Visiting Professor", callback_data=json.dumps({'type': 'priority', 'argument': 2}))]])

    bot.send_message(chat_id=update.message.chat_id, text="Choose your status:", reply_markup=reply)
    return register_conversation.END


@db_session
def end_of_registration(bot, update):
    """
    This is the end of registration.
    If everything is correct, send request to database.
    :param bot: bot object
    :param update: update object
    :return: end register_conversation
    """
    session_user = RegistrySession[update.callback_query.from_user.id]
    if Request.get(telegramID=session_user.telegramID) is not None:
        bot.send_message(chat_id=update.callback_query.from_user.id, text="You have already applied for enrollment!")
        return register_conversation.END

    Request(telegramID=session_user.telegramID,
            name=session_user.name,
            phone=session_user.phone,
            address=session_user.address,
            alias=session_user.alias,
            faculty=session_user.faculty)

    session_user.name = ""
    session_user.faculty = 0
    session_user.address = ""
    session_user.alias = ""
    commit()
    bot.send_message(chat_id=update.callback_query.from_user.id, text="Application was sent to library!")
    return register_conversation.END


"""
These objects are from Scroller class (see scroller.py)
They perform menus for viewing menu, registry requests
and booking requests.


Card - message which contains all required data about object
and allows to perform some actions (add, delete, modify)

"""


@db_session
def create_request_card(bot, update):
    """
    Creates request menu card
    :param bot: bot object
    :param update: update object
    :return: request card
    """
    registry = list(Request.select(lambda c: c.status == 0))

    request_card = Scroller('request', registry, update.message.chat_id)
    try:
        bot.send_message(text=request_card.create_message(), chat_id=update.message.chat_id,
                         reply_markup=request_card.create_keyboard())
    except FileNotFoundError as e:
        bot.send_message(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


@db_session
def create_media_card(bot, update):
    """
    Creates media menu card
    :param bot: bot object
    :param update: update object
    :return: media card
    """
    medias = list(Media.select())
    media_card = Scroller('media', medias, update.message.chat_id)

    try:
        bot.send_message(text=media_card.create_message(), chat_id=update.message.chat_id,
                         reply_markup=media_card.create_keyboard())
    except FileNotFoundError as e:
        bot.send_message(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


@db_session
def create_users_card(bot, update):
    """
    Creates users menu card
    :param bot: bot object
    :param update: update object
    :return: media card
    """

    registry = list(User.select())
    log = Scroller('users', registry, update.message.chat_id)
    try:
        bot.send_message(text=log.create_message(), chat_id=update.message.chat_id,
                         reply_markup=log.create_keyboard())
    except FileNotFoundError as e:
        bot.send_message(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


@db_session
def create_booking_request_card(bot, update):
    """
    Creates booking request menu card
    :param bot: bot object
    :param update: update object
    :return: booking request card
    """

    registry = list(MediaRequest.select())
    issue_card = Scroller('bookingRequest', registry, update.message.chat_id)
    try:
        bot.send_message(text=issue_card.create_message(), chat_id=update.message.chat_id,
                         reply_markup=issue_card.create_keyboard())
    except FileNotFoundError as e:
        bot.send_message(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


@db_session
def create_log_card(bot, update):
    """
    Creates log menu card
    :param bot: bot object
    :param update: update object
    :return: log card
    """

    registry = list(Log.select())
    log = Scroller('log', registry, update.message.chat_id)
    try:
        bot.send_message(text=log.create_message(), chat_id=update.message.chat_id,
                         reply_markup=log.create_keyboard())
    except FileNotFoundError as e:
        bot.send_message(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


@db_session
def create_debt_card(bot, update):  # воть тут

    """
    Creates log menu card
    :param bot: bot object
    :param update: update object
    :return: debtor card
    """

    registry = list(Log.select(lambda c: c.returned == 0 and c.expiry_date < dt.datetime.now()))
    log = Scroller('debtors', registry, update.message.chat_id)
    try:
        bot.send_message(text=log.create_message(), chat_id=update.message.chat_id, reply_markup=log.create_keyboard())
    except (FileNotFoundError, IndexError) as e:
        database.RegistrySession[update.message.chat_id].debtors_c = 0
        bot.send_message(text="Sorry, " + e.args[0] + ". Please, try again", chat_id=update.message.chat_id)


@db_session
def check_media_balance(bot, job):
    """
    checks the penalty for all media in log
    :param bot: bot object
    :param update: update object
    :return: log balance
    """

    log = Log.select(lambda c: c.expiry_date < datetime.datetime.now())
    for item in log:
        cost = MediaCopies.get(copyID=item.mediaID).mediaID.cost
        if item.balance + 100 <= cost:
            item.balance += 100


morning = time(7, 00)
j = updater.job_queue
j.run_daily(check_media_balance, morning)

CHOOSE_SEARCH_PARAMETER, CHOOSE_SEARCH_CRITERIA = range(2)

"""SEARCH BE CAREFUL"""


@db_session
def search_keyboard(bot, update):
    author = InlineKeyboardButton("By author",
                                  callback_data=json.dumps(
                                      {'type': 'search', 'argument': 'authors'}))
    name = InlineKeyboardButton("By name",
                                callback_data=json.dumps(
                                    {'type': 'search', 'argument': 'name'}))
    type = InlineKeyboardButton("By type",
                                callback_data=json.dumps(
                                    {'type': 'search', 'argument': 'type'}))

    publisher = InlineKeyboardButton("By publisher",
                                     callback_data=json.dumps(
                                         {'type': 'search', 'argument': 'publisher'}))
    up_row = [author, name, publisher, type]

    keyboard = InlineKeyboardMarkup([up_row])

    bot.send_message(text="What do you want to search by?", chat_id=update.message.chat_id,
                     reply_markup=keyboard)

    return CHOOSE_SEARCH_PARAMETER


@db_session
def enter_search_criteria(bot, update):
    query = json.loads(update.callback_query.data)
    telegram_id = update.callback_query.message.chat_id
    parameter = query['argument']
    database.RegistrySession[telegram_id].search_parameter = parameter
    bot.send_message(text="Enter search criteria:", chat_id=telegram_id)
    return CHOOSE_SEARCH_CRITERIA


@db_session
def search_media(bot, update):
    """
    :param bot: bot object
    :param update: update object
    :param parameter: field of search
    :param criteria: text of search
    :return: searched media
    """

    criteria = update.message.text
    parameter = database.RegistrySession[update.message.chat_id].search_parameter
    if parameter == 'name':
        medias = list(Media.select(lambda c: criteria in c.name))
    elif parameter == 'authors':
        medias = list(Media.select(lambda c: criteria in c.authors))
    elif parameter == 'publisher':
        medias = list(Media.select(lambda c: criteria in c.publisher))
    elif parameter == 'type':
        medias = list(Media.select(lambda c: c.type == criteria))

    media_card = Scroller('media', medias, update.message.chat_id)

    try:
        bot.send_message(text=media_card.create_message(), chat_id=update.message.chat_id,
                         reply_markup=media_card.create_keyboard())
        return search_conversation.END
    except FileNotFoundError as e:
        bot.send_message(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)
        return search_conversation.END


@db_session
def create_return_media_card(bot, update):
    """
    Creates return media menu card
    :param bot: bot object
    :param update: update object
    :return: return media card
    """

    registry = list(ReturnRequest.select())
    log = Scroller('return_request', registry, update.message.chat_id)
    try:
        bot.send_message(text=log.create_message(), chat_id=update.message.chat_id,
                         reply_markup=log.create_keyboard())
    except FileNotFoundError as e:
        bot.send_message(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


@db_session
def create_librarian_card(bot, update):
    """
    :param bot:
    :param update:
    :return: this feature sends message with information about librarians and keyboard with actions
    """

    libs = list(Librarian.select())
    admin = Admin.get(telegram_id=update.message.chat_id)
    if admin is not None:
        log = Scroller('librarians', libs, update.message.chat_id)
        if len(libs) == 0:
            bot.send_message(text="You have no librarians in system!",
                             chat_id=update.message.chat_id)
        else:
            bot.send_message(text=log.create_message(),
                             chat_id=update.message.chat_id,
                             reply_markup=log.create_keyboard())


"""
This section of functions edits already created cards
"""


@db_session
def edit_request_card(bot, update):
    """
    Edits request media menu card
    :param bot: bot object
    :param update: update object
    :return: return media card
    """
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


@db_session
def edit_media_card(bot, update):
    """
    Edits media menu card
    :param bot: bot object
    :param update: update object
    :return: media card
    """
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


@db_session
def edit_users_card(bot, update):
    """
    Edits users menu card
    :param bot: bot object
    :param update: update object
    :return: users card
    """
    query = update.callback_query
    try:
        registry = list(User.select())

        users_card = Scroller('users', registry, update.callback_query.from_user.id)
        bot.edit_message_text(text=users_card.create_message(), chat_id=query.message.chat_id,
                              message_id=query.message.message_id, reply_markup=users_card.create_keyboard())
    except UnboundLocalError as e:
        logging.error("Error occured: " + e.args[0])
        bot.edit_message_text(text="Error occured: " + e.args[0], chat_id=query.message.chat_id,
                              message_id=query.message.message_id)


@db_session
def edit_librarians_card(bot, update):
    """
        Edits librarians' card
        :param bot: bot object
        :param update: update object
        :return: information about librarian and keyboard with actions
        """
    query = update.callback_query
    registry = list(Librarian.select())

    libs_card = Scroller('librarians', registry, update.callback_query.from_user.id)
    bot.edit_message_text(text=libs_card.create_message(),
                          message_id=query.message.message_id,
                          chat_id=query.message.chat_id,
                          reply_markup=libs_card.create_keyboard())


@db_session
def edit_booking_request_card(bot, update):
    """
    Edits return media menu card
    :param bot: bot object
    :param update: update object
    :return: return media card
    """

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


@db_session
def edit_log_card(bot, update):
    """
    Edits log menu card
    :param bot: bot object
    :param update: update object
    :return: log card
    """

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


@db_session
def edit_debt_card(bot, update):  # воть тут
    """
    Edits log menu card
    :param bot: bot object
    :param update: update object
    :return: debtor card
    """

    query = update.callback_query
    registry = list(Log.select(lambda c: c.returned == 0 and c.expiry_date < dt.datetime.now()))
    log = Scroller('debtors', registry, query.message.chat_id)
    message = log.create_message()
    bot.edit_message_text(text=message, chat_id=query.message.chat_id,
                          message_id=query.message.message_id, reply_markup=log.create_keyboard())


@db_session
def edit_return_media(bot, update):
    """
    Edits return media menu card
    :param bot: bot object
    :param update: update object
    :return: return media card
    """
    registry = list(ReturnRequest.select())
    query = update.callback_query
    log = Scroller('return_request', registry, update.callback_query.message.chat_id)
    try:
        bot.edit_message_text(text=log.create_message(), chat_id=query.message.chat_id,
                              message_id=query.message.message_id, reply_markup=log.create_keyboard())
    except FileNotFoundError as e:
        bot.edit_message_text(text="Sorry, " + e.args[0], chat_id=update.message.chat_id)


@db_session
def edit_my_medias_card(bot, update):
    """
    Edits user's 'My medias' menu card
    :param bot: bot object
    :param update: update object
    :return: return user's 'My medias' menu card
    """
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
Things to work with medias and users
"""


@db_session
def librarian_authentication(user_id):
    """
    This function is responsible for checking if
    user is a librarian or not. If not - return false,
    if yes - return true.
    :param user_id: user;s Telegram ID
    :return: True/False
    """
    librarian = Librarian.get(telegramID=user_id)
    if librarian is not None:
        return True
    else:
        return False


@db_session
def librarian_interface(bot, update):
    """
    Prints out librarian's menu wih all features
    :param bot: bot object
    :param update: update object
    :return: message with commands
    """

    telegram_id = update.message.chat_id
    librarian = Librarian.get(telegramID=telegram_id)
    if not librarian_authentication(telegram_id):
        print("Unauthorized logging")
        return 0

    bot.send_message(text="""Hello, %s!
Here's a list of useful commands, which are only allowed to librarians:
/requests - see registry requests    

/log - see log of Library
/return - return a book
/users - list of users
/delete_copy (copy_id) - delete copy
""" % librarian.name, chat_id=telegram_id)


@db_session
def me(bot, update):
    """
    Prints out user's menu with information and features
    :param bot: bot object
    :param update: update object
    :return: message with features
    """
    telegram_id = update.message.chat_id
    my_user = User.get(telegramID=telegram_id)
    if my_user is None:
        bot.send_message(text="Sorry, you're not a user. /enroll now!", chat_id=telegram_id)
        return 0

    edit_button = InlineKeyboardButton("Edit",
                                       callback_data=json.dumps({'type': 'user_edit', 'argument': my_user.telegramID}))
    delete_button = InlineKeyboardButton("Delete",
                                         callback_data=json.dumps(
                                             {'type': 'user_delete', 'argument': my_user.telegramID}))
    my_medias_button = InlineKeyboardButton("My medias",
                                            callback_data=json.dumps({'type': 'my_medias', 'argument': 0}))
    my_balance_button = InlineKeyboardButton("My balance",
                                             callback_data=json.dumps(
                                                 {'type': 'my_balance', 'argument': my_user.telegramID}))
    keyboard = [[edit_button, delete_button], [my_medias_button], [my_balance_button]]
    keyboard = InlineKeyboardMarkup(keyboard)
    message = "Hello, %s! \nHere is information about you: \n👨‍🎓: %s (@%s) \n🏠: %s \n☎️: %s \n🎓: %s" % (
        my_user.name, my_user.name, my_user.alias, my_user.address, my_user.phone, convert_to_emoji(my_user.priority))
    bot.send_message(text=message, chat_id=telegram_id, reply_markup=keyboard)


@db_session
def delete_media(bot, update, media_id):
    """
    Asks librarian if it still wants to delete a particular
    media and all its copies.
    :param bot: bot object
    :param update: update object
    :param media_id: media to delete
    :return: message with confirmation
    """
    telegram_id = update.callback_query.message.chat_id

    #   If user is not a librarian, exit
    if not librarian_authentication(telegram_id):
        logging.warning("Patron was trying to delete a media!")
        return 0

    # Get media
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
    """
    Asks librarian if it still wants to delete a particular copy
    :param bot: bot object
    :param update: update object
    :param args: copy ID
    :return: message with confirmation
    """
    telegram_id = update.message.chat_id

    #   If user is not a librarian, exit
    if not librarian_authentication(telegram_id):
        logging.warning("Patron was trying to delete a copy!")
        return 0

    copy_id = "".join(args).strip()
    deleted_media = MediaCopies.get(copyID=copy_id)
    if deleted_media is None:
        bot.send_message(text="Sorry, copy with this ID doesn't exist", chat_id=update.message.chat_id)
        return 0
    message = "Are you sure you want to delete \"" + deleted_media.mediaID.name + "\" by " + \
              deleted_media.mediaID.authors + " (" + deleted_media.copyID + ")?"

    delete_query = json.dumps({'type': 'deleteCopy', 'argument': copy_id})
    stay_query = json.dumps({'type': 'cancelDeleteCopy', 'argument': copy_id})
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅", callback_data=delete_query),
                                      InlineKeyboardButton("🚫", callback_data=stay_query)]])
    bot.send_message(text=message, chat_id=update.message.chat_id, reply_markup=keyboard)


@db_session
def delete_user(bot, update, telegram_id):
    """
    Asks librarian if it still wants to delete a particular
    user
    :param bot: bot object
    :param update: update object
    :param telegram_id: user to delete
    :return: message with confirmation
    """
    current_telegram_id = update.callback_query.message.chat_id

    #   If user is not a librarian, exit
    if not librarian_authentication(current_telegram_id) or current_telegram_id != telegram_id:
        logging.warning("Patron was trying to delete a user!")
        return 0

    deleted_user = User.get(telegramID=telegram_id)
    if deleted_user is None:
        bot.send_message(text="Sorry, person with this alias doesn't exist", chat_id=current_telegram_id)
        return 0
    message = "Are you sure you want to delete " + deleted_user.name + " from the ILMK?"
    delete_state = json.dumps({'type': 'deleteUser', 'argument': telegram_id})
    stay_state = json.dumps({'type': 'cancelDeleteUser', 'argument': telegram_id})
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅", callback_data=delete_state),
                                      InlineKeyboardButton("🚫", callback_data=stay_state)]])

    bot.send_message(text=message, chat_id=current_telegram_id, reply_markup=keyboard)


@db_session
def add_copy(bot, update, media_id):
    """
    Adds copy of a book
    :param bot: bot object
    :param update: update object
    :param media_id: ID of abstract media to add
    :return: add a book, send a result
    """
    abstract_media = Media.get(mediaID=media_id)
    copies = list(abstract_media.copies)
    copy_to_add = MediaCopies(mediaID=media_id, copyID=str(media_id) + "-" + str(len(copies) + 1), available=1)
    copies.append(copy_to_add)
    abstract_media.copies = copies
    commit()
    bot.send_message(text="New copy has been added!", chat_id=update.callback_query.message.chat_id)


@db_session
def edit_media(bot, update, media_id):
    """
    Starting menu for media editing
    :param bot: bot object
    :param update: update object
    :param media_id: media to edit
    :return: print out a menu with options
    """
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


@db_session
def edit_user(bot, update, telegram_id):
    """
    Starting menu for media editing
    :param bot: bot object
    :param update: update object
    :param telegram_id: user to edit
    :return: print out a menu with options
    """
    name = InlineKeyboardButton("Full name",
                                callback_data=json.dumps(
                                    {'type': 'editUserName', 'argument': telegram_id, 'field': 'name'}))
    address = InlineKeyboardButton("Address",
                                   callback_data=json.dumps(
                                       {'type': 'editAddress', 'argument': telegram_id, 'field': 'addr'}))
    phone = InlineKeyboardButton("Phone",
                                 callback_data=json.dumps(
                                     {'type': 'editPhone', 'argument': telegram_id, 'field': 'phone'}))
    priority = InlineKeyboardButton("Priority",
                                    callback_data=json.dumps(
                                        {'type': 'editStat', 'argument': telegram_id, 'field': 'priority'}))

    up_row = [name, address]
    low_row = [phone, priority]

    keyboard = InlineKeyboardMarkup([up_row, low_row])

    bot.edit_message_text(text="What do you want to change?",
                          message_id=update.callback_query.message.message_id,
                          chat_id=update.callback_query.message.chat_id,
                          reply_markup=keyboard)


@db_session
def edit_field(bot, update):
    """
    Function which interacts with a certain field
    :param bot: bot object
    :param update: update object
    :return: message for user
    """

    query = json.loads(update.callback_query.data)
    telegram_id = update.callback_query.message.chat_id
    media_id = query['argument']
    field = query['field']
    media, user = [], []
    last_value = ""
    try:
        user = User[telegram_id]
    except ObjectNotFound:
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
        elif field == 'priority':
            last_value = user.priority

    session = RegistrySession[telegram_id]
    session.edit_media_cursor = media_id
    session.edit_media_state = field
    commit()

    if field == 'priority':
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Student",
                                   callback_data=json.dumps({'type': 'priorityEdited', 'argument': 5})),
              InlineKeyboardButton("Instructor",
                                   callback_data=json.dumps({'type': 'priorityEdited', 'argument': 4}))],
             [InlineKeyboardButton("TA",
                                   callback_data=json.dumps({'type': 'priorityEdited', 'argument': 3})),
              InlineKeyboardButton("Professor",
                                   callback_data=json.dumps({'type': 'priorityEdited', 'argument': 1}))],
             [InlineKeyboardButton("Visiting Professor",
                                   callback_data=json.dumps({'type': 'priorityEdited', 'argument': 2}))]])

        bot.edit_message_text(text="Your was %s. \nChoose your new status:",
                              message_id=update.callback_query.message.message_id,
                              chat_id=update.callback_query.message.chat_id,
                              reply_markup=keyboard)
    else:
        bot.edit_message_text(text="Last value: %s \nPlease, enter new value:" % last_value,
                              message_id=update.callback_query.message.message_id,
                              chat_id=update.callback_query.message.chat_id)

    return ENTER_VALUE


@db_session
def change_value(bot, update):
    """
    Changes certain value
    :param bot: bot object
    :param update: update object
    :return: changed parameter
    """

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
def create_new_media(bot, update):
    """
    Menu for adding a new media
    :param bot: bot object
    :param update: update object
    :return: media added
    """

    lib = Librarian.get(telegramID=update.message.chat_id)

    if lib is not None and lib.priority > 1:
        text_to_send = lib.add_media(update.message.text)
        bot.send_message(text=text_to_send, chat_id=update.message.chat_id)
        if text_to_send != "Media and %s its copies had been added":
            return NOT_FINISHED
        else:
            return new_media_conversation.END
    else:
        bot.send_message(text="Sorry, you have no enough permissions!", chat_id=update.message.chat_id)


@db_session
def create_new_user(bot, update):
    """
    Menu for adding a new user
    :param bot: bot object
    :param update: update object
    :return: user added
    """

    lib = Librarian.get(telegramID=update.message.chat_id)

    if lib is not None and lib.priority > 1:
        text_to_send = lib.add_user(update.message.text)
        if text_to_send != "Choose his/her status":
            bot.send_message(text=text_to_send, chat_id=update.message.chat_id)
            return NOT_FINISHED
        else:
            keyboard = priority_keyboard()
            bot.send_message(text=text_to_send, chat_id=update.message.chat_id, reply_markup=keyboard)
            return new_user_conversation.END
    else:
        bot.send_message(text="Sorry, you have no enough permissions!", chat_id=update.message.chat_id)


@db_session
def create_user_set_status(bot, update):
    # To get data from pressed button
    query = update.callback_query.data
    parsed_query = json.loads(query)
    argument = parsed_query['argument']

    # Set priority value as in argument
    session = RegistrySession.get(telegramID=update.callback_query.from_user.id)
    session.faculty = argument
    key = generate_key()

    LibrarianEnrollment(name=session.name, phone=session.phone, address=session.address,
                        faculty=session.faculty, registrykey=key)

    session.address = ""
    session.phone = ""
    session.name = ""
    session.faculty = 0

    commit()
    bot.send_message(text="User was added. Please, ask User to send the following command:",
                     chat_id=update.callback_query.from_user.id)
    bot.send_message(text="/start %s" % key,
                     chat_id=update.callback_query.from_user.id)


def cancel_process(bot, update):
    """
    Cancel conversations
    :param bot: bot object
    :param update: update object
    :return: conversation cancelled
    """
    bot.send_message(text="Process has been cancelled.", chat_id=update.message.chat_id)


@db_session
def renew_media(bot, update, argument):
    # select log and extend expiry date
    user = User.get(telegramID=update.callback_query.message.chat_id)
    renewed = user.renew_copy(argument, datetime.datetime.now())
    if renewed and user.priority != 2:
        database.Actions(implementer=str(update.callback_query.message.chat_id),
                         action="has renewed media #",
                         implementee=str(argument))
        bot.edit_message_text(text="You successfully renewed the media!",
                              chat_id=update.callback_query.message.chat_id,
                              message_id=update.callback_query.message.message_id)
    else:
        database.Actions(implementer=str(update.callback_query.message.chat_id),
                         action="has tried to renew already renewed media #",
                         implementee=str(argument))
        bot.edit_message_text(text="You have already renewed this media!",
                              chat_id=update.callback_query.message.chat_id,
                              message_id=update.callback_query.message.message_id)


@db_session
def get_actions(bot, update):
    database.Actions[1].generate_file()
    bot.send_document(chat_id=update.message.chat_id, document=open('actions.txt', 'rb'))

@db_session
def confirm_user(bot, update, args):
    """
    This function confirms user by his/her key
    :param bot: bot object
    :param update: update object
    :param args: confirmation key
    :return: user confirmed
    """

    key = "".join(args).strip()
    if not key:
        bot.send_message(text="Please, enter enrolling key after /start", chat_id=update.message.chat_id)
        return 0
    enroll_request = LibrarianEnrollment.get(registrykey=key)
    if enroll_request is None:
        bot.send_message(text="Error with the key. Please, try again", chat_id=update.message.chat_id)
        return 0

    User(name=enroll_request.name, address=enroll_request.address, phone=enroll_request.phone,
         priority=enroll_request.faculty, telegramID=update.message.chat_id, alias=update.message.from_user.username)
    bot.send_message(text="Hello %s! You have been successfully enrolled" % enroll_request.name,
                     chat_id=update.message.chat_id)
    enroll_request.delete()
    commit()


@db_session
def reboot(bot, update):
    """
    This function reboots system (for TC9)
    :param bot: bot object
    :param update: update object
    :return: rebooted system
    """
    telegram_id = update.message.chat_id
    if not librarian_authentication(telegram_id):
        return 0
    bot.send_message(text="Rebooting...",
                     chat_id=update.message.chat_id)
    os.system("reboot")


@db_session
def pay_for_media(bot, update, user_id, copy_id):
    query = update.callback_query
    record = list(Log.select(lambda c: c.libID == user_id and c.mediaID == copy_id and not c.returned))[0]
    record.balance = 0
    bot.edit_message_text(text="Fines for this Media have been returned", chat_id=query.message.chat_id,
                          message_id=query.message.message_id)


@db_session
def add_new_librarian(bot, update, args):
    """
    :param args: alias or id of new user
    :param bot: bot object
    :param update: update object
    :return: return nothing if user is not Admin, otherwise, ask for tgID and for newcomer's privilege
    'adm_s_pr' is 'admin sets privilege'
    'acpt_nl' is 'accept new librarian'
    """

    # Converts args into string
    alias_or_id = "".join(args).strip()

    user = Admin.get(telegram_id=update.message.chat_id)
    if user is None:
        return 0
    else:
        if not alias_or_id:
            bot.send_message(text="Please, write id or alias after /new_librarian",
                             chat_id=update.message.chat_id)
            return 0
        real_id = 0
        new_user_by_alias = User.get(alias=str(alias_or_id))
        new_user_by_id = User.get(telegramID=int(alias_or_id))
        if new_user_by_alias is None and new_user_by_id is None:
            bot.send_message(text="Sorry, we have no this user in our library system :(",
                             chat_id=update.message.chat_id)
            return 0
        elif new_user_by_alias is not None and new_user_by_id is not None:
            bot.send_message(text="Ooops, we have two users who have ones ID as his alias, we chose with such ID.",
                             chat_id=update.message.chat_id)
            return 0
        else:
            if new_user_by_alias is not None:
                real_id = new_user_by_alias.telegramID
            if new_user_by_id is not None:
                real_id = alias_or_id
            if Librarian.get(telegramID=real_id) is None:
                yes_button = InlineKeyboardButton("Yes",
                                                  callback_data=json.dumps({'type': 'acpt_nl', 'argument': 'Yes'}))
                no_button = InlineKeyboardButton("No", callback_data=json.dumps({'type': 'acpt_nl', 'argument': 'No'}))
                keyboard = InlineKeyboardMarkup([[yes_button, no_button]])
                user_name = User.get(telegramID=real_id).name
                user.new_lib_id = real_id
                bot.send_message(text=str("Is " + user_name + " a person you want to add as a new librarian?"),
                                 chat_id=update.message.chat_id,
                                 reply_markup=keyboard)
            else:
                bot.send_message(text="This user already is librarian!",
                                 chat_id=update.message.chat_id)


"""
This is a conversation handler. It helps smoothly iterating 
from one command to another. Entry point is /enroll command.

Using states handler switches from one function to another.
"""
register_conversation = ConversationHandler(entry_points=[CommandHandler("enroll", ask_name)],
                                            states={
                                                PHONE_NUMBER: [MessageHandler(Filters.text, ask_phone)],
                                                ADDRESS: [MessageHandler(Filters.text, ask_address)],
                                                PRIORITY: [MessageHandler(Filters.text, ask_priority)]

                                            },

                                            fallbacks=[CommandHandler('cancel', cancel_process)])

new_media_conversation = ConversationHandler(entry_points=[CommandHandler("add_media", create_new_media)],
                                             states={
                                                 NOT_FINISHED: [MessageHandler(Filters.text, create_new_media)]
                                             },
                                             fallbacks=[CommandHandler('cancel', cancel_process)])
new_user_conversation = ConversationHandler(entry_points=[CommandHandler("add_user", create_new_user)],
                                            states={
                                                NOT_FINISHED: [MessageHandler(Filters.text, create_new_user)]
                                            },

                                            fallbacks=[CommandHandler('cancel', cancel_process)])

search_conversation = ConversationHandler(entry_points=[CommandHandler("search", search_keyboard)],
                                          states={
                                              CHOOSE_SEARCH_PARAMETER: [
                                                  CallbackQueryHandler(enter_search_criteria,
                                                                       pattern="^{\"type\": \"search")],
                                              CHOOSE_SEARCH_CRITERIA:
                                                  [MessageHandler(Filters.text, search_media)]

                                          },

                                          fallbacks=[CommandHandler('cancel', cancel_process)])

edit_conv = ConversationHandler(entry_points=[CallbackQueryHandler(edit_field, pattern="^{\"type\": \"edit")],
                                states={
                                    ENTER_VALUE: [MessageHandler(Filters.text, change_value)]
                                },

                                fallbacks=[CommandHandler('cancel', cancel_process)])

end_create_user = CallbackQueryHandler(create_user_set_status, pattern="^{\"type\": \"setState")

"""
This part connects commands, queries and any other input information to features
in code. These are handlers.
"""
dispatcher.add_handler(register_conversation)
dispatcher.add_handler(new_media_conversation)
dispatcher.add_handler(new_user_conversation)
dispatcher.add_handler(edit_conv)
dispatcher.add_handler(search_conversation)
dispatcher.add_handler(end_create_user)

search_query_handler = CallbackQueryHandler(callback_query_selector)
dispatcher.add_handler(CommandHandler('requests', create_request_card))
dispatcher.add_handler(CommandHandler('reboot', reboot))
dispatcher.add_handler(CommandHandler('return', create_return_media_card))
dispatcher.add_handler(CommandHandler('medias', create_media_card))
dispatcher.add_handler(CommandHandler('issue', create_booking_request_card))
dispatcher.add_handler(CommandHandler('log', create_log_card))
dispatcher.add_handler(CommandHandler('debtors', create_debt_card))
dispatcher.add_handler(CommandHandler('me', me))
dispatcher.add_handler(CommandHandler('actions', get_actions))
dispatcher.add_handler(CommandHandler('start', confirm_user, pass_args=True))
dispatcher.add_handler(CommandHandler('delete_copy', delete_copy, pass_args=True))
dispatcher.add_handler(CommandHandler('users', create_users_card))
dispatcher.add_handler(CommandHandler('librarian', librarian_interface))
dispatcher.add_handler(CommandHandler('new_librarian', add_new_librarian, pass_args=True))
dispatcher.add_handler(CommandHandler('librarians', create_librarian_card))
dispatcher.add_handler(search_query_handler)

updater.start_polling()  # Start asking for server about any incoming requests
