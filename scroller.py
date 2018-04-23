import database as database
import json
import logging
from pony.orm import *
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import config as config
from button_actions import convert_to_emoji

db = Database()
# MySQL

db.bind(provider='mysql', host=config.db_host, user=config.db_username, passwd=config.db_password, db=config.db_name)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class Scroller:
    def __init__(self, state, list_update, telegram_id):
        self.state = state
        self.__telegram_id = telegram_id
        self.list = list_update
        self.__length = len(list_update)
        self.__cursor = 0

    @db_session
    def create_message(self):
        """
        This function creates a message, depending on state,
        defined during initializing process (see def __init__ (self))
        :return: Card with required information
        """

        if self.__cursor < 0 or self.__cursor > self.__length:
            self.__cursor = 0
            raise UnboundLocalError("Cursor is not in bound")
        if len(self.list) == 0:
            message = "Nothing found"
            return message
        try:
            if self.state == 'request':
                self.__cursor = database.RegistrySession[self.__telegram_id].request_c
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
                       convert_to_emoji(self.list[self.__cursor].faculty))
                return message
            elif self.state == 'media':
                self.__cursor = database.RegistrySession[self.__telegram_id].media_c
                if self.__cursor >= len(self.list):
                    self.__cursor = 0
                    database.RegistrySession[self.__telegram_id].media_c = 0
                    commit()
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
                               convert_to_emoji(self.list[self.__cursor].availability),
                               convert_to_emoji(self.list[self.__cursor].bestseller))
                return message

            elif self.state == 'bookingRequest':
                self.__cursor = database.RegistrySession[self.__telegram_id].book_r_c
                media_id = database.MediaCopies.get(copyID=self.list[self.__cursor].mediaID).mediaID

                message = """ Media booking request:
From: %s
What: %s
CopyID: %s

                """ % (database.User[self.list[self.__cursor].libID].name,
                       media_id.name + " by " + media_id.authors,
                       self.list[self.__cursor].mediaID)
                return message

            elif self.state == 'log':
                self.__cursor = database.RegistrySession[self.__telegram_id].log_c
                log = self.list[self.__cursor]
                user = database.User.get(telegramID=log.libID)
                message = """ Log:
Customer: %s
What: %s
Issue date: %s
Expiry date: %s
Returned: %s
Renewed: %s
                """ % (user.name + " (@" + user.alias + ")",
                       database.MediaCopies.get(copyID=log.mediaID).mediaID.name + " (" + log.mediaID + ")",
                    log.issue_date.strftime("%d %h %Y, %H:%M "),
                    log.expiry_date.strftime("%d %h %Y, %H:%M "),
                    convert_to_emoji(log.returned),
                    convert_to_emoji(log.renewed))

                return message
            elif self.state == 'user_medias':
                self.__cursor = database.RegistrySession[self.__telegram_id].my_medias_c
                log_record = self.list[self.__cursor]
                message = """ Your media #️⃣%s :
            
What: "%s" by %s
Issue date: %s
Expiry date: %s
                        """ % (log_record.mediaID,
                               database.MediaCopies.get(
                                   copyID=log_record.mediaID).mediaID.name,
                               database.MediaCopies.get(
                                   copyID=log_record.mediaID).mediaID.authors,
                               log_record.issue_date.strftime("%d %h %Y, %H:%M "),
                               log_record.expiry_date.strftime("%d %h %Y, %H:%M "))

                return message
            elif self.state == 'return_request':
                self.__cursor = database.RegistrySession[self.__telegram_id].return_c
                request = self.list[self.__cursor]
                patron = database.User[request.telegramID]
                media = database.MediaCopies.get(copyID=request.copyID).mediaID
                message = """Request #️⃣ %s 
What: \"%s\" by %s
CopyID: %s
From: %s (@%s)""" % (str(request.id), media.name, media.authors, request.copyID, patron.name, patron.alias)
                return message
            elif self.state == 'users':
                self.__cursor = database.RegistrySession[self.__telegram_id].users_c
                patron = self.list[self.__cursor]
                message = """ User %s information:
Address: %s
Alias: @%s
Telephone number: %s
Balance: %s""" % (patron.name, patron.address, patron.alias, patron.phone, patron.balance)

                return message
            elif self.state == 'librarians':
                self.__cursor = database.RegistrySession[self.__telegram_id].users_c
                lib = self.list[self.__cursor]
                patron = database.User[lib.telegramID]
                message = """ Librarian %s information:
Address: %s
Alias: @%s
Telephone number: %s
Balance: %s
Privilege level: %s""" % (patron.name, patron.address, patron.alias, patron.phone, patron.balance, lib.priority)

                return message

            elif self.state == 'debtors':
                self.__cursor = database.RegistrySession[self.__telegram_id].debtors_c
                debt = self.list[self.__cursor]
                user = database.User.get(telegramID=debt.libID)
                message = """ Debtors:
        Customer: %s
        What: %s
        Issue date: %s
        Expiry date: %s
        
        
        Debt: %s
        Returned: %s
        Renewed: %s
                    """ % (user.name + " (@" + user.alias + ")",
                           database.MediaCopies.get(copyID=debt.mediaID).mediaID.name + " (" + debt.mediaID + ")",
                           debt.issue_date.strftime("%d %h %Y, %H:%M "),
                           debt.expiry_date.strftime("%d %h %Y, %H:%M "),
                           list(database.Log.select(lambda c: c.mediaID == debt.mediaID and not c.returned))[0].balance,
                           convert_to_emoji(debt.returned),
                           convert_to_emoji(debt.renewed))

                return message
        except IndexError:
            self.__cursor = 0

    def create_keyboard(self):
        """
        This function creates buttons under the message for navigation
        and extra actions.
        :return: keyboard for scrolling through data
        """
        low_row = []  # Keyboard is a converted three-dimensional array.
        mid_row = []  # Our keyboard has three levels: 'low', 'mid' and 'up'
        up_row = []

        callback_next = 0  # Callback data for buttons 'Next' and 'Prev' (replaced by arrows)
        callback_prev = 0

        # If list is empty, pass nothing
        if len(self.list) == 0:
            return 0

        # Depending on state build appropriate keyboard
        if self.state == 'request':

            callback_prev = json.dumps({'type': 'prevItem', 'argument': 'request'})
            callback_next = json.dumps({'type': 'nextItem', 'argument': 'request'})

            button_accept = json.dumps({'type': 'approveRequest', 'argument': 0})
            button_reject = json.dumps({'type': 'rejectRequest', 'argument': 0})

            up_row.append(InlineKeyboardButton("✅", callback_data=button_accept))
            up_row.append(InlineKeyboardButton("🚫", callback_data=button_reject))

        elif self.state == 'media':
            callback_prev = json.dumps({'type': 'prevItem', 'argument': 'media'})
            callback_next = json.dumps({'type': 'nextItem', 'argument': 'media'})
            #   Buttons for editing (only for librarian)

            librarian = database.Librarian.get(telegramID=self.__telegram_id)
            if librarian is not None:

                mid_row.append(InlineKeyboardButton("Edit", callback_data=json.dumps(
                    {'type': 'media_edit', 'argument': self.list[self.__cursor].mediaID})))
                if librarian.priority > 2:
                    mid_row.append(InlineKeyboardButton("Delete", callback_data=json.dumps(
                        {'type': 'media_delete', 'argument': self.list[self.__cursor].mediaID})))
                if librarian.priority > 1:
                    mid_row.append(InlineKeyboardButton("Copy", callback_data=json.dumps(
                        {'type': 'media_add_copy', 'argument': self.list[self.__cursor].mediaID})))
                    mid_row.append(InlineKeyboardButton("Outstanding request", callback_data=json.dumps(
                        {'type': 'outstanding_request', 'argument': self.list[self.__cursor].mediaID})))

            if not self.list[self.__cursor].availability:
                user = database.User[self.__telegram_id]
                if user.is_in_line(self.list[self.__cursor]):
                    button = json.dumps({'type': 'get_out_of_line', 'argument': 0})
                    place = user.get_number_in_line(self.list[self.__cursor])
                    if place == 1:
                        place = "1st"
                    elif place == 2:
                        place = "2nd"
                    elif place == 3:
                        place = "3rd"
                    else:
                        place = str(place) + "th"
                    up_row.append(InlineKeyboardButton(
                        "Get out of line (%s)" % place,
                        callback_data=button))
                else:
                    button = json.dumps({'type': 'get_in_line', 'argument': 0})
                    up_row.append(InlineKeyboardButton("Get in line", callback_data=button))
            else:
                button = json.dumps({'type': 'book', 'argument': 0})
                up_row.append(InlineKeyboardButton("Book", callback_data=button))

        elif self.state == 'bookingRequest':
            callback_prev = json.dumps({'type': 'prevItem', 'argument': 'bookingRequest'})
            callback_next = json.dumps({'type': 'nextItem', 'argument': 'bookingRequest'})

            button_accept = json.dumps({'type': 'approveBookingRequest', 'argument': 0})
            button_reject = json.dumps({'type': 'rejectBookingRequest', 'argument': 0})

            up_row.append(InlineKeyboardButton("✅", callback_data=button_accept))
            up_row.append(InlineKeyboardButton("🚫", callback_data=button_reject))

        elif self.state == 'log':
            callback_prev = json.dumps({'type': 'prevItem', 'argument': 'log'})
            callback_next = json.dumps({'type': 'nextItem', 'argument': 'log'})
            # Get status of log record and add 'Ask for return' button

            log = self.list[self.__cursor]
            if not log.returned:
                up_row.append(InlineKeyboardButton("Ask for return", callback_data=json.dumps(
                    {'type': 'ask_for_return', 'argument': log.mediaID, 'user': log.libID})))
        elif self.state == 'user_medias':
            up_row.append(InlineKeyboardButton("Return", callback_data=json.dumps(
                {'type': 'returnMedia', 'argument': self.list[self.__cursor].mediaID})))
            if not self.list[self.__cursor].renewed:
                up_row.append(InlineKeyboardButton("Renew", callback_data=json.dumps(
                    {'type': 'renewMedia', 'argument': self.list[self.__cursor].mediaID})))
            callback_prev = json.dumps({'type': 'prevItem', 'argument': 'my_medias'})
            callback_next = json.dumps({'type': 'nextItem', 'argument': 'my_medias'})

        elif self.state == 'return_request':
            return_record = self.list[self.__cursor]
            log_record = list(database.Log.select(lambda c: c.libID == return_record.telegramID and c.mediaID == return_record.copyID))[0]

            button_accept = json.dumps({'type': 'accept', 'argument': 'return_request', 'id': return_record.id})
            button_reject = json.dumps({'type': 'reject', 'argument': 'return_request', 'id': return_record.id})
            button_pay = json.dumps({'type': 'pay','argument': return_record.telegramID,'media': return_record.copyID})

            if log_record.balance != 0:
                up_row.append(InlineKeyboardButton("💵", callback_data=button_pay))
            else:
                up_row.append(InlineKeyboardButton("✅", callback_data=button_accept))
            up_row.append(InlineKeyboardButton("🚫", callback_data=button_reject))

            callback_prev = json.dumps({'type': 'prevItem', 'argument': 'return_request'})
            callback_next = json.dumps({'type': 'nextItem', 'argument': 'return_request'})

        elif self.state == 'users':
            user = database.Librarian.get(telegramID=self.__telegram_id)
            log_record = self.list[self.__cursor].telegramID
            if user is not None:
                if user.priority > 2:
                    delete_user = json.dumps({'type': 'user_delete', 'argument': log_record})
                    up_row.append(InlineKeyboardButton("Delete", callback_data=delete_user))
            edit_user = json.dumps({'type': 'user_edit', 'argument': log_record, 'id': log_record})
            up_row.append(InlineKeyboardButton("Edit", callback_data=edit_user))
            callback_prev = json.dumps({'type': 'prevItem', 'argument': 'users'})
            callback_next = json.dumps({'type': 'nextItem', 'argument': 'users'})
        elif self.state == 'librarians':
            log_record = self.list[self.__cursor].telegramID
            delete_librarian = json.dumps({'type': 'lib_delete', 'argument': log_record})
            up_row.append(InlineKeyboardButton("Delete", callback_data=delete_librarian))
            change_librarian_privilege = json.dumps({'type': 'priv_edit', 'argument': log_record})
            mid_row.append(InlineKeyboardButton("Change privilege", callback_data=change_librarian_privilege))
            callback_prev = json.dumps({'type': 'prevItem', 'argument': 'librs'})
            callback_next = json.dumps({'type': 'nextItem', 'argument': 'librs'})
        elif self.state == 'debtors':
            callback_prev = json.dumps({'type': 'prevItem', 'argument': 'debtors'})
            callback_next = json.dumps({'type': 'nextItem', 'argument': 'debtors'})

            debt = self.list[self.__cursor]
            up_row.append(InlineKeyboardButton("Ask for return", callback_data=json.dumps(
                    {'type': 'ask_for_return', 'argument': debt.mediaID, 'user': debt.libID})))

        """ If cursor is on the edge position (0 or length of list with records),
        then don't append one of arrows."""
        if self.__cursor > 0:
            low_row.append(InlineKeyboardButton("⬅", callback_data=callback_prev))
        if self.__cursor < len(self.list) - 1:
            low_row.append(InlineKeyboardButton("➡", callback_data=callback_next))

        return InlineKeyboardMarkup([up_row, mid_row, low_row])
