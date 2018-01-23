
from user import Patron, ItemCard
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class Scroller:

    def __init__(self, state, list):
        self.state = state
        self.list = list
        self.__length = len(list)
        self.__cursor = 0
            
    def update(self, list):
        self.list = list

    def create_message(self):
        if len(self.list) == 0:
            message = "No requests found"
            return message
        if self.state == 'request':
            self.__type = Patron()
            self.__type.setRequest(self.list[self.__cursor])
            message = """Request # %s
            Name: %s
            Telegram alias: @%s
            Address: %s
            Phone: %s
            Faculty member: %s
                """ % (
            self.__type.getRequestID(), self.__type.getName(), self.__type.getAlias(), self.__type.getAddress(),
            self.__type.getPhone(), self.__type.getStatus())
            
            return message
        elif self.state == 'media':
            self.__type = ItemCard()
            self.__type.setItem(self.list[self.__cursor])
            message = """MediaID # %s
            Title: %s
            Author(s): %s
            Available: %s
            Bestseller? %s
                        """ % (
            self.__type.getMediaID(), self.__type.getTitle(), self.__type.getAuthors(), self.__type.getAvailability(),
            self.__type.getBestseller())
            return message

    def create_keyboard(self):
        low_row = []
        up_row = []

        if len(self.list) == 0:
            return 0

        if self.state == 'request':
            callbackPrev = 'prevRequest'
            callbackNext = 'nextRequest'
            up_row.append(InlineKeyboardButton("Approve", callback_data='approveRequest'))
            up_row.append(InlineKeyboardButton("Reject", callback_data='rejectRequest'))
        elif self.state == 'media':
            callbackPrev = 'prevItem'
            callbackNext = 'nextItem'
            up_row.append(InlineKeyboardButton("Book", callback_data='book'))

        if self.__cursor != 0:
            low_row.append(InlineKeyboardButton("Prev", callback_data=callbackPrev))
        if self.__cursor != len(self.list) - 1:
            low_row.append(InlineKeyboardButton("Next", callback_data=callbackNext))

        return InlineKeyboardMarkup([up_row,low_row])

    def increase_cursor(self):
        self.__cursor += 1

    def decrease_cursor(self):
        self.__cursor -= 1


    """ Button actions for accepting/rejecting users"""

    def approveRequest(self, bot, update, connection):
        query = update.callback_query
        self.__type.initialize()
        connection.cursor().execute(self.__type.insertInBase())
        deleteRow = "DELETE FROM request WHERE requestID = %s;" % (self.__type.getRequestID())
        connection.cursor().execute(deleteRow)
        connection.commit()
        bot.edit_message_text(text="Request has been successfully approved", chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
        bot.send_message(text="Your request has been approved!", chat_id= self.__type.getTelegramID())
        self.__cursor = 0

    def rejectRequest(self, bot, update, connection):
        query = update.callback_query
        deleteRow = "DELETE FROM request WHERE requestID = %s;" % (self.__type.getRequestID())
        connection.cursor().execute(deleteRow)
        connection.commit()
        bot.edit_message_text(text="Request has been successfully rejected", chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
        bot.send_message(text="Your request has been rejected :( You can try again or contact librarian @librarian",
                         chat_id=self.__type.getTelegramID())
        self.__cursor = 0


