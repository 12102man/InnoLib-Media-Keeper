from pony.orm import *
import datetime

db = Database()
# MySQL
db.bind(provider='mysql', host='37.46.132.57', user='telebot', passwd='Malinka2017', db='testbase')


class User(db.Entity):
    telegramID = PrimaryKey(int)
    name = Required(str)
    address = Required(str)
    medias = Set('MediaCopies')
    alias = Required(str)
    phone = Required(str)
    faculty = Required(bool)


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
    my_medias_c = Optional(int)
    return_c = Optional(int)

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


db.generate_mapping(create_tables=True)
set_sql_debug(True)
