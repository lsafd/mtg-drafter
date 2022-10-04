import os
import datetime
import requests
import urllib

from mtgsdk import Card
from mtgsdk import Set
from mtgsdk import Type
from mtgsdk import Supertype
from mtgsdk import Subtype
from mtgsdk import Changelog

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQLite database
db = SQL("sqlite:///draft.db")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # Define index that shows previous decks

    if request.method == "GET":

        # Select decks
        decks = db.execute("SELECT id, cardset FROM decks WHERE owner_id = ?", session["user_id"])

        # If no decks hide deck options
        if (decks != []):
            show_hidden = True

        # If decks show deck options
        else:
            show_hidden = False

        # Render index template
        return render_template("index.html", decks=decks, show_hidden=show_hidden)

    else:
        # If post without remove fail
        if not request.form.get("remove"):
            return apology

        # Remove requested decks and cards from those decks
        db.execute("DELETE FROM decks WHERE id = ?", request.form.get("remove"))
        db.execute("DELETE FROM chosen_cards WHERE deck_id = ?", request.form.get("remove"))

        # Select decks
        decks = db.execute("SELECT id, cardset FROM decks WHERE owner_id = ?", session["user_id"])

        # If no decks hide deck options
        if (decks != []):
            show_hidden = True

        # If decks show deck options
        else:
            show_hidden = False

        # Render index template
        return render_template("index.html", decks=decks, show_hidden=show_hidden)



@app.route("/draft", methods=["GET", "POST"])
@login_required
def draft():
    # Allow users to draft from a set of cards

    # Ensure set was submitted
    if not request.form.get("set") and not request.form.get("pick"):
        return apology("must provide a set", 400)

    # Set id of most recent deck created by a user
    deckid = db.execute("SELECT id FROM decks WHERE owner_id = ? ORDER BY id DESC LIMIT 1", session["user_id"])

    # If pick then add to chosen cards
    if request.form.get("pick"):
        db.execute("INSERT INTO chosen_cards (deck_id, card_id) VALUES(?, ?)", deckid[0]["id"], request.form.get("pick"))

    # Count the number of selected cards
    picks = db.execute("SELECT COUNT(card_id) FROM chosen_cards WHERE deck_id = ?", deckid[0]["id"])[0]["COUNT(card_id)"]

    # Define varibles to pass to html template
    cardids = []
    cardnames = []

    # If set not selected take set from most recently created deck
    if not request.form.get("set"):
        setid = db.execute("SELECT cardset FROM decks WHERE id = ?", deckid[0]["id"])[0]["cardset"]

    # If set requested then ensure set is of correct type and add deck with set to decks database
    else:
        setid = ""

        cardset = Set.where(name=request.form.get("set")).all()

        for sets in cardset:
            if sets.type == "core" or sets.type == "expansion" or sets.type == "masters":
                setid = sets.code

        db.execute("UPDATE decks SET cardset = ? WHERE id = ?", setid, deckid[0]["id"])

    # If all picks have been made then show results with all chosen cards
    # CHANGE THIS TO A SMALLER NUMBER TO MAKE TESTING EASIER
    if picks >= 3:
        for card in db.execute("SELECT card_id FROM chosen_cards WHERE deck_id = ?", deckid[0]["id"]):
            cardids.append(card["card_id"])
        # Find lands from the set so that user can add lands on results page
        landids = []
        landnames = []
        set_lands = Card.where(type="Basic Land").where(set=setid).all()
        for land in set_lands:
            if (land.name not in landnames):
                landids.append(land.multiverse_id)
                landnames.append(land.name)
        return render_template("results.html", cardids=cardids, landids=landids, landnames=landnames, length=len(landids))

    # Use MTG's api to generate a pack from the given set
    pack = Set.generate_booster(setid)

    for card in pack:
        # If the maximum number of cards that should be in the pack has not been reached ...
        if (len(cardids) <= 13 - (picks % 14)):
            # If the card has a legitimate id add its id and name to the respective sets (This is not always the case due to various problems with the api)
            if (card.multiverse_id != None):
                cardids.append(card.multiverse_id)
                cardnames.append(card.name)
            # If the card has no id then use other methods to try to find the id
            else:
                # Search for the card's id using MTG's gatherer
                cardurl = requests.get("https://gatherer.wizards.com/Pages/Search/Default.aspx?name=+[" + card.name + "]").url
                # If that works then parse the URL for the id
                try:
                    cardids.append(urllib.parse.parse_qs(urllib.parse.urlsplit(cardurl).query)["multiverseid"][0])
                    cardnames.append(card.name)
                except:
                    break
        else:
            break

    # Render the next set of cards
    return render_template("draft.html", cardids=cardids, cardnames=cardnames, length=len(cardnames))



@app.route("/setselect")
@login_required
def setselect():
    # Allow users to select a set from which to draft

    # Get a list of sets using MTG's api
    mtgsets = Set.all()
    cardsets = []
    # Add all cardsets of the correct types to a varible that will be passed to the template
    for cardset in mtgsets:
        if cardset.type == "core" or cardset.type == "expansion" or cardset.type == "masters":
            cardsets.append(cardset.name)
    # Create a new deck for the user
    db.execute("INSERT INTO decks (owner_id) VALUES(?)", session["user_id"])
    return render_template("setselect.html", cardsets=cardsets)


@app.route("/results", methods=["POST"])
@login_required
def results():
    # Allow users to see the cards they selected during the draft

    # If a specific deck is not requested return the most recent deck
    if not request.form.get("deck"):
        # Set id of most recent deck created by a user
        deckid = db.execute("SELECT id FROM decks WHERE owner_id = ? ORDER BY id DESC LIMIT 1", session["user_id"])[0]["id"]

    # If a deck is specified then use that deck
    else:
        deckid = request.form.get("deck")

    # Find the set based on the deck (Used to show lands of the correct type)
    setid = db.execute("SELECT cardset FROM decks WHERE id = ?", deckid)[0]["cardset"]

    # Add any requested lands to the deck
    if request.form.get("pick"):
        db.execute("INSERT INTO chosen_cards (deck_id, card_id) VALUES(?, ?)", deckid, request.form.get("pick"))

    cardids = []

    # Make a list with the ids of all the cards in the deck
    for card in db.execute("SELECT card_id FROM chosen_cards WHERE deck_id = ?", deckid):
        cardids.append(card["card_id"])

    # Find lands from the set so that user can add lands on results page
    landids = []
    landnames = []
    set_lands = Card.where(type="Basic Land").where(set=setid).all()
    for land in set_lands:
        if (land.name not in landnames):
            landids.append(land.multiverse_id)
            landnames.append(land.name)

    return render_template("results.html", cardids=cardids, landids=landids, landnames=landnames, length=len(landids), deckid=deckid)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password verification was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password verification", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 0:
            return apology("username already taken", 400)

        #Ensure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        # Add user to database
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")))

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/passwordupdate", methods=["GET", "POST"])
@login_required
def passwordupdate():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password verification was submitted
        elif not request.form.get("password-verify"):
            return apology("must provide password verification", 400)

        #Ensure passwords match
        if request.form.get("password") != request.form.get("password-verify"):
            return apology("passwords do not match", 400)

        # Update user password in database
        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(request.form.get("password")), session["user_id"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("passwordupdate.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
