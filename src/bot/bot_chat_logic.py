from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from enum import Enum

from database.db import Database
from bot.bot_functions import add_pic_from_pid, remove_from_fav, send_images_any
from bot.database_calls import search_memes_in_db, add_meme_to_db


class Buttons:
    find = "Подборка 🐜"
    lib = "Сохраненки 👨‍🦯"

    to_menu = "В меню 🍄‍🟫"

    add = "Добавить 🦃"
    delete = "Удалить 👹"

    load = "Загрузить 🥟"
    private = "Приватно 👀"
    public = "Публично 🐹"

    more = "Еще 🏓"


class State(Enum):
    MENU = 1

    FIND = 2
    FIND_WAITING_TAGS = 3
    
    SAVES = 4
    SAVES_WAIT_ADD = 5
    SAVES_WAIT_DEL = 6

    LOAD_WAITING_PIC = 7
    LOAD_WAITING_BOOL = 8


UNDEFINED = "ниче не понял 🧌"
HELLO = "Привет"
ACTION = "Что будем делать?"
IN_MENU = "В меню так в меню"

user_state: dict[int, State] = {}
last_tags: dict[int, [str]] = {}
load_bool: dict[int, bool] = {}

MENU = ReplyKeyboardMarkup(
    [[Buttons.find, Buttons.lib, Buttons.load]],
    resize_keyboard=True
)

FIND = ReplyKeyboardMarkup(
    [[Buttons.more, Buttons.to_menu]],
    resize_keyboard=True
)

SAVES = ReplyKeyboardMarkup(
    [[Buttons.add, Buttons.delete, Buttons.to_menu]],
    resize_keyboard=True
)

BACK = ReplyKeyboardMarkup([[Buttons.to_menu]], resize_keyboard=True)

