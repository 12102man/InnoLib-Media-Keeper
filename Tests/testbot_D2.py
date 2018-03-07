from telethon import TelegramClient
from telethon.tl.functions.messages import *
import time
from pony.orm import *
import logging
import Config.config as config
import Config.config_test as config_test
from Core.database import *
import os
import json
import pickle

bot_name = 'ILMKbot'
# MySQL
db = Database()

db.bind(provider='mysql', host=config.db_host, user=config.db_username, passwd=config.db_password, db=config.db_name)
db.generate_mapping(create_tables=True)

# API keys are hidden in config_test.py which is not in GitHub
# because they're personal. You can create your own ones on
# my.telegram.org

api_id_lib = config_test.api_id_lib
api_hash_lib = config_test.api_hash_lib
librarian = TelegramClient('session_name_lib', api_id_lib, api_hash_lib)
librarian_telegram_ID = config_test.librarian_telegram_ID
librarian.start()

api_id_1 = config_test.api_id_1
api_hash_1 = config_test.api_hash_1
client1 = TelegramClient('session_name_1', api_id_1, api_hash_1)
client1_telegram_ID = config_test.client1_telegram_ID
client1.start()

api_id_2 = config_test.api_id_2
api_hash_2 = config_test.api_hash_2
client2 = TelegramClient('session_name_2', api_id_2, api_hash_2)
client2_telegram_ID = config_test.client2_telegram_ID
client2.start()

api_id_3 = config_test.api_id_3
api_hash_3 = config_test.api_hash_3
client3 = TelegramClient('session_name_3', api_id_3, api_hash_3)
client3_telegram_ID = config_test.client3_telegram_ID
client3.start()

logging.basicConfig(level=logging.INFO)


def press_button(client, bot_entity, msg, data):
    try:
        request = GetBotCallbackAnswerRequest(
            bot_entity,
            msg.id,
            data=data
        )
        client.invoke(request)
    except RuntimeError:
        return 0


def update_message(client):
    return client.get_message_history(bot_name, limit=1).data[0]


def initialize():
    # Initializing sessions
    RegistrySession(telegramID=56069837, alias="", name="", phone="", address="", edit_media_state="", type="",
                    title="", author="", publisher="")
    RegistrySession(telegramID=client1_telegram_ID, alias="", name="", phone="", address="", edit_media_state="",
                    type="",
                    title="", author="", publisher="")
    RegistrySession(telegramID=client2_telegram_ID, alias="", name="", phone="", address="", edit_media_state="",
                    type="",
                    title="", author="", publisher="")
    RegistrySession(telegramID=client3_telegram_ID, alias="", name="", phone="", address="", edit_media_state="",
                    type="",
                    title="", author="", publisher="")
    commit()


@db_session
def flush_db():
    for elem in Media.select():
        elem.delete()
    for elem in LibrarianEnrollment.select():
        elem.delete()
    for elem in Log.select():
        elem.delete()
    for elem in MediaCopies.select():
        elem.delete()
    for elem in MediaRequest.select():
        elem.delete()
    for elem in Request.select():
        elem.delete()
    for elem in ReturnRequest.select():
        elem.delete()
    for elem in User.select():
        elem.delete()
    for elem in RegistrySession.select():
        elem.delete()
    commit()
    initialize()


