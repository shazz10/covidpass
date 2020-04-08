from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import jwt
import datetime
from functools import wraps

police_side = Blueprint('police_side', __name__)

SECRET_KEY = "keepitsecret!!"

def token_required(f):
	@wraps(f)
	def decorator(*args,**kwargs):

		token=None
		polices = mongo.db.police

		if 'x-access-tokens' in request.headers:
			token = request.headers['x-access-tokens']

		if not token:
			return jsonify({'id':'a valid token is missing','status':303})

		try:
			data = jwt.decode(token,SECRET_KEY)
			police = polices.find_one({"_id":ObjectId(data['pid'])})

		except Exception as e:
			return jsonify({"id":"token is invalid!!","status":302}) 

		return f(police,*args,**kwargs)

	return decorator

@police_side.route('/api/register_police',methods=['POST'])
def register():
	try:

		polices = mongo.db.police
		queues = mongo.db.queue
		existing_police = polices.find_one({'email':request.json['email']})

		if existing_police is None:
			hashpass = bcrypt.hashpw(request.json['password'].encode('utf-8'),bcrypt.gensalt())
			id = polices.insert({
				'name':request.json['name'],
				'email':request.json['email'],
				'phone':request.json['phone'],
				'district':request.json['district'],
				'state':request.json['state'],
				'password':hashpass,
				'viewing_users':[]
				})

			if not queues.find_one({"district":request.json['district']}):
				queues.insert({'queue':[],'count':0,'pointer':0,'district':request.json['district']})
			#polices.create_index([('district',1)], name='search_district', default_language='english')
			queue=queues.find_one_and_update({"district":request.json['district']},{"$push":{"queue":str(id)} ,"$inc":{"count":1}})
			
			#queues.find_one_and_update({"_id":q["_id"]},{"$push":{"queue":str(id)} ,"$inc":{"count":1}})

			return jsonify({'id':str(id),'status':201})
		else:
			return jsonify({'id':"user exists!!",'status':401})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})
		


@police_side.route('/api/login_police',methods=['POST'])
def login():
	try:
		polices = mongo.db.police
		login_police = polices.find_one({'email':request.json['email']})

		if login_police:
			if login_police['password'] == bcrypt.hashpw(request.json['password'].encode('utf-8'),login_police['password']):
				login_police['_id']=str(login_police['_id'])
				del login_police['password']
				del login_police['viewing_users']

				token = jwt.encode({'pid':login_police['_id'],'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=28800)},SECRET_KEY)
				token = token.decode('UTF-8')

				return jsonify({'id':login_police,"status":200,"token":token})
			else:
				return jsonify({'id':"password wrong","status":404})
		else:
			return jsonify({'id':"user not exists!!","status":403})
	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})



@police_side.route('/api/police/get_passes/<status>',methods=['GET'])
@token_required
def get_passes(status):
	try:
		passes = mongo.db.passes
		all_passes=[]
		for p in passes.find({"status":int(status)}):
			p['_id']=str(p['_id'])
			all_passes.append(p)
		return jsonify({'id':all_passes,"status":200})
	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})




@police_side.route('/api/police/get_pass',methods=['POST'])
@token_required
def get_pass():
	try:
		passes = mongo.db.passes

		p = passes.find_one({"_id":ObjectId(request.json['pid'])})
		if p:
			p['_id']= str(p['_id'])
			return jsonify({'id':p,"status":200})
		else:
			return jsonify({'id':"pass not exists!!","status":404})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})



@police_side.route('/api/police/validate_pass',methods=['PUT'])
@token_required
def validate_pass():
	try:
		passes = mongo.db.passes

		passes.find_one_and_update({"_id":ObjectId(request.json['pid'])},
			{'$set':{'status':int(request.json['status'])}})

		#implement notification here

		return jsonify({'id':"updated",'status':200})
	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})




@police_side.route('/api/police/get_user',methods=['POST'])
@token_required
def get_user():
	try:
		users = mongo.db.user

		user = users.find_one({"_id":ObjectId(request.json['uid'])})
		if user:
			user['_id']= str(user['_id'])
			del user['password']
			return jsonify({'id':user,"status":200})
		else:
			return jsonify({'id':"user not exists!!","status":404})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})



@police_side.route('/api/police/get_quarantine_users',methods=['GET'])
@token_required
def get_quarantine_users(current_user):
	try:
		quarantine = mongo.db.quarantine
		output=[]
		for id in current_user['viewing_users']:
			qu = quarantine.find_one({"_id":ObjectId(id)},{"_id":1,"uid":1,"name":1,"address":1,"location":1,"phone":1,
												"start_date":1,"end_date":1,"authority":1,"state":1,"district":1})
			if qu:
				qu["_id"]=str(qu["_id"])
				qu["location_lat"]=qu["location"]["coordinates"][0]
				qu["location_lon"]=qu["location"]["coordinates"][1]
				del qu["location"]
				output.append(qu)
		
		return jsonify({'id':output,"status":200})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@police_side.route('/api/police/get_quarantine_user_report',methods=['POST'])
@token_required
def get_quarantine_user_report(current_user):
	try:
		quarantine = mongo.db.quarantine
		quarantine_user_report = quarantine.find_one({"uid":request.json["uid"]},{"report":1})

		if quarantine_user_report:
			return jsonify({'id':quarantine_user_report['report'],"status":200})
		else:
			return jsonify({'id':"No user found!!","status":404})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@police_side.route('/api/police/get_quarantine_user_violation',methods=['POST'])
@token_required
def get_quarantine_user_violation(current_user):
	try:
		quarantine = mongo.db.quarantine
		quarantine_user_violation = quarantine.find_one({"uid":request.json["uid"]},{"violations":1})

		if quarantine_user_violation:
			return jsonify({'id':quarantine_user_violation['violations'],"status":200})
		else:
			return jsonify({'id':"No user found!!","status":404})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})

