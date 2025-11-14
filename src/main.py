from database.db import Database
from bot.bot_inline_logic import inline_handler
from bot.bot_chat_logic import global_handler, start, handle_photo_message
# from bot.bot_functions import handle_photo_message
from config import Config

from telegram.ext import Application, InlineQueryHandler, filters, MessageHandler, CommandHandler


def main():
    db = Database() 
    db._init_db()

    cfg = Config()
    
    required_match = float(cfg.find.required_match_score)
    recs_len = int(cfg.find.recommendations_count)
    ghosts = int(cfg.tags.ghosts_count)
    token = str(cfg.bot.token)

    app = Application.builder().token(token).build()

    async def message_router(update, context):
        await global_handler(update, context, db, ghosts)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))

    async def inline_router(update, context):
        await inline_handler(update, context, db,required_match,recs_len, ghosts)

    app.add_handler(InlineQueryHandler(inline_router))

    async def start_router(update, context):
        await start(update, context, db, ghosts)

    app.add_handler(CommandHandler("start", start_router))
        
    async def photo_message_router(update, context):
        await handle_photo_message(update, context, db, ghosts)
        
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.Document.IMAGE, 
        photo_message_router
    ))

    app.run_polling()

if __name__ == "__main__":
    main()
