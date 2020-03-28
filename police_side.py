from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo

police_side = Blueprint('police_side', __name__)

@police_side.route('/api/police/get_passes/<status>',methods=['GET'])
def get_passes(status):
	try:
		passes = mongo.db.passes
		all_passes=[]
		for p in passes.find({"status":int(status)}):
			p['_id']=str(p['_id'])
			all_passes.append(p)
		return jsonify(all_passes)
	except Exception as e:
		raise e
		return jsonify({'id':"failed",'status':500})

@police_side.route('/api/police/get_pass/<pid>',methods=['GET'])
def get_pass(pid):
	try:
		passes = mongo.db.passes

		p = passes.find_one({"_id":ObjectId(pid)})
		if p:
			p['_id']= str(p['_id'])
			return jsonify(p)
		else:
			return jsonify({'id':"pass not exists!!","status":404})

	except Exception as e:
		raise e
		return jsonify({'id':"failed",'status':500})



@police_side.route('/api/police/validate_pass',methods=['PUT'])
def validate_pass():
	try:
		passes = mongo.db.passes

		passes.find_one_and_update({"_id":ObjectId(request.json['pid'])},
			{'$set':{'status':int(request.json['status'])}})

		#implement notification here

		return jsonify({'id':"updated",'status':200})
	except Exception as e:
		raise e
		return jsonify({'id':"failed",'status':500})


@police_side.route('/api/police/get_user/<uid>',methods=['GET'])
def get_user(uid):
	try:
		users = mongo.db.user

		user = users.find_one({"_id":ObjectId(uid)})
		if user:
			user['_id']= str(user['_id'])
			del user['password']
			return jsonify(user)
		else:
			return jsonify({'id':"user not exists!!","status":404})

	except Exception as e:
		raise e
		return jsonify({'id':"failed",'status':500})