from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import jwt
from functools import wraps

delivery_user = Blueprint('delivery_user', __name__)

SECRET_KEY = "keepitsecret!!"

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

@delivery_user.route('/api/shop',methods=['GET'])
@token_required
def getAllShop(current_user):
    try:
        shops = mongo.db.shop
        users = mongo.db.user
        #current_user = users.find_one({'_id':ObjectId(request.json['uid'])})
        zone = current_user['zone']
        output=[]
        shops_in_zone=shops.find({'zone':int(zone)})
        if shops_in_zone is None:
            return jsonify({'result':'No shops exist in this zone','status':403})
        else:
            for shop in shops_in_zone:
                output.append({'id':str(shop['_id']),'name':shop['shopname'],'address':shop['address'],'phone':shop['phone'],'type':shop['type'],'items':shop['items']})
            return jsonify({'result':output,'status':200})


    except Exception as e:
        print(e)
        return jsonify({'result':"failed",'status':500})


@delivery_user.route('/api/items',methods=['GET'])
def getAllItems():
    try:
        items = mongo.db.item
        output=[]
        itemsCursor=items.find()
        if itemsCursor is None:
            return jsonify({'result':'No shops exist in this zone','status':201})
        else:
            for sitem in itemsCursor:
                output.append({'itemId':str(sitem['_id']),'itemname':sitem['itemname'],'price':sitem['price'],'type':str(sitem['type']),'unitqty':sitem['unitqty']})
            return jsonify({'result':output,'status':201})


    except Exception as e:
        print(e)
        return jsonify({'result':"failed",'status':500})

@delivery_user.route('/api/orders',methods=['GET'])
@token_required
def getAllOrders(current_user):
    try:
        orders = mongo.db.order
        output=[]
        userOrders=orders.find({'uid':str(current_user["_id"])})
        if userOrders is None:
            return jsonify({'result':'Yoy have not ordered anything','status':300})
        else:
            for sorder in userOrders:
                output.append({'orderId':str(sorder['_id']),'items':sorder['itemnames'],'qty':sorder['qty'],'amount':sorder['amount'],'time':sorder['time'],'status':sorder['status']})
            return jsonify({'result':output,'status':201})
    except Exception as e:
        print(e)
        return jsonify({'result':"failed",'status':500})


@delivery_user.route('/api/singleorder/<oid>',methods=['GET'])
def getSingleOrders(oid):
    try:
        orders = mongo.db.order
        items = mongo.db.item
        output=[]
        sorder=orders.find_one({'_id':ObjectId(oid)})
        current_items = sorder['items']
        current_prices = []
        for it in current_items:
            itemf = items.find_one({'_id':ObjectId(it)})
            current_prices.append(itemf['price'])
        return jsonify({'orderId':str(sorder['_id']),'items':sorder['itemnames'],'qty':sorder['qty'],'amount':sorder['amount'],'time':sorder['time'],'status':sorder['status'],'itemprices':current_prices})
    except Exception as e:
        print(e)
        return jsonify({'result':"failed",'status':500})

@delivery_user.route('/api/orders',methods=['POST'])
def pushOrder():
    try:
        orders = mongo.db.order
        id = orders.insert({
        'items':request.json['items'],
        'itemnames':request.json['itemnames'],
        'qty':request.json['qty'],
        'uid':str(current_user["_id"]),
        'amount':request.json['amount'],
        'time':request.json['time'],
        'status':request.json['status'],
        })

        return jsonify({'result':str(id),'status':201})
    except Exception as e:
        print(e)
        return jsonify({'result':"failed",'status':500})