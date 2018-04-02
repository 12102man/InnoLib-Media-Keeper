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

    if not user_medias[0].is_expired(datetime.datetime(2018, 4, 2, 12, 0, 0)) and user_medias[0].balance == 0:
        print("test 1 OK")
    else:
        print("test 1 FAIL")


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

    print("test 2 OK")


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

    print("test 3 OK")









test3()
