from database import *
from button_actions import generate_expiry_date
from button_actions import set_balance


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


@db_session
def initial_state():
    flush_db()
    User(telegramID=1010, name="Sergey Afonso", alias="@sergei", phone="30001", address="Via Margutta, 3",
         priority=1)
    User(telegramID=1011, name="Nadia Teixeira", alias="@nadia", phone="30002", address="Via Sacra, 13",
         priority=1)
    User(telegramID=1100, name="Elvira Espindola", alias="@elvira", phone="30003", address="Via del Corso, 22",
         priority=1)
    User(telegramID=1101, name="Andrey Velo", alias="@andrei", phone="30004", address="Avenida Mazatlan 250",
         priority=5)
    User(telegramID=1110, name="Veronika Rama", alias="@veronica", phone="30005", address="Stret Atocha, 27",
         priority=2)

    Media(mediaID=1, name="Introduction to algorithms (Third edition), 2009", type="Book",
          authors="Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest and Clifford Stein",
          publisher="MIT Press", cost=5000, fine=100, availability=1, bestseller=0)
    Media(mediaID=2, name="Design Patterns: Elements of Reusable Object-Oriented Software (First edition), 2003",
          type="Book",
          authors="Erich Gamma, Ralph Johnson, John Vlissides, Richard Helm",
          publisher="Addison-Wesley Professional", cost=1700, fine=100, availability=1, bestseller=1)
    Media(mediaID=3, name="Null References: The Billion Dollar Mistake",
          type="AV",
          authors="Tony Hoare.",
          publisher="None", cost=1000, fine=100, availability=1, bestseller=1)

    MediaCopies(mediaID=1, copyID="1-1", available=1)
    MediaCopies(mediaID=1, copyID="1-2", available=1)
    MediaCopies(mediaID=1, copyID="1-3", available=1)
    MediaCopies(mediaID=2, copyID="2-1", available=1)
    MediaCopies(mediaID=2, copyID="2-2", available=1)
    MediaCopies(mediaID=2, copyID="2-3", available=1)
    MediaCopies(mediaID=3, copyID="3-1", available=1)
    MediaCopies(mediaID=3, copyID="3-2", available=1)


@db_session
def test1():
    initial_state()
    p1 = User[1010]
    librarian = Librarian[1]
    Log(libID=p1.telegramID, mediaID='1-1', issue_date=datetime.datetime(2018, 3, 5, 12, 0, 0),
        expiry_date=generate_expiry_date(Media[1], p1, datetime.datetime(2018, 3, 5, 12, 0, 0)), returned=False,
        renewed=False)
    Log(libID=p1.telegramID, mediaID='2-1', issue_date=datetime.datetime(2018, 3, 5, 12, 0, 0),
        expiry_date=generate_expiry_date(Media[2], p1, datetime.datetime(2018, 3, 5, 12, 0, 0)), returned=False,
        renewed=False)
    p1.return_media('1-1')
    librarian.accept_return('1-1')
    user_medias = librarian.get_user_medias(p1)

    set_balance(datetime.datetime(2018, 4, 2, 12, 0, 0))

    assert (not user_medias[0].is_expired(datetime.datetime(2018, 4, 2, 12, 0, 0)) and user_medias[0].balance == 0)


