from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import jwt
import datetime
from functools import wraps
from flask import current_app
import sys

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
				'is_super':request.json["is_super"],
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
				
				if s['is_quarantine']==0 and request.json['is_quarantine']==1:
					
					support.find_one_and_update({"_id":s["_id"]},{"$set":{"is_quarantine":1}})
				if s['is_pass']==0 and request.json['is_pass']==1:
					
					support.find_one_and_update({"_id":s["_id"]},{"$set":{"is_pass":1}})
				if s['is_ngo']==0 and request.json['is_ngo']==1:
					
					support.find_one_and_update({"_id":s["_id"]},{"$set":{"is_ngo":1}})
				if s['is_shopper']==0 and request.json['is_shopper']==1:
					
					support.find_one_and_update({"_id":s["_id"]},{"$set":{"is_shopper":1}})
				

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


@police_side.route('/api/police/get_essentials',methods=['GET'])
@token_required
def get_essentials(current_user):
	try:
		
		info = mongo.db.info

		
		i = info.find_one({"state":current_user["state"],"district.name":current_user["district"]},{"district.$.city":1})
		

		return jsonify({'id':i["district"][0]["city"],"status":200})

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


@police_side.route('/api/police/register_ngo',methods=['POST'])
@token_required
def register_ngo(current_user):
	try:
		
		ngo = mongo.db.ngo
		
		data = {
			"name":request.json["name"],
			"state":current_user["state"],
			"district":current_user["district"],
			"director_name":request.json["director_name"],
			"phone_number":request.json["phone_number"],
			"activities":[]
		}
		ngo.insert(data)

		return jsonify({'id':"ngo inserted!!","status":201})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@police_side.route('/api/police/get_ngo_list',methods=['GET'])
@token_required
def get_ngo_list(current_user):
	try:
		
		ngo = mongo.db.ngo
		
		ngos = ngo.find({"state":current_user["state"],"district":current_user["district"]},{"_id":1,"name":1,"phone_number":1,"director_name":1})

		output=[]
		for n in ngos:
			if n:
				n["_id"] = str(n["_id"])
				output.append(n)
			
		return jsonify({'id':output,"status":200})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@police_side.route('/api/police/register_ngo_activity',methods=['POST'])
@token_required
def register_ngo_activity(current_user):
	try:
		
		ngo = mongo.db.ngo

		data = {
			"description":request.json["description"],
			"datetime":request.json["datetime"],
			"city":request.json["city"],
			"address":request.json["address"],
			"lat":request.json["lat"],
			"lon":request.json["lon"]
		}

		ngo.find_one_and_update({"_id":ObjectId(request.json["nid"])},{"$push":{"activities":data}})

		return jsonify({'id':"ngo activity inserted!!","status":201})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})
		

@police_side.route('/api/police/get_ngo_activities',methods=['POST'])
@token_required
def get_ngo_activities(current_user):
	try:
		
		ngo = mongo.db.ngo
		
		n = ngo.find_one({"_id":ObjectId(request.json["nid"])},{"activities":1})

		
		return jsonify({'id':n["activities"],"status":200})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@police_side.route('/api/police/add_state_quarantine_address',methods=['POST'])
@token_required
def add_state_quarantine_address(current_user):
	try:
		
		info = mongo.db.info

		i = info.find_one_and_update({"state":current_user["state"],"district.name":current_user["district"]},
										{"$push":{"district.$.state_q_address":request.json["address"]}})
		
		if i:
			return jsonify({'id':"address inserted!!","status":201})
		else:
			return jsonify({'id':"no such state and district present!!","status":400})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@police_side.route('/api/police/get_state_quarantine_address',methods=['GET'])
@token_required
def get_state_quarantine_address(current_user):
	try:
		info = mongo.db.info

		i = info.find_one({"state":current_user["state"],"district.name":current_user["district"]},{"district.$.state_q_address":1})
		if i:
			return jsonify({'id':i["district"][0]["state_q_address"],"status":201})
		else:
			return jsonify({'id':"no such state and district present!!","status":400})

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@police_side.route('/api/police/get_restricted_zones',methods=['GET'])
@token_required
def get_restricted_zones(current_user):
	try:
		restricted = mongo.db.restricted

		res = restricted.find({"state":current_user["state"],"district":current_user["district"]})
		output=[]
		for r in res:
			if r:
				r["_id"]=str(r["_id"])
				output.append(r)

		
		return jsonify({'id':output,"status":201})
		

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@police_side.route('/api/police/add_restricted_zones',methods=['POST'])
@token_required
def add_restricted_zones(current_user):
	try:
		restricted = mongo.db.restricted

		
		r=restricted.insert({
			"state":current_user["state"],
			"district":current_user["district"],
			"zone":request.json["zone"],
			"subzone":request.json["subzone"],
			"sector":request.json["sector"],
			"city":request.json["city"]
			})
		
		if r:
			return jsonify({'id':"zone inserted","status":201})
		else:
			return jsonify({'id':"failed insertion","status":400})

		

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@police_side.route('/api/police/remove_restricted_zones/<rid>',methods=['DELETE'])
@token_required
def remove_restricted_zones(current_user,rid):
	try:
		restricted = mongo.db.restricted

		
		r=restricted.remove({
			"_id":ObjectId(rid)
			})
		
		if r:
			return jsonify({'id':"zone removed","status":201})
		else:
			return jsonify({'id':"failed removal","status":400})

		

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@police_side.route('/api/police/get_police',methods=['GET'])
@token_required
def get_police(current_user):
	try:
		police = mongo.db.police

		polices=police.find({"state":current_user["state"],"district":current_user["district"],"is_quarantine":1},{"name":1,"email":1,"phone":1})
		output=[]
		for p in polices:
			p["_id"]=str(p["_id"])
			output.append(p)

		return jsonify({'id':output,'status':200})

		

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@police_side.route('/api/police/get_police_users',methods=['POST'])
@token_required
def get_police_users(current_user):
	try:
		police = mongo.db.police
		quarantine = mongo.db.quarantine

		users = police.find_one({"_id":ObjectId(request.json["pid"])},{"viewing_users_q":1,"viewing_users_s":1})
		
		home=[]
		state=[]

		for u in users["viewing_users_q"]:
			q = quarantine.find_one({"_id":ObjectId(u)},{"name":1,"address":1,"phone":1,"start_date":1,"end_date":1})
			if q:
				del q["_id"]
				
				home.append(q)

		for u in users["viewing_users_s"]:
			q = quarantine.find_one({"_id":ObjectId(u)},{"name":1,"address":1,"phone":1,"start_date":1,"end_date":1})
			if q:
				del q["_id"]
				
				state.append(q)

		return jsonify({"state":state,"home":home,'status':200})

		

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})