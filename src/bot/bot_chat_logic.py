from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from enum import Enum

from src.database.db import Database
from src.bot.bot_functions import add_pic_from_pid, add_pic, remove_from_fav


class Buttons:
    find = "Подборка 🐜"
    lib = "Библиотека 👨‍🦯"
    to_menu = "В меню 🍄‍🟫"

    add = "Добавить 🦃"
    pid = "По PID 🤷‍♀️"
    private = "Свою приватно 👀"
    public = "Свою публично 🐹"
    delete = "Удалить 👹"

    more = "Еще 🏓"


class State(Enum):
    MENU = 1

    FIND = 2
    FIND_WAITING_TAGS = 3
    
    LIBRARY = 4
    LIBRARY_WAITING_PID = 5
    LIBRARY_WAITING_TAGS = 6
    LIBRARY_WAITING_DELETE = 7


UNDEFINED = "ниче не понял 🧌"

user_state: dict[int, State] = {}
user_private_flag: dict[int, bool] = {}

MENU = ReplyKeyboardMarkup(
    [[Buttons.find, Buttons.lib]],
    resize_keyboard=True
)

LIBRARY = ReplyKeyboardMarkup(
    [[Buttons.add, Buttons.delete, Buttons.to_menu]],
    resize_keyboard=True
)

FIND = ReplyKeyboardMarkup(
    [[Buttons.more, Buttons.to_menu]],
    resize_keyboard=True
)

WAITING_TAGS = ReplyKeyboardMarkup(
    [[Buttons.to_menu]],
    resize_keyboard=True
)

BACK = ReplyKeyboardMarkup([[Buttons.to_menu]], resize_keyboard=True)


# === ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ===
async def global_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    uid = update.effective_user.id
    text = update.message.text
    state = user_state.get(uid, State.MENU) 

    if state == State.MENU:
        await menu_handler(update, context, db, ghosts)

    elif state == State.FIND:
        await find_handler(update, context, db, ghosts)

    elif state == State.LIBRARY:
        await library_handler(update, context, db, ghosts)

    elif state == State.FIND_WAITING_TAGS:
        await waiting_tags_handler(update, context, db, ghosts)
    
    elif state == State.LIBRARY_WAITING_PID:
        await library_waiting_pid_handler(update, db)

    elif state == State.LIBRARY_WAITING_TAGS:
        await library_waiting_tags_handler(update, context, db, ghosts, user_private_flag.get(uid, False))
        
    elif state == State.LIBRARY_WAITING_DELETE:
        await library_waiting_delete_handler(update, db)


# === МЕНЮ ===
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    uid = update.effective_user.id
    text = update.message.text

    if text == Buttons.find:
        user_state[uid] = State.FIND
        await find_handler(update, context, db, ghosts)

    elif text == Buttons.lib:
        user_state[uid] = State.LIBRARY
        await library_handler(update, context, db, ghosts)

    else:
        await update.message.reply_text(UNDEFINED)


# === ПОДБОРКА ===
async def find_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int, tags=[]):
    uid = update.effective_user.id
    text = update.message.text

    if not tags:
        await update.message.reply_text("Введите не более 20-ти тегов через запятую", reply_markup=WAITING_TAGS)
        user_state[uid] = State.FIND_WAITING_TAGS
        return

    if text == Buttons.more:
        await send_memes(update, db, ghosts, tags)
    elif text == Buttons.to_menu:
        user_state[uid] = State.MENU
        await menu_handler(update, context, db, ghosts)
    else:
        await send_memes(update, db, ghosts, tags)


async def waiting_tags_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    uid = update.effective_user.id
    text = update.message.text

    if text == Buttons.to_menu:
        user_state[uid] = State.MENU
        await menu_handler(update, context, db, ghosts)
        return

    tags = [t.strip().lower() for t in text.split(",") if t.strip()]

    if len(tags) == 0:
        await update.message.reply_text("Введите теги или вернитесь в меню")
        return

    if len(tags) > 20:
        await update.message.reply_text("Многовато тегов")
        return

    user_state[uid] = State.FIND
    await send_memes(update, db, ghosts, tags)


async def send_memes(update: Update, db: Database, ghosts: int, tags: list[str]):
    """
    Заглушка для отправки мемов по тегам.
    Здесь нужно подключить вашу функцию поиска мемов в базе.
    """
    # TODO: заменить на реальный поиск из БД
    memes = [f"https://i.ibb.co/WhpHnv7/Lainnizm.jpg" for _ in range(min(ghosts, 7))]

    for meme_url in memes:
        await update.message.reply_photo(meme_url)

    await update.message.reply_text("Выберите 'Еще 🏓' для следующей подборки или вернитесь в меню.", reply_markup=FIND)


# === БИБЛИОТЕКА ===
async def library_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    uid = update.effective_user.id
    text = update.message.text

    if text == Buttons.pid:
        user_state[uid] = State.LIBRARY_WAITING_PID
        await update.message.reply_text("Введите PID картинки:", reply_markup=BACK)

    elif text == Buttons.private:
        user_state[uid] = State.LIBRARY_WAITING_TAGS
        user_private_flag[uid] = True 
        await update.message.reply_text("Введите теги для приватной картинки:", reply_markup=BACK)

    elif text == Buttons.public:
        user_state[uid] = State.LIBRARY_WAITING_TAGS
        user_private_flag[uid] = False 
        await update.message.reply_text("Введите теги для публичной картинки:", reply_markup=BACK)

    elif text == Buttons.delete:
        user_state[uid] = State.LIBRARY_WAITING_DELETE
        await update.message.reply_text("Введите PID картинки для удаления:", reply_markup=BACK)

    elif text == Buttons.to_menu:
        user_state[uid] = State.MENU
        await menu_handler(update, context, db, ghosts)

    else:
        await update.message.reply_text("Неизвестная команда. Используйте кнопки меню.")


# === ОБРАБОТЧИК PID ===
async def library_waiting_pid_handler(update: Update, db: Database):
    text = update.message.text
    uid = update.effective_user.id

    if not text.isdigit():
        await update.message.reply_text("PID должен быть числом. Попробуйте снова.", reply_markup=BACK)
        return

    pid = int(text)
    await add_pic_from_pid(update, db, pid)
    await update.message.reply_text("Картинка добавлена в избранные.", reply_markup=LIBRARY)
    user_state[uid] = State.LIBRARY


# === ОБРАБОТЧИК ТЕГОВ ===
async def library_waiting_tags_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int, is_private: bool):
    text = update.message.text
    uid = update.effective_user.id

    tags = [t.strip() for t in text.split(",") if t.strip()]

    if not tags:
        await update.message.reply_text("Введите хотя бы один тег, разделённый запятой.", reply_markup=BACK)
        return

    await add_pic(update, db, is_private, ghosts, tags)
    await update.message.reply_text("Картинка добавлена.", reply_markup=LIBRARY)
    user_state[uid] = State.LIBRARY


# === ОБРАБОТЧИК УДАЛЕНИЯ ===
async def library_waiting_delete_handler(update: Update, db: Database):
    text = update.message.text
    uid = update.effective_user.id

    if text == Buttons.to_menu:
        user_state[uid] = State.LIBRARY
        await update.message.reply_text("", reply_markup=LIBRARY)
        return

    if not text.isdigit():
        await update.message.reply_text("PID должен быть числом.", reply_markup=BACK)
        return

    pid = int(text)
    await remove_from_fav(update, db, pid)
    await update.message.reply_text("Картинка удалена.", reply_markup=LIBRARY)
    user_state[uid] = State.LIBRARY
