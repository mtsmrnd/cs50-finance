import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user = session["user_id"]
    stockBalance = 0

    """GET DATA FOR TABLE"""
    test = db.execute("SELECT share_symbol, share_qty FROM portfolio WHERE user_id = ?", user)
    stocks = []
    for i in range(len(test)):
        aux = lookup(test[i]["share_symbol"])
        stocks.append(aux)
        stocks[i]["qty"] = test[i]["share_qty"]
        stocks[i]["total"] = usd(test[i]["share_qty"] * aux["price"])
        stockBalance += (test[i]["share_qty"] * aux["price"])

    """Change stock balance to format"""
    stockBalance = stockBalance
    """GET BALANCE IN CASH"""
    cashBalance = db.execute("SELECT cash FROM users WHERE id = ?", user)[0]["cash"]
    """sum balances"""
    totalBalance = usd(stockBalance + cashBalance)
    stockBalance = usd(stockBalance)
    cashBalance = usd(cashBalance)

    return render_template("index.html", cashBalance=cashBalance, stocks=stocks, stockBalance=stockBalance, totalBalance=totalBalance)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        company = request.form.get("symbol")
        if not company:
            return apology("must provide stock", 403)
        stockInfo = lookup(company)
        user = session["user_id"]
        if stockInfo is None:
            return apology("invalid stock", 403)
        else:
            price = float(stockInfo["price"])
            shares = float(request.form.get("shares"))
            balance = float(db.execute("SELECT cash FROM users WHERE id = ?", user)[0]["cash"])
            check_current = db.execute("SELECT EXISTS(SELECT 1 FROM portfolio WHERE user_id = ? AND share_symbol = ?) AS 'value'", user, company)[0]["value"]
            if price*shares > balance:
                return apology("insufficient funds", 403)
            else:
                db.execute("INSERT INTO transactions (share_symbol, share_price, share_qty, user_id) VALUES (?, ?, ?, ?)", company, price, shares, user)
                db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", price*shares, user)
                if check_current != 0:
                    db.execute("UPDATE portfolio SET share_qty = share_qty + ? WHERE user_id = ? AND share_symbol = ?", shares, user, company)
                else:
                    db.execute("INSERT INTO portfolio VALUES (?, ?, ?)", user, company, shares)
                return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("must provide stock", 403)
        stockInfo = lookup(symbol)
        if stockInfo is None:
            return apology("invalid stock", 403)
        else:
            return render_template("quoted.html", symbol=symbol, stockInfo=stockInfo)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not username:
            return apology("must provide username", 403)
        elif not password:
            return apology("must provide password", 403)
        elif not confirmation:
            return apology("must repeat password", 403)
        elif not password == confirmation:
            return apology("password don't match", 403)

        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, generate_password_hash(password))

        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")
