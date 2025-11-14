from database.db import Database
from bot.bot_inline_logic import inline_handler
from bot.bot_chat_logic import global_handler
from bot.bot_chat_logic import add_pic
from bot.bot_functions import handle_photo_message

from telegram.ext import Application, InlineQueryHandler, filters, MessageHandler, CommandHandler




def main():
    db = Database() 
    db._init_db()
    
    required_match = 0.2
    recs_len = 10
    ghosts = 10
    app = Application.builder().token("8458529948:AAEmS-rVnzjTFeh8Ri5QVefx_I9dAEnRPO8").build()

    async def message_router(update, context):
        await global_handler(update, context, db, ghosts)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))
    async def inline_router(update, context):
        await inline_handler(update, context, db,required_match,recs_len, ghosts)
    app.add_handler(InlineQueryHandler(inline_router))
    async def add_pic_router(update, context):
        await add_pic(update, context, True, db, ghosts)
    app.add_handler(CommandHandler("addmeme", add_pic_router))
    
    async def photo_message_router(update, context):
        await handle_photo_message(update, context, db, ghosts)
        
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.Document.IMAGE, 
        photo_message_router
    ))

    app.run_polling()

if __name__ == "__main__":
    main()