@db_session
def test2():
    initial_state()
    today = datetime.datetime(2018, 4, 2, 12, 0, 0)
    p1 = User[1010]
    s = User[1101]
    v = User[1110]
    librarian = Librarian[1]
    Log(libID=p1.telegramID, mediaID='1-1', issue_date=datetime.datetime(2018, 3, 5, 12, 0, 0),
        expiry_date=generate_expiry_date(Media[1], p1, datetime.datetime(2018, 3, 5, 12, 0, 0)), returned=False,
        renewed=False)
    Log(libID=p1.telegramID, mediaID='2-1', issue_date=datetime.datetime(2018, 3, 5, 12, 0, 0),
        expiry_date=generate_expiry_date(Media[2], p1, datetime.datetime(2018, 3, 5, 12, 0, 0)), returned=False,
        renewed=False)
    Log(libID=s.telegramID, mediaID='1-2', issue_date=datetime.datetime(2018, 3, 5, 12, 0, 0),
        expiry_date=generate_expiry_date(Media[1], s, datetime.datetime(2018, 3, 5, 12, 0, 0)), returned=False,
        renewed=False)
    Log(libID=s.telegramID, mediaID='2-2', issue_date=datetime.datetime(2018, 3, 5, 12, 0, 0),
        expiry_date=generate_expiry_date(Media[2], s, datetime.datetime(2018, 3, 5, 12, 0, 0)), returned=False,
        renewed=False)
    Log(libID=v.telegramID, mediaID='1-3', issue_date=datetime.datetime(2018, 3, 5, 12, 0, 0),
        expiry_date=generate_expiry_date(Media[1], v, datetime.datetime(2018, 3, 5, 12, 0, 0)), returned=False,
        renewed=False)
    Log(libID=v.telegramID, mediaID='2-3', issue_date=datetime.datetime(2018, 3, 5, 12, 0, 0),
        expiry_date=generate_expiry_date(Media[2], v, datetime.datetime(2018, 3, 5, 12, 0, 0)), returned=False,
        renewed=False)
    commit()

    p1_1, p1_2 = librarian.get_user_medias(p1)
    s_1, s_2 = librarian.get_user_medias(s)
    v_1, v_2 = librarian.get_user_medias(v)

    set_balance(datetime.datetime(2018, 4, 2, 12, 0, 0))

    assert (not p1_1.is_expired(today) and p1_1.balance == 0)
    assert (not p1_2.is_expired(today) and p1_2.balance == 0)

    assert (s_1.is_expired(today) and s_1.time_expired(today) == 7 and s_1.balance == 700)
    assert (s_2.is_expired(today) and s_2.time_expired(today) == 14 and s_2.balance == 1400)

    assert (v_1.is_expired(today) and v_1.time_expired(today) == 21 and v_1.balance == 2100)
    assert (v_2.is_expired(today) and v_2.time_expired(today) == 21 and v_2.balance == 1700)


@db_session
def test3():
    initial_state()
    today = datetime.datetime(2018, 4, 2, 12, 0, 0)
    p1 = User[1010]
    s = User[1101]
    v = User[1110]
    librarian = Librarian[1]

    Log(libID=p1.telegramID, mediaID='1-1', issue_date=datetime.datetime(2018, 3, 29, 12, 0, 0),
        expiry_date=generate_expiry_date(Media[1], p1, datetime.datetime(2018, 3, 29, 12, 0, 0)), returned=False,
        renewed=False)
    Log(libID=s.telegramID, mediaID='2-1', issue_date=datetime.datetime(2018, 3, 29, 12, 0, 0),
        expiry_date=generate_expiry_date(Media[2], s, datetime.datetime(2018, 3, 29, 12, 0, 0)), returned=False,
        renewed=False)
    Log(libID=v.telegramID, mediaID='2-2', issue_date=datetime.datetime(2018, 3, 29, 12, 0, 0),
        expiry_date=generate_expiry_date(Media[2], v, datetime.datetime(2018, 3, 29, 12, 0, 0)), returned=False,
        renewed=False)
    commit()
    p1.renew_copy('1-1', today)
    s.renew_copy('2-1', today)
    v.renew_copy('2-2', today)

    p1_media = librarian.get_user_medias(p1)[0]
    s_media = librarian.get_user_medias(s)[0]
    v_media = librarian.get_user_medias(v)[0]

    assert (p1_media.expiry_date == datetime.datetime(2018, 4, 30, 12, 0, 0))
    assert (s_media.expiry_date == datetime.datetime(2018, 4, 16, 12, 0, 0))
    assert (v_media.expiry_date == datetime.datetime(2018, 4, 9, 12, 0, 0))


@db_session
def test4():
    initial_state()
    march_nine = datetime.datetime(2018, 3, 29, 12, 0, 0)
    today = datetime.datetime(2018, 4, 2, 12, 0, 0)
    p1 = User[1010]
    s = User[1101]
    v = User[1110]
    librarian = Librarian[1]

    p1.book_media(Media[1], march_nine)
    s.book_media(Media[2], march_nine)
    v.book_media(Media[2], march_nine)

    librarian.outstanding_request(2, today)

    p1.renew_copy(p1.medias()[0].mediaID, today)
    s.renew_copy(s.medias()[0].mediaID, today)
    v.renew_copy(v.medias()[0].mediaID, today)

    p1_1 = librarian.get_user_medias(p1)[0]
    s_1 = librarian.get_user_medias(s)[0]
    v_1 = librarian.get_user_medias(v)[0]

    assert (p1_1.expiry_date == datetime.datetime(2018, 4, 30, 12, 0, 0))
    assert (s_1.expiry_date == today)
    assert (v_1.expiry_date == today)


