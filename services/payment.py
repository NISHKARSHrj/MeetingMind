import os
import uuid
import requests

from dotenv import load_dotenv

load_dotenv()

cashfree_app_id = os.getenv("cashfree_appid")
cashfree_secret_key = os.getenv("cashfree_secretkey")
cashfree_env = os.getenv("cashfree_env", "sandbox")

if cashfree_env == "production":
    cashfree_base_url = "https://api.cashfree.com/pg"
else:
    cashfree_base_url = "https://sandbox.cashfree.com/pg"

def create_payment_link(
    customer_id: int,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    amount: float,
    credits: int,
):
    link_id = (
        f"mm_{customer_id}_{uuid.uuid4().hex[:10]}"
    )

    payload = {
        "link_id": link_id,

        "link_amount": amount,

        "link_currency": "INR",

        "link_purpose": (
            f"MeetingMind - {credits} Credits"
        ),

        "link_partial_payments": False,

        "customer_details": {
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "customer_email": customer_email,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-client-id": cashfree_app_id,
        "x-client-secret": cashfree_secret_key,
        "x-api-version": "2025-01-01",
    }

    response = requests.post(
        f"{cashfree_base_url}/links",
        json=payload,
        headers=headers,
        timeout=30,
    )

    print("Cashfree status:", response.status_code)
    print("Cashfree response:", response.text)

    response.raise_for_status()

    return response.json()

def create_order(
    customer_id: int,
    customer_name: str,
    customer_email: str,
    amount: float,
    credits: int
):
    order_id = f"meetingmind_{customer_id}_{uuid.uuid4().hex[:10]}"

    payload = {
        "order_id": order_id,
        "order_amount": amount,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(customer_id),
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": "9999999999",
        },
        "order_tags": {
            "credits": str(credits),
            "user_id": str(customer_id),

        }
    }
    headers = {
        "Content-Type": "application/json",
        "x-client-id": cashfree_app_id,
        "x-client-secret": cashfree_secret_key,
        "x-api-version": "2025-01-01",
    }
    response = requests.post(
        f"{cashfree_base_url}/orders",
        json=payload,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()