from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import jwt
import datetime
from functools import wraps
import uuid

helper = Blueprint('helper', __name__)

SECRET_KEY = "keepitsecret!!"

PASSWORD = "Nitsuvidha1!"

shop_types=[
    {"name":"Essentials"},
    {"name":"Milk"},
    {"name":"Bread"},
    {"name":"Baby-Essentials"},
    {"name":"Fruits & Vegetable"},
    {"name":"Medicines"},
    {"name":"Gas Station"}
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
        info = mongo.db.info

        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return jsonify({'id':"not authorized",'status':404})
        if auth.password != PASSWORD:
            return jsonify({'id':"not authorized",'status':404})

        login_shop = shops.find_one({'email':auth.username})

        zones=[]
        infos = info.find()
        for i in infos:
            del i["_id"]
            zones.append(i)

        if login_shop:
            
            login_shop['_id']=str(login_shop['_id'])
            token = jwt.encode({'sid':login_shop['_id'],'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=7200)},SECRET_KEY)
            login_shop['token']=token.decode('UTF-8')

            return jsonify({'id':login_shop,"status":200,"available":zones,"shop_types":shop_types})
            
        else:
            id=shops.insert({
                'name':request.json['name'],
                'email':request.json['email'],
                'items':[],
                'orders':[],
                'history':[]
                })
            shops.create_index([('email',1)], name='search_email', default_language='english')
            token = jwt.encode({'sid':str(id),'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=7200)},SECRET_KEY)
            login_shop={
                '_id':str(id),
                'name':request.json['name'],
                'email':request.json['email'],
                'items':[],
                'orders':[],
                'token':token.decode('UTF-8')
            }
            return jsonify({'id':login_shop,"status":205,"available":zones,"shop_types":shop_types})

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


@helper.route('/api/shop/register',methods=['POST'])
@token_required
def registerShop(current_shop):
    try:
        shops = mongo.db.shop
        
        
        id = shops.find_one_and_update({"_id":current_shop["_id"]},{"$set":{
            'name':request.json['name'],
            'phone':request.json['phone'],
            'address':request.json['address'],
            'state':request.json['state'],
            'district':request.json['district'],
            'city':request.json['city'],
            'zone':request.json['zone'],
            'type':request.json['type']
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

        items = request.json['items']

        for i in range(len(items)):
            if "item_id" not in items[i].keys() or items[i]['item_id'][0] == "u":
                items[i]['item_id']=uuid.uuid1().hex

        shops.find_one_and_update({"_id":current_shop["_id"]},{"$set":{"items":items}})
            
        return jsonify({'id':"inventory updated!!",'status':200})

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})



@helper.route('/api/shop/get_current_inventory',methods=['GET'])
@token_required
def get_current_inventory(current_shop):
    try:
        items = current_shop["items"]

        return jsonify({'id':items,'status':200})

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


@helper.route('/api/shop/get_essentials',methods=['GET'])
@token_required
def get_essentials(current_shop):
    try:
        items = mongo.db.item

        item= items.find({})
        mappings=[]
        for i in item:
            mappings.append(i["mapping"])

        return jsonify({'id':{
            "mappings":mappings[0]
            },'status':200})

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


