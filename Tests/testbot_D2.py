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

bot_name = 'ILMKbot'
# MySQL
db = Database()

db.bind(provider='mysql', host=config.db_host, user=config.db_username, passwd=config.db_password, db=config.db_name)
db.generate_mapping(create_tables=True)

# API keys are hidden in config_test.py which is not in GitHub
# because they're personal. You can create your own ones on
# my.telegram.org

api_id_1 = config_test.api_id_1
api_hash_1 = config_test.api_hash_1
client1 = TelegramClient('session_name', api_id_1, api_hash_1)
client1_telegram_ID = config_test.client1_telegram_ID
client1.start()

"""
api_id_2 = config_test.api_id_2
api_hash_2 = config_test.api_hash_2
client2 = TelegramClient('session_name_1', api_id_2, api_hash_2)
client2_telegram_ID = config_test.client2_telegram_ID
client2.start()

api_id_3 = config_test.api_id_3
api_hash_3 = config_test.api_hash_3
client3 = TelegramClient('session_name_2', api_id_3, api_hash_3)
client3_telegram_ID = config_test.client3_telegram_ID
client3.start()
"""

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
    commit()


@db_session
def fast_test1():
    flush_db()
    Media(mediaID=1, name="Introduction to algorithms (Third edition), 2009", type="Book",
          authors="Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest and Clifford Stein",
          publisher="MIT Press", cost=1000, fine=100, availability=1, bestseller=1)
    Media(mediaID=2, name="Design Patterns: Elements of Reusable Object-Oriented Software (First edition), 2003",
          type="Book",
          authors="Erich Gamma, Ralph Johnson, John Vlissides, Richard Helm",
          publisher="Addison-Wesley Professional", cost=1000, fine=100, availability=1, bestseller=1)
    Media(mediaID=3, name="The Mythical Man-month (Second edition), 1995",
          type="Book",
          authors="Brooks,Jr., Frederick P.",
          publisher="Addison-Wesley Longman Publishing Co., Inc.", cost=1000, fine=100, availability=1, bestseller=1)
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

    User(telegramID=1010, name="Sergey Afonso", alias="@sergei", phone="30001", address="Via Margutta, 3", faculty=1)
    User(telegramID=1011, name="Nadia Teixeira", alias="@nadia", phone="30002", address="Via Sacra, 13", faculty=0)
    User(telegramID=1100, name="Elvira Espindola", alias="@elvira", phone="30003", address="Via del Corso, 22",
         faculty=0)

    commit()


@db_session
def fast_test2():
    fast_test1()
    MediaCopies.get(copyID="2-1").delete()
    MediaCopies.get(copyID="2-2").delete()
    MediaCopies.get(copyID="3-1").delete()
    User[1011].delete()
    commit()