@db_session
def test1():
    flush_db()
    Media(mediaID=1, name="Introduction to algorithms (Third edition), 2009", type="Book",
          authors="Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest and Clifford Stein",
          publisher="MIT Press", cost=1000, fine=100, availability=1, bestseller=0)
    Media(mediaID=2, name="Design Patterns: Elements of Reusable Object-Oriented Software (First edition), 2003",
          type="Book",
          authors="Erich Gamma, Ralph Johnson, John Vlissides, Richard Helm",
          publisher="Addison-Wesley Professional", cost=1000, fine=100, availability=1, bestseller=1)
    Media(mediaID=3, name="The Mythical Man-month (Second edition), 1995",
          type="Reference book",
          authors="Brooks,Jr., Frederick P.",
          publisher="Addison-Wesley Longman Publishing Co., Inc.", cost=1000, fine=100, availability=0, bestseller=0)
    Media(mediaID=4, name="Null References: The Billion Dollar Mistake",
          type="AV",
          authors="Tony Hoare.",
          publisher="None", cost=1000, fine=100, availability=1, bestseller=1)
    Media(mediaID=5, name="Information Entropy",
          type="AV",
          authors="Claude Shannon",
          publisher="None", cost=1000, fine=100, availability=1, bestseller=1)

    MediaCopies(mediaID=1, copyID="1-1", available=1)
    MediaCopies(mediaID=1, copyID="1-2", available=1)
    MediaCopies(mediaID=1, copyID="1-3", available=1)
    MediaCopies(mediaID=2, copyID="2-1", available=1)
    MediaCopies(mediaID=2, copyID="2-2", available=1)
    MediaCopies(mediaID=3, copyID="3-1", available=1)
    MediaCopies(mediaID=4, copyID="4-1", available=1)
    MediaCopies(mediaID=5, copyID="5-1", available=1)

    User(telegramID=324148065, name="Sergey Afonso", alias="@sergei", phone="30001", address="Via Margutta, 3",
         faculty=1)
    User(telegramID=239514818, name="Nadia Teixeira", alias="@nadia", phone="30002", address="Via Sacra, 13", faculty=0)
    User(telegramID=142289653, name="Elvira Espindola", alias="@elvira", phone="30003", address="Via del Corso, 22",
         faculty=0)
    commit()

    assert (Media[1].name == "Introduction to algorithms (Third edition), 2009")
    assert (Media[1].authors == "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest and Clifford Stein")
    assert (Media[1].type == "Book")
    assert (Media[1].publisher == "MIT Press")

    assert (Media[2].name == "Design Patterns: Elements of Reusable Object-Oriented Software (First edition), 2003")
    assert (Media[2].authors == "Erich Gamma, Ralph Johnson, John Vlissides, Richard Helm")
    assert (Media[2].type == "Book")
    assert (Media[2].publisher == "Addison-Wesley Professional")

    assert (Media[3].name == "The Mythical Man-month (Second edition), 1995")
    assert (Media[3].authors == "Brooks,Jr., Frederick P.")
    assert (Media[3].type == "Reference book")
    assert (Media[3].publisher == "Addison-Wesley Longman Publishing Co., Inc.")

    assert (Media[4].name == "Null References: The Billion Dollar Mistake")
    assert (Media[4].authors == "Tony Hoare.")
    assert (Media[4].type == "AV")
    assert (Media[4].publisher == "None")

    assert (Media[5].name == "Information Entropy")
    assert (Media[5].authors == "Claude Shannon")
    assert (Media[5].type == "AV")
    assert (Media[5].publisher == "None")

    assert (User[324148065].name == "Sergey Afonso")
    assert (User[324148065].alias == "@sergei")
    assert (User[324148065].phone == "30001")
    assert (User[324148065].address == "Via Margutta, 3")

    assert (User[142289653].name == "Elvira Espindola")
    assert (User[142289653].alias == "@elvira")
    assert (User[142289653].phone == "30003")
    assert (User[142289653].address == "Via del Corso, 22")

    assert (User[239514818].name == "Nadia Teixeira")
    assert (User[239514818].alias == "@nadia")
    assert (User[239514818].phone == "30002")
    assert (User[239514818].address == "Via Sacra, 13")

    assert (MediaCopies.get(copyID="1-1") is not None)
    assert (MediaCopies.get(copyID="1-2") is not None)
    assert (MediaCopies.get(copyID="1-3") is not None)
    assert (MediaCopies.get(copyID="2-1") is not None)
    assert (MediaCopies.get(copyID="2-2") is not None)
    assert (MediaCopies.get(copyID="3-1") is not None)
    assert (MediaCopies.get(copyID="4-1") is not None)
    assert (MediaCopies.get(copyID="5-1") is not None)


@db_session
def test2():
    test1()
    MediaCopies.get(copyID="1-1").delete()
    MediaCopies.get(copyID="1-2").delete()
    MediaCopies.get(copyID="3-1").delete()
    Media.get(mediaID=3).delete()
    User[239514818].delete()

    assert (MediaCopies.get(copyID="1-1") is None)
    assert (MediaCopies.get(copyID="1-2") is None)
    assert (MediaCopies.get(copyID="3-1") is None)
    assert (Media.get(mediaID=3) is None)
    assert (User.get(telegramID=239514818) is None)
    commit()


