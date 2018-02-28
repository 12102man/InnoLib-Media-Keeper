from telegram.ext import Updater
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler
from telegram.ext import Filters
from pony.orm import *
import config
from user import User, Media, RegistrySession

db = Database()
db.bind(provider='mysql', host='37.46.132.57', user='telebot', passwd='Malinka2017', db='testbase')
updater = Updater(token=config.token)


def create_new_patron(bot, update, state):
    """
    We need to create new record in database with filled TelegramID and then
    put there new data from message of librarian
    Ask required field to user and put it new entity
    Then commit it
    ATTENTION: registration is being done by LIBRARIAN, not PATRON by himself
    """
    #new_user = User.get(telegramID=update.message.chat_id)
    session = RegistrySession.get(telegramID=update.message.chat_id)
    if session is not None:
        if session.telegramID is None:
            """Тут ещё не понятно, сможет ли библиотекарь писать сразу ИД
            или бот сможет находить по алиасу ИД """
            session.request_c = update.message.text
            bot.send_message("write his full name")
            commit()
            return NAME
        elif session.name is None:
            session.name = update.message.text
            bot.send_message("write his full name")
            commit()
            return PHONE_NUMBER
        elif session.phone is None:
            session.phone = update.message.text
            bot.send_message("write his address")
            commit()
            return ADDRESS
        elif session.address is None:
            session.address = update.message.text
            bot.send_message("write is he a faculty member")
            commit()
            return FACULTY
        elif session.faculty is None:
            session.faculty = update.message.text
            bot.send_message("write is he a faculty member")
            new_user = User(telegramID=session.request_c, name=session.name,
                            phone=session.phone, address=session.address,
                            faculty=session.faculty)
            commit()
            return new_patron_conversation.END
    else:
        session_lib = RegistrySession(telegramID=update.message.chat_id)
        bot.send("start reg new patron, write his tgID/alias")
        commit()
        return TELEGRAM_ID


def create_new_media(bot, update, state):
    """
    The same thing as with NEW PATRON but with media
    """

    session = RegistrySession.get(telegramID=update.message.chat_id)
    if session is not None:
        if session.media_c is None:
            session.media_c = update.message.text
            new_media = Media(mediaID=session.media_c)
            bot.send_message("write his full name")
            commit()
            return TYPE
        else:
            new_media = Media.get(mediaID=session.media_c)
            if new_media.type is None:
                new_media.type = update.message.text
                bot.send_message("write its name")
                commit()
                return TITLE
            elif new_media.name is None:
                new_media.name = update.message.text
                bot.send_message("write its authors")
                commit()
                return PUBLISHER
            elif new_media.publisher is None:
                new_media.publisher = update.message.text
                commit()
                return new_media_conversation.END
    else:
        session_lib = RegistrySession(telegramID=update.message.chat_id)
        bot.send("start reg new media, write its libID")
        commit()
        return MEDIA_ID


def delete_patron(bot, update, state):
    if state == "find":
        """
        Librarian can also write a libID
        """
        name = update.message.text
        session = RegistrySession(telegramID=update.message.chat_id)
        current_patron = select(p for p in User if p.name == name)
        session.request_c = current_patron.telegramID
        bot.send_message(current_patron.name + " " + current_patron.address + " " + current_patron.phone)
        bot.send_message("Do you want to delete him")
        """  Print data about this patron to librarian and ask, does he want to delete him or no """
        return DELETE
    elif state == "delete":
        if update.message.text == "yes":
            session = RegistrySession.get(telegramID=update.message.text)
            User.get(telegramID=session.request_c).delete()
            bot.send_message("Delete completed")
        else:
            bot.send_message("Delete was cancelled")
        return delete_user_conversation.END
    else:
        bot.send_message("write his name")
        return FIND


def delete_media(bot, update, state):
    if state == "find":
        session = RegistrySession(telegramID=update.message.chat_id)
        lib_media_id = update.message.text
        session.request_c = lib_media_id
        current_media = select(m for m in Media if mediaID == lib_media_id)
        """  Print data about this media to librarian and ask, does he want to delete it or no """
        bot.send_message(current_media.name + " " + current_media.authors + " " + current_media.type)
        bot.send_message("Do you want to delete it")
        return DELETE
    elif state == "delete":
        if update.message.text == "yes":
            session = RegistrySession.get(telegramID=update.message.chat_id)
            Media.get(session.request_c).delte()
            bot.send_message("Delete completed")
        else:
            bot.send_message("Delete was cancelled")
        return delete_media_conversation.END
    else:
        bot.send_message("write its mediaID")
        return FIND
"""def modify_user():

def modify_media():"""


new_patron_handler = CommandHandler("add_new_user", create_new_patron("start"))
new_patron_conversation = ConversationHandler(entry_points=[new_patron_handler],
                                              states={
                                                    NAME: [MessageHandler(Filters.text, create_new_patron)],
                                                    TELEGRAM_ID: [MessageHandler(Filters.text, create_new_patron)],
                                                    PHONE_NUMBER: [MessageHandler(Filters.text, create_new_patron)],
                                                    ADDRESS: [MessageHandler(Filters.text, create_new_patron)],
                                                    FACULTY: [MessageHandler(Filters.text, create_new_patron)]
                                                },
                                              fallbacks=[])

new_media_handler = CommandHandler("add_new_media", create_new_media("start"))
new_media_conversation = ConversationHandler(entry_points=[new_media_handler],
                                             states={
                                                    MEDIA_ID: [MessageHandler(Filters.text, create_new_media)],
                                                    TYPE: [MessageHandler(Filters.text, create_new_media)],
                                                    TITLE: [MessageHandler(Filters.text, create_new_media)],
                                                    AUTHORS: [MessageHandler(Filters.text, create_new_media)],
                                                    COPY: [MessageHandler(Filters.text, create_new_media)]
                                                },
                                             fallbacks=[])

delete_user_handler = CommandHandler("delete_user", delete_patron)
delete_user_conversation = ConversationHandler(entry_points=[delete_user_handler],
                                               states={
                                                   FIND: [MessageHandler(Filters.text, delete_user("find"))],
                                                   DELETE: [MessageHandler(Filters.text, delete_user("delete"))]
                                               },
                                               fallbacks=[])

delete_media_handler = CommandHandler("delete_media", delete_media)
delete_media_conversation = ConversationHandler(entry_points=[delete_media_handler],
                                                states={
                                                   FIND: [MessageHandler(Filters.text, delete_media("find"))],
                                                   DELETE: [MessageHandler(Filters.text, delete_media("delete"))]
                                               },
                                                fallbacks=[])


updater.dispatcher.add_handler(new_patron_handler)
updater.dispatcher.add_handler(new_patron_conversation)

