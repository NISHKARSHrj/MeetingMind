from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

from datetime import datetime

from services.archive import archive_audio
from services.transcriber import transcribe_audio
from services.summarizer import generate_summary

from utils.logger import logger
from config import path

from services.credits import get_balance, deduct_credits, has_credits
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    user_id = update.effective_user.id
    
    if not has_credits(user_id):

        await update.message.reply_text(
            "❌ Free Trial Finished!\n\n"
            "❌ You have no free credits left.\n\n"
            "Use /buy to purchase more credits."
        )
        return

    
    if update.message.voice:
        telegram_file = update.message.voice
        extension = "ogg"

    elif update.message.audio:
        telegram_file = update.message.audio
        extension = "mp3"

    elif update.message.document:
        telegram_file = update.message.document
        filename = telegram_file.file_name
        extension = filename.split(".")[-1]

    else:
        await update.message.reply_text("❌ Unsupported file.")
        return
    logger.info("Fetching file from Telegram...")
    file = await context.bot.get_file(
        telegram_file.file_id
    )
    logger.info("File fetched successfully.")
    username = update.effective_user.username or "unknown"

    timestamp = update.message.date.strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    save_path = f"{path}{username}_{timestamp}.{extension}"

    await file.download_to_drive(save_path)
    processing = await update.message.reply_text(
        "🎙️ Audio received.\n\n⏳ Processing..."
    )
    logger.info(f"Audio saved to {save_path}")
    await archive_audio(
        bot=context.bot,
        file_path=save_path,
        username=username,
        timestamp=timestamp
    )
    try:
        await processing.edit_text(
            "📝 Transcribing audio..."
        )

        transcript = transcribe_audio(save_path)

        logger.info("Audio downloaded successfully.")
        
        await processing.edit_text(
            "🧠 Generating meeting summary..."
        )

        summary = generate_summary(transcript)
        deduct_credits(user_id)
        
        remaining = get_balance(user_id)

        summary += ("\n\n━━━━━━━━━━━━━━"
        f"\n💳 Credits Left: {remaining}"
        )
        await processing.edit_text(summary)

    except Exception as e:

        logger.exception(e)
        await update.message.reply_text("❌ Error occurred while processing the audio.")

    finally:

        try:
            Path(save_path).unlink(missing_ok=True)
            logger.info("🗑 Temporary file deleted.")

        except Exception as cleanup_error:
            logger.exception(cleanup_error)