from pony.orm import *
from search_engine import *

from button_actions import generate_expiry_date, check_copy
import datetime

import config as config

db = Database()
# MySQL
db.bind(provider='mysql', host=config.db_host, user=config.db_username, passwd=config.db_password, db=config.db_name)


class Admin(db.Entity):
    telegram_id = Required(int)
    new_lib_id = Optional(int)

    def __init__(self, **kwargs):
        # process kwargs if necessary
        if Admin.get(id=1) is not None:
            raise FileExistsError("Admin already exists")
        super().__init__(**kwargs)
        if database.RegistrySession.get(telegramID=self.telegram_id) is None:
            database.RegistrySession(telegramID=self.telegram_id)

    def set_privilege(self, level):
        """
        Sets privileges to existing or new librarian
        :param level: level of privileges
        :return: string depends on is the librarian newcomer or he already was him
        """
        new_lib = Librarian.get(telegramID=self.new_lib_id)
        if new_lib.priority == 0:
            action = "New librarian was added!"
        else:
            action = "Librarian privileges was changed!"
        if level == 'edit':
            new_lib.priority = 1
        if level == 'add':
            new_lib.priority = 2
        if level == 'delete':
            new_lib.priority = 3
        self.new_lib_id = 0
        commit()
        return action

    def add_new_librarian(self):
        """
        Adds record about new librarian
        :return:
        """
        Librarian(telegramID=self.new_lib_id,
                  name=User.get(telegramID=self.new_lib_id).name,
                  priority=0)
        Actions(implementer="Admin 1",
                action="has added librarian #",
                implementee=str(self.new_lib_id))
        commit()

    def delete_librarian(self, lib_id):
        """
        Deletes existing librarian
        :param lib_id: telegramID of librarian
        :return:
        """
        RegistrySession.get(telegramID=self.telegram_id).users_c = 0
        Librarian.get(telegramID=lib_id).delete()
        commit()


class User(db.Entity):
    telegramID = PrimaryKey(int)
    name = Required(str)
    address = Required(str)
    alias = Required(str)
    phone = Required(str)
    balance = Optional(int)
    priority = Optional(int, default=4)
    queue = Set('MediaQueue')

    def medias(self):
        return list(Log.select(lambda c: c.libID == self.telegramID and not c.returned))

    def add_to_queue(self, media_id):
        MediaQueue(user=self, mediaID=media_id)
        commit()

    def is_in_line(self, media):
        return not len(list(MediaQueue.select(lambda c: c.user == self and c.mediaID == media))) == 0

    def get_number_in_line(self, media):
        order_of_users = media.get_queue()
        user_place = list(filter(lambda o: o.user == self, order_of_users))
        return order_of_users.index(user_place[0]) + 1

    def renew_copy(self, copy_id, date):
        # select log and extend expiry date
        media = MediaCopies.get(copyID=copy_id).mediaID
        log = Log.get(mediaID=copy_id, libID=self.telegramID)
        if (not log.renewed) or (User.priority == 3 and len(media.get_queue) == 0):
            log.expiry_date = generate_expiry_date(media=media,
                                                   patron=self,
                                                   issue_date=date)
            log.renewed = 1
            commit()
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

    def book_media(self, media_item, date):
        if not media_item.availability:
            self.add_to_queue(media_item.mediaID)
            Actions(implementer="User#" + str(self.telegramID),
                    action="got in queue for media #",
                    implementee=str(media_item.mediaID))
            return -1
        if not check_copy(media_item.mediaID, self.telegramID):
            return -2

        copies_to_book = list(
            MediaCopies.select(lambda c: c.copyID.startswith(str(media_item.mediaID)) and c.available))
        item = copies_to_book[0]

        Log(libID=self.telegramID, mediaID=item.copyID,
            expiry_date=generate_expiry_date(media_item, self, date))

        item.available = False

        if len(copies_to_book) == 1:
            media_item.availability = False

        Actions(implementer="User#" + str(self.telegramID),
                action="has booked media #",
                implementee=str(item.copyID))
        return 0

    def return_media(self, copy_id):
        ReturnRequest(
            telegramID=self.telegramID,
            copyID=copy_id
        )

    def search(self, parameter, criteria):
        return search(parameter, criteria)


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
    keywords = Optional(str)

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

    faculty = Required(int)
    status = Optional(bool, default=False)


