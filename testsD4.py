from database import *
import time
from search_engine import *

template_test8 = """DAY MONTH YEAR | Admin 1 has added librarian #1
DAY MONTH YEAR | Admin 1 has added librarian #2
DAY MONTH YEAR | Admin 1 has added librarian #3
DAY MONTH YEAR | Librarian#2 has added media #1
DAY MONTH YEAR | Librarian#2 has added copy of media #1
DAY MONTH YEAR | Librarian#2 has added copy of media #1
DAY MONTH YEAR | Librarian#2 has added copy of media #1
DAY MONTH YEAR | Librarian#2 has added media #2
DAY MONTH YEAR | Librarian#2 has added copy of media #2
DAY MONTH YEAR | Librarian#2 has added copy of media #2
DAY MONTH YEAR | Librarian#2 has added copy of media #2
DAY MONTH YEAR | Librarian#2 has added media #3
DAY MONTH YEAR | Librarian#2 has added copy of media #3
DAY MONTH YEAR | Librarian#2 has added copy of media #3
DAY MONTH YEAR | Librarian#2 has added copy of media #3
DAY MONTH YEAR | Librarian#2 has added user #1010
DAY MONTH YEAR | Librarian#2 has added user #1011
DAY MONTH YEAR | Librarian#2 has added user #1100
DAY MONTH YEAR | Librarian#2 has added user #1101
DAY MONTH YEAR | Librarian#2 has added user #1110
DAY MONTH YEAR | User#1010 has booked media #3-1
DAY MONTH YEAR | User#1011 has booked media #3-2
DAY MONTH YEAR | User#1101 has booked media #3-3
DAY MONTH YEAR | User#1110 got in queue for media #3
DAY MONTH YEAR | User#1100 got in queue for media #3
DAY MONTH YEAR | Librarian#1 has placed an outstanding request for media #Media[3]
DAY MONTH YEAR | Outstanding Request of Librarian#1 for media #Media[3]has been denied"""

template_test9 = """DAY MONTH YEAR | Admin 1 has added librarian #1
DAY MONTH YEAR | Admin 1 has added librarian #2
DAY MONTH YEAR | Admin 1 has added librarian #3
DAY MONTH YEAR | Librarian#2 has added media #1
DAY MONTH YEAR | Librarian#2 has added copy of media #1
DAY MONTH YEAR | Librarian#2 has added copy of media #1
DAY MONTH YEAR | Librarian#2 has added copy of media #1
DAY MONTH YEAR | Librarian#2 has added media #2
DAY MONTH YEAR | Librarian#2 has added copy of media #2
DAY MONTH YEAR | Librarian#2 has added copy of media #2
DAY MONTH YEAR | Librarian#2 has added copy of media #2
DAY MONTH YEAR | Librarian#2 has added media #3
DAY MONTH YEAR | Librarian#2 has added copy of media #3
DAY MONTH YEAR | Librarian#2 has added copy of media #3
DAY MONTH YEAR | Librarian#2 has added copy of media #3
DAY MONTH YEAR | Librarian#2 has added user #1010
DAY MONTH YEAR | Librarian#2 has added user #1011
DAY MONTH YEAR | Librarian#2 has added user #1100
DAY MONTH YEAR | Librarian#2 has added user #1101
DAY MONTH YEAR | Librarian#2 has added user #1110
DAY MONTH YEAR | User#1010 has booked media #3-1
DAY MONTH YEAR | User#1011 has booked media #3-2
DAY MONTH YEAR | User#1101 has booked media #3-3
DAY MONTH YEAR | User#1110 got in queue for media #3
DAY MONTH YEAR | User#1100 got in queue for media #3
DAY MONTH YEAR | Librarian#3 has placed an outstanding request for media #3
DAY MONTH YEAR | [OR] Queue for media #3 has been deleted
DAY MONTH YEAR | [OR] Holders 1010 (with media #3-1), 1011 (with media #3-2), 1101 (with media #3-3), have been notified about Outstanding Request
DAY MONTH YEAR | [OR] Queue participants User[1100], User[1110], have been notified about Outstanding Request
"""


