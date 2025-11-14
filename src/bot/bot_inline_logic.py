from bot.database_calls import search_memes_in_db

from telegram import InlineQueryResultPhoto, Update
from telegram.ext import ContextTypes

from database.db import Database

# === MAIN INLINE HANDLER   ===

async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, required_match: float, recs_len: int, ghosts: int):
    query = update.inline_query.query
    tg_id = update.inline_query.from_user.id
    username = update.inline_query.from_user.username or "Unknown"
    
    print(f"Запрос: '{query}' от {username} (ID: {tg_id})")
    
    db_results = search_memes_in_db(tg_id, query, db, required_match, recs_len, ghosts)
   
    db_memes = []
    for pic_id in db_results:
        db_memes.append({
            "id": str(pic_id[0]),
            "title": f"Мем из БД {pic_id[0]}",
            "description": "Найден в базе данных",
            "photo_url": pic_id[1],
            "thumbnail_url": pic_id[1],
            "tags": ["из_базы"]
        })
    
    found_memes = db_memes

    results = []
    for meme in found_memes:
        results.append(
            InlineQueryResultPhoto(
                id=meme["id"],
                photo_url=meme["photo_url"],
                thumbnail_url=meme["thumbnail_url"],
                caption=f"{meme['id']}"
            )
        )
    
    await update.inline_query.answer(results, cache_time=1)
    print(f"Найдено {len(found_memes)} мемов по запросу '{query}'")