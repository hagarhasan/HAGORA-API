
import logging

from sqlalchemy import inspect, text

from database import engine

logger = logging.getLogger(__name__)


def run_migrations():
    with engine.begin() as connection:
        inspector = inspect(connection)
        tables = inspector.get_table_names()

        if "users" not in tables:
            raise RuntimeError(
                "The users table does not exist. "
                "Create the database tables first."
            )

        user_columns = {
            column["name"]
            for column in inspector.get_columns("users")
        }

        user_migrations = {
            "governorate": "VARCHAR",
            "username_changed_at": "TIMESTAMP",
            "notification_preferences": "VARCHAR",
        }

        for column_name, column_type in user_migrations.items():
            if column_name not in user_columns:
                connection.execute(
                    text(
                        f"ALTER TABLE users "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                )

        collisions = connection.execute(
            text(
                "SELECT lower(email) FROM users "
                "GROUP BY lower(email) HAVING COUNT(*) > 1"
            )
        ).fetchall()

        if collisions:
            logger.warning(
                "Skipped lowercasing user emails because "
                "%s case-insensitive email collision(s) exist.",
                len(collisions),
            )
        else:
            connection.execute(
                text(
                    "UPDATE users SET email = lower(email) "
                    "WHERE email != lower(email)"
                )
            )

        # Refresh the inspector after schema changes.
        inspector = inspect(connection)
        tables = inspector.get_table_names()

        if "orders" in tables:
            order_columns = {
                column["name"]
                for column in inspector.get_columns("orders")
            }

            order_migrations = {
                "payment_method": "VARCHAR DEFAULT 'cod'",
                "payment_status": "VARCHAR DEFAULT 'unpaid'",
                "idempotency_key": "VARCHAR",
                "shipping_governorate_code": "VARCHAR",
                "shipping_governorate_name": "VARCHAR",
                "currency": "VARCHAR DEFAULT 'EGP'",
            }

            for column_name, column_type in order_migrations.items():
                if column_name not in order_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE orders "
                            f"ADD COLUMN {column_name} {column_type}"
                        )
                    )

            connection.execute(
                text(
                    "UPDATE orders "
                    "SET payment_method = 'cod' "
                    "WHERE payment_method IS NULL"
                )
            )

            connection.execute(
                text(
                    "UPDATE orders "
                    "SET payment_status = 'unpaid' "
                    "WHERE payment_status IS NULL"
                )
            )

            connection.execute(
                text(
                    "UPDATE orders "
                    "SET currency = 'EGP' "
                    "WHERE currency IS NULL"
                )
            )
