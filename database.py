from pony.orm import *

from button_actions import generate_expiry_date, check_copy
import datetime

import config as config

db = Database()
# MySQL
db.bind(provider='mysql', host=config.db_host, user=config.db_username, passwd=config.db_password, db=config.db_name)


class User(db.Entity):
    telegramID = PrimaryKey(int)
    name = Required(str)
    address = Required(str)
    medias = Set('MediaCopies')
    alias = Required(str)
    phone = Required(str)
    faculty = Required(bool)
    balance = Optional(int)
    priority = Optional(int, default=4)
    queue = Set('MediaQueue')

    def add_to_queue(self, media_id):
        MediaQueue(user=self, mediaID=media_id)
        commit()

    def is_in_line(self, media):
        return not len(list(MediaQueue.select(lambda c: c.user == self and c.mediaID == media))) == 0

    def get_number_in_line(self, media):
        order_of_users = media.get_queue()
        user_place = list(filter(lambda o: o.user == self, order_of_users))
        return order_of_users.index(user_place[0]) + 1

    def renew_copy(self, copy_id):
        # select log and extend expiry date
        media = MediaCopies.get(copyID=copy_id).mediaID
        log = Log.get(mediaID=copy_id, libID=self.telegramID)
        if (not log.renewed) or (User.priority == 3 and len(media.get_queue) == 0):
            log.expiry_date = generate_expiry_date(media=media,
                                                   patron=self,
                                                   issue_date=log.expiry_date)
            log.renewed = 1
            return 1
        else:
            return 0

    def check_balance(self):
        balance = 0
        log_records = Log.select(lambda c: c.libID == self.telegramID)
        for record in log_records:
            balance += record.balance
        self.balance = balance
        return balance

    def book_media(self, media_item):
        if not media_item.availability:
            return -1
        if not check_copy(media_item.mediaID, self.telegramID):
            return -2

        copies_to_book = list(
            MediaCopies.select(lambda c: c.copyID.startswith(str(media_item.mediaID)) and c.available))
        item = copies_to_book[0]

        Log(libID=self.telegramID, mediaID=item.copyID,
            expiry_date=generate_expiry_date(media_item, self, datetime.datetime.now()))

        item.available = False

        if len(copies_to_book) == 1:
            media_item.availability = False

        return 0


class Media(db.Entity):
    mediaID = PrimaryKey(int, auto=True)
    name = Required(str)
    type = Required(str)
    authors = Required(str)
    publisher = Required(str)
    availability = Required(bool)
    bestseller = Required(bool)
    fine = Required(int)
    cost = Required(int)
    image = Set('Images')
    copies = Set('MediaCopies')

    queue = Set('MediaQueue')

    def get_queue(self):
        return list(MediaQueue.select().order_by(MediaQueue.id).order_by(lambda c: desc(c.user.priority)))

    def pop(self):
        return_value = self.get_queue()[0]
        return_value.delete()
        return return_value

    def delete_queue(self):
        for element in self.queue:
            element.delete()
        return 0

class Request(db.Entity):
    telegramID = Required(int)
    alias = Required(str)
    name = Required(str)
    address = Required(str)
    phone = Required(str)
    faculty = Required(bool)
    status = Optional(bool, default=False)


class MediaRequest(db.Entity):
    libID = Required(int)
    mediaID = Required(str)


class Librarian(db.Entity):
    telegramID = Required(int)
    name = Required(str)

    def check_return(self, copy_id):
        record = list(Log.select(lambda c: c.mediaID == copy_id and not c.returned))[0]
        if record.balance != 0:
            return [0, record.balance]
        else:
            return [1, 1]

    def accept_return(self, copy_id):
        if self.check_return(copy_id)[0] == 1:
            record = list(Log.select(lambda c: c.mediaID == copy_id and not c.returned))[0]
            copy = MediaCopies.get(copyID=copy_id)
            copy.available = True
            record.returned = True
            ReturnRequest.get(copyID=copy_id).delete()
            media = copy.mediaID
            if not media.queue.is_empty:
                user = media.pop().user
                copy.available = False
                Log(libID=user.telegramID, mediaID=copy_id,
                    expiry_date=generate_expiry_date(media, user, datetime.datetime.now()))
                return [2, user.telegramID]
            if not copy.mediaID.availability:
                copy.mediaID.availability = True
            return [1, 1]
        else:
            return [-1, self.check_return(copy_id)[1]]

    def reject_return(self, copy_id):
        record = ReturnRequest.get(copyID=copy_id)
        record.delete()

    def change_balance(self, copy_id, amount):
        record = Log.select(lambda c: c.mediaID == copy_id and not c.returned)
        record.balance = 0
    def outstanding_request(self, media_id):
        media = Media[media_id]
        queue = list(media.queue)
        media.delete_queue()
        return [1, queue]

class Images(db.Entity):
    mediaID = Required(Media)
    image = Required(str)
    imageID = Required(int)


class Log(db.Entity):
    libID = Required(int)
    mediaID = Required(str)
    issue_date = Required(datetime.datetime,
                          default=datetime.datetime.utcnow)
    expiry_date = Required(datetime.datetime,
                           default=datetime.datetime.utcnow)
    returned = Required(bool, default=0)
    renewed = Required(bool, default=0)
    balance = Optional(int, default=0)


class MediaCopies(db.Entity):
    mediaID = Required(Media)
    copyID = Required(str)
    available = Required(bool)
    current_owner = Optional(User)


class RegistrySession(db.Entity):
    # PrimaryKey
    telegramID = PrimaryKey(int)

    # Fields for registering or adding user
    user_telegramID = Optional(int, default=-1)
    alias = Optional(str, default="")
    name = Optional(str, default="")
    phone = Optional(str, default="")
    address = Optional(str, default="")
    faculty = Optional(bool)

    # Cursors for different tables
    request_c = Optional(int, default=0)
    media_c = Optional(int, default=0)
    book_r_c = Optional(int, default=0)
    log_c = Optional(int, default=0)
    edit_media_cursor = Optional(int, default=0)
    edit_media_state = Optional(str)
    my_medias_c = Optional(int, default=0)
    return_c = Optional(int, default=0)
    users_c = Optional(int, default=0)

    # Fields for media adding
    type = Optional(str, default="")
    title = Optional(str, default="")
    author = Optional(str, default="")
    price = Optional(int, default=-1)
    fine = Optional(int, default=-1)
    publisher = Optional(str, default="")
    no_of_copies = Optional(int)


class ReturnRequest(db.Entity):
    telegramID = Required(int)
    copyID = Required(str)


class LibrarianEnrollment(db.Entity):
    name = Required(str)
    phone = Required(str)
    faculty = Required(bool)
    address = Required(str)
    registrykey = PrimaryKey(str, max_len=100)


class MediaQueue(db.Entity):
    mediaID = Required(Media)
    user = Required(User)
    requestDate = Required(datetime.datetime,
                           default=datetime.datetime.utcnow)

    def is_empty(self):
        return len(list(MediaQueue.select(lambda c: c.mediaID == Media))) == 0


db.generate_mapping(create_tables=True)
