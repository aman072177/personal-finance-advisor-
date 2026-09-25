# Personal Finance Advisor Bot

A simple Flask + SQLite personal finance web app with optional Gemini AI advice.

## Features

- User registration and login
- Income tracking
- Expense tracking by category
- Budget management
- Savings calculation
- Overspending detection
- Dashboard and financial report
- Gemini-powered financial advice when `GEMINI_API_KEY` is configured
- Deployment configuration for Render

## Run locally

1. Install Python 3.11+.
2. Create a virtual environment:
   `python -m venv .venv`
3. Activate it.
4. Install dependencies:
   `pip install -r requirements.txt`
5. Copy `.env.example` to `.env`.
6. Put your Gemini API key in `.env` if you want AI advice.
7. Run:
   `python app.py`
8. Open `http://127.0.0.1:5000`

The app works without a Gemini key too; the AI button will show a rule-based fallback.

## GitHub

Create a new GitHub repository and upload all project files. Do not upload `.env`.

## Deployment

The included `render.yaml` is ready to use as a starting point for a Render deployment. Set `GEMINI_API_KEY` as a secret/environment variable in the hosting dashboard.

## Important

SQLite is suitable for a simple college demo. For a production deployment with multiple users, use a persistent hosted database such as PostgreSQL.
