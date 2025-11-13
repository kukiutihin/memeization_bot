from src.bot.database_calls import search_memes_in_db

from telegram import InlineQueryResultPhoto, Update
from telegram.ext import ContextTypes


# === ОСНОВНОЙ ОБРАБОТЧИК ===

async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    tg_id = update.inline_query.from_user.id
    username = update.inline_query.from_user.username or "Unknown"
    
    print(f"Запрос: '{query}' от {username} (ID: {tg_id})")
    
    db_results = search_memes_in_db(tg_id, query)
    print(db_results)
    # Создаем маппинг pic_id -> photo_url (временное решение)
    # photo_urls_mapping = {meme["id"]: meme["photo_url"] for meme in YOUR_MEMES}
    # print(photo_urls_mapping)
    db_memes = []
    for pic_id in db_results:
        # В реальном приложении здесь нужно получать данные мема из БД
        # Сейчас используем заглушку
        db_memes.append({
            "id": str(pic_id[0]),
            "title": f"Мем из БД {pic_id[0]}",
            "description": "Найден в базе данных",
            # "photo_url": photo_urls_mapping.get(str(pic_id), "https://i.ibb.co/WhpHnv7/Lainnizm.jpg"),
            # "thumbnail_url": photo_urls_mapping.get(str(pic_id), "https://i.ibb.co/WhpHnv7/Lainnizm.jpg"),
            "photo_url": pic_id[1],
            "thumbnail_url": pic_id[1],
            "tags": ["из_базы"]
        })
    
    # if not db_memes:
    #     print("В БД ничего не найдено, используем локальный поиск")
    #     found_memes = search_memes_by_tags(query, YOUR_MEMES, max_results=10)
    #     if not found_memes and query:
    #         found_memes = search_memes_by_category(query, YOUR_MEMES)
    #     if not found_memes:
    #         found_memes = YOUR_MEMES[:3]
    # else:
    #     found_memes = db_memes
    found_memes = db_memes
    # Создаем результаты для tg
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
