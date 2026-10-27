# Personal Finance Advisor Bot

Demo Link : https://personal-finance-advisor-kwkk.onrender.com/

Full Document : https://1drv.ms/w/c/ffa04e4c624d533b/IQARg0oTKeI_T7xDkI34yoxjAS0ZAfggQ1c-6HKRuupCOKo?e=tG6Kcv

Google drive link: https://drive.google.com/drive/folders/1_CR8qagsIX1Ozl5_4oVV9Mld9gUll1M8
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
