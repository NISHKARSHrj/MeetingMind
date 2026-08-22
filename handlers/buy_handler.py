from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import ContextTypes

from services.payment import create_payment_link
from services.packages import PACKAGES


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = []

    for package_id, package in PACKAGES.items():

        button_text = (
            f"🎟️ {package['name']} • "
            f"{package['credits']} Credits • "
            f"₹{package['price']}"
        )

        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"buy:{package_id}"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💳 *MeetingMind Credits*\n\n"
        "Choose a package below:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_buy_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    package_id = query.data.split(":")[1]

    package = PACKAGES.get(package_id)

    if not package:
        await query.edit_message_text(
            "❌ Invalid package."
        )
        return

    user = query.from_user

    try:

        payment = create_payment_link(
            customer_id=user.id,
            customer_name=user.first_name or "MeetingMind User",
            customer_email=f"{user.id}@meetingmind.local",
            customer_phone="9999999999",
            amount=package["price"],
            credits=package["credits"],
        )

        payment_url = payment.get("link_url")

        if not payment_url:
            raise ValueError(
                "Cashfree did not return payment URL."
            )

        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 Pay Now",
                    url=payment_url
                )
            ]
        ]

        reply_markup = InlineKeyboardMarkup(
            keyboard
        )

        await query.edit_message_text(
            f"🧠 *MeetingMind*\n\n"
            f"📦 Package: {package['name']}\n"
            f"🎟️ Credits: {package['credits']}\n"
            f"💰 Price: ₹{package['price']}\n\n"
            f"Click below to continue with payment.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:

        print(f"Payment error: {e}")

        await query.edit_message_text(
            "❌ Could not create payment link.\n\n"
            "Please try again later."
        )