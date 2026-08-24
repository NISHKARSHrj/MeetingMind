import os
import hmac
import base64
import hashlib

from flask import Flask, request, jsonify
from dotenv import load_dotenv

from utils.logger import logger

from services.payment_records import (
    process_successful_payment
)


load_dotenv()

app = Flask(__name__)


CASHFREE_SECRET_KEY = os.getenv(
    "cashfree_secretkey"
)


def verify_cashfree_signature(
    raw_body: bytes,
    timestamp: str,
    signature: str
) -> bool:

    if not CASHFREE_SECRET_KEY:

        logger.error(
            "CASHFREE_SECRET_KEY is missing."
        )

        return False

    signed_payload = (
        timestamp +
        raw_body.decode("utf-8")
    )

    generated_signature = base64.b64encode(
        hmac.new(
            CASHFREE_SECRET_KEY.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256
        ).digest()
    ).decode("utf-8")

    return hmac.compare_digest(
        generated_signature,
        signature
    )


@app.route(
    "/webhook/cashfree",
    methods=["POST"]
)
def cashfree_webhook():

    try:
        # Get raw request body

        raw_body = request.get_data()

        timestamp = request.headers.get(
            "x-webhook-timestamp"
        )

        signature = request.headers.get(
            "x-webhook-signature"
        )

        
        # Check webhook headers
        
        if not timestamp or not signature:

            logger.warning(
                "Missing Cashfree webhook headers."
            )

            return jsonify({
                "error": "Missing webhook signature"
            }), 400

        
        # Verify Cashfree signature
        
        is_valid = verify_cashfree_signature(
            raw_body=raw_body,
            timestamp=timestamp,
            signature=signature
        )

        if not is_valid:

            logger.warning(
                "Invalid Cashfree webhook signature."
            )

            return jsonify({
                "error": "Invalid signature"
            }), 401

        # Parse JSON
        
        data = request.get_json()

        logger.info(
            f"Verified Cashfree webhook: {data}"
        )

        # Check event type
        
        event_type = data.get("type")

        if event_type != "PAYMENT_SUCCESS_WEBHOOK":

            logger.info(
                f"Ignoring webhook event: {event_type}"
            )

            return jsonify({
                "status": "ignored"
            }), 200

        # Payment information
        
        payment_data = (
            data
            .get("data", {})
            .get("payment", {})
        )

        payment_status = payment_data.get(
            "payment_status"
        )

        payment_amount = payment_data.get(
            "payment_amount"
        )

        # Order information
        
        order_data = (
            data
            .get("data", {})
            .get("order", {})
        )

        order_tags = order_data.get(
            "order_tags",
            {}
        )

        link_id = order_tags.get(
            "link_id"
        )

        # Check payment status
        
        if payment_status != "SUCCESS":

            logger.info(
                f"Payment not successful: "
                f"{payment_status}"
            )

            return jsonify({
                "status": "payment_not_successful"
            }), 200

        # Check link_id
        
        if not link_id:

            logger.error(
                "link_id missing from Cashfree webhook."
            )

            return jsonify({
                "error": "link_id missing"
            }), 400

        # Check payment amount
        
        if payment_amount is None:

            logger.error(
                f"payment_amount missing: {link_id}"
            )

            return jsonify({
                "error": "payment_amount missing"
            }), 400

        logger.info(
            f"Processing successful payment: "
            f"{link_id}"
        )

        # Process payment atomically
        
        result = process_successful_payment(
            link_id=link_id,
            payment_amount=payment_amount
        )

        # Payment not found
        
        if result["status"] == "NOT_FOUND":

            logger.error(
                f"Payment record not found: "
                f"{link_id}"
            )

            return jsonify({
                "error": "Payment record not found"
            }), 404

        # User not found

        if result["status"] == "USER_NOT_FOUND":

            logger.error(
                f"User not found: "
                f"{result['user_id']}"
            )

            return jsonify({
                "error": "User not found"
            }), 404

        # Amount mismatch

        if result["status"] == "AMOUNT_MISMATCH":

            logger.error(
                f"Payment amount mismatch "
                f"for {link_id}: "
                f"Cashfree={result['payment_amount']} "
                f"Database={result['amount']}"
            )

            return jsonify({
                "error": "Payment amount mismatch"
            }), 400

        # Duplicate payment
        
        if result["status"] == "ALREADY_PAID":

            logger.info(
                f"Payment already processed: "
                f"{link_id}"
            )

            return jsonify({
                "status": "already_processed"
            }), 200

        
        # Payment successfully processed

        if result["status"] == "PAID":

            logger.info(
                f"Added {result['credits']} credits "
                f"to user {result['user_id']}"
            )

            return jsonify({
                "status": "payment_processed",
                "user_id": result["user_id"],
                "credits_added": result["credits"]
            }), 200

        # Unknown result
        
        logger.error(
            f"Unknown payment processing result: "
            f"{result}"
        )

        return jsonify({
            "error": "Unknown payment processing result"
        }), 500

    except Exception as e:

        logger.exception(
            "Webhook processing failed."
        )

        return jsonify({
            "error": "Webhook processing failed"
        }), 500


@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "status": "ok",
        "service": "MeetingMind"
    })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )