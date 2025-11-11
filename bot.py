import logging
from telegram import InlineQueryResultPhoto, Update
from telegram.ext import Application, InlineQueryHandler, ContextTypes

BOT_TOKEN = "8458529948:AAEmS-rVnzjTFeh8Ri5QVefx_I9dAEnRPO8"

YOUR_MEMES = [
    {
        "id": "1", 
        "title": "swag",
        "description": "Glaz",
        "photo_url": "https://radika1.link/2025/11/11/r6pxlz8oRjBOGrU9VLuqgAd63d0b2828dc4414.jpeg",
        "thumbnail_url": "https://radika1.link/2025/11/11/r6pxlz8oRjBOGrU9VLuqgAd63d0b2828dc4414.jpeg",
        "tags": ["кот", "cat", "смешной", "животные"]
    },
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

def search_memes_by_tags(query, memes_list, max_results=10):
    """
    Функция поиска мемов по тегам
    
    Args:
        query (str): поисковый запрос
        memes_list (list): список мемов для поиска
        max_results (int): максимальное количество результатов
    
    Returns:
        list: отфильтрованный список мемов
    """
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
    """
    Функция поиска по категориям 
    
    Args:
        query (str): поисковый запрос
        memes_list (list): список мемов для поиска
    
    Returns:
        list: отфильтрованный список мемов
    """
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

async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    print(f"Запрос: '{query}' от {update.inline_query.from_user.first_name}")
    found_memes = search_memes_by_tags(query, YOUR_MEMES, max_results=10)
    if not found_memes and query:
        found_memes = search_memes_by_category(query, YOUR_MEMES)

    if not found_memes:
        found_memes = YOUR_MEMES[:3]
    
    results = []
    for meme in found_memes:
        results.append(
            InlineQueryResultPhoto(
                id=meme["id"],
                photo_url=meme["photo_url"],
                thumbnail_url=meme["thumbnail_url"],
                title=meme["title"],
                description=meme["description"],
                # caption=f"id {meme['id']}"
                caption=f"{meme['title']}\n {meme['description']}\n Теги: {', '.join(meme['tags'])} \n ID:{meme['id']}"
            )
        )
    
    await update.inline_query.answer(results, cache_time=1)
    print(f"Найдено {len(found_memes)} мемов по запросу '{query}', отправлено {len(results)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(InlineQueryHandler(inline_handler))
    
    print("=" * 50)
    print("Бот запущен")
    print("=" * 50)
    app.run_polling()

if __name__ == "__main__":
    main()