class MediaRequest(db.Entity):
    libID = Required(int)
    mediaID = Required(str)


class Librarian(db.Entity):
    telegramID = PrimaryKey(int)
    name = Required(str)
    priority = Required(int)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if database.RegistrySession.get(telegramID=self.telegramID) is None:
            database.RegistrySession(telegramID=self.telegramID)


    def check_return(self, copy_id):
        record = list(Log.select(lambda c: c.mediaID == copy_id and not c.returned))[0]
        if record.balance != 0:
            return [0, record.balance]
        else:
            return [1, 1]

    def get_user_medias(self, user):
        return list(Log.select(lambda c: c.libID == user.telegramID and not c.returned))

    def accept_return(self, copy_id):
        if self.check_return(copy_id)[0] == 1:
            record = list(Log.select(lambda c: c.mediaID == copy_id and not c.returned))[0]
            copy = MediaCopies.get(copyID=copy_id)
            copy.available = True
            record.returned = True
            ReturnRequest.get(copyID=copy_id).delete()
            commit()
            media = copy.mediaID
            if len(media.queue) > 0:
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

    def outstanding_request(self, media_id, date):
        Actions(implementer="Librarian#" + str(self.telegramID),
                action="has placed an outstanding request for media #",
                implementee=str(media_id))
        if not self.priority in [2, 3]:
            Actions(implementer="Outstanding Request of Librarian#" + str(self.telegramID),
                    action="for media #",
                    implementee=str(media_id) + "has been denied")
            return [-1]
        media = Media[media_id]
        queue = []
        for element in media.queue:
            queue.append(element.user)
        media.delete_queue()
        Actions(implementer="[OR] Queue for media #" + str(media_id),
                action="has been deleted",
                implementee="")
        checked_out_copies = list(Log.select(lambda c: c.returned == 0 and c.mediaID.startswith(str(media.mediaID))))
        holders = []
        for i in range(len(checked_out_copies)):
            checked_out_copies[i].renewed = 1
            checked_out_copies[i].expiry_date = date
            holders.append([checked_out_copies[i].libID, checked_out_copies[i].mediaID])
        holders_string = ""
        for holder in holders:
            holders_string += str(holder[0]) + " (with media #" + str(holder[1]) + "), "
        queue_string = ""
        for elem in queue:
            queue_string += str(elem) + ", "
        Actions(implementer="[OR] Holders " + holders_string,
                action="have been notified about Outstanding Request",
                implementee="")
        Actions(implementer="[OR] Queue participants " + queue_string,
                action="have been notified about Outstanding Request",
                implementee="")
        return [1, queue, holders]

    def add_media(self, text):
        if not self.priority in [2, 3]:
            return -1
        session = RegistrySession.get(telegramID=self.telegramID)
        if session is not None:
            if session.type == "":
                if text == "/add_media":
                    return "Let's add a new media! What is the type of media?"
                session.type = text
                return "What is the title of media?"
            elif session.title == "":
                session.title = text
                commit()
                return "Who is the author?"
            elif session.author == "":
                session.author = text
                commit()
                return "What is the publisher?"
            elif session.publisher == "":
                session.publisher = text
                commit()
                return "What is the price?"
            elif session.price == -1:
                session.price = text
                commit()
                return "What is the fine?"
            elif session.fine == -1:
                session.fine = text
                commit()
                return "What are the keywords?"
            elif session.keywords == "":
                session.keywords = text
                commit()
                return "How many copies do you want to add?"
            elif session.no_of_copies == -1:
                no_of_copies = int(text)
                session.no_of_copies = no_of_copies
                Media(name=session.title, type=session.type, authors=session.author,
                      publisher=session.publisher, cost=session.price, fine=session.fine,
                      availability=True, bestseller=False, keywords=session.keywords)
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
                session.keywords = ""
                commit()
                return "Media and %s its copies had been added" % str(no_of_copies)
        else:
            RegistrySession(telegramID=self.telegramID)
            return "Please, enter type of media:"

    def add_user(self, text):
        session = RegistrySession.get(telegramID=self.telegramID)
        if session is not None:
            if session.name == "":
                session.name = text
                commit()
                return "Please, enter his phone"
            elif session.phone == "":
                session.phone = text
                commit()
                return "Please, enter new user's address"
            elif session.address == "":
                session.address = text
                commit()
                return "Choose his/her status"
            elif session.faculty == 0:
                return "Choose his/her status"
        else:
            RegistrySession(telegramID=self.telegramID)
            return "Let's add a new User! Please, enter new user's name"

    def add_copy(self, media_id):
        if not self.priority in [2, 3]:
            return -1
        abstract_media = Media.get(mediaID=media_id)
        if abstract_media is None:
            return -1
        copies = list(abstract_media.copies)
        copy_to_add = MediaCopies(mediaID=abstract_media.mediaID,
                                  copyID=str(abstract_media.mediaID) + "-" + str(len(copies) + 1), available=1)
        copies.append(copy_to_add)
        abstract_media.copies = copies
        Actions(implementer="Librarian#" + str(self.telegramID),
                action="has added copy of media #",
                implementee=str(abstract_media.mediaID))
        commit()
        return 1

    def __add_media__(self, params):
        if not self.priority in [2, 3]:
            return -1
        Media(mediaID=params['id'], name=params['name'],
              type=params['type'],
              authors=params['authors'],
              publisher=params['publisher'], cost=params['cost'], fine=params['cost'],
              availability=params['availability'], bestseller=params['bestseller'], keywords=params['keywords'])
        Actions(implementer="Librarian#" + str(self.telegramID),
                action="has added media #",
                implementee=str(params['id']))
        return 1

    def __add_user__(self, params):
        User(telegramID=params['telegramID'], address=params['address'], alias=params['alias'], phone=params['phone'],
             balance=0, priority=params['priority'], name=params['name'])
        Actions(implementer="Librarian#" + str(self.telegramID),
                action="has added user #",
                implementee=str(params['telegramID']))
        return 1

    def delete_copy(self, copy_id):
        if not self.priority in [3]:
            return -1
        MediaCopies.get(copyID=copy_id).delete()
        Actions(implementer="Librarian#" + str(self.telegramID),
                action="has deleted media copy #",
                implementee=str(copy_id))
        return 1


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

    def is_expired(self, check_date):
        return self.expiry_date < check_date

    def time_expired(self, check_date):
        assert self.is_expired(check_date)
        return (check_date - self.expiry_date).days


