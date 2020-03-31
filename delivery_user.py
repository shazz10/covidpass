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

@delivery_user.route('/api/get_shops',methods=['POST'])
@token_required
def getAllShop(current_user):
    try:
        shops = mongo.db.shop
        #users = mongo.db.user
        #current_user = users.find_one({'_id':ObjectId(request.json['uid'])})
        zone = request.json['zone']

        output=[]
        shops_in_zone=shops.find({'zone':int(zone),'type':int(request.json['type'])})
        
        for shop in shops_in_zone:
            shop['_id']=str(shop["_id"])
            output.append(shop)

        if len(output)>0:
            return jsonify({'id':output,'status':200})
        else:
            return jsonify({'id':"no shops exists!!",'status':400})


    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})



@delivery_user.route('/api/get_orders',methods=['GET'])
@token_required
def getAllOrders(current_user):
    try:
        orders = mongo.db.order
        users = mongo.db.user
        shops = mongo.db.shop
        output=[]
        dead_orders=[]
        for oid in current_user["orders"]:
            o = orders.find_one({"_id":ObjectId(oid)})
            if o:
                o["_id"]=str(o["_id"])
                shop = shops.find_one({"_id":ObjectId(o['sid'])})
                shop["_id"]=str(shop["_id"])
                o["shop_details"]=shop
                output.append(o)
            else:
                dead_orders.append(oid)

        if len(dead_orders)>0:
            for oid in dead_orders:
                users.find_one_and_update({"_id":current_user["_id"]},{"$pull":{'orders':oid}})

        return jsonify({'id':output,'status':200})
        
    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


# @delivery_user.route('/api/singleorder/<oid>',methods=['GET'])
# def getSingleOrders(oid):
#     try:
#         orders = mongo.db.order
#         items = mongo.db.item
#         output=[]
#         sorder=orders.find_one({'_id':ObjectId(oid)})
#         current_items = sorder['items']
#         current_prices = []
#         for it in current_items:
#             itemf = items.find_one({'_id':ObjectId(it)})
#             current_prices.append(itemf['price'])
#         return jsonify({'orderId':str(sorder['_id']),'items':sorder['itemnames'],'qty':sorder['qty'],'amount':sorder['amount'],'time':sorder['time'],'status':sorder['status'],'itemprices':current_prices})
#     except Exception as e:
#         print(e)
#         return jsonify({'id':"failed",'status':500})


@delivery_user.route('/api/push_orders',methods=['POST'])
@token_required
def pushOrder(current_user):
    try:
        orders = mongo.db.order
        users = mongo.db.user
        shops = mongo.db.shop

        id = orders.insert({
        'items':request.json['items'],
        'uid':str(current_user["_id"]),
        'sid':request.json['sid'],
        'amount':request.json['amount'],
        'time':request.json['time'],
        'status':0,
        })

        result1=users.find_one_and_update({"_id":current_user["_id"]},{'$push':{'orders':str(id)}})
        result2=shops.find_one_and_update({"_id":ObjectId(request.json["sid"])},{'$push':{'orders':str(id)}})

        if not result1 or not result2:
            orders.remove({"_id":ObjectId(id)})
            return jsonify({'id':"user or shop not present!!",'status':404})
        return jsonify({'id':str(id),'status':201})
    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})