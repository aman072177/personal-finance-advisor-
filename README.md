# Personal Finance Advisor Bot

Phone-friendly college project using Flask, SQLite and optional Gemini AI.

## Deploy on Render
Build command:
`pip install -r requirements.txt`

Start command:
`gunicorn app:app`

Add `GEMINI_API_KEY` in Render Environment if Gemini advice is required.
Never upload your API key to GitHub.

## Features
- Registration/login
- Income and expense tracking
- Expense categories
- Budget planning
- Savings calculation
- Overspending detection
- Dashboard
- Gemini AI financial advice
