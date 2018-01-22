import json

class Patron:
    def getLibID(self):
        try:
            return self.__libID
        except:
            return 0

    def setUser(self, jsonLine):
        self.__libID = jsonLine["libID"]
        self.__telegramID = jsonLine["telegramID"]
        self.__alias = jsonLine["alias"]
        self.__name = jsonLine["name"]
        self.__address = jsonLine["address"]
        self.__phone = jsonLine["phone"]
        self.__faculty = jsonLine["facultymember"]
        self.__medias = jsonLine["medias"]
        self.__balance = jsonLine["balance"]

    def setRequest(self, jsonLine):
        self.__requestID = jsonLine["requestID"]
        self.__telegramID = jsonLine["telegramID"]
        self.__alias = jsonLine["alias"]
        self.__name = jsonLine["name"]
        self.__address = jsonLine["address"]
        self.__phone = jsonLine["phone"]
        self.__faculty = jsonLine["facultymember"]


    """ Getters """
    def getRequestID(self):
        return self.__requestID
    def getTelegramID(self):
        return self.__telegramID
    def getAlias(self):
        return self.__alias
    def getName(self):
        return self.__name
    def getAddress(self):
        return self.__address
    def getPhone(self):
        return self.__phone
    def getMedias(self):
        return self.__medias
    def getBalance(self):
        return self.__balance
    def getStatus(self):
        return self.__faculty

    def initialize(self):
        self.__medias = []
        self.__balance = 0

    """ Setters """
    def setAlias(self, alias):
        self.__alias = alias
    def setTelegramID(self, id):
        self.__telegramID = id
    def setLibraryID(self, id):
        self.__libID = id
    def setBalance(self, balance):
        self.__balance = balance
    def setName(self, name):
        self.__name = name
    def setAddress(self, address):
        self.__address = address
    def setPhone(self, phone):
        self.__phone = phone
    def setFaculty(self, faculty):
        self.__faculty = faculty


    def payFine(self):
        self.__balance -= 100

    def insertInBase(self):
        try:
            query = """INSERT INTO user VALUES (null, %s, '%s', '%s', '%s', %s, %s, %s, '%s');""" % ( self.__telegramID, self.__alias, self.__name, self.__address,self.__phone, self.__faculty, self.__balance,  self.__medias)
            return query
        except:
            raise NameError('ERROR INSERTING IN DB')

    def update(self):
        try:
            query = """UPDATE user SET balance = %s, medias = '%s', address = '%s', phone = %s, name = '%s', facultymember = %s where telegramID = %s;""" % (self.__balance, self.__medias, self.__address, self.__phone, self.__name, self.__faculty, self.__telegramID)
            return query
        except:
            raise NameError('ERROR UPDATING')

    def addRequest(self):
        query = """INSERT INTO request VALUES (null, %s, '%s', '%s', '%s', %s, %s, 0);""" % (self.__telegramID, self.__alias, self.__name, self.__address,self.__phone, self.__faculty)
        return query


    def deleteMedia(self, mediaID):
        json_str = self.__medias
        mediaID = str(mediaID)
        data = json.loads(json_str)
        if mediaID in data:
            del data[data.index(mediaID)]
            self.__medias = str(data).replace("'", "\"")
        else:
            raise NameError('MEDIA IS NOT FOUND')

    def addMedia(self, mediaID):
        json_str = self.__medias
        data = json.loads(json_str)
        mediaID = str(mediaID)
        if not mediaID in data:
            update = '%s' % (mediaID)
            data.append(update)
            print(data)
            self.__medias = str(data).replace("'", "\"")
        else:
            raise NameError('MEDIA ALREADY EXISTS')







class ItemCard:

    def setItem(self, jsonLine):
        self.__mediaID = jsonLine["mediaID"]
        self.__type = jsonLine["type"]
        self.__title = jsonLine["title"]
        self.__authors = jsonLine["authors"]
        self.__availability = jsonLine["availability"]
        self.__bestseller = jsonLine["bestseller"]
        self.__copy = jsonLine["copy"]
        self.__parentchild = jsonLine["parentchild"]
        self.__fine = jsonLine["fine"]
        self.__cost = jsonLine["cost"]



