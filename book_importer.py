import pymysql
import json
import config
import random

""" MySQL connection """
connection = pymysql.connect(host=config.db_host,
                             user=config.db_username,
                             password=config.db_password,
                             db=config.db_name,
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)
cursor = connection.cursor()

json_file = open('dataset.json')
json_data = json.load(json_file)

for item in json_data['items']:
    title = item['title'].replace("\"","")
    try:
        publisher = item['publisher']
        publisher = publisher.replace("\"","")
    except:
        publisher = "-- // --"
    price = item['price']
    try:
        authors = ', '.join(item['authors'])
    except:
        authors = "-- // --"
    type_of_media = 'Book'
    try:
        image = item['cover']
    except:
        image = ""
    availability = 1
    bestseller = random.randint(0, 1)

    sql = """INSERT INTO media VALUES (null, "%s", "%s", "%s", %s, %s,0, 100, "%s", "%s", "%s");""" % (type_of_media,
                                                                                                        title,
                                                                                                        authors,
                                                                                                        availability,
                                                                                                        bestseller,
                                                                                                        price,
                                                                                                        image,
                                                                                                        publisher)
    print(sql)
    cursor.execute(sql)
    connection.commit()
