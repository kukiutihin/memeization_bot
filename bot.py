import logging
from bd2 import Database
from telegram import InlineQueryResultPhoto, Update
from telegram.ext import Application, InlineQueryHandler, ContextTypes, CommandHandler

BOT_TOKEN = "Token Bota"

db = Database()

YOUR_MEMES = [
    {
        "id": "2",
        "title": "eshkeree", 
        "description": "Уильям Фредерик",
        "photo_url": "https://i.ibb.co/xqqVWPD7/flat-750x-075-f-pad-750x1000-f8f8f8.jpg",
        "thumbnail_url": "https://i.ibb.co/xqqVWPD7/flat-750x-075-f-pad-750x1000-f8f8f8.jpg",
        "tags": ["программист", "it", "код", "работа"]
    },
    {
        "id": "3",
        "title": "Neco Arc", 
        "description": "Guranyaaaaa",
        "photo_url": "https://i.ibb.co/S4p6VFXp/s-TTNYry-k-Y4.jpg",
        "thumbnail_url": "https://i.ibb.co/S4p6VFXp/s-TTNYry-k-Y4.jpg",
        "tags": ["кофе", "утро", "программист", "it"]
    },
    {
        "id": "4",
        "title": "Cho", 
        "description": "Lain",
        "photo_url": "https://i.ibb.co/WhpHnv7/Lainnizm.jpg",
        "thumbnail_url": "https://i.ibb.co/WhpHnv7/Lainnizm.jpg",
        "tags": ["собака", "dog", "веселая", "животные"]
    }
]

# === ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ ===

def search_memes_in_db(tg_id: int, search_query: str):
    """Ищет мемы в базе данных по запросу"""
    search_tags = [tag.strip() for tag in search_query.split() if tag.strip()]
    
    try:
        favs_results, global_results = db.find(tg_id, search_tags)
        return global_results
    except Exception as e:
        print(f"Ошибка поиска в БД: {e}")
        return []

def add_meme_to_db(tg_id: int, photo_url: str, tags: list[str], is_private: bool = False):
    """Добавляет мем в базу данных"""
    try:
        db.add_to(tg_id, is_private, photo_url, tags)
        return True
    except Exception as e:
        print(f"Ошибка добавления мема в БД: {e}")
        return False

def add_to_favorites(tg_id: int, pic_id: int):
    """Добавляет мем в избранное"""
    try:
        db.add_from(tg_id, pic_id)
        return True
    except Exception as e:
        print(f"Ошибка добавления в избранное: {e}")
        return False

# === СТАРЫЕ ФУНКЦИИ ПОИСКА===

def search_memes_by_tags(query, memes_list, max_results=10):
    """Функция поиска мемов по тегам"""
    if not query:
        return memes_list[:max_results]
    
    query = query.lower().strip()
    filtered_memes = []
    
    for meme in memes_list:
        search_text = ' '.join(meme.get("tags", []) + [meme.get("title", ""), meme.get("description", "")])
        search_text = search_text.lower()

        if query in search_text:
            filtered_memes.append(meme)

        if len(filtered_memes) >= max_results:
            break
    
    return filtered_memes

def search_memes_by_category(query, memes_list):
    """Функция поиска по категориям"""
    query = query.lower().strip()
    
    category_keywords = {
        "животные": ["кот", "собака", "животные", "cat", "dog", "animals"],
        "it": ["программист", "it", "код", "ошибка", "404", "компьютер"],
        "кофе": ["кофе", "coffee", "утро", "бодрость"]
    }
    
    category = None
    for cat, keywords in category_keywords.items():
        if any(keyword in query for keyword in keywords):
            category = cat
            break
    
    if category:
        filtered_memes = []
        for meme in memes_list:
            meme_tags = ' '.join(meme.get("tags", [])).lower()
            if any(keyword in meme_tags for keyword in category_keywords[category]):
                filtered_memes.append(meme)
        return filtered_memes
    else:
        return search_memes_by_tags(query, memes_list)

# === ОСНОВНОЙ ОБРАБОТЧИК ===

async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    tg_id = update.inline_query.from_user.id
    username = update.inline_query.from_user.username or "Unknown"
    
    print(f"Запрос: '{query}' от {username} (ID: {tg_id})")
    
    db_results = search_memes_in_db(tg_id, query)
    
    photo_urls_mapping = {meme["id"]: meme["photo_url"] for meme in YOUR_MEMES}
    
    db_memes = []
    for pic_id in db_results:
        # нужно получать данные мема из БД
        # cейчас используем заглушку
        db_memes.append({
            "id": str(pic_id),
            "title": f"Мем из БД {pic_id}",
            "description": "Найден в базе данных",
            "photo_url": photo_urls_mapping.get(str(pic_id), "https://i.ibb.co/WhpHnv7/Lainnizm.jpg"),
            "thumbnail_url": photo_urls_mapping.get(str(pic_id), "https://i.ibb.co/WhpHnv7/Lainnizm.jpg"),
            "tags": ["из_базы"]
        })
    
    if not db_memes:
        print("В БД ничего не найдено, используем локальный поиск")
        found_memes = search_memes_by_tags(query, YOUR_MEMES, max_results=10)
        if not found_memes and query:
            found_memes = search_memes_by_category(query, YOUR_MEMES)
        if not found_memes:
            found_memes = YOUR_MEMES[:3]
    else:
        found_memes = db_memes
    
    results = []
    for meme in found_memes:
        results.append(
            InlineQueryResultPhoto(
                id=meme["id"],
                photo_url=meme["photo_url"],
                thumbnail_url=meme["thumbnail_url"],
                title=meme["title"],
                description=meme["description"],
                caption=f"{meme['title']}\n{meme['description']}\nТеги: {', '.join(meme['tags'])}\nID: {meme['id']}"
            )
        )
    
    await update.inline_query.answer(results, cache_time=1)
    print(f"Найдено {len(found_memes)} мемов по запросу '{query}'")

