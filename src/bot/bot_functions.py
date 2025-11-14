from telegram import Update
from telegram.ext import ContextTypes
from telegram import InputMediaPhoto

from bot.database_calls import add_meme_to_db, add_to_favorites, remove_fav
from database.db import Database


async def add_pic(update: Update, context: ContextTypes.DEFAULT_TYPE, is_private: bool, db: Database, ghosts: int):
    if not context.args:
        await update.message.reply_text(
            "Пришлите изображение и теги через запятую"
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
    try:
        meme_id_str = update.message.text 
        # print(meme_id_str, context)
        meme_id = int(meme_id_str)
        tg_id = update.effective_user.id
        if add_to_favorites(tg_id, meme_id, db):
            await update.message.reply_text("Изображение добавлено в избранные ✅")
        else:
            await update.message.reply_text("Ошибка, возможно id не существует ❌")
        # print(5)
    except ValueError:
        await update.message.reply_text("Введите корректный ID изображения")

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")
        print(f"Ошибка в add_pic_from_pid: {e}")



async def remove_from_fav(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    try:
        meme_id_str = update.message.text
        meme_id = int(meme_id_str)
        tg_id = update.effective_user.id
        
        if remove_fav(tg_id, meme_id, db):
            await update.message.reply_text("Изображение удалено из избранных ✅")
        else:
            await update.message.reply_text("Ошибка, возможно id не существует ❌")
        
    except ValueError:
        await update.message.reply_text("Введите корректный ID изображения")

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")
        print(f"Ошибка в remove_from_fav: {e}")

        

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

# async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database,  ghosts: int):
#     from bot.bot_chat_logic import load_bool

#     try:
#         if not update.message or not (update.message.photo or update.message.document):
#             return
        
#         tg_id = update.effective_user.id
#         username = update.effective_user.username or "Unknown"
#         caption = update.message.caption or ""
        
#         if update.message.photo:
#             photo = update.message.photo[-1]
#             file_id = photo.file_id
#             file_type = "photo"

#         elif update.message.document:
#             document = update.message.document
            
#             if document.mime_type is None or document.mime_type.startswith('image/'):
#                 file_id = document.file_id
#                 file_type = "document"

#             else:
#                 await update.message.reply_text("Пожалуйста, отправьте изображение")
#                 return

#         else:
#             return
        
#         parts = caption.split()
#         if not parts:
#             await update.message.reply_text(
#                 "Укажите теги в подписи к изображению"
#             )
#             return
        
#         is_private = load_bool.get(tg_id, False)
#         tags = [tag.strip() for tag in caption.split(',') if tag.strip()]
        
#         success = add_meme_to_db(tg_id, file_id, tags, db,ghosts, is_private)
        
#         if success:
#             response_text = (
#                 "Изображение успешно добавлено🎉"
#             )
            
#             await update.message.reply_text(response_text)
            
#             print(f"Добавлено новое изображение от {username}: {tags} (file_id: {file_id})")
#         else:
#             await update.message.reply_text("Ошибка при добавлении изображения в базу данных")
            
#     except Exception as e:
#         await update.message.reply_text(f"Ошибка при обработке изображения: {str(e)}")
#         print(f"Ошибка в handle_photo_message: {e}")