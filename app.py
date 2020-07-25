from helpers import login_required
from flask import Flask, flash, jsonify, redirect, render_template, request, session, Markup
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from tempfile import mkdtemp
from cs50 import SQL

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.debug = True

db = SQL("sqlite:///blog.db")

@app.route("/")
def index():
    rows = db.execute("select title, desc, uid from blogdata")
    rows = rows[::-1]
    print(rows)
    if rows != []:
        for row in rows:
            user = db.execute("select name from users where id = :id", id = row["uid"])
            row["name"] = user[0]["name"]
    return render_template("index.html", rows = rows)

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        name = request.form.get("username")
        passw = request.form.get("password")
        hash = db.execute("Select hash, id from users where name = :name", name = name)
        if len(hash) != 1 or not check_password_hash(hash[0]["hash"], passw):
            return render_template("error.html", msg="Username or password incorrect")
        session["user_id"] = hash[0]["id"]
        return redirect("/")

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        name = request.form.get("name")
        passw = request.form.get("password")
        repassw = request.form.get("re-password")
        check = db.execute("Select * from users where name = :name", name = name)
        if len(check) > 1:
            return render_template("error.html", msg = "User already exists")
        if passw != repassw:
            return render_template("error.html", msg = "Error: Passwords don't match")
        hashpass = generate_password_hash(passw)
        db.execute("Insert into users(name, hash) values(:username, :passw)", username=name, passw=hashpass)
        user_id = db.execute("Select id from users where name = :username", username=name)
        session["user_id"] = user_id[0]["id"]
        return redirect("/")
        
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/getblog")
def getBlog():
    bid = request.args.get("id")
    btitle = request.args.get("title")
    row = db.execute("select title, desc, blog from blogdata where uid = :id and title = :title", id = bid, title = btitle)
    print(row)
    if len(row) != 1:
        return render_template("error.html", msg="Post doesnot exist")
    name = db.execute("select name from users where id = :id", id=bid)
    title = row[0]["title"]
    desc = row[0]["desc"]
    blog = Markup(row[0]["blog"])
    return render_template("getblog.html", title = title, desc = desc, blog = blog, name = name[0]["name"])

@app.route("/write", methods = ["GET", "POST"])
@login_required
def write():
    if request.method == "GET":
        return render_template("write.html")
    else:
        title = request.form.get("title")
        desc = request.form.get("desc")
        blog = request.form.get("blog")
        db.execute("Insert into blogdata(title, desc, blog, uid) values(:title, :desc, :blog, :uid)", title = title, desc = desc, blog = blog, uid = session["user_id"])
        return redirect("/")