@db_session
def gui_test1():
    """
    Test 1 using Telegram users
    :return: Test procedured in Telegram
    """
    logging.info("Starting Test 1")
    try:
        # Adding media 1
        flush_db()
        librarian.send_message(bot_name, "/add_media")
        time.sleep(3)
        librarian.send_message(bot_name, "Book")
        time.sleep(3)
        librarian.send_message(bot_name, "Introduction to algorithms (Third edition), 2009")
        time.sleep(3)
        librarian.send_message(bot_name, "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest and Clifford Stein")
        time.sleep(3)
        librarian.send_message(bot_name, "MIT Press")
        time.sleep(3)
        librarian.send_message(bot_name, "1000")
        time.sleep(3)
        librarian.send_message(bot_name, "100")
        time.sleep(3)
        librarian.send_message(bot_name, "3")
        time.sleep(3)

        # Adding media 2
        librarian.send_message(bot_name, "/add_media")
        time.sleep(3)
        librarian.send_message(bot_name, "Book")
        time.sleep(3)
        librarian.send_message(bot_name,
                               "Design Patterns: Elements of Reusable Object-Oriented Software (First edition), 2003")
        time.sleep(3)
        librarian.send_message(bot_name, "Erich Gamma, Ralph Johnson, John Vlissides, Richard Helm")
        time.sleep(3)
        librarian.send_message(bot_name, "Addison-Wesley Professional")
        time.sleep(3)
        librarian.send_message(bot_name, "1000")
        time.sleep(3)
        librarian.send_message(bot_name, "100")
        time.sleep(3)
        librarian.send_message(bot_name, "2")
        time.sleep(3)

        # Adding media 3
        librarian.send_message(bot_name, "/add_media")
        time.sleep(3)
        librarian.send_message(bot_name, "Reference book")
        time.sleep(3)
        librarian.send_message(bot_name,
                               "The Mythical Man-month (Second edition), 1995")
        time.sleep(3)
        librarian.send_message(bot_name, "Brooks,Jr., Frederick P.")
        time.sleep(3)
        librarian.send_message(bot_name, "Addison-Wesley Longman Publishing Co., Inc.")
        time.sleep(3)
        librarian.send_message(bot_name, "1000")
        time.sleep(3)
        librarian.send_message(bot_name, "100")
        time.sleep(3)
        librarian.send_message(bot_name, "1")
        time.sleep(3)

        # Adding AV 1
        librarian.send_message(bot_name, "/add_media")
        time.sleep(3)
        librarian.send_message(bot_name, "AV")
        time.sleep(3)
        librarian.send_message(bot_name,
                               "Null References: The Billion Dollar Mistake")
        time.sleep(3)
        librarian.send_message(bot_name, "Tony Hoare")
        time.sleep(3)
        librarian.send_message(bot_name, "None")
        time.sleep(3)
        librarian.send_message(bot_name, "1000")
        time.sleep(3)
        librarian.send_message(bot_name, "100")
        time.sleep(3)
        librarian.send_message(bot_name, "1")
        time.sleep(3)

        # Adding AV 2
        librarian.send_message(bot_name, "/add_media")
        time.sleep(3)
        librarian.send_message(bot_name, "AV")
        time.sleep(3)
        librarian.send_message(bot_name,
                               "Information Entropy")
        time.sleep(3)
        librarian.send_message(bot_name, "Claude Shannon")
        time.sleep(3)
        librarian.send_message(bot_name, "None")
        time.sleep(3)
        librarian.send_message(bot_name, "1000")
        time.sleep(3)
        librarian.send_message(bot_name, "100")
        time.sleep(3)
        librarian.send_message(bot_name, "1")
        time.sleep(3)

        # Adding user 1
        librarian.send_message(bot_name, "/add_user")
        time.sleep(3)
        librarian.send_message(bot_name, "Sergey Afonso")
        time.sleep(3)
        librarian.send_message(bot_name, "30001")
        time.sleep(3)
        librarian.send_message(bot_name, "Via Margutta, 3")
        time.sleep(3)
        librarian.send_message(bot_name, "1")
        time.sleep(3)
        message = librarian.get_message_history(bot_name, limit=1).data[0].message
        client1.send_message(bot_name, message)

        # Adding user 2
        librarian.send_message(bot_name, "/add_user")
        time.sleep(3)
        librarian.send_message(bot_name, "Nadia Teixeira")
        time.sleep(3)
        librarian.send_message(bot_name, "30002")
        time.sleep(3)
        librarian.send_message(bot_name, "Via Sacra, 13")
        time.sleep(3)
        librarian.send_message(bot_name, "0")
        time.sleep(3)
        message = librarian.get_message_history(bot_name, limit=1).data[0].message
        client2.send_message(bot_name, message)

        # Adding user 3
        librarian.send_message(bot_name, "/add_user")
        time.sleep(3)
        librarian.send_message(bot_name, "Elvira Espindola")
        time.sleep(3)
        librarian.send_message(bot_name, "30003")
        time.sleep(3)
        librarian.send_message(bot_name, "Via del Corso, 22")
        time.sleep(3)
        librarian.send_message(bot_name, "0")
        time.sleep(3)
        message = librarian.get_message_history(bot_name, limit=1).data[0].message
        client3.send_message(bot_name, message)
        time.sleep(3)

        assert (len(MediaCopies.select()) == 8 and len(User.select()) == 3)
        assert (Media[1].name == "Introduction to algorithms (Third edition), 2009")
        assert (Media[1].authors == "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest and Clifford Stein")
        assert (Media[1].type == "Book")
        assert (Media[1].publisher == "MIT Press")

        assert (Media[2].name == "Design Patterns: Elements of Reusable Object-Oriented Software (First edition), 2003")
        assert (Media[2].authors == "Erich Gamma, Ralph Johnson, John Vlissides, Richard Helm")
        assert (Media[2].type == "Book")
        assert (Media[2].publisher == "Addison-Wesley Professional")

        assert (Media[3].name == "The Mythical Man-month (Second edition), 1995")
        assert (Media[3].authors == "Brooks,Jr., Frederick P.")
        assert (Media[3].type == "Reference book")
        assert (Media[3].publisher == "Addison-Wesley Longman Publishing Co., Inc.")

        assert (Media[4].name == "Null References: The Billion Dollar Mistake")
        assert (Media[4].authors == "Tony Hoare.")
        assert (Media[4].type == "AV")
        assert (Media[4].publisher == "None")

        assert (Media[5].name == "Information Entropy")
        assert (Media[5].authors == "Claude Shannon")
        assert (Media[5].type == "AV")
        assert (Media[5].publisher == "None")

        assert (User[324148065].name == "Sergey Afonso")
        assert (User[324148065].alias == "@sergei")
        assert (User[324148065].phone == "30001")
        assert (User[324148065].address == "Via Margutta, 3")

        assert (User[142289653].name == "Elvira Espindola")
        assert (User[142289653].alias == "@elvira")
        assert (User[142289653].phone == "30003")
        assert (User[142289653].address == "Via del Corso, 22")

        assert (User[239514818].name == "Nadia Teixeira")
        assert (User[239514818].alias == "@nadia")
        assert (User[239514818].phone == "30002")
        assert (User[239514818].address == "Via Sacra, 13")

        assert (MediaCopies.get(copyID="1-1") is not None)
        assert (MediaCopies.get(copyID="1-2") is not None)
        assert (MediaCopies.get(copyID="1-3") is not None)
        assert (MediaCopies.get(copyID="2-1") is not None)
        assert (MediaCopies.get(copyID="2-2") is not None)
        assert (MediaCopies.get(copyID="3-1") is not None)
        assert (MediaCopies.get(copyID="4-1") is not None)
        assert (MediaCopies.get(copyID="5-1") is not None)
        logging.info("Test 1 is Successful")
    except AssertionError:
        logging.info("Test 1 is Failed")


