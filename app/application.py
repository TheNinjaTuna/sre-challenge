import sqlite3
import os
import logging
from flask import Flask, session, redirect, url_for, request, render_template, abort
from argon2 import PasswordHasher


app = Flask(__name__)

ph = PasswordHasher()

#app.secret_key = os.getenv("APP_SECRET").encode()
app.secret_key = b"192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf"
app.logger.setLevel(logging.INFO)


def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    return cursor


def is_authenticated():
    if "username" in session:
        return True
    return False


def authenticate(username, password):
    cursor = get_db_connection()
    user = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    cursor.close()

    if user ==  None:
        app.logger.warning(f"A user tried logging in with the username { username } but no record was found.")
        abort(401)

    if user["username"] == username and ph.verify(user["password"], password):
        app.logger.info(f"the user '{username}' logged in successfully with password.")
        session["username"] = username
        return True

    app.logger.warning(f"the user '{ username }' failed to log in.")
    abort(401)


@app.route("/")
def index():
    return render_template("index.html", is_authenticated=is_authenticated())


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if authenticate(username, password):
            return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
