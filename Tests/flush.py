from pony.orm import *

import config as config

db1 = Database()
db1.bind(provider='mysql', host=config.db_host, user=config.db_username, passwd=config.db_password,
         db=config.db_name)
db1.generate_mapping(create_tables=True)
db1.disconnect()

db1.drop_table('images', with_all_data=True)
db1.drop_table('librarian', with_all_data=True)
db1.drop_table('librarianenrollment', with_all_data=True)
db1.drop_table('log', with_all_data=True)
db1.drop_table('media', with_all_data=True)
db1.drop_table('mediacopies', with_all_data=True)
db1.drop_table('mediarequest', with_all_data=True)
db1.drop_table('registrysession', with_all_data=True)
db1.drop_table('request', with_all_data=True)
db1.drop_table('returnrequest', with_all_data=True)
db1.drop_table('user', with_all_data=True)

