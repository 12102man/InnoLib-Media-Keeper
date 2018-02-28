from telethon import TelegramClient
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
import time
import logging
import pymysql
import config
import config_test

bot_name = 'ILMKbot'
connection = pymysql.connect(host=config.db_host,
                             user=config.db_username,
                             password=config.db_password,
                             db=config.db_name,
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)
cursor = connection.cursor()

# API keys are hidden in config_test.py which is not in GitHub
# because they're personal. You can create your own ones on
# my.telegram.org

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


def flash_table():
    cursor.execute("DELETE FROM user;")
    connection.commit()
    cursor.execute("DELETE FROM mediarequest;")
    connection.commit()
    cursor.execute("DELETE FROM log;")
    connection.commit()
    cursor.execute("DELETE FROM librarian;")
    connection.commit()
    cursor.execute("DELETE FROM media;")
    connection.commit()


def test1():
    try:
        logging.info("Starting Test 1")
        client1.send_message(bot_name, "Starting Test 1")
        flash_table()
        cursor.execute("INSERT INTO user VALUES (NULL, 56069837, 'man12102', 'Mikhail', '4-418', 88005553535, 1, 0);")
        connection.commit()
        cursor.execute("INSERT INTO librarian VALUES (0, 56069837, 'Mikhail');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Book', 'War & Peace (Copy 1)', 'Leo Tolstoi', 1, 1, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Book', 'War & Peace (Copy 2)', 'Leo Tolstoi', 1, 1, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()
        cursor.execute("INSERT INTO mediacopies VALUES (1,1,1)")
        connection.commit()
        cursor.execute("INSERT INTO mediacopies VALUES (1,2,1)")
        connection.commit()

        client1.send_message(bot_name, "/medias")
        time.sleep(3)

        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "nextItem")

        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "prevItem")

        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "book")

        client1.send_message(bot_name, "/issue")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "approveBookingRequest")

        cursor.execute('SELECT * FROM log;')
        data = cursor.fetchall()
        client1.send_message(bot_name, "/log")

        if len(data) == 1:
            client1.send_message(bot_name, "Test 1 is Successful")
            logging.info("Test 1 is successful")
        else:
            client1.send_message(bot_name, "Test 1 is Failed")
            logging.info("Test 1 is Failed")
    except:
        client1.send_message(bot_name, "Test 1 is Failed")
        logging.info("Test 1 is Failed")


def test2():
    try:
        logging.info("Starting Test 2")
        client1.send_message(bot_name, "Starting Test 2")
        flash_table()
        cursor.execute("INSERT INTO user VALUES (NULL, 56069837, 'man12102', 'Mikhail', '4-418', 88005553535, 1, 0);")
        connection.commit()
        cursor.execute("INSERT INTO librarian VALUES (0, 56069837, 'Mikhail');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Book', 'War & Peace (Copy 1)', 'Leo Tolstoi', 1, 0, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Book', 'War & Peace (Copy 2)', 'Leo Tolstoi', 0, 0, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()

        client1.send_message(bot_name, "/medias")
        time.sleep(3)

        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "nextItem")

        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "book")

        cursor.execute('SELECT * FROM log;')
        line = cursor.fetchone()

        if line == None:
            client1.send_message(bot_name, "Test 2 is Successful")
            logging.info("Test 2 is successful")
        else:
            client1.send_message(bot_name, "Test 2 is Failed")
            logging.info("Test 2 is Failed")
    except:
        client1.send_message(bot_name, "Test 2 is Failed")
        logging.info("Test 2 is Failed")


