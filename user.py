import pymysql
import config
import logging
"""
Connection to database. Configuration values 
are hidden in config.py 
"""
connection = pymysql.connect(host=config.db_host,
                             user=config.db_username,
                             password=config.db_password,
                             db=config.db_name,
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)
cursor = connection.cursor()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

"""
Class Patron:
    - makes user interaction easier;
    - holds user's values;
    - allows to work with database (get/set values)
"""


class Patron:
    def __init__(self):
        self.__requestid = 0
        self.__libid = 0
        self.__telegramid = 0
        self.__alias = 0
        self.__address = 0
        self.__name = 0
        self.__phone = 0
        self.__faculty = 0
        self.__balance = 0

    """
    set_user(self, json_line)

    Function parses the JSON-line record from MySQL
    database into class attributes. All attributes
    are private.
    """

    def set_user(self, json_line):
        self.__libid = json_line["libID"]
        self.__telegramid = json_line["telegramID"]
        self.__alias = json_line["alias"]
        self.__name = json_line["name"]
        self.__address = json_line["address"]
        self.__phone = json_line["phone"]
        self.__faculty = json_line["facultymember"]
        self.__balance = json_line["balance"]

    """
    set_request(self, json_line)

    Function parses the JSON-line record from MySQL 
    database into class attributes. Request has another
    attributes, not like User. All attributes 
    are private.
    """

    def set_request(self, json_line):
        self.__requestid = json_line["requestID"]
        self.__telegramid = json_line["telegramID"]
        self.__alias = json_line["alias"]
        self.__name = json_line["name"]
        self.__address = json_line["address"]
        self.__phone = json_line["phone"]
        self.__faculty = json_line["facultymember"]

    """ Getters """

    def get_lib_id(self):
        return self.__libid

    def get_request_id(self):
        return self.__requestid

    def get_telegram_id(self):
        return self.__telegramid

    def get_alias(self):
        return self.__alias

    def get_name(self):
        return self.__name

    def get_address(self):
        return self.__address

    def get_phone(self):
        return self.__phone

    def get_balance(self):
        return self.__balance

    def get_status(self):
        return self.__faculty

    """ Setters """

    def set_alias(self, alias):
        self.__alias = alias

    def set_telegram_id(self, tele_id):
        self.__telegramid = tele_id

    def set_library_id(self, lib_id):
        self.__libid = lib_id

    def set_balance(self, balance):
        self.__balance = balance

    def set_name(self, name):
        self.__name = name

    def set_address(self, address):
        self.__address = address

    def set_phone(self, phone):
        self.__phone = phone

    def set_faculty(self, faculty):
        self.__faculty = faculty

    def pay_fine(self):
        self.__balance -= 100

    """
        Database functions.
        They work with database
    """

    """
    insert_in_base(self)
    
    Inserts user into database. 
    Used for moving request to user
    """

    def insert_in_base(self):
        query = """INSERT INTO user VALUES (null, %s, '%s', '%s', '%s', %s, %s, %s);""" % (self.__telegramid,
                                                                                           self.__alias,
                                                                                           self.__name,
                                                                                           self.__address,
                                                                                           self.__phone,
                                                                                           self.__faculty,
                                                                                           self.__balance)
        cursor.execute(query)
        connection.commit()

    """
    update(self)
    
    Updates user info. If user attributes are changed,
    they need to be uploaded to the database.
    """

    def update(self):
        query = """UPDATE user SET balance = %s,  address = '%s', 
phone = %s, name = '%s', facultymember = %s where telegramid = %s;""" % (self.__balance,
                                                                         self.__address,
                                                                         self.__phone,
                                                                         self.__name,
                                                                         self.__faculty,
                                                                         self.__telegramid)

        cursor.execute(query)
        connection.commit()

    """
    add_request(self)
    
    Adds formed request to a specific request table.
    """

    def add_request(self):
        query = """INSERT INTO request VALUES (null, %s, '%s', '%s', '%s', %s, %s);""" % (self.__telegramid,
                                                                                          self.__alias,
                                                                                          self.__name,
                                                                                          self.__address,
                                                                                          self.__phone,
                                                                                          self.__faculty)
        cursor.execute(query)
        connection.commit()

    """
    make_media_request(self, media_id)
    
    Adds request for taking media from library.
    """

    def make_media_request(self, media_id):
        sql = "INSERT INTO mediarequest VALUES (%s, %s);" % (self.__libid, media_id)
        cursor.execute(sql)
        connection.commit()

    """
    find(self, telegram_id)
      
    Finds current user in table using telegram id and creates an object of this user.
    """

    def find(self, telegram_id):
        connection.connect()
        sql = "SELECT * from user WHERE telegramID = %s;" % telegram_id
        cursor.execute(sql)
        found_data = cursor.fetchall()
        if len(found_data) == 0:
            raise FileNotFoundError("User not found")
        else:
            self.set_user(found_data[0])


    def exists(self, tele_id):
        sql = "SELECT * from user WHERE telegramID = %s;" % tele_id
        cursor.execute(sql)
        found_data = cursor.fetchall()
        if len(found_data) == 0:
            return False
        else:
            return True


