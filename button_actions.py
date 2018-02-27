from pony.orm import *

import new_user as database
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
    telegramID = query.message.chat_id
    session = database.RegistrySession[telegramID]

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
    telegramID = query.message.chat_id
    session = database.RegistrySession[telegramID]
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
        telegramID = query.message.chat_id
        session = database.RegistrySession[telegramID]
        media = list(database.Media.select())[session.media_c]

        # If media can't be booked, then reject booking
        if media.availability == 0:
            bot.edit_message_text(text="🤦🏻‍♂️ Media can't be booked. This item is not available now",
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
        # Else: book an item
        else:
            # if database.Log.select(lambda c: c.)
            copies_list = list(media.copies)
            i = 0
            while not copies_list[i].available and i < len(copies_list):
                i += 1
            log_record = database.Log(libID=telegramID, mediaID=copies_list[i].copyID,
                                      expiry_date=generate_expiry_date(media, user, datetime.datetime.now()))
            copies_list[i].available = False

            available_list = [x for x in copies_list if x.available]
            if len(available_list) == 0:
                media.availability = 0
            copies_list = set(copies_list)
            media.copies = copies_list

            session.media_c = 0
            commit()

            bot.edit_message_text(text="🤘 Media has been successfully booked. Please visit the library to get it.",
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
    else:
        bot.edit_message_text(text="🤦🏻‍♂️ You're not enrolled into the System. Shame on you! Enroll now! /enroll",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)


def make_return_request(bot, update, copyID):
    telegramID = update.callback_query.message.chat_id
    database.ReturnRequest(
        telegramID=telegramID,
        copyID=copyID
    )
    bot.edit_message_text(
        text="Return request has been successfully added",
        message_id=update.callback_query.message.message_id,
        chat_id=telegramID
    )


"""
def generate_expiry_date(self, media, patron, issue_date)

This function generates expiry date based on type of media and user.
"""


def accept_return(bot, update, requestID):
    request = database.ReturnRequest[requestID]
    copyID = request.copyID
    userID = request.telegramID

    #   Setting log.return to 1
    log_record = database.Log.get(mediaID=request.copyID)
    log_record.returned = True

    #   Correcting user medias
    media_copy = database.MediaCopies.get(copyID=copyID)
    media_copy.available = True

    request.delete()

    commit()
    bot.send_message(text="Media %s has been successfully returned" % copyID, chat_id=userID)
    bot.edit_message_text(text="Media %s has been successfully returned" % copyID,
                          message_id=update.callback_query.message.message_id,
                          chat_id=update.callback_query.message.chat_id)


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
