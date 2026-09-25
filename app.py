import os
import sqlite3
from datetime import date
from functools import wraps

from flask import Flask, request, redirect, url_for, session, render_template_string, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "college-demo-secret-change-me")
DB = os.getenv("DB_PATH", "finance.db")

CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Education", "Health", "Entertainment", "Other"]

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS incomes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        source TEXT NOT NULL,
        entry_date TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        note TEXT,
        entry_date TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL
    );
    """)
    con.commit()
    con.close()

init_db()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

STYLE = """
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;background:#f4f7fb;color:#182230}
nav{background:#172033;color:white;padding:15px 5%;display:flex;justify-content:space-between;align-items:center}
nav a{color:white;text-decoration:none;margin-left:16px}.brand{font-weight:700;font-size:20px}
.container{max-width:1050px;margin:28px auto;padding:0 18px}
.hero{background:linear-gradient(135deg,#2563eb,#7c3aed);color:white;border-radius:18px;padding:28px;margin-bottom:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px}
.card{background:white;border-radius:14px;padding:20px;box-shadow:0 3px 14px #00000012;margin-bottom:16px}
.stat{font-size:28px;font-weight:700;margin-top:8px}
form{display:grid;gap:10px}input,select,button{padding:12px;border:1px solid #d5dce5;border-radius:9px;font-size:15px}
button{background:#2563eb;color:white;border:0;cursor:pointer;font-weight:600}.danger{background:#dc2626}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px;border-bottom:1px solid #e5e7eb}
.alert{background:#fff7ed;padding:12px;border-radius:9px;margin-bottom:12px}
a.btn{display:inline-block;background:white;color:#2563eb;padding:10px 15px;border-radius:9px;text-decoration:none;font-weight:600}
small{color:#667085}.error{color:#b42318}
@media(max-width:600px){nav{flex-direction:column;gap:10px;align-items:flex-start}nav a{margin:0 12px 0 0}.container{margin-top:18px}}
</style>
"""

BASE = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{title}}</title>""" + STYLE + """</head><body>
<nav><div class="brand">💰 Finance Advisor</div><div>
{% if session.get('user_id') %}<a href="{{url_for('dashboard')}}">Dashboard</a><a href="{{url_for('logout')}}">Logout</a>{% else %}<a href="{{url_for('login')}}">Login</a><a href="{{url_for('register')}}">Register</a>{% endif %}
</div></nav><main class="container">
{% with messages=get_flashed_messages() %}{% for m in messages %}<div class="alert">{{m}}</div>{% endfor %}{% endwith %}
{{content|safe}}</main></body></html>"""

def page(title, content):
    return render_template_string(BASE, title=title, content=content)

@app.route("/")
def home():
    if session.get("user_id"): return redirect(url_for("dashboard"))
    return page("Personal Finance Advisor", """
    <div class="hero"><h1>Personal Finance Advisor Bot</h1>
    <p>Track income, expenses, budgets and savings in one simple dashboard.</p>
    <a class="btn" href="/register">Get Started</a></div>
    <div class="grid"><div class="card"><h3>📊 Dashboard</h3><p>See income, spending and savings.</p></div>
    <div class="card"><h3>💸 Expenses</h3><p>Record expenses by category.</p></div>
    <div class="card"><h3>🤖 AI Advice</h3><p>Get Gemini-powered financial suggestions when an API key is configured.</p></div></div>""")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username=request.form["username"].strip()
        password=request.form["password"]
        if not username or not password:
            flash("Username and password are required.")
        else:
            con=db()
            try:
                con.execute("INSERT INTO users(username,password) VALUES(?,?)",(username,generate_password_hash(password)))
                con.commit()
                flash("Registration successful. Please login.")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Username already exists.")
            finally: con.close()
    return page("Register","""<div class="card"><h2>Create account</h2><form method="post">
    <input name="username" placeholder="Username" required><input name="password" type="password" placeholder="Password" required>
    <button>Create Account</button></form></div>""")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        con=db(); u=con.execute("SELECT * FROM users WHERE username=?",(request.form["username"].strip(),)).fetchone(); con.close()
        if u and check_password_hash(u["password"],request.form["password"]):
            session["user_id"]=u["id"]; session["username"]=u["username"]; return redirect(url_for("dashboard"))
        flash("Invalid username or password.")
    return page("Login","""<div class="card"><h2>Login</h2><form method="post">
    <input name="username" placeholder="Username" required><input name="password" type="password" placeholder="Password" required>
    <button>Login</button></form></div>""")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("home"))

@app.route("/income", methods=["POST"])
@login_required
def income():
    amount=float(request.form["amount"]); source=request.form["source"].strip()
    con=db(); con.execute("INSERT INTO incomes(user_id,amount,source,entry_date) VALUES(?,?,?,?)",(session["user_id"],amount,source,date.today().isoformat())); con.commit(); con.close()
    flash("Income added."); return redirect(url_for("dashboard"))

@app.route("/expense", methods=["POST"])
@login_required
def expense():
    amount=float(request.form["amount"]); category=request.form["category"]; note=request.form.get("note","")
    con=db(); con.execute("INSERT INTO expenses(user_id,amount,category,note,entry_date) VALUES(?,?,?,?,?)",(session["user_id"],amount,category,note,date.today().isoformat())); con.commit(); con.close()
    flash("Expense added."); return redirect(url_for("dashboard"))

@app.route("/budget", methods=["POST"])
@login_required
def budget():
    category=request.form["category"]; amount=float(request.form["amount"])
    con=db(); old=con.execute("SELECT id FROM budgets WHERE user_id=? AND category=?",(session["user_id"],category)).fetchone()
    if old: con.execute("UPDATE budgets SET amount=? WHERE id=?",(amount,old["id"]))
    else: con.execute("INSERT INTO budgets(user_id,category,amount) VALUES(?,?,?)",(session["user_id"],category,amount))
    con.commit(); con.close(); flash("Budget saved."); return redirect(url_for("dashboard"))

@app.route("/dashboard")
@login_required
def dashboard():
    uid=session["user_id"]; con=db()
    inc=con.execute("SELECT COALESCE(SUM(amount),0) x FROM incomes WHERE user_id=?",(uid,)).fetchone()["x"]
    exp=con.execute("SELECT COALESCE(SUM(amount),0) x FROM expenses WHERE user_id=?",(uid,)).fetchone()["x"]
    budgets=con.execute("SELECT * FROM budgets WHERE user_id=? ORDER BY category",(uid,)).fetchall()
    recent=con.execute("SELECT * FROM expenses WHERE user_id=? ORDER BY id DESC LIMIT 8",(uid,)).fetchall()
    overs=[]
    for b in budgets:
        spent=con.execute("SELECT COALESCE(SUM(amount),0) x FROM expenses WHERE user_id=? AND category=?",(uid,b["category"])).fetchone()["x"]
        if spent>b["amount"]: overs.append((b["category"],spent,b["amount"]))
    con.close(); savings=inc-exp
    advice="Your spending is within the recorded budgets." if not overs else "Overspending detected in: "+", ".join(x[0] for x in overs)+". Consider reducing non-essential spending."
    content=render_template_string("""<div class="hero"><h1>Hello, {{name}} 👋</h1><p>Personal Finance Dashboard</p></div>
    <div class="grid"><div class="card"><small>Total Income</small><div class="stat">₹{{"%.2f"|format(inc)}}</div></div>
    <div class="card"><small>Total Expenses</small><div class="stat">₹{{"%.2f"|format(exp)}}</div></div>
    <div class="card"><small>Savings</small><div class="stat">₹{{"%.2f"|format(savings)}}</div></div></div>
    <div class="grid"><div class="card"><h2>Add Income</h2><form method="post" action="/income"><input name="amount" type="number" step="0.01" placeholder="Amount" required><input name="source" placeholder="Salary / Freelance" required><button>Add Income</button></form></div>
    <div class="card"><h2>Add Expense</h2><form method="post" action="/expense"><input name="amount" type="number" step="0.01" placeholder="Amount" required><select name="category">{% for c in cats %}<option>{{c}}</option>{% endfor %}</select><input name="note" placeholder="Note"><button>Add Expense</button></form></div>
    <div class="card"><h2>Set Budget</h2><form method="post" action="/budget"><select name="category">{% for c in cats %}<option>{{c}}</option>{% endfor %}</select><input name="amount" type="number" step="0.01" placeholder="Monthly budget" required><button>Save Budget</button></form></div></div>
    <div class="card"><h2>🤖 Financial Advice</h2><p>{{advice}}</p><form method="post" action="/api/advice"><button>Generate Gemini Advice</button></form></div>
    {% if overs %}<div class="card"><h2>⚠️ Overspending</h2>{% for x in overs %}<p>{{x[0]}}: ₹{{"%.2f"|format(x[1])}} spent vs ₹{{"%.2f"|format(x[2])}} budget</p>{% endfor %}</div>{% endif %}
    <div class="card"><h2>Recent Expenses</h2><table><tr><th>Date</th><th>Category</th><th>Amount</th><th>Note</th></tr>{% for e in recent %}<tr><td>{{e.entry_date}}</td><td>{{e.category}}</td><td>₹{{"%.2f"|format(e.amount)}}</td><td>{{e.note}}</td></tr>{% endfor %}</table></div>""",name=session["username"],inc=inc,exp=exp,savings=savings,cats=CATEGORIES,advice=advice,overs=overs,recent=recent)
    return page("Dashboard",content)

@app.route("/api/advice", methods=["POST"])
@login_required
def api_advice():
    con=db(); uid=session["user_id"]
    inc=con.execute("SELECT COALESCE(SUM(amount),0) x FROM incomes WHERE user_id=?",(uid,)).fetchone()["x"]
    exp=con.execute("SELECT COALESCE(SUM(amount),0) x FROM expenses WHERE user_id=?",(uid,)).fetchone()["x"]
    rows=con.execute("SELECT category,COALESCE(SUM(amount),0) spent FROM expenses WHERE user_id=? GROUP BY category ORDER BY spent DESC",(uid,)).fetchall(); con.close()
    key=os.getenv("GEMINI_API_KEY")
    advice=None
    if key:
        try:
            from google import genai
            client=genai.Client(api_key=key)
            prompt=f"Give concise educational personal-finance advice. Income total ₹{inc:.2f}, expenses ₹{exp:.2f}, categories: {[(r['category'],round(r['spent'],2)) for r in rows]}. Mention savings and practical budget steps. Do not give investment guarantees."
            advice=client.models.generate_content(model=os.getenv("GEMINI_MODEL","gemini-2.5-flash"),contents=prompt).text
        except Exception:
            advice="Gemini could not be reached right now. Basic rule-based advice: track expenses weekly, keep a budget for each category, and aim to save part of your income."
    else:
        advice="Gemini API key is not configured yet. Basic advice: review your biggest spending category, set a realistic budget, and try to save a fixed part of every income."
    return page("AI Advice",f"""<div class="card"><h2>🤖 AI Financial Advice</h2><p>{advice}</p><a href="/dashboard">← Back to Dashboard</a></div>""")

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)),debug=False)