@db_session
def gui_test2():
    """
    Test 2 using Telegram users
    :return: Test procedured in Telegram
    """
    test1()
    logging.info("Starting Test 2")
    try:
        # Deleting copy 2-1
        librarian.send_message(bot_name, "/delete_copy 2-1")
        time.sleep(3)
        message = librarian.get_message_history(bot_name, limit=1).data[0]
        press_button(librarian, bot_name, message, b'{"type": "deleteCopy", "argument": "2-1"}')

        # Deleting copy 2-2
        librarian.send_message(bot_name, "/delete_copy 2-2")
        time.sleep(3)
        message = librarian.get_message_history(bot_name, limit=1).data[0]
        press_button(librarian, bot_name, message, b'{"type": "deleteCopy", "argument": "2-2"}')

        # Deleting copy 3-1
        librarian.send_message(bot_name, "/delete_copy 3-1")
        time.sleep(3)
        message = librarian.get_message_history(bot_name, limit=1).data[0]
        press_button(librarian, bot_name, message, b'{"type": "deleteCopy", "argument": "3-1"}')

        # Deleting p2
        librarian.send_message(bot_name, "/users")
        time.sleep(3)

        message = librarian.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(librarian, bot_name, message, next)
        time.sleep(3)

        message = librarian.get_message_history(bot_name, limit=1).data[0]
        delete = message.reply_markup.rows[0].buttons[0].data
        press_button(librarian, bot_name, message, delete)
        time.sleep(3)

        message = librarian.get_message_history(bot_name, limit=1).data[0]
        delete = message.reply_markup.rows[0].buttons[0].data
        press_button(librarian, bot_name, message, delete)

        assert (len(MediaCopies.select()) == 5 and len(User.select()) == 2)
        assert (MediaCopies.get(copyID="1-1") is None)
        assert (MediaCopies.get(copyID="1-2") is None)
        assert (MediaCopies.get(copyID="3-1") is None)
        assert (User.get(telegramID=239514818) is None)
        logging.info("Test 2 is Successful")
    except AssertionError:
        logging.info("Test 2 is Failed")


