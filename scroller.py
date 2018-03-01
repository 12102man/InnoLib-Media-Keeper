from user import Patron, ItemCard, BookingRequest, log
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config
import pymysql
import datetime
import logging
from pony.orm import *
import new_user
import json
from button_actions import convert_to_emoji

db = Database()
# MySQL
db.bind(provider='mysql', host='37.46.132.57', user='telebot', passwd='Malinka2017', db='testbase')

""" MySQL connection """
connection = pymysql.connect(host=config.db_host,
                             user=config.db_username,
                             password=config.db_password,
                             db=config.db_name,
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)
cursor = connection.cursor()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class Scroller:
    def __init__(self, state, list_update, telegram_id):
        self.state = state
        self.__telegram_id = telegram_id
        self.list = list_update
        self.__length = len(list_update)
        self.__cursor = 0

    """
    This function updates a list from database
    """

    def update(self, list_update):
        self.list = list_update
        self.__length = len(list_update)

    """
    This function converts states to emojis
    for cooler view in Telegram message
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

    """
    create_message (self)
    This function creates a message, depending on state, 
    defined during initializing process (see def __init__ (self)
    """

    @db_session
    def create_message(self):
        """
        if self.__cursor < 0 or self.__cursor >= self.__length:
            self.__cursor = 0
            raise UnboundLocalError("Cursor is not in bound")
        """
        if len(self.list) == 0:
            message = "Nothing found"
            return message
        if self.state == 'request':
            self.__cursor = new_user.RegistrySession[self.__telegram_id].request_c

            message = """Request #️⃣ %s
            Name: %s
            Telegram alias: @%s
            Address: %s
            Phone: %s
            Faculty member: %s
                """ % (self.list[self.__cursor].id,
                       self.list[self.__cursor].name,
                       self.list[self.__cursor].alias,
                       self.list[self.__cursor].address,
                       self.list[self.__cursor].phone,
                       self.list[self.__cursor].faculty)
            return message
        elif self.state == 'media':
            self.__cursor = new_user.RegistrySession[self.__telegram_id].media_c

            message = """MediaID #️⃣ %s
            Type: %s
            Title: "%s"
            Author(s): %s
            Available: %s
            Bestseller: %s
                        """ % (self.list[self.__cursor].mediaID,
                               self.list[self.__cursor].type,
                               self.list[self.__cursor].name,
                               self.list[self.__cursor].authors,
                               self.list[self.__cursor].availability,
                               self.list[self.__cursor].bestseller)
            return message

        elif self.state == 'bookingRequest':
            self.__cursor = new_user.RegistrySession[self.__telegram_id].book_r_c
            mediaID = new_user.MediaCopies.get(copyID=self.list[self.__cursor].mediaID).mediaID

            message = """ Media booking request:
            From: %s
            What: %s
            CopyID: %s
            """ % (new_user.User[self.list[self.__cursor].libID].name,
                   mediaID.name + " by " + mediaID.authors,
                   self.list[self.__cursor].mediaID)
            return message

        elif self.state == 'log':
            self.__cursor = new_user.RegistrySession[self.__telegram_id].log_c
            log = self.list[self.__cursor]
            user = new_user.User.get(telegramID=log.libID)
            message = """ Log:
Customer: %s
What: %s
Issue date: %s
Expiry date: %s
Returned: %s
Renewed: %s
                        """ % (user.name + " (@" + user.alias + ")",
                               new_user.MediaCopies.get(copyID=log.mediaID).mediaID.name + " (" + log.mediaID + ")",
                               log.issue_date.strftime("%d %h %Y, %H:%M "),
                               log.expiry_date.strftime("%d %h %Y, %H:%M "),
                               convert_to_emoji(log.returned),
                               convert_to_emoji(log.renewed))
            return message
        elif self.state == 'user_medias':
            self.__cursor = new_user.RegistrySession[self.__telegram_id].my_medias_c
            log_record = self.list[self.__cursor]
            message = """ Your media #️⃣%s :
            
What: "%s" by %s
Issue date: %s
Expiry date: %s
                               """ % (log_record.mediaID,
                                      new_user.MediaCopies.get(
                                          copyID=log_record.mediaID).mediaID.name,
                                      new_user.MediaCopies.get(
                                          copyID=log_record.mediaID).mediaID.authors,
                                      log_record.issue_date.strftime("%d %h %Y, %H:%M "),
                                      log_record.expiry_date.strftime("%d %h %Y, %H:%M "))
            return message
        elif self.state == 'return_request':
            self.__cursor = new_user.RegistrySession[self.__telegram_id].return_c
            request = self.list[self.__cursor]
            patron = new_user.User[request.telegramID]
            media = new_user.MediaCopies.get(copyID=request.copyID).mediaID
            message = """Request #️⃣ %s 
What: \"%s\" by %s
CopyID: %s
From: %s (@%s)""" % (str(request.id), media.name, media.authors, request.copyID, patron.name, patron.alias)
            return message

        elif self.state == 'users':
            self.__cursor = new_user.User[self.__telegram_id].users_c
            request = self.list[self.__cursor]
            patron = new_user.User[request.telegramID]
            message = """ User %s %s information:
Address: %s
Alias: @%s
Telephone number: %s""" % (patron.name, patron.address, patron.alias, patron.phone)
            return message

    """
    
    create_keyboard(self)

    This function creates buttons under the message for navigation 
    and extra actions.
    """

    def create_keyboard(self):
        low_row = []  # Keyboard is a converted two-dimensional array.
        mid_row = []
        up_row = []  # Our keyboard has two levels: 'low' and 'up'

        callback_next = 0  # Callback data for buttons 'Next' and 'Prev' (replaced by arrows)
        callback_prev = 0

        # If list is empty, pass nothing
        if len(self.list) == 0:
            return 0

        # Depending on state build appropriate keyboard
        if self.state == 'request':
            callback_prev = 'prevRequest'
            callback_next = 'nextRequest'
            up_row.append(InlineKeyboardButton("✅", callback_data='approveRequest'))
            up_row.append(InlineKeyboardButton("🚫", callback_data='rejectRequest'))
        elif self.state == 'media':
            callback_prev = 'prevItem'
            callback_next = 'nextItem'
            if new_user.Librarian.get(telegramID=self.__telegram_id) is not None:
                mid_row.append(InlineKeyboardButton("Edit", callback_data=json.dumps(
                    {'type': 'media_edit', 'argument': self.list[self.__cursor].mediaID})))
                mid_row.append(InlineKeyboardButton("Delete", callback_data=json.dumps(
                    {'type': 'media_delete', 'argument': self.list[self.__cursor].mediaID})))
                mid_row.append(InlineKeyboardButton("Copy", callback_data=json.dumps(
                    {'type': 'media_add_copy', 'argument': self.list[self.__cursor].mediaID})))
            up_row.append(InlineKeyboardButton("Book", callback_data='book'))
        elif self.state == 'bookingRequest':
            callback_prev = 'prevBookingRequest'
            callback_next = 'nextBookingRequest'
            up_row.append(InlineKeyboardButton("✅", callback_data='approveBookingRequest'))
            up_row.append(InlineKeyboardButton("🚫", callback_data='rejectBookingRequest'))
        elif self.state == 'log':
            callback_prev = 'prevLogItem'
            callback_next = 'nextLogItem'
            log = self.list[self.__cursor]
            if not log.returned:
                up_row.append(InlineKeyboardButton("Ask for return", callback_data=json.dumps({'type': 'ask_for_return', 'argument': log.mediaID, 'user': log.libID})))
        elif self.state == 'user_medias':
            up_row.append(InlineKeyboardButton("Return", callback_data=json.dumps(
                {'type': 'returnMedia', 'argument': self.list[self.__cursor].mediaID})))
            callback_prev = json.dumps({'type': 'prevItem', 'argument': 'my_medias'})
            callback_next = json.dumps({'type': 'nextItem', 'argument': 'my_medias'})
        elif self.state == 'return_request':
            log_record = self.list[self.__cursor].id
            a = json.dumps({'type': 'accept', 'argument': 'return_request', 'id': log_record})
            print(a)
            up_row.append(InlineKeyboardButton("✅", callback_data=a))
            up_row.append(InlineKeyboardButton("🚫", callback_data=json.dumps({'type': 'reject', 'argument': 'return_request', 'id': log_record})))

            callback_prev = json.dumps({'type': 'prevItem', 'argument': 'return_request'})
            callback_next = json.dumps({'type': 'nextItem', 'argument': 'return_request'})

        elif self.state == 'users':
            log_record = self.list[self.__cursor].id
            a = json.dumps({'type': 'accept', 'argument': 'users', 'id': log_record})
            print(a)
            callback_prev = json.dumps({'type': 'prevItem', 'argument': 'users'})
            callback_next = json.dumps({'type': 'nextItem', 'argument': 'users'})

        """ If cursor is on the egde position (0 or length of list with records),
        then don't append one of arrows."""
        if self.__cursor > 0:
            low_row.append(InlineKeyboardButton("⬅", callback_data=callback_prev))
        if self.__cursor < len(self.list) - 1:
            low_row.append(InlineKeyboardButton("➡", callback_data=callback_next))

        return InlineKeyboardMarkup([up_row, mid_row, low_row])
