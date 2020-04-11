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
		support = mongo.db.support

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
				'is_quarantine':request.json['is_quarantine'],
				'is_pass':request.json['is_pass'],
				'is_ngo':request.json["is_ngo"],
				'is_shopper':request.json["is_shopper"],
				'viewing_users_q':[],
				'viewing_users_s':[]
				})

			if request.json['is_quarantine']==1:
				if not queues.find_one({"state":request.json['state'],"district":request.json['district']}):
					queues.insert({'queue':[],'count':0,'pointer':0,'district':request.json['district'],"state":request.json['state']})
				#polices.create_index([('district',1)], name='search_district', default_language='english')
				queue=queues.find_one_and_update({"state":request.json['state'],"district":request.json['district']},{"$push":{"queue":str(id)} ,"$inc":{"count":1}})
			
			#queues.find_one_and_update({"_id":q["_id"]},{"$push":{"queue":str(id)} ,"$inc":{"count":1}})
			s=support.find_one({"state":request.json['state'],"district":request.json['district']})
			if not s:
				support.insert({
						"state":request.json['state'],
						"district":request.json['district'],
						'is_quarantine':request.json['is_quarantine'],
						'is_pass':request.json['is_pass'],
						'is_ngo':request.json["is_ngo"],
						'is_shopper':request.json["is_shopper"]
					})
			else:
				update={}
				if s['is_quarantine']==0 and request.json['is_quarantine']==1:
					update["is_quarantine"]=1
				if s['is_pass']==0 and request.json['is_pass']==1:
					update["is_pass"]=1
				if s['is_ngo']==0 and request.json['is_ngo']==1:
					update["is_ngo"]=1
				if s['is_shopper']==0 and request.json['is_shopper']==1:
					update["is_shopper"]=1
				support.find_one_and_update({"_id":s["_id"]},{"$set":update})

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
				del login_police['viewing_users_q']
				del login_police['viewing_users_s']

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



@police_side.route('/api/police/get_quarantine_users/<type>',methods=['GET'])
@token_required
def get_quarantine_users(current_user,type):

	try:
		quarantine = mongo.db.quarantine
		output=[]

		view=""
		if int(type)==1:
			view="viewing_users_q"
		else:
			view="viewing_users_s"

		for id in current_user[view]:
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


@police_side.route('/api/police/update_quarantine_user',methods=['POST'])
@token_required
def update_quarantine_user(current_user):
	try:
		quarantine = mongo.db.quarantine

		qid = request.json['qid']
		end_date = request.json['end_date']
		
		quarantine.find_one_and_update({"_id":ObjectId(qid)},{"$set":{"end_date":end_date}})

		return jsonify({'id':"quarantine user removed!!","status":200})
		

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@police_side.route('/api/police/delete_quarantine_user',methods=['POST'])
@token_required
def delete_quarantine_user(current_user):
	try:
		police = mongo.db.police
		quarantine = mongo.db.quarantine
		history_quarantine = mongo.db.history_quarantine 

		qid = request.json['qid']

		type = (int)(request.json['type'])
		
		if type==1:
			police.find_one_and_update({"_id":current_user["_id"]},{"$pull":{"viewing_users_q":qid}})
		else:
			police.find_one_and_update({"_id":current_user["_id"]},{"$pull":{"viewing_users_s":qid}})

		q = quarantine.find_one({"_id":ObjectId(qid)})
		if q:
			del q["_id"]
			q["pid"]=str(current_user["_id"])
			history_quarantine.insert(q)

		quarantine.remove({"_id":ObjectId(qid)})

		return jsonify({'id':"quarantine user removed!!","status":200})
		

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})

