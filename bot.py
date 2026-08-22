from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import Bot_token
from telegram.ext import CallbackQueryHandler

from handlers.start_handler import start
from handlers.voice_handler import handle_voice
from handlers.error_handler import error_handler
from handlers.balance_handler import balance
from handlers.buy_handler import buy , handle_buy_callback
from handlers.help_handler import help_command
def main():
    app = Application.builder().token(Bot_token).build()

    app.add_handler(CommandHandler("start", start))
    
    app.add_handler(MessageHandler(filters.Document.ALL| filters.VOICE| filters.AUDIO, handle_voice))
    
    app.add_handler(CommandHandler("balance", balance))

    app.add_handler(CommandHandler("buy", buy))

    app.add_handler(CallbackQueryHandler(handle_buy_callback, pattern=r"^buy:"))
    
    app.add_handler(CommandHandler("help", help_command))

    app.add_error_handler(error_handler)

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()