LOAD = ReplyKeyboardMarkup(
    [[Buttons.public, Buttons.private]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    text = update.message.text
    
    await update.message.reply_text(HELLO, reply_markup=MENU)
    await menu_handler(update, text, db, ghosts)


async def global_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    uid = update.effective_user.id
    state = user_state.get(uid, State.MENU) 

    if state == State.MENU:
        await menu_handler(update, context, db, ghosts)

    elif state == State.FIND:
        await find_handler(update, context, db, ghosts)

    elif state == State.FIND_WAITING_TAGS:
        await waiting_tags_handler(update, context, db, ghosts)

    elif state == State.SAVES:
        await saves_handler(update, context, db, ghosts)

    elif state == State.SAVES_WAIT_ADD:
        await saves_wait_handler(update, context, db, ghosts, add_pic_from_pid)

    elif state == State.SAVES_WAIT_DEL:
        await saves_wait_handler(update, context, db, ghosts, remove_from_fav)

    elif state == State.LOAD_WAITING_PIC:
        await load_wait_pic_handler(update, context, db, ghosts)

    elif state == State.LOAD_WAITING_BOOL:
        await load_wait_bool_handler(update, context, db)


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    uid = update.effective_user.id
    text = update.message.text

    if text == Buttons.find:
        user_state[uid] = State.FIND_WAITING_TAGS
        await update.message.reply_text(
            "Введите до 20 тегов через запятую:",
            reply_markup=BACK
        )
        return
    
    elif text == Buttons.lib:
        user_state[uid] = State.SAVES
        await update.message.reply_text(
            ACTION,
            reply_markup=SAVES
        )
        return
    
    elif text == Buttons.load:
        user_state[uid] = State.LOAD_WAITING_PIC
        await update.message.reply_text(
            "Пришлите изображение и список тегов через запятую (tag1,tag2,...)",
            reply_markup=BACK
        )
        return


# async def load_wait_bool_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
#     uid = update.effective_user.id
#     text = update.message.text

#     if text == Buttons.to_menu:
#         user_state[uid] = State.MENU
#         await update.message.reply_text(IN_MENU, reply_markup=MENU)
#         return

#     if text == Buttons.public:
#         user_state[uid] = State.MENU
#         load_bool[uid] = False

#     elif text == Buttons.private:
#         user_state[uid] = State.MENU
#         load_bool[uid] = True

#     else:
#         await update.message.reply_text(UNDEFINED, reply_markup=LOAD)
#         return

#     user_state[uid] = State.MENU
#     await update.message.reply_text(ACTION, reply_markup=MENU)


async def saves_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    uid = update.effective_user.id
    text = update.message.text

    if text == Buttons.add:
        user_state[uid] = State.SAVES_WAIT_ADD
        await update.message.reply_text(
            "Введите id изображения:",
            reply_markup=BACK
        )
        return

    elif text == Buttons.delete:
        user_state[uid] = State.SAVES_WAIT_DEL
        await update.message.reply_text(
            "Введите id изображения:",
            reply_markup=BACK
        )
        return

    elif text == Buttons.to_menu:
        user_state[uid] = State.MENU
        await update.message.reply_text(IN_MENU, reply_markup=MENU)
        return

    await update.message.reply_text(ACTION, reply_markup=MENU)


async def saves_wait_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int, func):
    uid = update.effective_user.id
    text = update.message.text

    if text == Buttons.to_menu:
        user_state[uid] = State.MENU
        await update.message.reply_text(IN_MENU, reply_markup=MENU)
        return

    await func(update, context, db)

    user_state[uid] = State.SAVES
    await update.message.reply_text(ACTION, reply_markup=SAVES)


async def find_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    uid = update.effective_user.id
    text = update.message.text

    if text == Buttons.more:
        tags = last_tags.get(uid)
        if tags:
            memes = search_memes_in_db(uid, ",".join(tags), db, 0.2, 20, ghosts)
            if memes:
                await send_images_any(update, memes)
            else:
                await update.message.reply_text("Не нашли ничего по таким тегам 😢", reply_markup=FIND)
        else:
            await update.message.reply_text("Теги не найдены, вернитесь в меню.", reply_markup=MENU)

        return

    if text == Buttons.to_menu:
        user_state[uid] = State.MENU
        await update.message.reply_text(IN_MENU, reply_markup=MENU)
        return

    await update.message.reply_text(UNDEFINED)


async def waiting_tags_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    uid = update.effective_user.id
    text = update.message.text

    if text == Buttons.to_menu:
        user_state[uid] = State.MENU
        await update.message.reply_text(IN_MENU, reply_markup=MENU)
        return

    tags = [t.strip() for t in text.lower().split(",")]

    last_tags[uid] = tags

    memes = search_memes_in_db(uid, ",".join(tags), db, 0.2, 20, ghosts)
    if memes:
        await send_images_any(update, memes)
    else:
        await update.message.reply_text("Не нашли ничего по таким тегам 😢", reply_markup=FIND)

    user_state[uid] = State.FIND
    await update.message.reply_text(ACTION, reply_markup=FIND)



pending_uploads: dict[int, dict] = {}

async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    uid = update.effective_user.id
    caption = update.message.caption or ""

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = "photo"

    elif update.message.document and (update.message.document.mime_type or "").startswith("image/"):
        file_id = update.message.document.file_id
        file_type = "document"

    else:
        await update.message.reply_text("Пожалуйста, отправьте изображение")
        return

    tags = [tag.strip() for tag in caption.split(',') if tag.strip()]
    if not tags:
        await update.message.reply_text("Укажите хотя бы один тег в подписи к изображению")
        return

    pending_uploads[uid] = {
        "file_id": file_id,
        "tags": tags,
        "db": db,
        "ghosts": ghosts
    }

    user_state[uid] = State.LOAD_WAITING_BOOL
    await update.message.reply_text(
        "Как будем загружать?",
        reply_markup=LOAD
    )

async def load_wait_bool_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    uid = update.effective_user.id
    text = update.message.text

    if text not in [Buttons.public, Buttons.private]:
        await update.message.reply_text("Жмите на кнопки", reply_markup=LOAD)
        return

    if uid not in pending_uploads:
        await update.message.reply_text("Пожалуйста загрузите изображение")
        return

    data = pending_uploads.pop(uid) 
    is_private = (text == Buttons.private)

    success = add_meme_to_db(
        uid,
        data["file_id"],
        data["tags"],
        data["db"],
        data["ghosts"],
        is_private
    )

    if success:
        # if is_private:
        #     await add_pic_from_pid(update, context, db)

        await update.message.reply_text("Изображение успешно добавлено 🎉", reply_markup=MENU)
    else:
        await update.message.reply_text("Ошибка при добавлении мема в базу данных", reply_markup=MENU)

    user_state[uid] = State.MENU


async def load_wait_pic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, ghosts: int):
    uid = update.effective_user.id
    text = update.message.text

    if text == Buttons.to_menu:
        user_state[uid] = State.MENU
        await update.message.reply_text(IN_MENU, reply_markup=MENU)
        return

    user_state[uid] = State.LOAD_WAITING_BOOL

    await update.message.reply_text(
        "Как будем загружать?",
        reply_markup=LOAD
    )






