from telegram.ext import Updater
from telegram.ext import CommandHandler
from pony.orm import *
import user
import config

db = Database()
updater = Updater(token=config.token)
new_patron = Pony_patron()
new_media = Pony_media()
current_patron = Pony_patron()
current_media = Pony_media()

def create_new_patron(bot, update, state):
    """
    We need to create new record in database with filled TelegramID and then
    put there new data from message of librarian
    Ask required field to user and put it new entity
    Then commit it
    """
    global new_patron
    if state == "start":
        return NAME
    if state == "name":
        new_patron.set_name(update.message.text)
        return TELEGRAM_ID
    if state == "telegram_id":
        new_patron.set_telegram_id(update.message.text)
        return ALIAS
    if state == "alias":
        new_patron.set_alias(update.message.text)
        return PHONE_NUMBER
    if state == "phone_number":
        new_patron.set_phone(update.message.text)
        return ADDRESS
    if state == "address":
        new_patron.set_address(update.message.text)
        return FACULTY
    if state == "faculty":
        new_patron.set_faculty(update.message.text)
        return COMMIT
    if state == "commit":
        commit()
        return new_patron_conversation.END


def create_new_media(bot, update, state):
    """
    The same thing as with NEW PATRON but with media
    """

    global new_media
    if state == "start":
        return TYPE
    if state == "type":
        new_media.set_type(update.message.text)
        return TITLE
    if state == "title":
        new_media.set_type(update.message.text)
        return AUTHORS
    if state == "authors":
        new_media.set_type(update.message.text)
        return COPY
    if state == "copy":
        new_media.set_type(update.message.text)
        return COMMIT
    if state == "commit":
        commit()
        return new_media_conversation.END


def delete_user(bot, update, state):
    global current_patron
    if state == "find":
        name = update.message.text
        current_patron = select(from db with attribute 'name' == name)
        """  Print data about this patron to librarian and ask, does he want to delete him or no """
        return DELETE
    if state == "delete":
        if update.message.text == "yes":
            delete(current_patron)
            bot.send_message("Delete successful")
        else:
            bot.send_message("Delete was cancelled")
        return delete_user_conversation.END


def delete_media():
    global current_media
    if state == "find":
        lid_media_id = update.message.text
        current_media = select(from db with attribute 'libid' == lib_media_id)
        """  Print data about this media to librarian and ask, does he want to delete it or no """
        return DELETE
    if state == "delete":
        if update.message.text == "yes":
            delete(current_media)
            bot.send_message("Delete successful")
        else:
            bot.send_message("Delete was cancelled")
        return delete_media_conversation.END
"""def modify_user():

def modify_media():"""



new_patron_handler = CommandHanlder("add_new_user", create_new_user("start"))
new_patron_conversation = ConversationHandler(entry_points=[new_user_handler],
                                                states={
                                                    NAME: [MessageHandler(Filters.text, create_new_patron("name"))],
                                                    TELEGRAM_ID: [MessageHandler(Filters.text, create_new_patron("telegram_id"))],
                                                    ALIAS: [MessageHandler(Filters.text, create_new_patron("alias"))],
                                                    PHONE_NUMBER: [MessageHandler(Filters.text, create_new_patron("phone_number"))],
                                                    ADDRESS: [MessageHandler(Filters.text, create_new_patron("address"))],
                                                    FACULTY: [MessageHandler(Filters.text, create_new_patron("faculty"))],
                                                    COMMIT: [MessageHandler(Filters.text, create_new_patron("commit"))]
                                                },
                                                fallbacks=[])

new_media_handler = CommandHanlder("add_new_media", create_new_media("start"))
new_media_conversation = ConversationHandler(entry_points=[new_media_handler],
                                                states={
                                                    TYPE: [MessageHandler(Filters.text, create_new_patron("type"))],
                                                    TITLE: [MessageHandler(Filters.text, create_new_patron("title"))],
                                                    AUTHORS: [MessageHandler(Filters.text, create_new_patron("authors"))],
                                                    COPY: [MessageHandler(Filters.text, create_new_patron("copy"))],
                                                    COMMIT: [MessageHandler(Filters.text, create_new_media("commit"))]
                                                },
                                                fallbacks=[])

delete_user_handler = CommandHandler("delete_user", delete_user)
delete_user_conversation = ConversationHandler(entry_points=[delete_user_handler],
                                               states={
                                                   FIND: [MessageHandler(Filters.text, delete_user("find"))],
                                                   DELETE: [MessageHandler(Filters.text, delete_user("delete"))]
                                               })

delete_media_handler = CommandHandler("delete_media", delete_media)
delete_media_conversation = ConversationHandler(entry_points=[delete_media_handler],
                                               states={
                                                   FIND: [MessageHandler(Filters.text, delete_media("find"))],
                                                   DELETE: [MessageHandler(Filters.text, delete_media("delete"))]
                                               })


updater.dispatcher.add_handler(new_patron_handler)
updater.dispatcher.add_handler(new_patron_conversation)