@db_session
def test1():
    logging.info("Starting Test 1")
    try:
        # Adding media 1
        client1.send_message(bot_name, "/add_media")
        time.sleep(3)
        client1.send_message(bot_name, "Book")
        time.sleep(3)
        client1.send_message(bot_name, "Introduction to algorithms (Third edition), 2009")
        time.sleep(3)
        client1.send_message(bot_name, "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest and Clifford Stein")
        time.sleep(3)
        client1.send_message(bot_name, "MIT Press")
        time.sleep(3)
        client1.send_message(bot_name, "1000")
        time.sleep(3)
        client1.send_message(bot_name, "100")
        time.sleep(3)
        client1.send_message(bot_name, "3")
        time.sleep(3)

        # Adding media 2
        client1.send_message(bot_name, "/add_media")
        time.sleep(3)
        client1.send_message(bot_name, "Book")
        time.sleep(3)
        client1.send_message(bot_name,
                             "Design Patterns: Elements of Reusable Object-Oriented Software (First edition), 2003")
        time.sleep(3)
        client1.send_message(bot_name, "Erich Gamma, Ralph Johnson, John Vlissides, Richard Helm")
        time.sleep(3)
        client1.send_message(bot_name, "Addison-Wesley Professional")
        time.sleep(3)
        client1.send_message(bot_name, "1000")
        time.sleep(3)
        client1.send_message(bot_name, "100")
        time.sleep(3)
        client1.send_message(bot_name, "2")
        time.sleep(3)

        # Adding media 3
        client1.send_message(bot_name, "/add_media")
        time.sleep(3)
        client1.send_message(bot_name, "Book")
        time.sleep(3)
        client1.send_message(bot_name,
                             "The Mythical Man-month (Second edition), 1995")
        time.sleep(3)
        client1.send_message(bot_name, "Brooks,Jr., Frederick P.")
        time.sleep(3)
        client1.send_message(bot_name, "Addison-Wesley Longman Publishing Co., Inc.")
        time.sleep(3)
        client1.send_message(bot_name, "1000")
        time.sleep(3)
        client1.send_message(bot_name, "100")
        time.sleep(3)
        client1.send_message(bot_name, "1")
        time.sleep(3)

        # Adding AV 1
        client1.send_message(bot_name, "/add_media")
        time.sleep(3)
        client1.send_message(bot_name, "AV")
        time.sleep(3)
        client1.send_message(bot_name,
                             "Null References: The Billion Dollar Mistake")
        time.sleep(3)
        client1.send_message(bot_name, "Tony Hoare")
        time.sleep(3)
        client1.send_message(bot_name, "None")
        time.sleep(3)
        client1.send_message(bot_name, "1000")
        time.sleep(3)
        client1.send_message(bot_name, "100")
        time.sleep(3)
        client1.send_message(bot_name, "1")
        time.sleep(3)

        # Adding AV 2
        client1.send_message(bot_name, "/add_media")
        time.sleep(3)
        client1.send_message(bot_name, "AV")
        time.sleep(3)
        client1.send_message(bot_name,
                             "Information Entropy")
        time.sleep(3)
        client1.send_message(bot_name, "Claude Shannon")
        time.sleep(3)
        client1.send_message(bot_name, "None")
        time.sleep(3)
        client1.send_message(bot_name, "1000")
        time.sleep(3)
        client1.send_message(bot_name, "100")
        time.sleep(3)
        client1.send_message(bot_name, "1")
        time.sleep(3)

        # Adding user 1
        client1.send_message(bot_name, "/add_user")
        time.sleep(3)
        client1.send_message(bot_name, "Sergey Afonso")
        time.sleep(3)
        client1.send_message(bot_name, "30001")
        time.sleep(3)
        client1.send_message(bot_name, "Via Margutta, 3")
        time.sleep(3)
        client1.send_message(bot_name, "1")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0].message
        client1.send_message(bot_name, message)

        # Adding user 2
        client1.send_message(bot_name, "/add_user")
        time.sleep(3)
        client1.send_message(bot_name, "Nadia Teixeira")
        time.sleep(3)
        client1.send_message(bot_name, "30002")
        time.sleep(3)
        client1.send_message(bot_name, "Via Sacra, 13")
        time.sleep(3)
        client1.send_message(bot_name, "0")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0].message
        # client2.send_message(bot_name, message)

        # Adding user 3
        client1.send_message(bot_name, "/add_user")
        time.sleep(3)
        client1.send_message(bot_name, "Elvira Espindola")
        time.sleep(3)
        client1.send_message(bot_name, "30003")
        time.sleep(3)
        client1.send_message(bot_name, "Via del Corso, 22")
        time.sleep(3)
        client1.send_message(bot_name, "0")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0].message
        # client3.send_message(bot_name, message)

        assert (len(MediaCopies.select()) == 8 and len(User.select()) == 3)
        logging.info("Test 1 is Successful")
    except AssertionError:
        logging.info("Test 1 is Failed")


