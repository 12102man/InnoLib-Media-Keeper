from telethon import TelegramClient
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
import time
from pony.orm import *
import logging
import Config.config as config
import Config.config_test as config_test
from Core.database import *

bot_name = 'ILMKbot'
# MySQL
db = Database()

db.bind(provider='mysql', host=config.db_host, user=config.db_username, passwd=config.db_password, db=config.db_name)
db.generate_mapping(create_tables=True)
sql_debug(True)

# API keys are hidden in config_test.py which is not in GitHub
# because they're personal. You can create your own ones on
# my.telegram.org

"""
api_id_1 = config_test.api_id_1
api_hash_1 = config_test.api_hash_1
client1 = TelegramClient('session_name', api_id_1, api_hash_1)
client1_telegram_ID = config_test.client1_telegram_ID
client1.start()

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


def flush_db():
    global db
    db.drop_table('images', with_all_data=True)
    db.drop_table('librarian', with_all_data=True)
    db.drop_table('librarianenrollment', with_all_data=True)
    db.drop_table('log', with_all_data=True)
    db.drop_table('media', with_all_data=True)
    db.drop_table('mediacopies', with_all_data=True)
    db.drop_table('mediarequest', with_all_data=True)
    db.drop_table('registrysession', with_all_data=True)
    db.drop_table('request', with_all_data=True)
    db.drop_table('returnrequest', with_all_data=True)
    db.drop_table('user', with_all_data=True)

    db = Database()
    db.bind(provider='mysql', host=config.db_host, user=config.db_username, passwd=config.db_password,
            db=config.db_name)
    db.generate_mapping(create_tables=True)


@db_session
def test1():
    logging.info("Starting Test 1")

    # client1.send_message(bot_name, "Starting Test 1")
    Media(mediaID=1, name="Introduction to Algorithms (Third Edition), 2009", type="Book",
          authors="Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest and Clifford Stein", publisher="MIT Press",
          availability=True, bestseller=True, fine=100, cost=1000)
    MediaCopies(mediaID=1, copyID="1-1", available=True)
    commit()


def drop():
    global db
    db.drop_all_tables()


def tear_down():
    db.drop_all_tables(with_all_data=True)


tear_down()

