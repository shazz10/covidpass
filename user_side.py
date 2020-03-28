from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo

user_side = Blueprint('user_side', __name__)

@user_side.route('/api/register',methods=['POST'])
def register():
	try:

		users = mongo.db.user
		existing_user = users.find_one({'email':request.json['email']})

		if existing_user is None:
			hashpass = bcrypt.hashpw(request.json['password'].encode('utf-8'),bcrypt.gensalt())
			id = users.insert({
				'name':request.json['name'],
				'email':request.json['email'],
				'phone':request.json['phone'],
				'password':hashpass,
				'passes':[]
				})
			#session['imei'] = request.json['imei']
			return jsonify({'id':str(id),'status':201})
		else:
			return jsonify({'id':"user exists!!",'status':401})

	except Exception as e:
		raise e
		return jsonify({'id':"failed",'status':500})
		

@user_side.route('/api/login',methods=['POST'])
def login():
	try:
		users = mongo.db.user
		login_user = users.find_one({'email':request.json['email']})

		if login_user:
			if login_user['password'] == bcrypt.hashpw(request.json['password'].encode('utf-8'),login_user['password']):
				#session['imei'] = request.json['imei']
				login_user['_id']=str(login_user['_id'])
				del login_user['password']
				return jsonify({'id':login_user,"status":200})
			else:
				return jsonify({'id':"password wrong","status":404})
		else:
			return jsonify({'id':"user not exists!!","status":403})
	except Exception as e:
		raise e
		return jsonify({'id':"failed",'status':500})

@user_side.route('/api/generate_pass',methods=['POST'])
def generate_pass():
	try:
		passes = mongo.db.passes
		users = mongo.db.user

		id = passes.insert({
			'proof':request.json['proof'],
			# 'type':request.json['type'],#3types within jsr(1), within state(2), outof state(3)
			# 'destination':request.json['destination'],
			# 'vehicle':request.json['vehicle'],
			# 'purpose':request.json['purpose'],
			# 'time':request.json['time'],
			# 'duration':request.json['duration'],
			'status':0,
			'uid':request.json['uid']
			})
		#add passenger(name,aadhar,vehicle number,reason)
		#reason: medical , goods (please specify)
		#approval, reason of rejection
		users.find_one_and_update({"_id":ObjectId(request.json['uid'])},
			{'$push':{'passes':str(id)}})
		

		return jsonify({'id':str(id),'status':200})

	except Exception as e:
		raise e
		return jsonify({'id':"failed",'status':500})