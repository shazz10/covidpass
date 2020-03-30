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


@delivery_shopper.route('/api/items',methods=['GET'])
def getAllItems():
    try:
        items=mongo.db.item
        output=[]
        ItemCursor=items.find()
        for item in ItemCursor:
            output.append({'itemId':str(item['_id']),'itemName':item['itemname'],'category':item['category'],'itemPrice':item['itemPrice'],'itemQty':item['itemQty'],'item_add_qty':item['item_add_qty']})
        return jsonify({'result':output,'status':201})
    except Exception as e:
        print(e)
        return jsonify({'result':"failed",'status':500})



@delivery_shopper.route('/api/shop/orders',methods=['GET'])
@token_required
def getAllShopOrders(current_shop):
    try:
        shops=mongo.db.shop
        orders = mongo.db.order
        output=[]
        orders_list=current_shop['orders']

        if len(orders_list)==0:
            return jsonify({'result':'No orders exist','status':300})
        else:
            for order in orders_list:
                sorder=orders.find_one({'_id':ObjectId(order)})
                output.append({'order_id':str(sorder['_id']),'items':sorder['items'],'uid':sorder['uid'],'amount':sorder['amount'],'time':sorder['time'],'status':sorder['status']})
            return jsonify({'result':output,'status':201})
    except Exception as e:
        print(e)
        return jsonify({'result':"failed",'status':500})


@delivery_shopper.route('/api/shop/edit_order',methods=['POST'])
@token_required
def editOrders(current_shop):
    try:
        orders = mongo.db.order
        
        result=orders.find_one_and_update({"_id":ObjectId(request.json['oid'])},{'$set':{'items':request.json['items']}})

        if result:
            return jsonify({'result':"updated successfully",'status':201})
        else:
            return jsonify({'result':'No orders exist','status':300})

    except Exception as e:
        print(e)
        return jsonify({'result':"failed",'status':500})


@delivery_shopper.route('/api/shop/update_status',methods=['PUT'])
@token_required
def editStatusOrders(current_shop):
    try:
        orders = mongo.db.order

        result=orders.find_one_and_update({"_id":ObjectId(request.json['oid'])},{'$set':{'status':request.json['status']}})

        if result:
            return jsonify({'result':"updated successfully",'status':201})
        else:
            return jsonify({'result':'No orders exist','status':300})

    except Exception as e:
        print(e)
        return jsonify({'result':"failed",'status':500})


@delivery_shopper.route('/api/shop/reject_order',methods=['PUT'])
@token_required
def rejectOrder(current_shop):
    try:
        orders = mongo.db.order
        shops = mongo.db.shop

        result=orders.find_one_and_update({"_id":ObjectId(request.json['oid'])},{'$set':{'status':-1}})
        shops.find_one_and_update({"_id":current_shop["_id"]},{'$pull':{'orders':request.json['oid']}})

        if result:
            return jsonify({'result':"updated successfully",'status':201})
        else:
            return jsonify({'result':'No orders exist','status':300})
            
    except Exception as e:
        print(e)
        return jsonify({'result':"failed",'status':500})