@db_session
def flush_db():
    for elem in Media.select():
        elem.delete()
    for elem in LibrarianEnrollment.select():
        elem.delete()
    for elem in Librarian.select():
        elem.delete()
    for elem in Log.select():
        elem.delete()
    for elem in MediaCopies.select():
        elem.delete()
    for elem in MediaRequest.select():
        elem.delete()
    for elem in Request.select():
        elem.delete()
    for elem in Admin.select():
        elem.delete()
    for elem in Actions.select():
        elem.delete()
    for elem in ReturnRequest.select():
        elem.delete()
    for elem in User.select():
        elem.delete()
    for elem in RegistrySession.select():
        elem.delete()
    Admin(id=1, telegram_id=1, new_lib_id=0)
    commit()


@db_session
def test1():
    """If admin already exists, FileExistsError is raised"""
    try:
        flush_db()
        Admin(telegram_id=2, new_lib_id=0)
    except FileExistsError:
        pass


@db_session
def test2():
    flush_db()
    """ Librarians are created from Users """
    user1 = User(telegramID=1, name="Lib1", alias="@", phone="0", address="0",
                 priority=1)
    user2 = User(telegramID=2, name="Lib2", alias="@", phone="0", address="0",
                 priority=1)
    user3 = User(telegramID=3, name="Lib3", alias="@", phone="0", address="0",
                 priority=1)
    admin = Admin[1]
    admin.new_lib_id = 1
    admin.add_new_librarian()
    admin.set_privilege('edit')
    admin.new_lib_id = 2
    admin.add_new_librarian()
    admin.set_privilege('add')
    admin.new_lib_id = 3
    admin.add_new_librarian()
    admin.set_privilege('delete')

    user1.delete()
    user2.delete()
    user3.delete()

    assert len(list(Librarian.select())) == 3


@db_session
def test3():
    test2()
    lib1 = Librarian[1]
    lib2 = Librarian[2]
    lib3 = Librarian[3]

    # Trying to add d1 and 3 copies
    assert -1 == lib1.__add_media__(
        {'id': 1, 'name': "Introduction to algorithms (Third edition), 2009", 'type': "Book",
         'authors': "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest and Clifford Stein",
         'publisher': "MIT Press", 'cost': 5000, 'fine': 100, 'availability': 1,
         'bestseller': 0, 'keywords': 'Algorithms, Data Structures, Complexity, Computational Theory'})
    assert -1 == lib1.add_copy(1)
    assert -1 == lib1.add_copy(1)
    assert -1 == lib1.add_copy(1)

    # Trying to add d2 and 3 copies
    assert -1 == lib1.__add_media__(
        {'id': 2, 'name': "Algorithms + Data Structures = Programs (First edition), 1978",
         'type': "Book",
         'authors': "Niklaus Wirth",
         'publisher': "Prentice Hall PTR", 'cost': 5000, 'fine': 100, 'availability': 1, 'bestseller': 0,
         'keywords': 'Algorithms, Data Structures, Search Algorithms, Pascal'})
    assert -1 == lib1.add_copy(2)
    assert -1 == lib1.add_copy(2)
    assert -1 == lib1.add_copy(2)

    # Trying to add d3 and 3 copies
    assert -1 == lib1.__add_media__(
        {'id': 3, 'name': "The Art of Computer Programming (Third edition), 1997",
         'type': "Book",
         'authors': "Donald E. Knuth",
         'publisher': "Addison Wesley Longman Publishing Co., Inc.", 'cost': 5000, 'fine': 100, 'availability': 1,
         'bestseller': 0, 'keywords': 'Algorithms, Data Structures, Search Algorithms, Pascal'})
    assert -1 == lib1.add_copy(3)
    assert -1 == lib1.add_copy(3)
    assert -1 == lib1.add_copy(3)


