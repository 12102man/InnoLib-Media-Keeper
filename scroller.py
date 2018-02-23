from user import Patron, ItemCard, BookingRequest, log
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config
import pymysql
import datetime
import logging
from pony.orm import *
import new_user

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
            self.__type = log()  # Initializing certain type of class with data
            self.__type.set_log(self.list[self.__cursor])
            message = """ Log:
                        Customer: %s
                        What: %s
                        Issue date: %s
                        Expiry date: %s
                        Returned: %s
                        Renewed: %s
                        """ % (self.__type.get_lib_id(), self.__type.get_media_id(), self.__type.get_issue_date(),
                               self.__type.get_expiry_date(), self.__type.is_returned(), self.__type.is_renewed())
            return message

    """
    create_keyboard(self)
    
    This function creates buttons under the message for navigation 
    and extra actions.
    """

    def create_keyboard(self):
        low_row = []  # Keyboard is a converted two-dimensional array.
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
            up_row.append(InlineKeyboardButton("Book", callback_data='book'))
        elif self.state == 'bookingRequest':
            callback_prev = 'prevBookingRequest'
            callback_next = 'nextBookingRequest'
            up_row.append(InlineKeyboardButton("✅", callback_data='approveBookingRequest'))
            up_row.append(InlineKeyboardButton("🚫", callback_data='rejectBookingRequest'))
        elif self.state == 'log':
            callback_prev = 'prevLogItem'
            callback_next = 'nextLogItem'

        """ If cursor is on the egde position (0 or length of list with records),
        then don't append one of arrows."""
        if self.__cursor > 0:
            low_row.append(InlineKeyboardButton("⬅", callback_data=callback_prev))
        if self.__cursor < len(self.list) - 1:
            low_row.append(InlineKeyboardButton("➡", callback_data=callback_next))

        return InlineKeyboardMarkup([up_row, low_row])


"""
def generate_expiry_date(self, media, patron, issue_date)

This function generates expiry date based on type of media and user.
"""


@staticmethod
def generate_expiry_date(media, patron, issue_date):
    type_of_media = media.get_type()
    date = issue_date

    if type_of_media == 'Book':
        if media.get_bestseller() == 1 and patron.get_status() != 1:
            date += datetime.timedelta(weeks=2)
        elif patron.get_status() == 1:
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
