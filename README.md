# HAGORA API

FastAPI backend for the **HAGORA** makeup store. It handles authentication, user profiles, orders, shipping rates and password reset emails.

- **Frontend:** [HAGORA-Makeup-Store](https://github.com/hagarhasan/HAGORA-Makeup-Store) (React 19 + TypeScript)
- **Live site:** https://hagarhasan.github.io/HAGORA-Makeup-Store
- **Hosting:** Vercel (API) + Neon (PostgreSQL)

## Tech stack

- Python, FastAPI, Uvicorn
- SQLAlchemy ORM (PostgreSQL in production, SQLite for local development)
- JWT access tokens and hashed passwords
- FastAPI-Mail (SMTP) for password reset emails

## Features

- Register and login with JWT tokens
- User profile: name, username (can be changed once every 60 days), phone, governorate, city, address
- Change password, forgot password and reset password by email
- Notification preferences
- Product catalog (fetched from an external makeup API, with a built-in fallback list)
- Orders (cash on delivery, prices in EGP) with shipping rates per Egyptian governorate and idempotent order creation

## API endpoints

Interactive docs are available at `/docs` (Swagger UI).

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | No | Health check |
| GET | `/products` | No | Product catalog |
| GET | `/governorates` | No | Governorates and shipping rates |
| POST | `/register` | No | Create an account |
| POST | `/login` | No | Login and get an access token |
| POST | `/forgot-password` | No | Send a password reset email |
| POST | `/reset-password` | No | Set a new password using a reset token |
| GET | `/me` | Yes | Current user profile |
| PUT | `/me/name` | Yes | Update first and last name |
| PUT | `/me/basic-profile` | Yes | Update name and email |
| PUT | `/me/username` | Yes | Update username |
| PUT | `/me/profile` | Yes | Update phone and address details |
| PUT | `/me/password` | Yes | Change password |
| GET / PUT | `/me/notification-preferences` | Yes | Read or update notification settings |
| POST | `/orders` | Yes | Create an order |
| GET | `/orders` | Yes | List my orders |
| GET | `/orders/{order_id}` | Yes | Get one of my orders |

Authenticated requests send the header `Authorization: Bearer <access_token>`.

## Environment variables

Copy `.env.example` to `.env` for local development. On Vercel, add them in **Settings, Environment Variables**.

| Variable | Description |
|---|---|
| `SECRET_KEY` | Long random string used to sign JWT tokens (required) |
| `DATABASE_URL` | Database URL. If missing, a local SQLite file is used |
| `MAIL_USERNAME` | SMTP username (for example a Gmail address) |
| `MAIL_PASSWORD` | SMTP password (for Gmail, an App Password) |
| `MAIL_FROM` | Sender address |
| `MAIL_PORT` | SMTP port, usually `587` |
| `MAIL_SERVER` | SMTP server, for example `smtp.gmail.com` |
| `MAIL_STARTTLS` | `True` |
| `MAIL_SSL_TLS` | `False` |
| `FRONTEND_URL` | Frontend URL used in password reset links |

Never commit `.env` files or real credentials.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
copy .env.example .env          # then edit the values
uvicorn main:app --reload
```

The API runs on http://127.0.0.1:8000 and the docs on http://127.0.0.1:8000/docs.

## Deployment

The API is deployed on **Vercel** and connected to this repository, so every push to `main` creates a new deployment. The database is a **Neon** PostgreSQL instance, configured through the `DATABASE_URL` environment variable.

CORS is configured in `main.py` to allow the local dev servers and the GitHub Pages site. If the frontend domain changes, update the `allow_origins` list.