@db_session
def test4():
    test2()
    lib1 = Librarian[1]
    lib2 = Librarian[2]
    lib3 = Librarian[3]

    # Trying to add d1 and 3 copies
    assert 1 == lib2.__add_media__(
        {'id': 1, 'name': "Introduction to algorithms (Third edition), 2009", 'type': "Book",
         'authors': "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest and Clifford Stein",
         'publisher': "MIT Press", 'cost': 5000, 'fine': 100, 'availability': 1,
         'bestseller': 0, 'keywords': 'Algorithms, Data Structures, Complexity, Computational Theory'})
    assert 1 == lib2.add_copy(1)
    assert 1 == lib2.add_copy(1)
    assert 1 == lib2.add_copy(1)

    # Trying to add d2 and 3 copies
    assert 1 == lib2.__add_media__(
        {'id': 2, 'name': "Algorithms + Data Structures = Programs (First edition), 1978",
         'type': "Book",
         'authors': "Niklaus Wirth",
         'publisher': "Prentice Hall PTR", 'cost': 5000, 'fine': 100, 'availability': 1, 'bestseller': 0,
         'keywords': 'Algorithms, Data Structures, Search Algorithms, Pascal'})
    assert 1 == lib2.add_copy(2)
    assert 1 == lib2.add_copy(2)
    assert 1 == lib2.add_copy(2)

    # Trying to add d3 and 3 copies
    assert 1 == lib2.__add_media__(
        {'id': 3, 'name': "The Art of Computer Programming (Third edition), 1997",
         'type': "Book",
         'authors': "Donald E. Knuth",
         'publisher': "Addison Wesley Longman Publishing Co., Inc.", 'cost': 5000, 'fine': 100, 'availability': 1,
         'bestseller': 0, 'keywords': 'Algorithms, Data Structures, Search Algorithms, Pascal'})
    assert 1 == lib2.add_copy(3)
    assert 1 == lib2.add_copy(3)
    assert 1 == lib2.add_copy(3)

    # Adding users
    assert 1 == lib2.__add_user__({'telegramID': 1010, 'name': "Sergey Afonso", 'alias': "@sergei", 'phone': "30001",
                                   'address': "Via Margutta, 3",
                                   'priority': 1})
    assert 1 == lib2.__add_user__(
        {'telegramID': 1011, 'name': "Nadia Teixeira", 'alias': "@nadia", 'phone': "30002", 'address': "Via Sacra, 13",
         'priority': 1})
    assert 1 == lib2.__add_user__(
        {'telegramID': 1100, 'name': "Elvira Espindola", 'alias': "@elvira", 'phone': "30003",
         'address': "Via del Corso, 22",
         'priority': 1})
    assert 1 == lib2.__add_user__(
        {'telegramID': 1101, 'name': "Andrey Velo", 'alias': "@andrei", 'phone': "30004",
         'address': "Avenida Mazatlan 250",
         'priority': 5})
    assert 1 == lib2.__add_user__(
        {'telegramID': 1110, 'name': "Veronika Rama", 'alias': "@veronica", 'phone': "30005",
         'address': "Stret Atocha, 27",
         'priority': 2})

    assert User.get(telegramID=1010) is not None
    assert User.get(telegramID=1011) is not None
    assert User.get(telegramID=1100) is not None
    assert User.get(telegramID=1101) is not None
    assert User.get(telegramID=1110) is not None


@db_session
def test5():
    test4()
    lib3 = Librarian[3]
    assert 1 == lib3.delete_copy('3-1')
    assert len(list(Media[3].copies)) == 2


@db_session
def test6():
    test4()
    l1 = Librarian[1]
    p1 = User[1010]
    p2 = User[1011]
    p3 = User[1100]
    s = User[1101]
    v = User[1110]
    today = datetime.datetime(2018, 4, 25, 12, 0, 0)
    p1.book_media(Media[3], today)
    p2.book_media(Media[3], today)
    s.book_media(Media[3], today)
    v.book_media(Media[3], today)
    p3.book_media(Media[3], today)

    l1_status = l1.outstanding_request(Media[3], today)

    assert l1_status[0] == -1


