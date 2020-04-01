from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import jwt
import datetime
from functools import wraps

user_side = Blueprint('user_side', __name__)

SECRET_KEY = "keepitsecret!!"

PASSWORD = "Nitsuvidha1!"

zones=[
	{"name":"All of Jamshedpur","id":0},
	{"name":"Mango","id":1},
	{"name":"Kadma","id":2},
	{"name":"Sonari","id":3},
	{"name":"Bistupur","id":4},
	{"name":"Sakchi","id":5},
	{"name":"Golmuri","id":6},
	{"name":"Jugsalai","id":7},
	{"name":"Burma Mines","id":8},
	{"name":"Telco","id":9},
	{"name":"Parsudih","id":10}
]

shop_types=[
    {"name":"Essentials","id":1},
    {"name":"Milk","id":2},
    {"name":"Bread","id":3},
    {"name":"Baby-Essentials","id":4},
    {"name":"Fruits & Vegetable","id":5},
    {"name":"Medicines","id":6},
    {"name":"Gas Station","id":7}
]

def token_required(f):
	@wraps(f)
	def decorator(*args,**kwargs):

		token=None
		users = mongo.db.user

		if 'x-access-tokens' in request.headers:
			token = request.headers['x-access-tokens']

		if not token:
			return jsonify({'id':'a valid token is missing','status':303})

		try:
			data = jwt.decode(token,SECRET_KEY)
			user = users.find_one({"_id":ObjectId(data['uid'])})

		except Exception as e:
			return jsonify({"id":"token is invalid!!","status":302}) 

		return f(user,*args,**kwargs)

	return decorator


# @user_side.route('/api/register',methods=['POST'])
# def register():
# 	try:

# 		users = mongo.db.user
# 		existing_user = users.find_one({'email':request.json['email']})

# 		if existing_user is None:
# 			hashpass = bcrypt.hashpw(request.json['password'].encode('utf-8'),bcrypt.gensalt())
# 			id = users.insert({
# 				'name':request.json['name'],
# 				'email':request.json['email'],
# 				'phone':request.json['phone'],
# 				'address':request.json['address'],
# 				'zone':request.json['zone'],
# 				'password':hashpass,
# 				'passes':[],
# 				'orders':[]
# 				})

# 			return jsonify({'id':str(id),'status':201})
# 		else:
# 			return jsonify({'id':"user exists!!",'status':401})

# 	except Exception as e:
# 		print(e)
# 		return jsonify({'id':"failed",'status':500})
		

# @user_side.route('/api/login',methods=['POST'])
# def login():
# 	try:
# 		users = mongo.db.user
# 		login_user = users.find_one({'email':request.json['email']})

# 		if login_user:
# 			if login_user['password'] == bcrypt.hashpw(request.json['password'].encode('utf-8'),login_user['password']):
# 				login_user['_id']=str(login_user['_id'])
# 				token = jwt.encode({'uid':login_user['_id'],'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=720)},SECRET_KEY)
# 				login_user['token']=token.decode('UTF-8')
# 				del login_user['password']
# 				return jsonify({'id':login_user,"status":200})
# 			else:
# 				return jsonify({'id':"password wrong","status":404})
# 		else:
# 			return jsonify({'id':"user not exists!!","status":403})
# 	except Exception as e:
# 		print(e)
# 		return jsonify({'id':"failed",'status':500})



@user_side.route('/api/glogin',methods=['POST'])
def glogin():
	try:
		users = mongo.db.user
		auth = request.authorization
		if not auth or not auth.username or not auth.password:
			return jsonify({'id':"not authorized",'status':404})
		if auth.password != PASSWORD:
			return jsonify({'id':"not authorized",'status':404})

		login_user = users.find_one({'email':auth.username})

		if login_user:
			login_user['_id']=str(login_user['_id'])
			token = jwt.encode({'uid':login_user['_id'],'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=7200)},SECRET_KEY)
			login_user['token']=token.decode('UTF-8')
			return jsonify({'id':login_user,"status":200,"zone":zones})
		else:
			id=users.insert({
				'name':request.json['name'],
				'email':request.json['email'],
				'passes':[],
				'orders':[]
				})
			
			users.create_index([('email',1)], name='search_email', default_language='english')
			token = jwt.encode({'uid':str(id),'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=7200)},SECRET_KEY)
			login_user={
				'_id':str(id),
				'name':request.json['name'],
				'email':request.json['email'],
				'passes':[],
				'orders':[],
				'token':token.decode('UTF-8')
			}
			return jsonify({'id':login_user,"status":205,"zone":zones})
	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@user_side.route('/api/gregister',methods=['POST'])
@token_required
def gregister(current_user):
	try:

		users = mongo.db.user
		
		id = users.find_one_and_update({"_id":current_user["_id"]},{"$set":{
			'name':request.json['name'],
			'phone':request.json['phone'],
			'address':request.json['address'],
			'zone':request.json['zone'],
			}})


		return jsonify({'id':"user updated",'status':201})
		

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})

@user_side.route('/api/get_essentials',methods=['GET'])
@token_required
def get_essentials(current_user):
	try:
		essentials={
		"delivery_cost":50,
		"cess_rate":1.5,
		"zones":zones,
		"shop_types":shop_types
		}
		return jsonify({'id':essentials,"status":200})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@user_side.route('/api/generate_pass',methods=['POST'])
@token_required
def generate_pass(current_user):
	try:
		passes = mongo.db.passes
		users = mongo.db.user

		id = passes.insert({
			'proof':request.json['proof'],
			'type':request.json['type'],#3types within jsr(1), within state(2), outof state(3)
			'senior_citizen':request.json['senior_citizen'],
			'passenger_count':request.json['passenger_count'],
			'urgency':request.json['urgency'],
			'urgency_text':request.json['urgency_text'],
			'destination':request.json['destination'],
			'vehicle':request.json['vehicle'],
			'purpose':request.json['purpose'],
			'date':request.json['date'],
			'time':request.json['time'],
			'duration':request.json['duration'],
			'status':0,
			'uid':str(current_user['_id'])
			})
		passes.create_index([('status',1)], name='search_status', default_language='english')

		#add passenger(name,aadhar,vehicle number,reason)
		#reason: medical , goods (please specify)
		#approval, reason of rejection
		
		result=users.find_one_and_update({"_id":current_user["_id"]},{'$push':{'passes':str(id)}})

		if not result:
			passes.remove({"_id":ObjectId(id)})
			return jsonify({'id':"user not present!!",'status':404})
		
		return jsonify({'id':str(id),'status':200})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})



@user_side.route('/api/user_passes',methods=['GET'])
@token_required
def user_passes(current_user):
	try:
		passes = mongo.db.passes
		users = mongo.db.user

		user_passes=[]
		dead_passes=[]
		for pid in current_user['passes']:
			p = passes.find_one({"_id":ObjectId(pid)})
			if p:
				p["_id"]=str(p["_id"])
				user_passes.append(p)
			else:
				dead_passes.append(pid)

		if len(dead_passes)>0:
			for pid in dead_passes:
				users.find_one_and_update({"_id":current_user["_id"]},{"$pull":{'passes':pid}})

		return jsonify({'id':user_passes,"status":200})
	except Exception as e:
		print(e)
		return jsonify({'id':"failed","status":500})