"""
Class ItemCard:
    - makes media interaction easier;
    - holds media's values;
    - allows to work with database (get/set values)
"""


class ItemCard:
    def __init__(self):
        self.__mediaid = 0
        self.__type = 0
        self.__title = 0
        self.__type = 0
        self.__authors = 0
        self.__availability = 0
        self.__bestseller = 0
        self.__copy = 0
        self.__fine = 0
        self.__cost = 0

    """
    set_item(self, json_line)

    Function parses the JSON-line record from MySQL
    database into class attributes. All attributes
    are private.
    """

    def set_item(self, json_line):
        self.__mediaid = json_line["mediaID"]
        self.__type = json_line["type"]
        self.__title = json_line["title"]
        self.__authors = json_line["authors"]
        self.__availability = json_line["availability"]
        self.__bestseller = json_line["bestseller"]
        self.__copy = json_line["copy"]
        self.__fine = json_line["fine"]
        self.__cost = json_line["cost"]

    """ Getters """

    def get_media_id(self):
        return self.__mediaid

    def get_type(self):
        return self.__type

    def get_title(self):
        return self.__title

    def get_authors(self):
        return self.__authors

    def get_availability(self):
        return self.__availability

    def get_bestseller(self):
        return self.__bestseller

    """ Setters """

    def set_availability(self):
        sql = "SELECT * FROM mediarequest WHERE libID = %s;" % self.__mediaid
        cursor.execute(sql)
        selection = cursor.fetchall()
        if len(selection) == 0:
            self.__availability = 0
        else:
            self.__availability = 1

    def set_type(self, type_of_doc):
        self.__type = type_of_doc

    def set_title(self, title):
        self.__title = title

    """
    update(self)
    
    Updates media info. If user attributes are changed,
    they need to be uploaded to the database.
    """

    def update(self):
        if self.exists(media_id=self.__mediaid):
            query = """UPDATE media SET type = '%s', title = '%s', authors = '%s', 
availability = %s, bestseller = %s where mediaid = %s;""" % (self.__type,
                                                             self.__title,
                                                             self.__authors,
                                                             self.__availability,
                                                             self.__bestseller,
                                                             self.__mediaid)
            cursor.execute(query)
            connection.commit()
        else:
            raise ModuleNotFoundError

    """
    find(self, media_id)

    Finds current media in table using media id and creates an object of this media item.
    """

    def find(self, media_id):
        connection.connect()
        sql = "SELECT * FROM media WHERE mediaID = %s;" % media_id
        cursor.execute(sql)
        found_data = cursor.fetchall()
        if len(found_data) == 0:
            raise FileNotFoundError("Media not found")
        else:
            self.set_item(found_data[0])


    def get_list(self, table):
        connection.connect()
        sql = "SELECT * FROM %s;" % table
        cursor.execute(sql)
        res = cursor.fetchall()
        return res


    @staticmethod
    def exists(media_id):
        sql = "SELECT * FROM media WHERE mediaID = %s;" % media_id
        cursor.execute(sql)
        found_data = cursor.fetchall()
        if len(found_data) == 0:
            return False
        else:
            return True


"""
Class BookingRequest:
    - works with booking requests;
    - allows to work with database (get/set values)
"""


class BookingRequest:
    """
    def __init__ (self)

    Setting class attributes to 0
    """

    def __init__(self):
        self.__username = 0
        self.__lib_id = 0
        self.__media_id = 0
        self.__media_name = 0

    """
    set_request(self, json_line)
    
    Moves data from JSON-line database to values 
    in class attributes. 
    """

    def set_request(self, json_line):
        connection.connect()
        self.__lib_id = json_line["libID"]
        self.__media_id = json_line["mediaID"]

        cursor.execute("SELECT * FROM user WHERE libID = %s;" % self.__lib_id)
        user_data = cursor.fetchall()
        if len(user_data) == 0:
            logging.error("User not found")
            raise FileNotFoundError("User Not Found")
        else:
            record = user_data[0]
            self.__username = record["name"] + " (%s)" % record["alias"]

        cursor.execute("SELECT * FROM media WHERE mediaID = %s;" % self.__media_id)
        media_data = cursor.fetchall()
        if len(media_data) == 0:
            logging.error("Media not found")
            raise FileNotFoundError("Media Not Found")
        else:
            record = media_data[0]
            self.__media_name = """\"%s\"""" % record["title"]

    """ Getters """

    def get_username(self):
        return self.__username

    def get_media_name(self):
        return self.__media_name

    def get_lib_id(self):
        return self.__lib_id

    def get_media_id(self):
        return self.__media_id


class log:
    """
    def __init__ (self)

    Setting class attributes to 0
    """

    def __init__(self):
        self.__lib_id = 0
        self.__media_id = 0
        self.__issue_date = 0
        self.__expiry_date = 0
        self.__returned = 0
        self.__renewed = 0

    def set_log(self, json_line):


    def get_lib_id(self):
        return self.__lib_id

    def get_media_id(self):
        return self.__media_id

    def get_issue_date(self):
        return self.__issue_date

    def get_expiry_date(self):
        return self.__expiry_date

    def is_returned(self):
        return self.__returned

    def is_renewed(self):
        return self.__renewed

