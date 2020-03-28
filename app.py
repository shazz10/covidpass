from flask import Flask, request, jsonify, session
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo


app = Flask("__name__")

#database config starts

app.config["MONGO_DBNAME"]="covidpass"
app.config["MONGO_URI"]="mongodb://localhost:27017/covidpass"

mongo.init_app(app)

#database config ends

#user usecases start

from user_side import user_side
app.register_blueprint(user_side)

#user usecases ends


#police usecases starts

from police_side import police_side
app.register_blueprint(police_side)

#police usecases ends

if __name__ == '__main__':
	app.run(host='0.0.0.0',port='5000',debug=True)