
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    username = Column(String, unique=True, index=True, nullable=True)
    username_changed_at = Column(DateTime(timezone=True), nullable=True)

    phone = Column(String, index=True, nullable=True)
    governorate = Column(String, nullable=True)
    city = Column(String, nullable=True)
    address = Column(String, nullable=True)
    notification_preferences = Column(String, nullable=True)

    orders = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(String, nullable=False, default="pending")
    payment_method = Column(String, nullable=False, default="cod")
    payment_status = Column(String, nullable=False, default="unpaid")
    idempotency_key = Column(String, unique=True, index=True, nullable=True)
    shipping_governorate_code = Column(String, nullable=True)
    shipping_governorate_name = Column(String, nullable=True)
    subtotal = Column(Float, nullable=False)
    discount_code = Column(String, nullable=True)
    discount_amount = Column(Float, nullable=False, default=0)
    shipping_cost = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="EGP")

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    governorate = Column(String, nullable=False)
    city = Column(String, nullable=False)
    address = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint(
            "order_id",
            "product_id",
            name="uq_order_product",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)

    product_id = Column(Integer, nullable=False)
    product_name = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    product_image = Column(String, nullable=True)

    unit_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    line_total = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
