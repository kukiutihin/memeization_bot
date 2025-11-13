from telegram import Update
from telegram.ext import ContextTypes
from telegram import InputMediaPhoto

from bot.database_calls import add_meme_to_db, add_to_favorites, remove_fav
from database.db import Database

async def add_pic(update: Update, context: ContextTypes.DEFAULT_TYPE, is_private: bool, db: Database, ghosts: int):
    if not context.args:
        await update.message.reply_text(
            "Пришлите изображение и теги через запятую, либо вернитесь в меню"
        )
        return
    
    try:
        print(context.args)
        if len(context.args) < 2:
            await update.message.reply_text("Пришлите изображение и теги через запятую")
            return
        
        photo_url = context.args[0]
        tags_str = context.args[1]
        
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        
        if not tags:
            await update.message.reply_text("Укажите хотя бы один тег")
            return
        
        tg_id = update.effective_user.id
        
        add_meme_to_db(tg_id, photo_url, tags, db, ghosts, is_private)
        print("Мем добавлен")
            
    except Exception as e:
        await update.message.reply_text(f"Ошибка при обработке команды: {str(e)}")
        print(f"Ошибка в add_meme_command: {e}")
    

async def add_pic_from_pid(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    if not context.args:
        await update.message.reply_text(
            "Чтобы добавить изображение в избранные, напишите PID"
        )
        return
    
    try:
        meme_id_str = context.args[0]
        
        if not meme_id_str.isdigit():
            await update.message.reply_text("PID должен быть числом")
            return
        
        meme_id = int(meme_id_str)
        tg_id = update.effective_user.id
        
        add_to_favorites(tg_id, meme_id, db)
                    
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")
        print(f"Ошибка в add_meme_from_id_simple_command: {e}")


async def remove_from_fav(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    if not context.args:
        await update.message.reply_text(
            "Чтобы удалить изображение из избранных, напишите PID"
        )
        return
    
    try:
        meme_id_str = context.args[0]
        
        if not meme_id_str.isdigit():
            await update.message.reply_text("PID должен быть числом")
            return
        
        meme_id = int(meme_id_str)
        tg_id = update.effective_user.id
        
        remove_fav(tg_id, meme_id, db)
                    
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")
        print(f"Ошибка в add_meme_from_id_simple_command: {e}")
        
async def send_images_any(update: Update, image_tuples: list):
    media_group = []
    
    for image_id, image_url in image_tuples:
        media_group.append(
            InputMediaPhoto(
                media=image_url,
                caption=f"🆔 ID: {image_id}"
            )
        )
    
    await update.message.reply_media_group(media=media_group)