# === КОМАНДЫ БОТА ===

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start"""
    
    await update.message.reply_text(
        "Meme Bot запущен!\n\n"
        "Используйте инлайн режим:\n"
        " @username_бота [теги]\n\n"
    )

async def add_meme_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для добавления нового мема"""
    if not context.args:
        await update.message.reply_text(
            "Чтобы добавить мем, используйте:\n"
            "/addmeme <URL_картинки> <теги через запятую> <приватный: да/нет>\n\n"
            "Пример:\n"
            "/addmeme https://example.com/meme.jpg кот,смешной,животные нет\n\n"
            "Параметры:\n"
            "URL_картинки - прямая ссылка на изображение\n"
            "Теги - через запятую без пробелов\n"
            "Приватный - 'да' или 'нет' (по умолчанию 'нет')"
        )
        return
    
    try:
        if len(context.args) < 2:
            await update.message.reply_text("Недостаточно аргументов. Нужно: URL, теги, [приватный]")
            return
        
        photo_url = context.args[0]
        tags_str = context.args[1]
        is_private = False  # по умолчанию публичный
        
        # Обрабатываем флаг приватности (если передан)
        if len(context.args) > 2:
            private_flag = context.args[2].lower()
            if private_flag in ['да', 'yes', 'true', '1', 'private']:
                is_private = True
            elif private_flag in ['нет', 'no', 'false', '0', 'public']:
                is_private = False
            else:
                await update.message.reply_text("Неверный флаг приватности. Используйте 'да' или 'нет'")
                return
        
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        
        if not tags:
            await update.message.reply_text("Укажите хотя бы один тег")
            return
        
        if not (photo_url.startswith('http://') or photo_url.startswith('https://')):
            await update.message.reply_text("Неверный формат URL. Должен начинаться с http:// или https://")
            return
        
        tg_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        success = add_meme_to_db(tg_id, photo_url, tags, is_private)
        
        if success:
            await update.message.reply_text(
                f"Мем успешно добавлен\n\n"
                f"URL: {photo_url}\n"
                f"Теги: {', '.join(tags)}\n"
                f"Приватный: {'Да' if is_private else 'Нет'}\n"
                f"Добавил: @{username}"
            )
            print(f"Добавлен новый мем от {username}: {tags}")
        else:
            await update.message.reply_text("Ошибка при добавлении мема в базу данных")
            
    except Exception as e:
        await update.message.reply_text(f"Ошибка при обработке команды: {str(e)}")
        print(f"Ошибка в add_meme_command: {e}")

def _find_meme_by_id(meme_id: int):
    """Находит мем по ID в базе данных"""
    try:
        # ищем в локальном списке
        for meme in YOUR_MEMES:
            if str(meme_id) == meme["id"]:
                return meme
        
        # здесь должен быть запрос к БД
        return None
        
    except Exception as e:
        print(f"Ошибка поиска мема по ID: {e}")
        return None
    
async def add_meme_from_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавляет мем по ID в избранное"""
    if not context.args:
        await update.message.reply_text(
            "Чтобы добавить мем в избранное, используйте:\n"
            "/fav <ID_мема>\n\n"
            "Пример:\n"
            "/fav 2"
        )
        return
    
    try:
        meme_id_str = context.args[0]
        
        if not meme_id_str.isdigit():
            await update.message.reply_text("ID мема должен быть числом")
            return
        
        meme_id = int(meme_id_str)
        tg_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        meme = _find_meme_by_id(meme_id)
        
        if not meme:
            await update.message.reply_text(f"Мем с ID {meme_id} не найден")
            return
        
        success = add_to_favorites(tg_id, meme_id)
        
        caption = (
            f"{meme['title']}\n"
            f"{meme['description']}\n"
            f"Теги: {', '.join(meme['tags'])}\n"
            f"ID: {meme_id}\n\n"
        )
        
        if success:
            caption += "Добавлено в избранное"
            print(f"Мем {meme_id} добавлен в избранное пользователем {username}")
        else:
            caption += "Ошибка при добавлении в избранное"
        
        await update.message.reply_photo(
            photo=meme['photo_url'],
            caption=caption
        )
            
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")
        print(f"Ошибка в add_meme_from_id_simple_command: {e}")

# === ЗАПУСК БОТА ===

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("addmeme", add_meme_command))
    app.add_handler(CommandHandler("fav", add_meme_from_id_command))
    app.add_handler(InlineQueryHandler(inline_handler))
    
    print("=" * 50)
    print("Бот запущен")
    print("Команды: /start, /addmeme, /fav")
    print("Инлайн: @memeizat_bot[теги]")
    print("=" * 50)
    
    app.run_polling()

if __name__ == "__main__":
    main()