@db_session
def test3():
    test1()
    logging.info("Starting Test 3")
    try:

        librarian.send_message(bot_name, "/users")
        time.sleep(3)

        message = librarian.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data

        button_bytes = message.reply_markup.rows[0].buttons[0].data
        user_id = int(json.loads(button_bytes.decode('utf8').replace("'", '"'))["argument"])
        assert (
            User.exists(telegramID=user_id) and User[user_id].name == "Elvira Espindola" and User[
                user_id].phone == "30003" and not User[user_id].faculty)
        press_button(librarian, bot_name, message, next)
        time.sleep(3)

        message = librarian.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[1].data
        press_button(librarian, bot_name, message, next)
        time.sleep(3)

        message = librarian.get_message_history(bot_name, limit=1).data[0]
        button_bytes = message.reply_markup.rows[0].buttons[0].data
        user_id = int(json.loads(button_bytes.decode('utf8').replace("'", '"'))["argument"])
        assert (
            User.exists(telegramID=user_id) and User[user_id].name == "Sergey Afonso" and User[
                user_id].phone == "30001" and
            User[user_id].faculty)
        press_button(librarian, bot_name, message, next)
        time.sleep(3)

        logging.info("Test 3 is successful")

    except AssertionError:
        logging.info("Test 3 is failed")


@db_session
def test4():
    test2()
    logging.info("Starting Test 4")
    try:
        librarian.send_message(bot_name, "/users")
        time.sleep(3)

        # Getting current user's ID
        message = librarian.get_message_history(bot_name, limit=1).data[0]
        button_bytes = message.reply_markup.rows[0].buttons[0].data
        user_id = int(json.loads(button_bytes.decode('utf8').replace("'", '"'))["argument"])
        assert (user_id != 239514818)

        # Moving to next user
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(librarian, bot_name, message, next)
        time.sleep(3)

        # Getting current user's ID
        message = librarian.get_message_history(bot_name, limit=1).data[0]
        button_bytes = message.reply_markup.rows[0].buttons[0].data
        user_id = int(json.loads(button_bytes.decode('utf8').replace("'", '"'))["argument"])
        assert (
            User.exists(telegramID=user_id) and User[user_id].name == "Sergey Afonso" and User[
                user_id].phone == "30001" and
            User[user_id].faculty)
        logging.info("Test 4 is Successful")
    except AssertionError:
        logging.info("Test 4 is Failed")


