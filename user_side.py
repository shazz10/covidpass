from flask import Blueprint, request, jsonify, session, send_from_directory, url_for
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import jwt
import datetime
from functools import wraps
import os
import uuid


user_side = Blueprint('user_side', __name__)

SECRET_KEY = "keepitsecret!!"

PASSWORD = "Nitsuvidha1!"

UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__)) + "/uploads/"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


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
		quarantine = mongo.db.quarantine

		auth = request.authorization
		if not auth or not auth.username or not auth.password:
			return jsonify({'id':"not authorized",'status':404})
		if auth.password != PASSWORD:
			return jsonify({'id':"not authorized",'status':404})

		login_user = users.find_one({'email':auth.username})

		if login_user:
			login_user['_id']=str(login_user['_id'])
			token = jwt.encode({'uid':login_user['_id'],'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=28800)},SECRET_KEY)
			login_user['token']=token.decode('UTF-8')

			quarantine_user = quarantine.find_one({"uid":login_user['_id']})
			location={
					"location_lat":None,
					"location_lon":None
					}
			if quarantine_user:
				location['location_lat']=quarantine_user['location']['coordinates'][0]
				location['location_lon']=quarantine_user['location']['coordinates'][1]


			return jsonify({'id':login_user,"status":200,"zone":zones,"location":location})
		else:
			id=users.insert({
				'name':request.json['name'],
				'email':request.json['email'],
				'passes':[],
				'orders':[]
				})
			
			users.create_index([('email',1)], name='search_email', default_language='english')
			token = jwt.encode({'uid':str(id),'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=28800)},SECRET_KEY)
			login_user={
				'_id':str(id),
				'name':request.json['name'],
				'email':request.json['email'],
				'passes':[],
				'orders':[],
				'token':token.decode('UTF-8')
				}
			location={
					"location_lat":None,
					"location_lon":None
					}
			
			return jsonify({'id':login_user,"status":205,"zone":zones,"location":location})
	except Exception as e:
		raise(e)
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
			'state':request.json['state'],
			'district':request.json['district']
			}})


		return jsonify({'id':"user updated",'status':201})
		

	except Exception as e:
		print(e)
		return jsonify({'id':"failed",'status':500})


@user_side.route('/api/get_essentials',methods=['GET'])
@token_required
def get_essentials(current_user):
	try:
		quarantine = mongo.db.quarantine

		user = quarantine.find_one({"uid":str(current_user["_id"])})

		is_quarantined=0
		if user:
			is_quarantined=1

		essentials={
		"delivery_cost":50,
		"cess_rate":1.5,
		"zones":zones,
		"shop_types":shop_types,
		"is_quarantined":is_quarantined
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
			'name':request.json['name'],
			'proof':request.json['proof'],
			'type':request.json['type'],
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


@user_side.route('/api/register_quarantine',methods=['POST'])
@token_required
def register_quarantine(current_user):
	try:
		
		quarantine = mongo.db.quarantine
		queues = mongo.db.queue
		polices = mongo.db.police

		qu=quarantine.find_one({"uid":str(current_user["_id"])})
		if not qu:
			id=quarantine.insert({
				'uid':str(current_user['_id']),
				'name':request.json['name'],
				'address':request.json['address'],
				'state':request.json['state'],
				'district':request.json['district'],
				'phone':request.json['phone'],
				'location':{"type":"Point","coordinates":[request.json['location_lat'],request.json['location_lon']]},
				'authority':request.json['authority'],
				'start_date':request.json['start_date'],
				'end_date':request.json['end_date'],
				'report':[],
				'violations':[]
				})
			quarantine.create_index([('uid',1)], name='search_uid', default_language='english')
			quarantine.create_index([('location',"2dsphere")], name='search_location', default_language='english')

			q=queues.find_one({"district":request.json['district']})
			
			pointer = q['pointer']
			count = q['count']
			if count>0:
				polices.find_one_and_update({"_id":ObjectId(q['queue'][pointer])},{"$push":{"viewing_users":str(id)}})
				pointer+=1
				if pointer == count:
					pointer=0

				queues.find_one_and_update({"_id":q['_id']},{"$set":{"pointer":pointer}})



			return jsonify({'id':"registered","status":200})
		else:
			return jsonify({'id':"user exists!!","status":205})
	except Exception as e:
		print(e)
		return jsonify({'id':"failed","status":500})


@user_side.route('/api/report_quarantine',methods=['POST'])
@token_required
def report_quarantine(current_user):
	try:
		
		quarantine = mongo.db.quarantine
		quarantine_user= quarantine.find_one({"uid":str(current_user["_id"])})

		filename = str(uuid.uuid4())+str(len(quarantine_user['report']))+'.txt'

		with open(UPLOAD_FOLDER+filename,"w") as f:
			f.write(request.json['img'])


		time = datetime.datetime.utcnow()
		time+= datetime.timedelta(minutes=330)
		time = str(time).split('.')[0]
		
		report = {
			"img":url_for('user_side.uploaded_file',filename=filename),
			"location_lat":request.json['location_lat'],
			"location_lon":request.json['location_lon'],
			"report_time":time,
			"location_error":request.json["location_error"]
		}

		quarantine.find_one_and_update({"uid":str(current_user["_id"])},{"$push":{"report":report}})

		return jsonify({'id':"reported","status":200})
	
	except Exception as e:
		raise(e)
		return jsonify({'id':"failed","status":500})


@user_side.route('/api/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER ,filename)



@user_side.route('/api/get_user_report',methods=['GET'])
@token_required
def get_report_quarantine(current_user):
	try:
		
		quarantine = mongo.db.quarantine
		quarantine_user= quarantine.find_one({"uid":str(current_user["_id"])})

		

		time = datetime.datetime.utcnow()
		time+= datetime.timedelta(minutes=330)
		time = str(time).split(' ')[0]
		time = datetime.datetime.strptime(time,"%Y-%m-%d")

		if quarantine_user:
			end = quarantine_user['end_date']
			end = datetime.datetime.strptime(end,"%d/%m/%Y")
			left = (end-time).days
			return jsonify({'id':quarantine_user["report"],"status":200,"left":left})
		else:
			return jsonify({'id':"user not present","status":400})
	
	except Exception as e:
		raise(e)
		return jsonify({'id':"failed","status":500})



@user_side.route('/api/report_violation',methods=['POST'])
@token_required
def report_violation(current_user):
	try:
		
		quarantine = mongo.db.quarantine

		time = datetime.datetime.utcnow()
		time+= datetime.timedelta(minutes=330)
		time = str(time).split('.')[0]
		
		violation = {
			"location_lat":request.json['location_lat'],
			"location_lon":request.json['location_lon'],
			"report_time":time,
		}

		quarantine.find_one_and_update({"uid":str(current_user["_id"])},{"$push":{"violations":violation}})

		return jsonify({'id':"reported","status":200})
	
	except Exception as e:
		raise(e)
		return jsonify({'id':"failed","status":500})


@user_side.route('/api/get_quarantine_near',methods=['POST'])
@token_required
def get_quarantine_near(current_user):
	try:
		
		quarantine = mongo.db.quarantine

		q_users = quarantine.find({"location":{"$near":
												{
													"$geometry":
														{
														 "type":"Point",
														 "coordinates":[request.json["location_lat"],request.json["location_lon"]]
														},
													"$maxDistance": 500,
												}, 
											  }
									})

		count=0
		for q in q_users:
			count+=1
		

		return jsonify({'id':count,"status":200})
	
	except Exception as e:
		raise(e)
		return jsonify({'id':"failed","status":500})

