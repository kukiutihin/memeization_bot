from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from enum import Enum

from database.db import Database
from bot.bot_functions import add_pic_from_pid, add_pic, remove_from_fav


class Buttons:
    find = "Подборка 🐜"
    # lib = "Библиотека 👨‍🦯"

    to_menu = "В меню 🍄‍🟫"

    # add = "Добавить 🦃"
    # pid = "По PID 🤷‍♀️"
    # private = "Свою приватно 👀"
    # public = "Свою публично 🐹"
    # delete = "Удалить 👹"

    more = "Еще 🏓"


class State(Enum):
    MENU = 1

    FIND = 2
    FIND_WAITING_TAGS = 3
    
    # LIBRARY = 4
    # LIBRARY_WAITING_PID = 5
    # LIBRARY_WAITING_TAGS = 6
    # LIBRARY_WAITING_DELETE = 7


UNDEFINED = "ниче не понял 🧌"

user_state: dict[int, State] = {}
# user_private_flag: dict[int, bool] = {}

MENU = ReplyKeyboardMarkup(
    [[Buttons.find]],
    resize_keyboard=True
)

# KEY = ReplyKeyboardMarkup(
#     [[Buttons.my_key, Buttons.transfer, Buttons.to_menu]],
#     resize_keyboard=True
# )

# LIBRARY = ReplyKeyboardMarkup(
#     [[Buttons.add, Buttons.delete, Buttons.to_menu]],
#     resize_keyboard=True
# )

FIND = ReplyKeyboardMarkup(
    [[Buttons.more, Buttons.to_menu]],
    resize_keyboard=True
)

WAITING_TAGS = ReplyKeyboardMarkup(
    [[Buttons.to_menu]],
    resize_keyboard=True
)

BACK = ReplyKeyboardMarkup([[Buttons.to_menu]], resize_keyboard=True)


async def global_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    uid = update.effective_user.id
    text = update.message.text
    state = user_state.get(uid, State.MENU) 

    if state == State.MENU:
        await menu_handler(update, text, db, ghosts)

    elif state == State.FIND:
        await find_handler(update, text, db, ghosts)

    # elif state == State.LIBRARY:
    #     await library_handler(update, text, db, ghosts)

    # elif state == State.FIND_WAITING_TAGS:
    #     await waiting_tags_handler(update, text, db, ghosts)
    
    # elif state == State.LIBRARY_WAITING_PID:
    #     await library_waiting_pid_handler(update, context, db)

    # elif state == State.LIBRARY_WAITING_TAGS:
    #     await library_waiting_tags_handler(update, context, db, ghosts, user_private_flag[uid])
        
    # elif state == State.LIBRARY_WAITING_DELETE:
    #     await library_waiting_delete_handler(update, context, db)

        

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    text = update.message.text
    uid = update.effective_user.id

    if text == Buttons.find:
        user_state[uid] = State.FIND
        await find_handler(update, context, db, ghosts)

    # elif text == Buttons.lib:
    #     user_state[uid] = State.LIBRARY
    #     await library_handler(update, context, db, ghosts)

    # else:
    #     await update.message.reply_text(UNDEFINED)


async def find_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int, tags = []):
    text = update.message.text
    uid = update.effective_user.id

    if not tags:
        await update.message.reply_text("Введите не более 20-ти тегов через запятую")
        user_state[uid] = State.FIND_WAITING_TAGS
        return

    if text == Buttons.more:
        await find_handler(update, context, db, ghosts, tags)

    elif text == Buttons.to_menu:
        await menu_handler(update, context, db, ghosts)

    else:
        await update.message.reply_text(UNDEFINED)


async def waiting_tags_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    uid = update.effective_user.id
    text = update.message.text

    tags = update.message.text
    tags = tags.lower().split(",")

    if text == Buttons.to_menu:
        user_state[uid] = State.MENU
        await menu_handler(update, context, db, ghosts)

    # TODO выгрузить 7 картинок из дб

    if len(tags) == 0:
        await update.message.reply_text("Введите теги или вернитесь в меню")
        return

    if len(tags) > 20:
        await update.message.reply_text("Многовато тегов")
        return

    user_state[uid] = State.FIND
    await find_handler(update, context, db, ghosts, tags)


# async def library_handler(update, context, db, ghosts):
#     uid = update.effective_user.id
#     text = update.message.text

#     if text == Buttons.pid:
#         user_state[uid] = State.LIBRARY_WAITING_PID
#         await update.message.reply_text("Введите PID картинки:", reply_markup=BACK)

#     elif text == Buttons.private:
#         user_state[uid] = State.LIBRARY_WAITING_TAGS
#         user_private_flag[uid] = True 
#         await update.message.reply_text("Введите теги для приватной картинки:", reply_markup=BACK)

#     elif text == Buttons.public:
#         user_state[uid] = State.LIBRARY_WAITING_TAGS
#         user_private_flag[uid] = False 
#         await update.message.reply_text("Введите теги для публичной картинки:", reply_markup=BACK)

#     elif text == Buttons.delete:
#         user_state[uid] = State.LIBRARY_WAITING_DELETE
#         await update.message.reply_text("Введите PID картинки для удаления:", reply_markup=BACK)

#     elif text == Buttons.to_menu:
#         user_state[uid] = State.MENU
#         await menu_handler(update, context, db, ghosts)

#     else:
#         await update.message.reply_text("Неизвестная команда. Используйте кнопки меню.")


# async def library_waiting_pid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
#     text = update.message.text

#     if not text.isdigit():
#         await update.message.reply_text("PID должен быть числом. Попробуйте снова.")
#         return

#     pid = int(text)
#     await add_pic_from_pid(update, context, db, pid)



# async def library_waiting_tags_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int, is_private: bool):
#     text = update.message.text
#     tags = [t.strip() for t in text.split(",") if t.strip()]

#     if not tags:
#         await update.message.reply_text("Введите хотя бы один тег, разделённый запятой.")
#         return

#     await add_pic(update, context, is_private, db, ghosts, tags)


# async def library_waiting_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
#     uid = update.effective_user.id
#     text = update.message.text

#     if text == Buttons.to_menu:
#         user_state[uid] = State.LIBRARY
#         await update.message.reply_text("", reply_markup=LIBRARY)  
#         return

#     if not text.isdigit():
#         await update.message.reply_text("PID должен быть числом.", reply_markup=BACK)
#         return

#     pid = int(text)
#     await remove_from_fav(update, context, db, pid)

#     user_state[uid] = State.LIBRARY
#     await update.message.reply_text("", reply_markup=LIBRARY)



# async def key_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     text = update.message.text
#     uid = update.effective_user.id

#     if text == Buttons.my_key:
#         # TODO

#     elif text == Buttons.transfer:
#         # TODO

#     elif text == Buttons.to_menu:
#         await menu_handler(update, context)

#     else:
#         update.message.reply_text(UNDEFINED)