def test5():
    test2()
    logging.info("Starting Test 5")
    try:
        client2.send_message(bot_name, "/medias")
        time.sleep(3)

        # Pressing "Book" button
        message = client2.get_message_history(bot_name, limit=1).data[0]
        book = message.reply_markup.rows[0].buttons[0].data
        press_button(client2, bot_name, message, book)
        time.sleep(3)

        # Checking message
        message = client2.get_message_history(bot_name, limit=1).data[0].message
        assert (message == "🤦🏻‍♂️ You're not enrolled into the System. Shame on you! Enroll now! /enroll")
        logging.info("Test 5 is Successful")
    except AssertionError:
        logging.info("Test 5 is Failed")


@db_session
def test6():
    test2()
    logging.info("Starting Test 6")
    try:

        # PART 1 Client 1 takes book 1
        client1.send_message(bot_name, "/medias")
        time.sleep(3)
        # Pressing "Book" button
        message = client1.get_message_history(bot_name, limit=1).data[0]
        book = message.reply_markup.rows[0].buttons[0].data
        press_button(client1, bot_name, message, book)
        time.sleep(3)

        # PART 2 Client 1 takes book 2
        client1.send_message(bot_name, "/medias")
        time.sleep(3)
        # Moving to next book
        message = client1.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(client1, bot_name, message, next)
        time.sleep(3)
        # Pressing "Book" button
        message = client1.get_message_history(bot_name, limit=1).data[0]
        book = message.reply_markup.rows[0].buttons[0].data
        press_button(client1, bot_name, message, book)
        time.sleep(3)

        # PART 3 Client 3 takes book 1
        client3.send_message(bot_name, "/medias")
        time.sleep(3)
        # Pressing "Book" button
        message = client3.get_message_history(bot_name, limit=1).data[0]
        book = message.reply_markup.rows[0].buttons[0].data
        press_button(client3, bot_name, message, book)
        time.sleep(3)

        # Correcting date
        for record in Log.select():
            fifth_march = record.issue_date.replace(day=5)
            delta = record.issue_date - fifth_march

            record.issue_date = fifth_march
            record.expiry_date = record.expiry_date - delta
            commit()

        # Getting menu with users
        librarian.send_message(bot_name, "/users")
        time.sleep(1.5)
        # Moving to next user
        message = librarian.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(librarian, bot_name, message, next)
        time.sleep(3)

        log_1, log_2 = select(record for record in Log)

        # Checking expiry dates
        assert (log_1.expiry_date.day == 2 and log_1.expiry_date.month == 4)
        assert (log_2.expiry_date.day == 2 and log_1.expiry_date.month == 4)
        logging.info("Test 6 is Successful")
    except AssertionError:
        logging.info("Test 6 is Failed")


