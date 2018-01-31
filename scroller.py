from user import Patron, ItemCard, BookingRequest
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config
import pymysql
import datetime


""" MySQL connection """
connection = pymysql.connect(host=config.db_host,
                             user=config.db_username,
                             password=config.db_password,
                             db=config.db_name,
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)
cursor = connection.cursor()


class Scroller:
    def __init__(self, state, list_update):
        self.state = state
        self.list = list_update
        self.__length = len(list_update)
        self.__cursor = 0
        self.__type = 0

    """
    This function updates a list from database
    """

    def update(self, list_update):
        self.list = list_update

    """
    This function converts states to emojis
    for cooler view in Telegram message
    """

    @staticmethod
    def convert_to_emoji(state):
        if state == 1:
            return "✅"
        elif state == 0:
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

    def create_message(self):
        if len(self.list) == 0:
            message = "Nothing found"
            return message
        if self.state == 'request':
            self.__type = Patron()  # Initializing certain type of class with data
            self.__type.set_request(self.list[self.__cursor])  # Putting data inside
            message = """Request #️⃣ %s
            Name: %s
            Telegram alias: @%s
            Address: %s
            Phone: %s
            Faculty member: %s
                """ % (self.__type.get_request_id(), self.__type.get_name(),
                       self.__type.get_alias(), self.__type.get_address(),
                       self.__type.get_phone(), self.convert_to_emoji(self.__type.get_status()))
            return message
        elif self.state == 'media':
            self.__type = ItemCard()  # Initializing certain type of class with data
            self.__type.set_item(self.list[self.__cursor])
            message = """MediaID #️⃣ %s
            Type: %s
            Title: "%s"
            Author(s): %s
            Available: %s
            Bestseller: %s
                        """ % (self.__type.get_media_id(),
                               self.convert_to_emoji(self.__type.get_type()),
                               self.__type.get_title(),
                               self.__type.get_authors(),
                               self.convert_to_emoji(self.__type.get_availability()),
                               self.convert_to_emoji(self.__type.get_bestseller()))
            return message

        elif self.state == 'bookingRequest':
            self.__type = BookingRequest()  # Initializing certain type of class with data
            self.__type.set_request(self.list[self.__cursor])
            message = """ Media booking request:
            From: %s
            What: %s
            """ % (self.__type.get_username(), self.__type.get_media_name())
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

        """ If cursor is on the egde position (0 or length of list with records),
            then don't append one of arrows."""
        if self.__cursor != 0:
            low_row.append(InlineKeyboardButton("⬅", callback_data=callback_prev))
        if self.__cursor != len(self.list) - 1:
            low_row.append(InlineKeyboardButton("➡", callback_data=callback_next))

        return InlineKeyboardMarkup([up_row, low_row])

    """
    Functions for increasing / decreasing cursor. 
    """

    def increase_cursor(self):
        self.__cursor += 1

    def decrease_cursor(self):
        self.__cursor -= 1

    """ Button actions for accepting/rejecting users"""

    """
    def approve_request(self)
    This function accepts request for enrolling the system
    """

    def approve_request(self, bot, update):
        if isinstance(self.__type, Patron):
            query = update.callback_query
            self.__type.insert_in_base()

            #   Deleting request from 'request' table
            delete_row = "DELETE FROM request WHERE requestID = %s;" % (self.__type.get_request_id())
            cursor.execute(delete_row)
            connection.commit()

            #   Editing message
            bot.edit_message_text(text="Request has been successfully approved", chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
            bot.send_message(text="Your request has been approved!", chat_id=self.__type.get_telegram_id())
            self.__cursor = 0

    """
        def reject_request(self)
        This function rejects request for enrolling the system
    """

    def reject_request(self, bot, update):
        if isinstance(self.__type, Patron):
            query = update.callback_query

            #   Deleting request from 'request' table
            delete_row = "DELETE FROM request WHERE requestID = %s;" % (self.__type.get_request_id())
            cursor.execute(delete_row)
            connection.commit()

            #   Editing message
            bot.edit_message_text(text="Request has been successfully rejected", chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
            bot.send_message(text="Your request has been rejected :( You can try again or contact librarian @librarian",
                             chat_id=self.__type.get_telegram_id())
            self.__cursor = 0

    """
        def book_media(self)
        This function is responsible for booking items 
    """

    def book_media(self, bot, update):
        media = ItemCard()  # Creating an instance of Media
        query = update.callback_query
        media.set_item(self.list[self.__cursor])  # Setting media

        # If media can't be booked, then reject booking
        if media.get_availability() == 0:
            bot.edit_message_text(text="🤦🏻‍♂️ Media can't be booked. This item is not available now",
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
        # Else: book an item
        else:
            media.set_availability(0)
            patron = Patron()
            patron.find(query.message.chat_id)

            media.update()
            patron.make_media_request(media.get_media_id())
            bot.edit_message_text(text="🤘 Media has been successfully booked. Please visit the library to get it.",
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
        self.__cursor = 0

    """
    def accept_booking_request(self, bot, update)
    
    This function accepts booking request
    """

    def accept_booking_request(self, bot, update):
        media = ItemCard()  # Creating and filling with data Media instance
        te = self.list[self.__cursor]["mediaID"]
        media.find(te)

        patron = Patron()  # Creating and filling with data Patron instance
        patron.find(update.callback_query.message.chat_id)  # Finding patron by Telegram ID
        issue_date = datetime.datetime.utcnow()
        # Moving request to 'log' table
        sql = """INSERT INTO log (libID, mediaID, issuedate, expirydate, renewed, returned) 
VALUES (%s, %s, '%s', '%s', 0,0);""" % (patron.get_lib_id(),
                                        media.get_media_id(),
                                        issue_date.strftime("%Y-%m-%d %H:%M:%S"),
                                        self.generate_expiry_date(media,
                                                                  patron,
                                                                  issue_date).strftime("%Y-%m-%d %H:%M:%S"))
        print(sql)
        cursor.execute(sql)
        connection.commit()

        cursor.execute("DELETE FROM mediarequest WHERE mediaID = %s;" % media.get_media_id())
        connection.commit()
        bot.send_message(text="""🤘 Media #%s has been successfully issued. 
Don't forget to return it on time!""" % media.get_media_id(),
                         chat_id=patron.get_telegram_id())

    """
    def accept_booking_request(self, bot, update)

    This function rejects booking request. 
    """

    def reject_booking_request(self, bot, update):
        media = ItemCard()  # Creating and filling with data Media instance
        te = self.list[self.__cursor]["mediaID"]
        media.find(te)

        # Deleting request from 'mediarequest' table
        cursor.execute("DELETE FROM mediarequest WHERE mediaID = %s;" % media.get_media_id())
        connection.commit()
        bot.send_message(
            text="🤦🏻‍♂️ Request for media #%s has been rejected :(" % media.get_media_id(),
            chat_id=update.callback_query.message.chat_id)

    """
    def generate_expiry_date(self, media, patron, issue_date)
    
    This function generates expiry date based on type of media and user.
    """

    @staticmethod
    def generate_expiry_date(media, patron, issue_date):
        type_of_media = media.get_type()
        date = issue_date

        if type_of_media == 'Book':
            if media.get_bestseller() == 1:
                date += datetime.timedelta(weeks=2)
            elif patron.get_status() == 1:
                date += datetime.timedelta(weeks=4)
            else:
                date += datetime.timedelta(weeks=4)
            return date
        elif type_of_media == 'AV' or type_of_media == 'Journals':
            date += datetime.timedelta(weeks=2)
            return date
        else:
            date += datetime.timedelta(weeks=2)
            return date