def test3():
    try:
        logging.info("Starting Test 3")
        client1.send_message(bot_name, "Starting Test 3")
        flash_table()
        cursor.execute("INSERT INTO user VALUES (NULL, 56069837, 'man12102', 'Mikhail', '4-418', 88005553535, 1, 0);")
        connection.commit()
        cursor.execute("INSERT INTO user VALUES (NULL, 12345678, 'tester', 'tester', '4-418', 88005553535, 0, 0);")
        connection.commit()
        cursor.execute("INSERT INTO librarian VALUES (0, 56069837, 'Mikhail');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Book', 'War & Peace (Copy 1)', 'Leo Tolstoi', 1, 0, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()

        client1.send_message(bot_name, "/medias")
        time.sleep(3)

        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "book")

        client1.send_message(bot_name, "/issue")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "approveBookingRequest")

        cursor.execute('SELECT * FROM log;')
        line = cursor.fetchone()
        issue = line['issuedate']
        expiry = line['expirydate']
        delta = (expiry - issue).days / 7
        client1.send_message(bot_name, " Issue date: %s, Expiry date: %s, Delta: %s" % (issue, expiry, delta))
        if delta == 4:
            client1.send_message(bot_name, "Test 3 is Successful")
            logging.info("Test 3 is successful")
        else:
            client1.send_message(bot_name, "Test 3 is Failed")
            logging.info("Test 3 is Failed")
    except:
        client1.send_message(bot_name, "Test 3 is Failed")
        logging.info("Test 3 is Failed")


def test4():
    try:
        logging.info("Starting Test 4")
        client1.send_message(bot_name, "Starting Test 4")
        flash_table()
        cursor.execute("INSERT INTO user VALUES (NULL, 56069837, 'man12102', 'Mikhail', '4-418', 88005553535, 1, 0);")
        connection.commit()
        cursor.execute("INSERT INTO user VALUES (NULL, 12345678, 'tester', 'tester', '4-418', 88005553535, 0, 0);")
        connection.commit()
        cursor.execute("INSERT INTO librarian VALUES (0, 56069837, 'Mikhail');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Book', 'War & Peace (Copy 1)', 'Leo Tolstoi', 1, 1, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()

        client1.send_message(bot_name, "/medias")
        time.sleep(3)

        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "book")

        client1.send_message(bot_name, "/issue")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "approveBookingRequest")

        cursor.execute('SELECT * FROM log;')
        line = cursor.fetchone()
        issue = line['issuedate']
        expiry = line['expirydate']
        delta = (expiry - issue).days / 7
        client1.send_message(bot_name, " Issue date: %s, Expiry date: %s, Delta: %s" % (issue, expiry, delta))
        if delta == 4:
            client1.send_message(bot_name, "Test 4 is Successful")
            logging.info("Test 4 is successful")
        else:
            client1.send_message(bot_name, "Test 4 is Failed")
            logging.info("Test 4 is Failed")
    except:
        client1.send_message(bot_name, "Test 4 is Failed")
        logging.info("Test 4 is Failed")


def test5():
    try:
        logging.info("Starting Test 5")
        client1.send_message(bot_name, "Starting Test 5")
        client2.send_message(bot_name, "Starting Test 5")
        client3.send_message(bot_name, "Starting Test 5")

        flash_table()
        cursor.execute(
            "INSERT INTO user VALUES (NULL, 56069837, 'man12102', 'Mikhail', '4-418', 88005553535, 0, 0);")
        connection.commit()
        cursor.execute(
            "INSERT INTO user VALUES (NULL, 239514818, 'simplearink', 'Arina', '4-418', 88005553535, 1, 0);")
        connection.commit()
        cursor.execute(
            "INSERT INTO user VALUES (NULL, 324148065, 'broccoIi_nastya', 'Maxim', '4-416', 88005553535, 1, 0);")
        connection.commit()
        cursor.execute("INSERT INTO librarian VALUES (0, 56069837, 'Mikhail');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Book', 'War & Peace (Copy 1)', 'Leo Tolstoi', 1, 1, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Book', 'War & Peace (Copy 2)', 'Leo Tolstoi', 1, 0, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()

        # User 1 books a book
        client1.send_message(bot_name, "/medias")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "book")

        # User 2 books a book
        client2.send_message(bot_name, "/medias")
        time.sleep(3)
        message = client2.get_message_history(bot_name, limit=1).data[0]
        press_button(client2, bot_name, message, "nextItem")
        message = client2.get_message_history(bot_name, limit=1).data[0]
        press_button(client2, bot_name, message, "book")

        # User 3 tries to book a book
        client3.send_message(bot_name, "/medias")
        time.sleep(3)
        message = client3.get_message_history(bot_name, limit=1).data[0]
        press_button(client3, bot_name, message, "nextItem")
        message = client3.get_message_history(bot_name, limit=1).data[0]
        press_button(client3, bot_name, message, "book")

        # Accept first request
        client1.send_message(bot_name, "/issue")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "approveBookingRequest")

        # Accept second request
        client1.send_message(bot_name, "/issue")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "approveBookingRequest")

        cursor.execute('SELECT * FROM log;')
        data = cursor.fetchall()
        client1.send_message(bot_name, "/log")
        time.sleep(2)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "nextLogItem")

        if len(data) == 2:
            client1.send_message(bot_name, "Test 5 is Successful")
            client2.send_message(bot_name, "Test 5 is Successful")
            client3.send_message(bot_name, "Test 5 is Successful")
            logging.info("Test 5 is successful")
        else:
            client1.send_message(bot_name, "Test 5 is Failed")
            client2.send_message(bot_name, "Test 5 is Failed")
            client3.send_message(bot_name, "Test 5 is Failed")
            logging.info("Test 5 is Failed")
    except:
        client1.send_message(bot_name, "Test 5 is Failed")
        client2.send_message(bot_name, "Test 5 is Failed")
        client3.send_message(bot_name, "Test 5 is Failed")
        logging.info("Test 5 is Failed")


