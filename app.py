import os

from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath
from datetime import datetime

from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME") 
app.config["MONGO_URI"] = os.environ.get("MONGO_URI") 
app.secret_key = os.environ.get("SECRET_KEY") 

UPLOADS_PATH = join(dirname(realpath(__file__)), 'static/media')

mongo = PyMongo(app)

@app.route("/")
@app.route("/recipes")
def get_recipes():
    Recipe = list(mongo.db.Receipt.find())

    return render_template("recipes.html", Recipe=Recipe)


@app.route("/home")
def home():
    # return redirect(url_for("home"))
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(request.form.get("username")))
                    return redirect(url_for("profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    return render_template("profile.html", username=username)

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add-recipe", methods=["GET", "POST"])
@app.route("/edit-recipe/<id>", methods=["GET", "POST"])
def add_recipe(id=None):
    if request.method == "POST":
        image = saveLocalImage(request)

        recipe = {
            "Name ": request.form.get("Name"),
            "Prep_time": request.form.get("Prep_time"),
            "Cook_time": request.form.get("Cook_time"),
            "Total_time": request.form.get("Total_time"),
            "Description": request.form.get("Description"),
            "Ingredients": request.form.get("Ingredients"),
            "Instructions": request.form.get("Instructions"),
            "created_by": session["user"]
        }

        if image:
            recipe.update({"Image": image})

        if id:
            mongo.db.Receipt.find_one_and_update({"_id": ObjectId(id)}, {"$set": recipe})
            flash("Recipe Successfully Updated")
        else:
            mongo.db.Receipt.insert_one(recipe)
            flash("Recipe Successfully Added")
        return redirect(url_for("get_recipes"))

    if id:
        Recipe = mongo.db.Receipt.find_one({"_id": ObjectId(id)})

        if Recipe['created_by'] == session["user"] or Recipe['Added_by'] == session["user"]:
            return render_template("add_recipe.html", Recipe=Recipe)

        flash("You can only edit your recepes")
        return redirect(url_for("get_recipes"))

    return render_template("add_recipe.html", Recipe=None)


@app.route("/recipe/<id>", methods=["GET"])
def get_recipe(id):
    Recipe = mongo.db.Receipt.find_one({"_id": ObjectId(id)})
    return render_template("recipe.html", Recipe=Recipe)

@app.route("/delete-recipe/<id>", methods=["GET"])
def delete_recipe(id):
    mongo.db.Receipt.delete_one({'_id': ObjectId(id)})

    flash("Recipe Successfully Deleted")
    return redirect(url_for("get_recipes"))


def saveLocalImage(request):
    try:
        if len(request.files) > 0:
            if request.files['image'].filename != '':
                image = request.files['image']

                newName = secure_filename(f'{datetime.now().strftime("%m_%d_%Y_%H_%M_%S_%f")}_{image.filename}')

                finalPath = os.path.join(UPLOADS_PATH, newName)
                image.save(finalPath)

                return newName
    except:
        pass

    return None
    

if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)