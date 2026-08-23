from services.database import connection, cursor


def create_payment_record(
    link_id: str,
    user_id: int,
    credits: int,
    amount: float
):

    cursor.execute(
        """
        INSERT INTO payments (
            link_id,
            user_id,
            credits,
            amount,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            link_id,
            user_id,
            credits,
            amount,
            "PENDING"
        )
    )

    connection.commit()


def get_payment_record(link_id: str):

    cursor.execute(
        """
        SELECT
            id,
            link_id,
            user_id,
            credits,
            amount,
            status,
            created_at
        FROM payments
        WHERE link_id = ?
        """,
        (link_id,)
    )

    return cursor.fetchone()


def process_successful_payment(
    link_id: str,
    payment_amount: float
):

    try:

        # --------------------------------
        # Get payment
        # --------------------------------

        cursor.execute(
            """
            SELECT
                user_id,
                credits,
                amount,
                status
            FROM payments
            WHERE link_id = ?
            """,
            (link_id,)
        )

        payment = cursor.fetchone()

        if not payment:

            return {
                "status": "NOT_FOUND"
            }

        user_id, credits, amount, status = payment

        # --------------------------------
        # Duplicate protection
        # --------------------------------

        if status == "PAID":

            return {
                "status": "ALREADY_PAID",
                "user_id": user_id,
                "credits": credits,
                "amount": amount
            }

        # --------------------------------
        # Amount verification
        # --------------------------------

        if float(payment_amount) != float(amount):

            return {
                "status": "AMOUNT_MISMATCH",
                "user_id": user_id,
                "credits": credits,
                "amount": amount,
                "payment_amount": payment_amount
            }

        # --------------------------------
        # Get current user
        # --------------------------------

        cursor.execute(
            """
            SELECT credits
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:

            return {
                "status": "USER_NOT_FOUND"
            }

        # --------------------------------
        # Mark payment PAID
        # --------------------------------

        cursor.execute(
            """
            UPDATE payments
            SET status = 'PAID'
            WHERE link_id = ?
            AND status = 'PENDING'
            """,
            (link_id,)
        )

        # --------------------------------
        # Add credits
        # --------------------------------

        cursor.execute(
            """
            UPDATE users
            SET credits = credits + ?
            WHERE user_id = ?
            """,
            (
                credits,
                user_id
            )
        )

        # --------------------------------
        # Commit BOTH operations
        # --------------------------------

        connection.commit()

        return {
            "status": "PAID",
            "user_id": user_id,
            "credits": credits,
            "amount": amount
        }

    except Exception:

        # --------------------------------
        # Rollback everything
        # --------------------------------

        connection.rollback()

        raise