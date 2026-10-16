
import json
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import engine
from models import Base, User, PasswordResetToken, Order, OrderItem
from schemas import (
    UserCreate,
    UserLogin,
    BasicProfileUpdate,
    NameUpdate,
    UsernameUpdate,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    NotificationPreferencesUpdate,
    ProfileUpdate,
    OrderCreateRequest,
)
from security import (
    hash_password,
    verify_password,
    create_access_token,
    create_reset_token,
)
from dependencies import get_current_user, get_db
from email_service import send_reset_email
from migrations import run_migrations
from shipping import (
    EGYPT_GOVERNORATES,
    GOVERNORATE_SHIPPING_RATES,
    get_governorate_by_code,
    get_shipping_rate_for_governorate,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://hagarhasan.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
run_migrations()


PRODUCT_CATALOG = {
    1: {
        "id": 1,
        "name": "Hydrating Serum",
        "brand": "HAGORA",
        "price": 220.0,
        "image_link": "",
    },
    2: {
        "id": 2,
        "name": "Velvet Lip Gloss",
        "brand": "HAGORA",
        "price": 180.0,
        "image_link": "",
    },
    3: {
        "id": 3,
        "name": "Glow Foundation",
        "brand": "HAGORA",
        "price": 320.0,
        "image_link": "",
    },
    4: {
        "id": 4,
        "name": "Radiant Concealer",
        "brand": "HAGORA",
        "price": 260.0,
        "image_link": "",
    },
    5: {
        "id": 5,
        "name": "Daily Cleanser",
        "brand": "HAGORA",
        "price": 210.0,
        "image_link": "",
    },
    6: {
        "id": 6,
        "name": "Soft Matte Blush",
        "brand": "HAGORA",
        "price": 170.0,
        "image_link": "",
    },
}


def normalize_name(value: str | None) -> str:
    return " ".join((value or "").split())


def ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def is_profile_completed(user: User) -> bool:
    return all([
        user.username,
        user.phone,
        user.governorate,
        user.city,
        user.address,
    ])


def user_public_fields(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "phone": user.phone,
        "governorate": user.governorate,
        "city": user.city,
        "address": user.address,
    }


def get_profile_response(user: User):
    next_change_at = None

    if user.username_changed_at is not None:
        next_change_at = (
            ensure_utc(user.username_changed_at) + timedelta(days=60)
        )

    return {
        **user_public_fields(user),
        "username_changed_at": (
            ensure_utc(user.username_changed_at).isoformat()
            if user.username_changed_at
            else None
        ),
        "next_username_change_at": (
            next_change_at.isoformat() if next_change_at else None
        ),
        "profile_completed": is_profile_completed(user),
    }


def serialize_order(order: Order) -> dict[str, Any]:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "subtotal": round(float(order.subtotal), 2),
        "discount_code": order.discount_code,
        "discount_amount": round(float(order.discount_amount), 2),
        "shipping_cost": round(float(order.shipping_cost), 2),
        "total": round(float(order.total), 2),
        "currency": order.currency,
        "first_name": order.first_name,
        "last_name": order.last_name,
        "phone": order.phone,
        "governorate": order.governorate,
        "city": order.city,
        "address": order.address,
        "created_at": (
            order.created_at.isoformat() if order.created_at else None
        ),
        "updated_at": (
            order.updated_at.isoformat() if order.updated_at else None
        ),
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "brand": item.brand,
                "product_image": item.product_image,
                "unit_price": round(float(item.unit_price), 2),
                "quantity": item.quantity,
                "line_total": round(float(item.line_total), 2),
            }
            for item in order.items
        ],
    }


