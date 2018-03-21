from pony.orm import *

import database as database
import datetime

db = Database()
# MySQL
db.bind(provider='mysql', host='37.46.132.57', user='telebot', passwd='Malinka2017', db='testbase')

""" Button actions for accepting/rejecting users"""

"""
def approve_request(self)
This function accepts request for enrolling the system
"""


@db_session
def approve_request(bot, update):
    query = update.callback_query
    telegram_id = query.message.chat_id
    session = database.RegistrySession[telegram_id]

    request = list(database.Request.select(lambda c: c.status == 0))[session.request_c]

    enrolled_user = database.User(telegramID=request.telegramID,
                                  phone=request.phone,
                                  address=request.address,
                                  faculty=request.faculty,
                                  alias=request.alias,
                                  name=request.name)
    database.Request[request.id].status = 1

    session.request_c = 0
    commit()
    # Editing message
    bot.edit_message_text(text="Request has been successfully approved", chat_id=query.message.chat_id,
                          message_id=query.message.message_id)
    bot.send_message(text="Your request has been approved!", chat_id=int(enrolled_user.telegramID))


"""
    def reject_request(self)
    This function rejects request for enrolling the system
"""


@db_session
def reject_request(bot, update):
    query = update.callback_query
    telegram_id = query.message.chat_id
    session = database.RegistrySession[telegram_id]
    request = list(database.Request.select(lambda c: c.status == 0))[session.request_c]
    declined_id = request.telegramID
    database.Request[request.id].delete()
    session.request_c = 0
    commit()

    #   Editing message
    bot.edit_message_text(text="Request has been successfully rejected", chat_id=query.message.chat_id,
                          message_id=query.message.message_id)
    bot.send_message(text="Your request has been rejected :( You can try again or contact librarian @librarian",
                     chat_id=declined_id)


"""
    def book_media(self)
    This function is responsible for booking items 
"""


