from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import jwt
import datetime
from functools import wraps

helper = Blueprint('helper', __name__)

SECRET_KEY = "keepitsecret!!"

shop_type=[
    {"name":"Essentials","id":1}
]

def token_required(f):
    @wraps(f)
    def decorator(*args,**kwargs):

        token=None
        shops = mongo.db.shop

        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']

        if not token:
            return jsonify({'id':'a valid token is missing','status':303})

        try:
            data = jwt.decode(token,SECRET_KEY)
            shop = shops.find_one({"_id":ObjectId(data['sid'])})

        except Exception as e:
            return jsonify({"id":"token is invalid!!","status":302}) 

        return f(shop,*args,**kwargs)

    return decorator


@helper.route('/api/shop/login',methods=['POST'])
def loginShop():
    try:
        shops = mongo.db.shop
        login_shop = shops.find_one({'email':request.json['email']})

        if login_shop:
            
            login_shop['_id']=str(login_shop['_id'])
            token = jwt.encode({'sid':login_shop['_id'],'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=720)},SECRET_KEY)
            login_shop['token']=token.decode('UTF-8')

            return jsonify({'id':login_shop,"status":200})
            
        else:
            id=shops.insert({
                'name':request.json['name'],
                'email':request.json['email'],
                'items':[],
                'orders':[]
                })
            shops.create_index([('email',1)], name='search_email', default_language='english')
            token = jwt.encode({'sid':str(id),'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=720)},SECRET_KEY)
            return jsonify({'id':{"token":token},"status":205})

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


@helper.route('/api/shop/register',methods=['POST'])
@token_required
def registerShop(current_shop):
    try:
        shops = mongo.db.shop
        
        print(type(request.json["zone"]))
        id = shops.find_one_and_update({"_id":current_shop["_id"]},{"$set":{
            'name':request.json['name'],
            'phone':request.json['phone'],
            'address':request.json['address'],
            'zone':int(request.json['zone']),
            }})

        return jsonify({'id':"shop updated",'status':201})

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


@helper.route('/api/shop/update_inventory',methods=['POST'])
@token_required
def updateInventory(current_shop):
    try:
        shops = mongo.db.shop
        shops.find_one_and_update({"_id":current_shop["_id"]},{"$set":{"items":request.json['items']}})
            
        return jsonify({'id':"inventory updated!!",'status':200})

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})



