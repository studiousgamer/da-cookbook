from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
import databases
import json
from authlib.integrations.flask_client import OAuth
import config
from loginpass import create_flask_blueprint, Google
from flask_wtf.csrf import CSRFProtect
import uuid
from datetime import datetime

creds = json.load(open('config.json'))
app= Flask(__name__)
app.config.from_pyfile('config.py')
csrf = CSRFProtect(app)

oauth = OAuth(app)
database = databases.Database()
backends = [Google]

@app.route('/')
def home():
    if 'user' in session:
        recipes = [
            database.getRecipeByID(recipe)
            for recipe in database.getUserRecipes(session['user']['_id'])
        ]

        print(recipes)
        return render_template('user.html', user=session['user'], recipes=recipes)
    return render_template('index.html')

@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user', None)
    return redirect(url_for('home'))

@app.route("/new", methods=['GET', 'POST'])
def new():
    if request.method == "GET":
        return render_template("new.html")
    ingredients = []
    steps = []
    recipe = request.form.to_dict()
    for i in recipe:
        if 'ingredients' in i and 'Amt' not in i and 'Scale' not in i:
            num = i.split("#")[1]
            ing = {
                "name": recipe[i],
                "amount": recipe[f"ingredientsAmt#{num}"],
                "scale": recipe[f"ingredientsScale#{num}"],
            }

            ingredients.append(ing)
        elif "step" in i:
            steps.append(recipe[i])
    recipe = {
        "_id": str(uuid.uuid4()),
        "title": recipe['title'],
        "description": recipe['description'],
        "ingredients": ingredients,
        "steps": steps,
        "type": recipe['type'],
        "tags": recipe['tags'].split(" "),
        "by": session['user']['_id'],
        "likes": [],
        "favorite": [],
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    database.addRecipe(recipe)
    return redirect(url_for('home'))

@app.route("/recipe/<id>", methods=['GET', 'DELETE'])
def recipe(id):
    recipe = database.getRecipeByID(id)
    recipe['by'] = database.getUser(recipe['by'])
    if 'user' in session:
        if request.method == "DELETE" and session['user']['_id'] == recipe['by']['_id']:
            try:
                database.deleteRecipe(id)
                return "deleted"
            except:
                return abort(404)
        return render_template("recipe.html", recipe=recipe, user=session['user'])
    return render_template("recipe.html", recipe=recipe, user=None)

@app.route("/recipe/<id>/like", methods=['POST'])
def like(id):
    if 'user' not in session:
        return abort(401)
    result = database.likeRecipe(session['user']['_id'], id)
    if not result:
        database.unlikeRecipe(session['user']['_id'], id)
    return "liked"

@app.route("/recipe/<id>/favorite", methods=['POST'])
def favorite(id):
    if 'user' not in session:
        return abort(401)
    result = database.addFavorite(session['user']['_id'], id)
    if not result:
        database.removeFavorite(session['user']['_id'], id)
    return "favorited"

@app.route("/liked")
def liked():
    if 'user' not in session:
        return abort(401)
    liked = database.getLiked(session['user']['_id'])
    liked = [database.getRecipeByID(i) for i in liked]
    for i in liked:
        i['by'] = database.getUser(i['by'])
    return render_template("display.html", content=liked, user=session['user'], type="Liked")

@app.route("/favorites")
def favorites():
    if 'user' not in session:
        return abort(401)
    favorites = database.getLiked(session['user']['_id'])
    favorites = [database.getRecipeByID(i) for i in favorites]
    for i in favorites:
        i['by'] = database.getUser(i['by'])
    return render_template("display.html", content=favorites, user=session['user'], type="Favorites")

def handle_authorize(remote, token, user_info):
    if not database.userExists(user_info['email']):
        database.addUser(user_info['email'])
    session['user'] = database.getUserWithMail(user_info['email'])
    return redirect(url_for('home'))

bp = create_flask_blueprint(backends, oauth, handle_authorize)
app.register_blueprint(bp, url_prefix='/')

if __name__ == '__main__':
    app.run(debug=True)