def book_media(bot, update):
    query = update.callback_query

    user = database.User.get(telegramID=query.message.chat_id)
    if user is not None:
        telegram_id = query.message.chat_id
        session = database.RegistrySession[telegram_id]
        media = list(database.Media.select())[session.media_c]

        status = user.book_media(media)
        if status == -1:
            bot.edit_message_text(text="This media is unavailable :( ",
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
        elif status == -2:
            bot.edit_message_text(text="You already have this media copy 🤦🏻‍♂",
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)

        elif status == 0:
            bot.edit_message_text(text="🤘 Media has been successfully booked. Please visit the library to get it.",
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
            # Media cursor - to 0
            session.media_c = 0

        else:
            bot.edit_message_text(text="Sorry, error has been occurred",
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
    else:
        bot.edit_message_text(text="🤦🏻‍♂️ You're not enrolled into the System. Shame on you! Enroll now! /enroll",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)


def add_in_line(bot, update):
    query = update.callback_query
    telegram_id = query.message.chat_id
    session = database.RegistrySession[telegram_id]
    media = list(database.Media.select())[session.media_c]
    user = database.User[telegram_id]
    a = list(database.Log.select(
        lambda c: c.libID == telegram_id and c.mediaID.startswith(str(media.mediaID))))
    if not user.is_in_line(media) and len(list(database.Log.select(
            lambda c: c.libID == telegram_id and c.mediaID.startswith(str(media.mediaID))))) == 0:
        user.add_to_queue(media)
        bot.edit_message_text(text="You have been successfully added to the line!",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
    else:
        bot.edit_message_text(text="Sorry, mate, but you are already in line!",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
    """
    def make_return_request(media, patron, issue_date)
    
    This function generates expiry date based on type of media and user.
    """


def make_return_request(bot, update, copy_id):
    telegram_id = update.callback_query.message.chat_id
    database.ReturnRequest(
        telegramID=telegram_id,
        copyID=copy_id
    )
    bot.edit_message_text(
        text="Return request has been successfully added",
        message_id=update.callback_query.message.message_id,
        chat_id=telegram_id
    )


def accept_return(bot, update, request_id):
    request = database.ReturnRequest[request_id]
    copy_id = request.copyID
    user_id = request.telegramID
    media = database.MediaCopies.get(copyID=copy_id).mediaID

    status = database.Librarian.get(telegramID=update.callback_query.message.chat_id).accept_return(copy_id)

    if status[0] == 1:
        #   Setting log.return to 1
        log_record = database.Log.select(lambda c: c.mediaID == request.copyID and not c.returned)
        log_record.returned = True
        log_record.balance = 0

        #   Correcting user medias
        media_copy = database.MediaCopies.get(copyID=copy_id)
        media_copy.available = True

        request.delete()

        commit()
        bot.send_message(text="Media %s has been successfully returned" % copy_id, chat_id=user_id)
        bot.edit_message_text(text="Media %s has been successfully returned" % copy_id,
                              message_id=update.callback_query.message.message_id,
                              chat_id=update.callback_query.message.chat_id)

    elif status[0] == 2:
        user = status[1]
        # Making a record in log
        database.Log(libID=user.telegramID, mediaID=copy_id,
                     expiry_date=generate_expiry_date(media, user, datetime.datetime.now()))
        bot.send_message(text="Media %s has been successfully returned" % copy_id, chat_id=user_id)
        bot.edit_message_text(text="Media %s has been successfully returned" % copy_id,
                              message_id=update.callback_query.message.message_id,
                              chat_id=update.callback_query.message.chat_id)
        bot.send_message(text="Dear %s, media #%s is available now! You can take it from library, time starts now!" % (
            user.name, copy_id),
                         chat_id=user.telegramID)

    elif status[0] == -1:
        bot.edit_message_text(text="This user needs to pay %s rubles to return this media item." % status[1],
                              message_id=update.callback_query.message.message_id,
                              chat_id=update.callback_query.message.chat_id)

    else:
        bot.edit_message_text(text="Sorry, error has been occurred",
                              chat_id=update.callback_query.message.chat_id,
                              message_id=update.callback_query.message.message_id)


def reject_return(bot, update, request_id):
    request = database.ReturnRequest[request_id]
    copy_id = request.copyID
    user_id = request.telegramID

    request.delete()

    commit()
    bot.send_message(
        text="Return request for Media #%s has been rejected. Please, contact librarian @librarian" % copy_id,
        chat_id=user_id)
    bot.edit_message_text(text="Return request for Media #%s has been rejected" % copy_id,
                          message_id=update.callback_query.message.message_id,
                          chat_id=update.callback_query.message.chat_id)


def ask_for_return(bot, update, copy_id, user_id):
    abstract_media = database.MediaCopies.get(copyID=copy_id).mediaID
    user = database.User[user_id]

    commit()
    bot.send_message(
        text="""Hello, %s! 
You recently took a book %s by %s (%s). Library and librarians need it ASAP. Could you please bring it back? Thank you!""" % (

            user.name,
            abstract_media.name,
            abstract_media.authors,
            copy_id),

        chat_id=user_id)
    bot.edit_message_text(text="Message to %s(@%s) has been sent" % (user.name, user.alias),
                          message_id=update.callback_query.message.message_id,
                          chat_id=update.callback_query.message.chat_id)


"""
def generate_expiry_date(self, media, patron, issue_date)

This function generates expiry date based on type of media and user.
"""


def generate_expiry_date(media, patron, issue_date):
    type_of_media = media.type
    date = issue_date

    if type_of_media == 'Book':
        if media.bestseller and patron.faculty != 1:
            date += datetime.timedelta(weeks=2)
        elif patron.faculty:
            date += datetime.timedelta(weeks=4)
        else:
            date += datetime.timedelta(weeks=3)
        return date
    elif type_of_media == 'AV' or type_of_media == 'Journals':
        date += datetime.timedelta(weeks=2)
        return date
    else:
        date += datetime.timedelta(weeks=2)
        return date


"""
def check_copy(copyID, userID)

Function checks the number of copies of a particular media and returns True if there are not such ones
"""


def check_copy(media_id, user_id):
    a = str(media_id)
    number_of_copies = len(
        database.Log.select(lambda c: c.libID == user_id and not c.returned and c.mediaID.startswith(a)))
    if number_of_copies == 0:
        return True
    return False


"""
def convert_to_emoji(state):

Converts states to emojis
"""


def convert_to_emoji(state):
    if state:
        return "✅"
    elif not state:
        return "❌"
    elif state == 'Book':
        return "📚"
    elif state == 'AV':
        return "📀"
    else:
        return state


def print_balance(bot, update, telegram_id):
    user = database.User[telegram_id]
    user.check_balance()
    overdue = database.Log.select(lambda c: c.libID == user.telegramID and c.expiry_date <= datetime.datetime.now())
    elements = ""
    if len(overdue) == 0:
        element = "None"
    else:
        for element in overdue:
            overdue_days = str((datetime.datetime.now() - element.expiry_date).days)
            elements += """ \"%s\" by %s (%s) for %s day(s)\n""" % (
                database.MediaCopies.get(copyID=element.mediaID).mediaID.name,
                database.MediaCopies.get(copyID=element.mediaID).mediaID.authors,
                element.mediaID, overdue_days)
    if len(overdue) == 0:
        bot.edit_message_text(text="""Your balance is: %s""" % (user.balance),
                              message_id=update.callback_query.message.message_id,
                              chat_id=update.callback_query.message.chat_id)
    else:
        bot.edit_message_text(text="""Your balance is: %s \nOverdue medias: \n%s""" % (user.balance, elements),
                              message_id=update.callback_query.message.message_id,
                              chat_id=update.callback_query.message.chat_id)
