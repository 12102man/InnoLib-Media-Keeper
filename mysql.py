
import pymysql
from user import Patron


connection = pymysql.connect(host='37.46.132.57',
                             user='telebot',
                             password='Malinka2017',
                             db='lmstelebot',
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)

sql = "SELECT * FROM request;"

cursor = connection.cursor()
cursor.execute(sql)

result = cursor.fetchall()
test = Patron()
print(result[0])
test.setRequest(result[0])