@db_session
def test7():
    test1()
    logging.info("Starting Test 7")
    try:

        # PART 1. Client1 issues b1
        client1.send_message(bot_name, "/medias")
        time.sleep(3)
        # Pressing "Book" button
        message = client1.get_message_history(bot_name, limit=1).data[0]
        book = message.reply_markup.rows[0].buttons[0].data
        press_button(client1, bot_name, message, book)
        time.sleep(3)

        # PART 2 Client 1 takes book 2
        client1.send_message(bot_name, "/medias")
        time.sleep(3)
        # Moving to next book
        message = client1.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(client1, bot_name, message, next)
        time.sleep(3)
        # Pressing "Book" button
        message = client1.get_message_history(bot_name, limit=1).data[0]
        book = message.reply_markup.rows[0].buttons[0].data
        press_button(client1, bot_name, message, book)
        time.sleep(3)

        # PART 3 Client 1 takes book 3
        client1.send_message(bot_name, "/medias")
        time.sleep(3)
        # Moving to next book
        message = client1.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(client1, bot_name, message, next)
        time.sleep(3)
        # Moving to next book
        message = client1.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[1].data
        press_button(client1, bot_name, message, next)
        time.sleep(3)
        # Pressing "Book" button
        message = client1.get_message_history(bot_name, limit=1).data[0]
        book = message.reply_markup.rows[0].buttons[0].data
        press_button(client1, bot_name, message, book)
        time.sleep(3)

        # PART 4 Client 1 takes AV1
        client1.send_message(bot_name, "/medias")
        time.sleep(3)
        # Moving to next book
        message = client1.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(client1, bot_name, message, next)
        time.sleep(3)
        # Moving to next book
        message = client1.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[1].data
        press_button(client1, bot_name, message, next)
        time.sleep(3)
        # Moving to next book
        message = client1.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[1].data
        press_button(client1, bot_name, message, next)
        time.sleep(3)
        # Pressing "Book" button
        message = client1.get_message_history(bot_name, limit=1).data[0]
        book = message.reply_markup.rows[0].buttons[0].data
        press_button(client1, bot_name, message, book)
        time.sleep(3)

        # USER 2 ACTIONS
        # PART 1. Client2 issues b1
        client2.send_message(bot_name, "/medias")
        time.sleep(3)
        # Pressing "Book" button
        message = client2.get_message_history(bot_name, limit=1).data[0]
        book = message.reply_markup.rows[0].buttons[0].data
        press_button(client2, bot_name, message, book)
        time.sleep(3)

        # PART 2 Client2 takes book 2
        client2.send_message(bot_name, "/medias")
        time.sleep(3)
        # Moving to next book
        message = client2.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(client2, bot_name, message, next)
        time.sleep(3)
        # Pressing "Book" button
        message = client2.get_message_history(bot_name, limit=1).data[0]
        book = message.reply_markup.rows[0].buttons[0].data
        press_button(client2, bot_name, message, book)
        time.sleep(3)

        # PART 4 Client2 takes AV2
        client2.send_message(bot_name, "/medias")
        time.sleep(3)
        # Moving to next book
        message = client2.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(client2, bot_name, message, next)
        time.sleep(3)
        # Moving to next book
        message = client2.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[1].data
        press_button(client2, bot_name, message, next)
        time.sleep(3)
        # Moving to next book
        message = client2.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[1].data
        press_button(client2, bot_name, message, next)
        time.sleep(3)
        # Moving to next book
        message = client2.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[1].data
        press_button(client2, bot_name, message, next)
        time.sleep(3)
        # Pressing "Book" button
        message = client2.get_message_history(bot_name, limit=1).data[0]
        book = message.reply_markup.rows[0].buttons[0].data
        press_button(client2, bot_name, message, book)
        time.sleep(3)

        # Getting menu with users
        librarian.send_message(bot_name, "/users")
        # Moving to next user
        message = librarian.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(librarian, bot_name, message, next)
        time.sleep(3)
        # Moving to next user
        message = librarian.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(librarian, bot_name, message, next)
        time.sleep(3)

        # Correcting date
        for record in Log.select():
            fifth_march = record.issue_date.replace(day=5)
            delta = record.issue_date - fifth_march

            record.issue_date = fifth_march
            record.expiry_date = record.expiry_date - delta
            commit()

        u1_b1, u1_b2, u1_a1, u2_b1, u2_b2, u2_a2 = select(record for record in Log)
        assert (u1_b1.expiry_date.month == 4 and u1_b1.expiry_date.day == 2)
        assert (u1_b2.expiry_date.month == 4 and u1_b2.expiry_date.day == 2)
        assert (u1_a1.expiry_date.month == 3 and u1_a1.expiry_date.day == 19)
        assert (u2_b1.expiry_date.month == 3 and u2_b1.expiry_date.day == 26)
        assert (u2_b2.expiry_date.month == 3 and u2_b2.expiry_date.day == 19)
        assert (u2_a2.expiry_date.month == 3 and u2_a2.expiry_date.day == 19)
        logging.info("Test 7 is Successful")

    except AssertionError:
        logging.info("Test 7 is Failed")


