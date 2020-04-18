from flask import Flask, request, jsonify, session
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import os


app = Flask("__name__")


# #database config starts

app.config["MONGO_DBNAME"]="covidpass"
app.config["MONGO_URI"]="mongodb+srv://saanayy:COVID19token-gen@token-gen-wiy46.mongodb.net/covidpass"
#username-saanayy
#password-COVID19token-gen

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

#delivery_user usecases start

from delivery_user import delivery_user
app.register_blueprint(delivery_user)

#delivery_user usecases ends

#helper usecases start

from helper import helper
app.register_blueprint(helper)

#helper usecases ends

#delivery_shopper usecases start

from delivery_shopper import delivery_shopper
app.register_blueprint(delivery_shopper)

#delivery_shopper usecases ends

#input zone info
@app.route('/api/insert_stateinfo',methods=['POST'])
def insert_stateinfo():
	try:
		info = mongo.db.info
		
		if info.find_one({"state":request.json["state"]}):
			info.find_one_and_update({"state":request.json["state"]},{"$push":{"district":{"name":request.json["district"],"emergency_contact":[],"city":[]}}})
		else:
			info.insert({"state":request.json["state"],"district":[{"name":request.json["district"],"emergency_contact":[],"city":[]}]})
									

		return jsonify({'id':"success!!",'status':200})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@app.route('/api/insert_zoneinfo',methods=['POST'])
def insert_zoneinfo():
	try:
		info = mongo.db.info
		
		i = info.find_one_and_update({"state":request.json["state"],"district.name":request.json["district"]},
									 {"$push":{"district.$.city":request.json["city"]}})


		return jsonify({'id':"success!!",'status':200})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@app.route('/api/insert_contactinfo',methods=['POST'])
def insert_contactinfo():
	try:
		info = mongo.db.info
		
		i = info.find_one_and_update({"state":request.json["state"],"district.name":request.json["district"]},
									 {"$push":{"district.$.emergency_contact":request.json["emergency_contact"]}})

		return jsonify({'id':"success!!",'status':200})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})




#input items info
@app.route('/api/mapping_insert',methods=['POST'])
def insertItem():
	try:
		items = mongo.db.item
		
		items.insert(request.json)
		return jsonify({'id':"inventory updated!!",'status':200})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})




if __name__ == '__main__':
	app.run(host='0.0.0.0',port=os.environ.get('PORT', '5000'),debug=True)