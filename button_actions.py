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
        media = list(database.Media.select())[session.request_c]

        # If media can't be booked, then reject booking
        if media.availability == 0:
            bot.edit_message_text(text="🤦🏻‍♂️ Media can't be booked. This item is not available now",
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
        # Else: book an item
        else:
            copies_list = list(media.copies)
            i = 0
            while not copies_list[i].available and i < len(copies_list):
                i +=1
            log_record = database.Log(libID=telegramID, mediaID=copies_list[i].copyID, expiry_date=generate_expiry_date(media, user, datetime.datetime.now()))
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


"""
def accept_booking_request(self, bot, update)

This function accepts booking request
"""


def accept_booking_request(bot, update):
    query = update.callback_query
    telegramID = query.message.chat_id
    session = database.RegistrySession[telegramID]
    user = database.User[telegramID]
    media = database.Media[session.media_c]

    patron = Patron()  # Creating and filling with data Patron instance
    libID = self.list[self.__cursor]["libID"]



"""
def reject_booking_request(self, bot, update)

This function rejects booking request. 
"""


def reject_booking_request(self, bot, update):
    media = ItemCard()  # Creating and filling with data Media instance
    try:
        te = self.list[self.__cursor]["mediaID"]
        media.find(te)

        # Deleting request from 'mediarequest' table
        libID = self.list[self.__cursor]["libID"]

        patron = Patron()
        cursor.execute("SELECT * FROM user WHERE libID = %s;" % libID)
        telegramID = cursor.fetchone()['telegramID']
        patron.find(telegramID)  # Finding patron by Telegram ID
        cursor.execute("DELETE FROM mediarequest WHERE mediaID = %s;" % media.get_media_id())
        connection.commit()
        bot.send_message(
            text="🤦🏻‍♂️ Request for media #%s has been rejected :(" % media.get_media_id(),
            chat_id=patron.get_telegram_id())
    except (pymysql.err.InternalError, IndexError, FileNotFoundError) as e:
        logging.error("Can't insert into database: " + e.args[0])
        bot.edit_message_text(text="Error occured: " + e.args[0], chat_id=update.callback_query.message.chat_id,
                              message_id=update.callback_query.message.message_id)

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