@db_session
def test8():
    test1()
    logging.info("Starting Test 8")
    try:
        delta = datetime.datetime.now() - datetime.datetime.now().replace(day=5).replace(month=3)
        Log(libID=client1_telegram_ID, mediaID='1-1', issue_date=datetime.datetime(2018, 2, 9, 12, 0, 0),
            expiry_date=datetime.datetime(2018, 2, 9, 12, 0, 0) + datetime.timedelta(weeks=4) + delta, returned=False,
            renewed=False)
        Log(libID=client1_telegram_ID, mediaID='2-1', issue_date=datetime.datetime(2018, 2, 2, 12, 0, 0),
            expiry_date=datetime.datetime(2018, 2, 2, 12, 0, 0) + datetime.timedelta(weeks=4) + delta, returned=False,
            renewed=False)

        Log(libID=client2_telegram_ID, mediaID='1-2', issue_date=datetime.datetime(2018, 2, 5, 12, 0, 0),
            expiry_date=datetime.datetime(2018, 2, 5, 12, 0, 0) + datetime.timedelta(weeks=3) + delta, returned=False,
            renewed=False)
        Log(libID=client2_telegram_ID, mediaID='4-1', issue_date=datetime.datetime(2018, 2, 17, 12, 0, 0),
            expiry_date=datetime.datetime(2018, 2, 17, 12, 0, 0) + datetime.timedelta(weeks=2) + delta, returned=False,
            renewed=False)

        commit()

        # Getting menu with users
        librarian.send_message(bot_name, "/users")
        time.sleep(1.5)
        # Moving to next user
        message = librarian.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(librarian, bot_name, message, next)
        time.sleep(3)

        # Moving to next user
        message = librarian.get_message_history(bot_name, limit=1).data[0]
        assert ("OVERDUE: 7 days!" in message.message)
        assert ("OVERDUE: 2 days!" in message.message)
        next = message.reply_markup.rows[1].buttons[1].data
        press_button(librarian, bot_name, message, next)
        time.sleep(3)

        # Moving to next user
        message = librarian.get_message_history(bot_name, limit=1).data[0]
        assert ("OVERDUE: 3 days!" in message.message)

        logging.info("Test 8 is Successful")
    except AssertionError:
        logging.info("Test 8 is Failed")


@db_session
def test9():
    test1()
    logging.info("Starting Test 9")
    try:
        librarian.send_message(bot_name, "/reboot")
        time.sleep(25)
        assert (Media[1].name == "Introduction to algorithms (Third edition), 2009")
        assert (Media[1].authors == "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest and Clifford Stein")
        assert (Media[1].type == "Book")
        assert (Media[1].publisher == "MIT Press")

        assert (Media[2].name == "Design Patterns: Elements of Reusable Object-Oriented Software (First edition), 2003")
        assert (Media[2].authors == "Erich Gamma, Ralph Johnson, John Vlissides, Richard Helm")
        assert (Media[2].type == "Book")
        assert (Media[2].publisher == "Addison-Wesley Professional")

        assert (Media[3].name == "The Mythical Man-month (Second edition), 1995")
        assert (Media[3].authors == "Brooks,Jr., Frederick P.")
        assert (Media[3].type == "Reference book")
        assert (Media[3].publisher == "Addison-Wesley Longman Publishing Co., Inc.")

        assert (Media[4].name == "Null References: The Billion Dollar Mistake")
        assert (Media[4].authors == "Tony Hoare.")
        assert (Media[4].type == "AV")
        assert (Media[4].publisher == "None")

        assert (Media[5].name == "Information Entropy")
        assert (Media[5].authors == "Claude Shannon")
        assert (Media[5].type == "AV")
        assert (Media[5].publisher == "None")

        assert (User[324148065].name == "Sergey Afonso")
        assert (User[324148065].alias == "@sergei")
        assert (User[324148065].phone == "30001")
        assert (User[324148065].address == "Via Margutta, 3")

        assert (User[142289653].name == "Elvira Espindola")
        assert (User[142289653].alias == "@elvira")
        assert (User[142289653].phone == "30003")
        assert (User[142289653].address == "Via del Corso, 22")

        assert (User[239514818].name == "Nadia Teixeira")
        assert (User[239514818].alias == "@nadia")
        assert (User[239514818].phone == "30002")
        assert (User[239514818].address == "Via Sacra, 13")

        assert (MediaCopies.get(copyID="1-1") is not None)
        assert (MediaCopies.get(copyID="1-2") is not None)
        assert (MediaCopies.get(copyID="1-3") is not None)
        assert (MediaCopies.get(copyID="2-1") is not None)
        assert (MediaCopies.get(copyID="2-2") is not None)
        assert (MediaCopies.get(copyID="3-1") is not None)
        assert (MediaCopies.get(copyID="4-1") is not None)
        assert (MediaCopies.get(copyID="5-1") is not None)
        logging.info("Test 9 is Successful")
    except AssertionError:
        logging.info("Test 9 is Failed")


test2()