class MediaCopies(db.Entity):
    mediaID = Required(Media)
    copyID = Required(str)
    available = Required(bool)


class RegistrySession(db.Entity):
    # PrimaryKey
    telegramID = PrimaryKey(int)

    # Fields for registering or adding user
    user_telegramID = Optional(int, default=-1)
    alias = Optional(str, default="")
    name = Optional(str, default="")
    phone = Optional(str, default="")
    address = Optional(str, default="")
    faculty = Optional(int, default=0)

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
    no_of_copies = Optional(int, default=-1)
    debtors_c = Optional(int, default=0)
    keywords = Optional(str, default="")

    search_parameter = Optional(str, default="")
    search_criteria = Optional(str, default="")


class ReturnRequest(db.Entity):
    telegramID = Required(int)
    copyID = Required(str)


class LibrarianEnrollment(db.Entity):
    name = Required(str)
    phone = Required(str)
    faculty = Required(int)
    address = Required(str)
    registrykey = PrimaryKey(str, max_len=100)


class MediaQueue(db.Entity):
    mediaID = Required(Media)
    user = Required(User)
    requestDate = Required(datetime.datetime,
                           default=datetime.datetime.utcnow)

    def is_empty(self):
        return len(list(MediaQueue.select(lambda c: c.mediaID == self.mediaID))) == 0


class Actions(db.Entity):
    implementer = Required(str)  # item who makes action
    action = Required(str)
    implementee = Optional(str)  # item which action is taken at
    timestamp = Required(datetime.datetime,
                         default=datetime.datetime.utcnow)

    def generate_file(self):
        with open('actions.txt', 'w') as f:
            list_of_actions = Actions.select()
            for action in list_of_actions:
                f.write(action.timestamp.strftime(
                    "%d %b %Y") + " | " + action.implementer + " " + action.action + action.implementee + "\n")


db.generate_mapping(create_tables=True)
