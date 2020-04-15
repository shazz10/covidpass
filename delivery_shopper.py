from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import jwt
from functools import wraps


delivery_shopper = Blueprint('delivery_shopper', __name__)


SECRET_KEY = "keepitsecret!!"

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




@delivery_shopper.route('/api/shop/orders/<status>',methods=['GET'])
@token_required
def getAllShopOrders(current_shop,status):
    try:
        shops=mongo.db.shop
        orders = mongo.db.order
        output=[]
        
        orders_list=[]
        
        if int(status)==3:
            orders_list=current_shop['history']
        else:
            orders_list=current_shop['orders']

        if len(orders_list)==0:
            return jsonify({'id':[],'status':300})
        else:
            for order in orders_list:
                sorder=orders.find_one({'_id':ObjectId(order)})
                if sorder and sorder["status"]==int(status):
                    sorder['_id']=str(sorder["_id"])
                    output.append(sorder)
            return jsonify({'id':output,'status':201})
    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})



@delivery_shopper.route('/api/shop/edit_order',methods=['POST'])
@token_required
def editOrders(current_shop):
    try:
        orders = mongo.db.order
        
        result=orders.find_one_and_update({"_id":ObjectId(request.json['oid'])},
            {'$set':{'items':request.json['items'],'amount':request.json['amount'],'delivery_time':request.json["delivery_time"],'status':1}})

        if result:
            return jsonify({'id':"updated successfully",'status':201})
        else:
            return jsonify({'id':'No orders exist','status':300})

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


@delivery_shopper.route('/api/shop/update_status',methods=['PUT'])
@token_required
def editStatusOrders(current_shop):
    try:
        orders = mongo.db.order
        shops = mongo.db.shop
        result = orders.find_one_and_update({"_id":ObjectId(request.json['oid'])},{'$inc':{'status':1}})
        if result:
            shops.find_one_and_update({"_id":current_shop["_id"]},{"$pull":{"orders":request.json['oid']}})
            shops.find_one_and_update({"_id":current_shop["_id"]},{"$push":{"history":request.json['oid']}})

        if result:
            return jsonify({'id':"updated successfully",'status':201})
        else:
            return jsonify({'id':'No orders exist','status':300})

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


@delivery_shopper.route('/api/shop/reject_order',methods=['PUT'])
@token_required
def rejectOrder(current_shop):
    try:
        orders = mongo.db.order
        shops = mongo.db.shop

        result=orders.find_one_and_update({"_id":ObjectId(request.json['oid'])},{'$set':{'status':-1}})
        shops.find_one_and_update({"_id":current_shop["_id"]},{'$pull':{'orders':request.json['oid']}})

        if result:
            return jsonify({'id':"updated successfully",'status':201})
        else:
            return jsonify({'id':'No orders exist','status':300})
            
    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})