@db_session
def test7():
    test4()
    l3 = Librarian[3]
    p1 = User[1010]
    p2 = User[1011]
    p3 = User[1100]
    s = User[1101]
    v = User[1110]
    today = datetime.datetime(2018, 4, 25, 12, 0, 0)
    p1.book_media(Media[3], today)
    p2.book_media(Media[3], today)
    s.book_media(Media[3], today)
    v.book_media(Media[3], today)
    p3.book_media(Media[3], today)

    status, queue, raw_holders = l3.outstanding_request(3, today)
    holders = [User[int(e[0])] for e in raw_holders]

    assert (status == 1)
    assert (len(Media[3].queue) == 0)
    assert p1 in holders
    assert p2 in holders
    assert s in holders

    assert v in queue
    assert p3 in queue


@db_session
def test8():
    test6()
    list(Actions.select())[0].generate_file()
    today = datetime.datetime.now()
    a = open('actions.txt', 'r').read().strip()
    b = template_test8.strip()

    # Replace today date in template
    b = b.replace("DAY", today.strftime("%d")).replace("MONTH", today.strftime("%b")).replace("YEAR",
                                                                                              today.strftime("%Y"))
    assert a == b


@db_session
def test9():
    flush_db()
    test7()
    today = datetime.datetime.now()
    list(Actions.select())[0].generate_file()
    a = open('actions.txt', 'r').read().strip()
    b = template_test9.strip()

    # Replace today date in template
    b = b.replace("DAY", today.strftime("%d"))
    b = b.replace("MONTH", today.strftime("%b"))
    b = b.replace("YEAR", today.strftime("%Y")).strip()

    a = a.strip().replace("\n", " ").strip()
    b = b.strip().replace("\n", " ").strip()

    test = a == b
    assert test


@db_session
def test10():
    test4()
    m1 = Media[1]
    v = User[1110]
    search_results = v.search('name', 'Introduction to Algorithms')

    assert len(search_results) == 1
    assert m1 in search_results


@db_session
def test11():
    test4()
    m1 = Media[1]
    m2 = Media[2]
    v = User[1110]
    search_results = v.search('name', 'Algorithms')
    assert len(search_results) == 2
    assert m1 in search_results
    assert m2 in search_results


@db_session
def test12():
    test4()
    m1 = Media[1]
    m2 = Media[2]
    m3 = Media[3]
    v = User[1110]
    search_results = v.search('keywords', 'Algorithms')
    assert len(search_results) == 3
    assert m1 in search_results
    assert m2 in search_results
    assert m3 in search_results


@db_session
def test13():
    test4()
    v = User[1110]
    search_results = v.search('name', 'Algorithms AND Programming')
    assert len(search_results) == 0


@db_session
def test14():
    test4()
    lib2 = Librarian[2]
    m1 = Media[1]
    m2 = Media[2]
    m3 = Media[3]
    v = User[1110]
    search_results = v.search('name', 'Algorithms OR Programming')
    assert len(search_results) == 3
    assert m1 in search_results
    assert m2 in search_results
    assert m3 in search_results

    flush_db()
    Admin.select().delete()
    Admin(telegram_id=157723117)  # Alexander's ID


if __name__ == "__main__":

    tests_array = [test1, test2, test3, test4, test5, test6, test7, test8, test9, test10, test11, test12, test13,
                   test14]
    print("Starting test suite...")
    for i in range(0, len(tests_array)):
        try:
            tests_array[i]()
            print("Test %d OK" % (i + 1))
        except (AssertionError, TypeError) as e:
            print(("Test %d FAIL \nError: " + str(e)) % (i + 1))
            break
    print("Test suite is over!")
