from pony.orm import *
import datetime

db = Database()
# MySQL
db.bind(provider='mysql', host='37.46.132.57', user='telebot', passwd='Malinka2017', db='testbase')


class User(db.Entity):
    name = Required(str)
    address = Required(str)
    medias = Set('MediaCopies')

    telegramID = PrimaryKey(int)
    alias = Required(str)
    phone = Required(str)
    faculty = Required(bool)


class Media(db.Entity):
    mediaID = PrimaryKey(int, auto=True)
    name = Required(str)  # title?

    type = Required(str)
    authors = Required(str)  # or [str]?
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
    alias = Optional(str)
    name = Optional(str)
    phone = Optional(str)
    address = Optional(str)
    faculty = Optional(bool)
    telegramID = PrimaryKey(int)
    request_c = Optional(int, default=0)
    media_c = Optional(int, default=0)
    book_r_c = Optional(int, default=0)
    log_c = Optional(int, default=0)
    type = Optional(str)
    title = Optional(str)
    author = Optional(str)
    price = Optional(int, default=0)
    fine = Optional(int, default=0)
    edit_media_cursor = Optional(int, default=0)
    edit_media_state = Optional(str)
    publisher = Optional(str)


db.generate_mapping(create_tables=True)
set_sql_debug(True)