@db_session
def test2():
    fast_test1()
    logging.info("Starting Test 2")
    try:
        # Deleting copy 2-1
        client1.send_message(bot_name, "/delete_copy 2-1")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, b'{"type": "deleteCopy", "argument": "2-1"}')

        # Deleting copy 2-2
        client1.send_message(bot_name, "/delete_copy 2-2")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, b'{"type": "deleteCopy", "argument": "2-2"}')

        # Deleting copy 3-1
        client1.send_message(bot_name, "/delete_copy 3-1")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, b'{"type": "deleteCopy", "argument": "3-1"}')

        # Deleting p2
        client1.send_message(bot_name, "/users")
        time.sleep(3)

        message = client1.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(client1, bot_name, message, next)
        time.sleep(3)

        message = client1.get_message_history(bot_name, limit=1).data[0]
        delete = message.reply_markup.rows[0].buttons[0].data
        press_button(client1, bot_name, message, delete)
        time.sleep(3)

        message = client1.get_message_history(bot_name, limit=1).data[0]
        delete = message.reply_markup.rows[0].buttons[0].data
        press_button(client1, bot_name, message, delete)

        assert (len(MediaCopies.select()) == 5 and len(User.select()) == 2)
        logging.info("Test 2 is Successful")
    except AssertionError:
        logging.info("Test 2 is Failed")


@db_session
def test3():
    fast_test1()
    logging.info("Starting Test 3")
    try:

        client1.send_message(bot_name, "/users")
        time.sleep(3)

        message = client1.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[0].data

        button_bytes = message.reply_markup.rows[0].buttons[0].data
        user_id = int(json.loads(button_bytes.decode('utf8').replace("'", '"'))["argument"])
        assert (
            User.exists(telegramID=user_id) and User[user_id].name == "Sergey Afonso" and User[
                user_id].phone == "30001" and
            User[user_id].faculty)
        press_button(client1, bot_name, message, next)
        time.sleep(3)

        message = client1.get_message_history(bot_name, limit=1).data[0]
        next = message.reply_markup.rows[1].buttons[1].data
        press_button(client1, bot_name, message, next)
        time.sleep(3)

        message = client1.get_message_history(bot_name, limit=1).data[0]
        button_bytes = message.reply_markup.rows[0].buttons[0].data
        user_id = int(json.loads(button_bytes.decode('utf8').replace("'", '"'))["argument"])
        assert (
            User.exists(telegramID=user_id) and User[user_id].name == "Elvira Espindola" and User[
                user_id].phone == "30003" and not User[user_id].faculty)
        press_button(client1, bot_name, message, next)
        time.sleep(3)

        logging.info("Test 3 is successful")

    except AssertionError:
        logging.info("Test 3 is failed")

@db_session
def test4():
    fast_test2()
    logging.info("Starting Test 4")
    try:
        client1.send_message(bot_name, "/users")
        time.sleep(3)

        # Getting current user's ID
        message = client1.get_message_history(bot_name, limit=1).data[0]
        button_bytes = message.reply_markup.rows[0].buttons[0].data
        user_id = int(json.loads(button_bytes.decode('utf8').replace("'", '"'))["argument"])
        assert (user_id != 1011)

        # Moving to next user
        next = message.reply_markup.rows[1].buttons[0].data
        press_button(client1, bot_name, message, next)
        time.sleep(3)

        # Getting current user's ID
        message = client1.get_message_history(bot_name, limit=1).data[0]
        button_bytes = message.reply_markup.rows[0].buttons[0].data
        user_id = int(json.loads(button_bytes.decode('utf8').replace("'", '"'))["argument"])
        assert (
        user_id != 1011 and User.exists(telegramID=user_id) and User[user_id].name == "Elvira Espindola" and User[
            user_id].phone == "30003" and not User[user_id].faculty)
        logging.info("Test 4 is Successful")
    except AssertionError:
        logging.info("Test 4 is Failed")

test4()
