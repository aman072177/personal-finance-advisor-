import os
from datetime import date
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///finance.db"
).replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

try:
    from google import genai
except ImportError:
    genai = None


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    incomes = db.relationship("Income", backref="user", lazy=True, cascade="all, delete-orphan")
    expenses = db.relationship("Expense", backref="user", lazy=True, cascade="all, delete-orphan")
    budgets = db.relationship("Budget", backref="user", lazy=True, cascade="all, delete-orphan")


class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    entry_date = db.Column(db.Date, nullable=False, default=date.today)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), default="")
    entry_date = db.Column(db.Date, nullable=False, default=date.today)


class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)


with app.app_context():
    db.create_all()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    return db.session.get(User, session.get("user_id"))


def financial_summary(user):
    income = sum(x.amount for x in user.incomes)
    expense = sum(x.amount for x in user.expenses)
    savings = income - expense
    by_category = {}
    for item in user.expenses:
        by_category[item.category] = by_category.get(item.category, 0) + item.amount
    return {
        "income": round(income, 2),
        "expenses": round(expense, 2),
        "savings": round(savings, 2),
        "by_category": by_category,
    }


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or len(password) < 6:
            flash("Enter a username and a password of at least 6 characters.", "error")
            return render_template("register.html")
        if User.query.filter_by(username=username).first():
            flash("That username already exists.", "error")
            return render_template("register.html")
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash("Account created. You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    summary = financial_summary(user)
    categories = sorted(summary["by_category"].items(), key=lambda x: x[1], reverse=True)
    budgets = {b.category: b.amount for b in user.budgets}
    recent_expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.entry_date.desc(), Expense.id.desc()).limit(8).all()
    recent_income = Income.query.filter_by(user_id=user.id).order_by(Income.entry_date.desc(), Income.id.desc()).limit(5).all()
    return render_template(
        "dashboard.html",
        user=user,
        summary=summary,
        categories=categories,
        budgets=budgets,
        recent_expenses=recent_expenses,
        recent_income=recent_income,
    )


@app.route("/income", methods=["POST"])
@login_required
def add_income():
    try:
        amount = float(request.form["amount"])
        if amount <= 0:
            raise ValueError
    except (KeyError, ValueError):
        flash("Enter a valid income amount.", "error")
        return redirect(url_for("dashboard"))
    source = request.form.get("source", "Other").strip() or "Other"
    entry_date = request.form.get("entry_date") or date.today().isoformat()
    item = Income(user_id=session["user_id"], amount=amount, source=source, entry_date=date.fromisoformat(entry_date))
    db.session.add(item)
    db.session.commit()
    flash("Income added.", "success")
    return redirect(url_for("dashboard"))


@app.route("/expense", methods=["POST"])
@login_required
def add_expense():
    try:
        amount = float(request.form["amount"])
        if amount <= 0:
            raise ValueError
    except (KeyError, ValueError):
        flash("Enter a valid expense amount.", "error")
        return redirect(url_for("dashboard"))
    category = request.form.get("category", "Other").strip() or "Other"
    description = request.form.get("description", "").strip()
    entry_date = request.form.get("entry_date") or date.today().isoformat()
    item = Expense(
        user_id=session["user_id"],
        amount=amount,
        category=category,
        description=description,
        entry_date=date.fromisoformat(entry_date),
    )
    db.session.add(item)
    db.session.commit()
    flash("Expense added.", "success")
    return redirect(url_for("dashboard"))


@app.route("/budget", methods=["POST"])
@login_required
def add_budget():
    category = request.form.get("category", "").strip()
    try:
        amount = float(request.form["amount"])
        if not category or amount <= 0:
            raise ValueError
    except (KeyError, ValueError):
        flash("Enter a valid category and budget.", "error")
        return redirect(url_for("dashboard"))

    budget = Budget.query.filter_by(user_id=session["user_id"], category=category).first()
    if budget:
        budget.amount = amount
    else:
        db.session.add(Budget(user_id=session["user_id"], category=category, amount=amount))
    db.session.commit()
    flash("Budget saved.", "success")
    return redirect(url_for("dashboard"))


@app.route("/api/advice")
@login_required
def api_advice():
    user = current_user()
    summary = financial_summary(user)
    budgets = {b.category: b.amount for b in user.budgets}
    overspending = {
        category: round(amount - budgets[category], 2)
        for category, amount in summary["by_category"].items()
        if category in budgets and amount > budgets[category]
    }

    fallback = (
        f"You earned ₹{summary['income']:.2f} and spent ₹{summary['expenses']:.2f}. "
        f"Your current savings are ₹{summary['savings']:.2f}. "
    )
    if overspending:
        fallback += "You are over budget in: " + ", ".join(overspending.keys()) + ". "
    if summary["savings"] > 0:
        fallback += "Consider setting aside part of your savings as an emergency fund."
    else:
        fallback += "Try reducing non-essential expenses and setting a small weekly savings target."

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or genai is None:
        return jsonify({"advice": fallback, "ai": False})

    prompt = f"""
You are a personal finance assistant. Give practical, non-judgmental budgeting guidance.
Do not recommend specific financial products or investments.
User summary:
Income: ₹{summary['income']}
Expenses: ₹{summary['expenses']}
Savings: ₹{summary['savings']}
Expenses by category: {summary['by_category']}
Budgets: {budgets}
Overspending: {overspending}
Give 4 short bullet points and one next-month savings target.
"""
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
        )
        return jsonify({"advice": response.text, "ai": True})
    except Exception:
        return jsonify({"advice": fallback, "ai": False})


@app.route("/report")
@login_required
def report():
    user = current_user()
    summary = financial_summary(user)
    return render_template("report.html", user=user, summary=summary)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=os.getenv("FLASK_DEBUG") == "1")