def test7():
    try:
        logging.info("Starting Test 7")
        client1.send_message(bot_name, "Starting Test 7")
        client2.send_message(bot_name, "Starting Test 7")

        flash_table()
        cursor.execute(
            "INSERT INTO user VALUES (NULL, 56069837, 'man12102', 'Mikhail', '4-418', 88005553535, 0, 0);")
        connection.commit()
        cursor.execute(
            "INSERT INTO user VALUES (NULL, 239514818, 'simplearink', 'Arina', '4-418', 88005553535, 1, 0);")
        connection.commit()
        cursor.execute("INSERT INTO librarian VALUES (0, 56069837, 'Mikhail');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Book', 'War & Peace (Copy 1)', 'Leo Tolstoi', 1, 1, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Book', 'War & Peace (Copy 2)', 'Leo Tolstoi', 1, 0, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()

        # Book by first user
        client1.send_message(bot_name, "/medias")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "book")
        time.sleep(2)

        # Book by second user
        client2.send_message(bot_name, "/medias")
        time.sleep(3)
        message = client2.get_message_history(bot_name, limit=1).data[0]
        press_button(client2, bot_name, message, "nextItem")
        message = client2.get_message_history(bot_name, limit=1).data[0]
        press_button(client2, bot_name, message, "book")

        # Accept first request
        client1.send_message(bot_name, "/issue")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "approveBookingRequest")

        # Accept second request
        client1.send_message(bot_name, "/issue")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "approveBookingRequest")

        cursor.execute('SELECT * FROM log;')
        data = cursor.fetchall()
        client1.send_message(bot_name, "/log")
        time.sleep(2)

        if len(data) == 2:
            client1.send_message(bot_name, "Test 7 is Successful")
            logging.info("Test 7 is successful")
        else:
            client1.send_message(bot_name, "Test 7 is Failed")
            logging.info("Test 7 is Failed")
    except:
        client1.send_message(bot_name, "Test 7 is Failed")
        logging.info("Test 7 is Failed")


def test8():
    try:
        logging.info("Starting Test 8")
        client1.send_message(bot_name, "Starting Test 8")
        flash_table()
        cursor.execute(
            "INSERT INTO user VALUES (NULL, 56069837, 'man12102', 'Mikhail', '4-418', 88005553535, 0, 0);")
        connection.commit()
        cursor.execute("INSERT INTO user VALUES (NULL, 12345678, 'tester', 'tester', '4-418', 88005553535, 1, 0);")
        connection.commit()
        cursor.execute("INSERT INTO librarian VALUES (0, 56069837, 'Mikhail');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Book', 'War & Peace (Copy 1)', 'Leo Tolstoi', 1, 0, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()

        client1.send_message(bot_name, "/medias")
        time.sleep(3)

        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "book")

        client1.send_message(bot_name, "/issue")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "approveBookingRequest")

        cursor.execute('SELECT * FROM log;')
        line = cursor.fetchone()
        issue = line['issuedate']
        expiry = line['expirydate']
        delta = (expiry - issue).days / 7
        client1.send_message(bot_name, " Issue date: %s, Expiry date: %s, Delta: %s" % (issue, expiry, delta))
        if delta == 3:
            client1.send_message(bot_name, "Test 8 is Successful")
            logging.info("Test 8 is successful")
        else:
            client1.send_message(bot_name, "Test 8 is Failed")
            logging.info("Test 8 is Failed")
    except:
        client1.send_message(bot_name, "Test 8 is Failed")
        logging.info("Test 8 is Failed")


