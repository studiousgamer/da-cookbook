from pymongo import MongoClient
import uuid
import json
import random
import config
from datetime import datetime

class Database:
    def __init__(self):
        self.db = MongoClient(config.MONGO_URI).Cookbook
        self.users = self.db.users
        self.recipes = self.db.recipes

    def addUser(self, email):
        user = {
            "_id": str(uuid.uuid4()),
            "email": email,
            "username": email.split('@')[0],
            "recipes": [],
            "favorites": [],
            "liked": [],
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.users.insert_one(user)
    
    def getUser(self, id):
        return self.users.find_one({'_id': id})
    
    def getUserWithMail(self, email):
        return self.users.find_one({'email': email})
    
    def userExists(self, email):
        return self.users.find_one({'email': email}) != None

    def getRecipesOfUser(self, user):
        return self.recipes.find({'by': user})

    def getRecipeByID(self, ID):
        return self.client.Cookbook.recipes.find_one({'_id': ID})
    
    def getRandomRecipes(self, number):
        return self.recipes.aggregate([{'$sample': {'size': number}}])
    
    def addRecipe(self, recipe):
        self.recipes.insert_one(recipe)
        self.users.update_one({'_id': recipe['by']}, {'$push': {'recipes': recipe['_id']}})