@db_session
def test5():
    initial_state()
    today = datetime.datetime(2018, 4, 2, 12, 0, 0)
    p1 = User[1010]
    s = User[1101]
    v = User[1110]

    p1.book_media(Media[3], today)
    s.book_media(Media[3], today)
    v.book_media(Media[3], today)

    assert (Media[3].get_queue()[0].user == v)


@db_session
def test6():
    initial_state()
    p1 = User[1010]
    p2 = User[1011]
    p3 = User[1100]
    s = User[1101]
    v = User[1110]
    librarian = Librarian[1]
    today = datetime.datetime(2018, 4, 2, 12, 0, 0)

    p1.book_media(Media[3], today)
    p2.book_media(Media[3], today)
    s.book_media(Media[3], today)
    v.book_media(Media[3], today)
    p3.book_media(Media[3], today)

    users = [e.user for e in Media[3].get_queue()]
    assert (users == [s, v, p3])


@db_session
def test7():
    test6()
    p1 = User[1010]
    p2 = User[1011]
    p3 = User[1100]
    s = User[1101]
    v = User[1110]
    today = datetime.datetime(2018, 4, 2, 12, 0, 0)
    librarian = Librarian[1]

    status, queue, raw_holders = librarian.outstanding_request(3, today)
    holders = [User[int(e[0])] for e in raw_holders]
    assert (status == 1)
    assert (len(Media[3].queue) == 0)
    assert (queue.__contains__(s) and queue.__contains__(v) and queue.__contains__(p3))
    assert (holders.__contains__(p1) and holders.__contains__(p2))


@db_session
def test8():
    test6()
    p1 = User[1010]
    p2 = User[1011]
    p3 = User[1100]
    s = User[1101]
    v = User[1110]
    librarian = Librarian[1]
    p2.return_media(p2.medias()[0].mediaID)
    status, popped_user = librarian.accept_return(p2.medias()[0].mediaID)
    assert (status == 2)
    assert (User[popped_user] == s)
    assert (len(p2.medias()) == 0)

    queue = [e.user for e in Media[3].get_queue()]
    assert (queue.__contains__(v) and queue.__contains__(p3))


@db_session
def test9():
    test6()
    today = datetime.datetime(2018, 4, 2, 12, 0, 0)
    p1 = User[1010]
    p3 = User[1100]
    s = User[1101]
    v = User[1110]
    commit()
    librarian = Librarian[1]
    p1.renew_copy(p1.medias()[0].mediaID, today)
    commit()

    p1_1 = librarian.get_user_medias(p1)[0]
    assert (
        MediaCopies.get(copyID=p1_1.mediaID).mediaID == Media[3] and p1_1.expiry_date == datetime.datetime(2018, 4, 16,
                                                                                                           12,
                                                                                                           0, 0))

    users = [e.user for e in Media[3].get_queue()]
    assert (users == [s, v, p3])


@db_session
def test10():
    initial_state()
    p1 = User[1010]
    v = User[1110]
    librarian = Librarian[1]
    march_six = datetime.datetime(2018, 3, 26, 12, 0, 0)
    march_nine = datetime.datetime(2018, 3, 29, 12, 0, 0)

    p1.book_media(Media[1], march_six)
    p1.renew_copy(p1.medias()[0].mediaID, march_nine)

    v.book_media(Media[1], march_six)
    v.renew_copy(v.medias()[0].mediaID, march_nine)

    p1_1 = librarian.get_user_medias(p1)[0]
    v_1 = librarian.get_user_medias(v)[0]

    assert (
        Media[int(p1_1.mediaID.split('-')[0])] == Media[1] and p1_1.expiry_date == datetime.datetime(2018, 4, 26, 12, 0,
                                                                                                     0))
    assert (
        Media[int(v_1.mediaID.split('-')[0])] == Media[1] and v_1.expiry_date == datetime.datetime(2018, 4, 5, 12, 0,
                                                                                                   0))


tests_array = [test1, test2, test3, test4, test5, test6, test7, test8, test9, test10]

for i in range(0, len(tests_array)):
    try:
        tests_array[i]()
        print("Test %d OK" % (i + 1))
    except (AssertionError, TypeError) as e:
        print(("Test %d FAIL \nError: " + str(e)) % (i + 1))
