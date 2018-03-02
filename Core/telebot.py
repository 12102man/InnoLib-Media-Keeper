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
from Core.key_generator import generate_key

# MySQL
db = Database()

db.bind(provider='mysql', host=config.db_host, user=config.db_username, passwd=config.db_password, db=config.db_name)
db.generate_mapping(create_tables=True)

updater = Updater(token=config.token)
dispatcher = updater.dispatcher

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# States for switching between handlers

NAME, FACULTY, PHONE_NUMBER, ADDRESS, END_OF_SIGNUP, BOOK_SEARCH, ARTICLE_SEARCH, AV_SEARCH, NOT_FINISHED, ENTER_VALUE = range(
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
    if query_type == 'Faculty':

        session_user = RegistrySession[update.callback_query.from_user.id]
        session_user.faculty = True
        commit()
        end_of_registration(bot, update)

    elif query_type == 'NotFaculty':

        session_user = RegistrySession[update.callback_query.from_user.id]
        session_user.faculty = False
        commit()
        end_of_registration(bot, update)

    elif query_type == 'approveRequest':
        approve_request(bot, update)
    elif query_type == 'rejectRequest':
        reject_request(bot, update)
    elif query_type == 'book':
        book_media(bot, update)

    # 'Delete' states

    #   Requests for deleting
    elif query_type == 'media_delete':
        delete_media(bot, update, argument)
    elif query_type == 'user_delete':
        delete_user(bot, update, argument)

    # Confirmed deletes
    elif query_type == 'deleteMedia':
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
        User.get(telegramID=argument).delete()
        commit()
        bot.send_message(text="User has been successfully deleted!",
                         chat_id=update.callback_query.from_user.id)
    elif query_type == 'cancelDeleteUser':
        bot.send_message(text="User hasn't been deleted!",
                         chat_id=update.callback_query.from_user.id)

    # 'Edit' states

    #   Inverse states
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
    elif query_type == 'reject':
        if argument == 'return_request':
            reject_return(bot, update, parsed_query['id'])
    elif query_type == 'ask_for_return':
        ask_for_return(bot, update, argument, parsed_query['user'])

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
        if session.phone is None:
            ask_phone(bot, update)
        elif session.address is None:
            ask_address(bot, update)
        elif session.faculty is None:
            ask_faculty(bot, update)
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
    :return: FACULTY statement
    """
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



@db_session
def ask_faculty(bot, update):
    """
    This is the fourth handler. It asks user's status
    (faculty member or not)
    :param bot: bot object
    :param update: update object
    :return: end register_conversation
    """

    session_user = RegistrySession[update.message.chat_id]
    session_user.address = update.message.text
    commit()


    #   Buttons for answering Yes or No. callback_data is what bot gets as a query (see callback_query_selector())
    reply = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Yes", callback_data=json.dumps({'type': 'Faculty', 'argument': 0})),
          InlineKeyboardButton("No", callback_data=json.dumps({'type': 'Faculty', 'argument': 0}))]])

    bot.send_message(chat_id=update.message.chat_id, text="Are you a faculty member?", reply_markup=reply)
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
    Request(
        telegramID=session_user.telegramID,

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
                                         callback_data=json.dumps({'type': 'user_delete', 'argument': my_user.telegramID}))
    my_medias_button = InlineKeyboardButton("My medias",
                                            callback_data=json.dumps({'type': 'my_medias', 'argument': 0}))

    keyboard = [[edit_button, delete_button], [my_medias_button]]
    keyboard = InlineKeyboardMarkup(keyboard)
    message = "Hello, %s! \nHere is information about you: \n👨‍🎓: %s (@%s) \n🏠: %s \n☎️: %s \n🎓: %s" % (
        my_user.name, my_user.name, my_user.alias, my_user.address, my_user.phone, convert_to_emoji(my_user.faculty))
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
    telegram_id = update.callback_query.message.chat_id

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
    if not librarian_authentication(current_telegram_id):
        logging.warning("Patron was trying to delete a user!")
        return 0

    deleted_user = User.get(telegramID=telegram_id)
    if deleted_user is None:
        bot.send_message(text="Sorry, copy with this alias doesn't exist", chat_id=current_telegram_id)
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

    """
    Menu for adding a new user
    :param bot: bot object
    :param update: update object
    :return: user added
    """

    session = RegistrySession.get(telegramID=update.message.chat_id)
    if session is not None:
        if session.name == "":
            if update.message.text == "/add_user":
                bot.send_message(text="Let's add a new User! Please, enter new user's name",
                                 chat_id=update.message.chat_id)
                return NOT_FINISHED
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
            key = generate_key()

            LibrarianEnrollment(name=session.name, phone=session.phone,
                                address=session.address, faculty=session.faculty, registrykey=key)

            session.name = ""
            session.phone = ""
            session.address = ""
            commit()
            bot.send_message(text="User was added. Please, ask User to send the following command:",
                             chat_id=update.message.chat_id)
            bot.send_message(text="/start %s" % key,
                             chat_id=update.message.chat_id)
            db.execute("UPDATE registrysession SET faculty = NULL WHERE telegramid = %s;" % str(update.message.chat_id))
            commit()

            return new_user_conversation.END


def cancel_process(bot, update):

    """
    Cancel conversations
    :param bot: bot object
    :param update: update object
    :return: conversation cancelled
    """
    bot.send_message(text="Process has been cancelled.", chat_id=update.message.chat_id)


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
    enroll_request = LibrarianEnrollment.get(registrykey=key)
    if enroll_request is None:
        bot.send_message(text="Error with the key. Please, try again", chat_id=update.message.chat_id)
        return 0

    User(name=enroll_request.name, address=enroll_request.address, phone=enroll_request.phone,
         faculty=enroll_request.faculty, telegramID=update.message.chat_id, alias=update.message.from_user.username)
    bot.send_message(text="Hello %s! You have been successfully enrolled" % enroll_request.name,
                     chat_id=update.message.chat_id)
    enroll_request.delete()
    commit()


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

edit_conv = ConversationHandler(entry_points=[CallbackQueryHandler(edit_field, pattern="^{\"type\": \"edit")],
                                states={
                                    ENTER_VALUE: [MessageHandler(Filters.text, change_value)]
                                },

                                fallbacks=[CommandHandler('cancel', cancel_process)])


"""
This part connects commands, queries and any other input information to features
in code. These are handlers.
"""
dispatcher.add_handler(register_conversation)
dispatcher.add_handler(new_media_conversation)
dispatcher.add_handler(new_user_conversation)
dispatcher.add_handler(edit_conv)


search_query_handler = CallbackQueryHandler(callback_query_selector)
dispatcher.add_handler(CommandHandler('requests', create_request_card))
dispatcher.add_handler(CommandHandler('return', create_return_media_card))
dispatcher.add_handler(CommandHandler('medias', create_media_card))
dispatcher.add_handler(CommandHandler('issue', create_booking_request_card))
dispatcher.add_handler(CommandHandler('log', create_log_card))
dispatcher.add_handler(CommandHandler('me', me))
dispatcher.add_handler(CommandHandler('start', confirm_user, pass_args=True))
dispatcher.add_handler(CommandHandler('delete_copy', delete_copy, pass_args=True))
dispatcher.add_handler(CommandHandler('users', create_users_card))
dispatcher.add_handler(CommandHandler('librarian', librarian_interface))
dispatcher.add_handler(search_query_handler)

updater.start_polling()  # Start asking for server about any incoming requests