def normalize_remote_product(item: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {
            "id": 0,
            "name": "Product",
            "brand": "HAGORA",
            "price": 0.0,
            "image_link": "",
            "api_featured_image": "",
        }

    price = item.get("price")
    try:
        price_value = float(price) if price not in (None, "") else 0.0
    except (TypeError, ValueError):
        price_value = 0.0

    image_link = (
        item.get("api_featured_image")
        or item.get("image_link")
        or ""
    )

    return {
        "id": int(item.get("id")) if item.get("id") is not None else 0,
        "name": item.get("name") or "Product",
        "brand": item.get("brand") or "HAGORA",
        "price": price_value,
        "category": item.get("product_type") or item.get("category") or "makeup",
        "product_type": item.get("product_type") or item.get("category") or "makeup",
        "description": item.get("description") or "",
        "image_link": image_link,
        "api_featured_image": image_link,
        "product_link": item.get("product_link") or "",
        "website_link": item.get("website_link") or "",
        "rating": item.get("rating"),
        "tag_list": item.get("tag_list") or [],
    }


def fetch_remote_products() -> list[dict[str, Any]]:
    with urllib.request.urlopen(
        "https://makeup-api.herokuapp.com/api/v1/products.json",
        timeout=15,
    ) as response:
        data = json.loads(response.read().decode("utf-8"))

    if not isinstance(data, list):
        raise ValueError("Remote catalog payload is not a list")

    return [
        normalize_remote_product(item)
        for item in data
        if item and item.get("id") is not None
    ]


@app.get("/products")
def list_products():
    try:
        return fetch_remote_products()
    except Exception:
        return [
            normalize_remote_product(product)
            for product in PRODUCT_CATALOG.values()
        ]


def load_catalog_lookup() -> dict[int, dict[str, Any]]:
    """Fetch the remote catalog once per request, not once per order line."""
    try:
        return {
            int(item["id"]): item
            for item in fetch_remote_products()
            if item.get("id") is not None
        }
    except Exception:
        return {}


def get_catalog_product(
    product_id: int,
    lookup: dict[int, dict[str, Any]] | None = None,
):
    product_id = int(product_id)

    if lookup is None:
        lookup = load_catalog_lookup()

    if product_id in lookup:
        return lookup[product_id]

    static_product = PRODUCT_CATALOG.get(product_id)

    if static_product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return static_product


def get_username_change_status(user: User):
    if user.username_changed_at is None:
        return {
            "eligible": True,
            "next_change_at": None,
            "remaining_seconds": 0,
        }

    last_changed_at = ensure_utc(user.username_changed_at)
    next_change_at = last_changed_at + timedelta(days=60)
    now = datetime.now(timezone.utc)
    remaining = max(0, (next_change_at - now).total_seconds())

    return {
        "eligible": now >= next_change_at,
        "next_change_at": next_change_at.isoformat(),
        "remaining_seconds": remaining,
    }


def enforce_username_change(
    db: Session,
    user: User,
    new_username: str,
):
    if not new_username:
        return

    clean_username = new_username.strip().lower()

    if clean_username == (user.username or "").strip().lower():
        return

    duplicate = (
        db.query(User)
        .filter(
            User.username == clean_username,
            User.id != user.id,
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Username already taken",
        )

    status = get_username_change_status(user)

    if not status["eligible"]:
        next_change_at = status["next_change_at"]

        raise HTTPException(
            status_code=409,
            detail=(
                "Username can only be changed once every 60 days. "
                f"Next eligible date: {next_change_at}"
            ),
        )

    user.username = clean_username
    user.username_changed_at = datetime.now(timezone.utc)


@app.get("/")
def home():
    return {"message": "Backend is working!"}


@app.get("/governorates")
def get_governorates():
    return {
        "governorates": [
            {
                "code": item["code"],
                "name_en": item["name_en"],
                "name_ar": item["name_ar"],
                "shipping_rate": float(
                    GOVERNORATE_SHIPPING_RATES[item["code"]]
                ),
            }
            for item in EGYPT_GOVERNORATES
        ],
        "shipping_rates": GOVERNORATE_SHIPPING_RATES,
    }


@app.post("/register")
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    new_user = User(
        email=user.email,
        password=hash_password(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
    )

    db.add(new_user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    db.refresh(new_user)

    access_token = create_access_token({"sub": str(new_user.id)})

    return {
        "message": "User registered successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
        },
    }


@app.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if not existing_user or not verify_password(
        user.password, existing_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        {"sub": str(existing_user.id)}
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return get_profile_response(current_user)


# Disabled until a real admin-role authorization system is implemented.
@app.get("/users")
def get_users():
    raise HTTPException(
        status_code=403,
        detail="Admin access is not configured.",
    )


@app.put("/me/name")
def update_name(
    profile: NameUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.first_name = normalize_name(profile.first_name)
    current_user.last_name = normalize_name(profile.last_name)

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Name updated successfully",
        "user": user_public_fields(current_user),
    }


@app.put("/me/basic-profile")
def update_basic_profile(
    profile: BasicProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_email = (
        db.query(User)
        .filter(
            User.email == profile.email,
            User.id != current_user.id,
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    current_user.first_name = normalize_name(profile.first_name)
    current_user.last_name = normalize_name(profile.last_name)
    current_user.email = profile.email

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Basic profile updated successfully",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
        },
    }


@app.put("/me/username")
def update_username(
    payload: UsernameUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_username_change(db, current_user, payload.username)

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Username updated successfully",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
        },
        "username_change_status": get_username_change_status(current_user),
    }


@app.put("/me/profile")
def update_profile(
    profile: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if profile.username is not None:
        enforce_username_change(db, current_user, profile.username)

    if profile.phone is not None:
        current_user.phone = profile.phone

    if profile.governorate is not None:
        current_user.governorate = profile.governorate

    if profile.city is not None:
        current_user.city = profile.city

    if profile.address is not None:
        current_user.address = profile.address

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile updated successfully",
        "user": user_public_fields(current_user),
    }


@app.put("/me/password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(request.current_password, current_user.password):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect",
        )

    current_user.password = hash_password(request.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@app.get("/me/notification-preferences")
def get_notification_preferences(
    current_user: User = Depends(get_current_user),
):
    defaults = {
        "orderUpdates": True,
        "promotions": False,
        "newsletter": False,
    }

    if not current_user.notification_preferences:
        return {"preferences": defaults}

    try:
        preferences = json.loads(current_user.notification_preferences)
    except (TypeError, json.JSONDecodeError):
        preferences = defaults

    return {"preferences": {**defaults, **preferences}}


@app.put("/me/notification-preferences")
def update_notification_preferences(
    preferences: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved_preferences = preferences.model_dump()
    current_user.notification_preferences = json.dumps(saved_preferences)
    db.commit()

    return {
        "message": "Notification preferences saved",
        "preferences": saved_preferences,
    }


@app.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    message = {
        "message": "If the email exists, a reset link has been sent."
    }

    if not user:
        return message

    token = create_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    reset_token = PasswordResetToken(
        token=token,
        user_id=user.id,
        expires_at=expires_at,
    )

    db.add(reset_token)
    db.commit()

    background_tasks.add_task(
        send_reset_email,
        user.email,
        token,
    )

    return message


@app.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == request.token)
        .first()
    )

    if not reset_token:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token",
        )

    expires_at = reset_token.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        db.delete(reset_token)
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token",
        )

    user = (
        db.query(User)
        .filter(User.id == reset_token.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid reset token",
        )

    user.password = hash_password(request.new_password)

    db.delete(reset_token)
    db.commit()

    return {"message": "Password reset successfully"}


@app.post("/orders")
def create_order(
    request: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not request.items:
        raise HTTPException(
            status_code=400,
            detail="Order must include at least one item",
        )

    if request.idempotency_key:
        existing = (
            db.query(Order)
            .filter(
                Order.user_id == current_user.id,
                Order.idempotency_key == request.idempotency_key,
            )
            .first()
        )

        if existing:
            return {
                "message": "Order already created",
                "order": serialize_order(existing),
            }

    shipping_rate = get_shipping_rate_for_governorate(
        request.governorate_code
    )
    governorate_details = get_governorate_by_code(
        request.governorate_code
    )

    quantities: dict[int, int] = {}
    for line in request.items:
        quantities[line.product_id] = (
            quantities.get(line.product_id, 0) + line.quantity
        )

    catalog_lookup = load_catalog_lookup()

    order_lines = []
    subtotal = 0.0

    for product_id, quantity in quantities.items():
        product = get_catalog_product(product_id, catalog_lookup)

        price = float(product.get("price") or 0)

        if price <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Product {product_id} is unavailable",
            )

        line_total = price * quantity
        subtotal += line_total

        order_lines.append({
            "product_id": product["id"],
            "product_name": product["name"],
            "brand": product.get("brand"),
            "product_image": product.get("image_link"),
            "unit_price": price,
            "quantity": quantity,
            "line_total": line_total,
        })

    discount_code = (
        request.discount_code.strip().upper()
        if request.discount_code
        else None
    )

    if discount_code and discount_code != "HAGORA20":
        raise HTTPException(
            status_code=400,
            detail="Invalid discount code",
        )

    discount_amount = 0.0

    if discount_code == "HAGORA20":
        discount_amount = round(subtotal * 0.2, 2)

    shipping_cost = round(float(shipping_rate), 2)
    total = round(subtotal - discount_amount + shipping_cost, 2)

    order_number = (
        f"HAG-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-"
        f"{uuid.uuid4().hex[:6].upper()}"
    )

    order = Order(
        order_number=order_number,
        user_id=current_user.id,
        status="pending",
        payment_method="cod",
        payment_status="unpaid",
        idempotency_key=request.idempotency_key,
        subtotal=round(subtotal, 2),
        discount_code=discount_code,
        discount_amount=round(discount_amount, 2),
        shipping_cost=shipping_cost,
        total=total,
        currency="EGP",
        first_name=normalize_name(request.first_name),
        last_name=normalize_name(request.last_name),
        phone=request.phone,
        governorate=governorate_details["code"],
        city=request.city,
        address=request.address,
    )

    db.add(order)
    db.flush()

    for item in order_lines:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item["product_id"],
                product_name=item["product_name"],
                brand=item["brand"],
                product_image=item["product_image"],
                unit_price=item["unit_price"],
                quantity=item["quantity"],
                line_total=item["line_total"],
            )
        )

    db.commit()
    db.refresh(order)

    return {
        "message": "Order created successfully",
        "order": serialize_order(order),
    }


@app.get("/orders")
def get_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return {"orders": [serialize_order(order) for order in orders]}


@app.get("/orders/{order_id}")
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return {"order": serialize_order(order)}


# Disabled until a real admin-role authorization system is implemented.
@app.delete("/admin/users/by-email")
def delete_user_by_email():
    raise HTTPException(
        status_code=403,
        detail="Admin access is not configured.",
    )