def test9():
    try:
        logging.info("Starting Test 9")
        client1.send_message(bot_name, "Starting Test 9")
        flash_table()
        cursor.execute(
            "INSERT INTO user VALUES (NULL, 56069837, 'man12102', 'Mikhail', '4-418', 88005553535, 0, 0);")
        connection.commit()
        cursor.execute("INSERT INTO user VALUES (NULL, 12345678, 'tester', 'tester', '4-418', 88005553535, 1, 0);")
        connection.commit()
        cursor.execute("INSERT INTO librarian VALUES (0, 56069837, 'Mikhail');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Book', 'War & Peace (Copy 1)', 'Leo Tolstoi', 1, 1, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()

        client1.send_message(bot_name, "/medias")
        time.sleep(3)

        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "book")

        client1.send_message(bot_name, "/issue")
        time.sleep(3)
        message = client1.get_message_history(bot_name, limit=1).data[0]
        press_button(client1, bot_name, message, "approveBookingRequest")

        cursor.execute('SELECT * FROM log;')
        line = cursor.fetchone()
        issue = line['issuedate']
        expiry = line['expirydate']
        delta = (expiry - issue).days / 7
        client1.send_message(bot_name, " Issue date: %s, Expiry date: %s, Delta: %s" % (issue, expiry, delta))
        if delta == 2:
            client1.send_message(bot_name, "Test 9 is Successful")
            logging.info("Test 9 is successful")
        else:
            client1.send_message(bot_name, "Test 9 is Failed")
            logging.info("Test 9 is Failed")
    except:
        client1.send_message(bot_name, "Test 9 is Failed")
        logging.info("Test 9 is Failed")


def test10():
    try:
        logging.info("Starting Test 10")
        client1.send_message(bot_name, "Starting Test 10")
        flash_table()
        cursor.execute(
            "INSERT INTO user VALUES (NULL, 56069837, 'man12102', 'Mikhail', '4-418', 88005553535, 1, 0);")
        connection.commit()
        cursor.execute("INSERT INTO librarian VALUES (0, 56069837, 'Mikhail');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Book', 'War & Peace (Copy 1)', 'Leo Tolstoi', 1, 1, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()
        cursor.execute(
            "INSERT INTO media VALUES (NULL, 'Reference book', 'Innopolis Map (15th century)', 'Nikolay Nikiforov', 0, 1, 0, 100, 100, 'null', 'Very Big Publisher');")
        connection.commit()

        # Ask for book A
        client1.send_message(bot_name, "/medias")
        time.sleep(3)
        message = update_message(client1)
        press_button(client1, bot_name, message, "book")

        # Ask for book B
        client1.send_message(bot_name, "/medias")
        time.sleep(3)
        message = update_message(client1)

        press_button(client1, bot_name, message, "nextItem")  # Move to the next book
        message = update_message(client1)
        press_button(client1, bot_name, message, "book")  # Book a reference book

        # Approve request for book A
        client1.send_message(bot_name, "/issue")
        time.sleep(3)
        message = update_message(client1)
        press_button(client1, bot_name, message, "approveBookingRequest")

        cursor.execute('SELECT * FROM log;')
        log = cursor.fetchall()

        cursor.execute("SELECT * FROM media WHERE title = 'War & Peace (Copy 1)';")
        mediaID = cursor.fetchone()['mediaID']
        if len(log) == 1 and log[0]['mediaID'] == mediaID:
            client1.send_message(bot_name, "Test 10 is Successful")
            logging.info("Test 10 is successful")
        else:
            client1.send_message(bot_name, "Test 10 is Failed")
            logging.info("Test 10 is Failed")
    except:
        client1.send_message(bot_name, "Test 10 is Failed")
        logging.info("Test 10 is Failed")


test1()
test2()
test3()
test4()
test5()
test7()
test8()
test9()
test10()
