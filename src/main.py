from src.database.db import Database
from src.bot.bot_inline_logic import inline_handler
from src.bot.bot_chat_logic import global_handler

from telegram.ext import Application, InlineQueryHandler, filters, MessageHandler




def main():
    db = Database() 
    db._init_db()

    app = Application.builder().token("8265795628:AAGZ7gud7mTsr7SNcBwx-qae0CxwAZBWmB4").build()

    async def message_router(update, context):
        await global_handler(update, context, db, 10)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))
    app.add_handler(InlineQueryHandler(inline_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
