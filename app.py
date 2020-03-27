from flask import Flask, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId

app = Flask("__name__")

app.config["MONGO_DBNAME"]="covidpass"
app.config["MONGO_URI"]="mongodb://localhost:27017/covidpass"

mongo = PyMongo(app)

#user usecases start

@app.route('/api/register',methods=['POST'])
def register():
	try:

		users = mongo.db.user
		existing_user = users.find_one({'imei':request.json['imei']})

		if existing_user is None:
			hashpass = bcrypt.hashpw(request.json['password'].encode('utf-8'),bcrypt.gensalt())
			id = users.insert({
				'name':request.json['name'],
				'imei':request.json['imei'],
				'email':request.json['email'],
				'phone':request.json['phone'],
				'password':hashpass,
				'passes':[]
				})
			#session['imei'] = request.json['imei']
			return jsonify({'id':str(id),'status':201})
		else:
			return jsonify({'id':"user exists!!",'status':404})

	except Exception as e:
		raise e
		return jsonify({'status':500})
		

@app.route('/api/login',methods=['POST'])
def login():
	try:
		users = mongo.db.user
		login_user = users.find_one({'imei':request.json['imei']})

		if login_user:
			if login_user['password'] == bcrypt.hashpw(request.json['password'].encode('utf-8'),login_user['password']):
				#session['imei'] = request.json['imei']
				return jsonify({'id':str(login_user['_id']),'status':200})
			else:
				return jsonify({'id':"password wrong","status":404})
		else:
			return jsonify({'id':"user not exists!!","status":404})
	except Exception as e:
		raise e
		return jsonify({'status':500})

@app.route('/api/generate_pass',methods=['POST'])
def generate_pass():
	try:
		passes = mongo.db.passes
		users = mongo.db.user

		id = passes.insert({
			'proof':request.json['proof'],
			'destination':request.json['destination'],
			'vehicle':request.json['vehicle'],
			'purpose':request.json['purpose'],
			'time':request.json['time'],
			'duration':request.json['duration'],
			'status':0,
			'uid':request.json['uid']
			})
		
		users.find_one_and_update({"_id":ObjectId(request.json['uid'])},
			{'$push':{'passes':str(id)}})
		

		return jsonify({'id':str(id),'status':200})

	except Exception as e:
		raise e
		return jsonify({'status':500})

#user usecases ends


#police usecases starts
@app.route('/api/get_passes/<status>',methods=['GET'])
def get_passes(status):
	passes = mongo.db.passes
	all_passes=[]
	for p in passes.find({"status":int(status)}):
		p['_id']=str(p['_id'])
		all_passes.append(p)
	return jsonify(all_passes)

#police usecases ends

if __name__ == '__main__':
	app.run(debug=True)