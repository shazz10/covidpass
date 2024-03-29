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
        ItemCursor=items.find({})
        for item in ItemCursor:
            output.append({
                'itemName':item['itemName'],
                'category':item['category'],
                'itemPrice':item['itemPrice'],
                'itemQty':item['itemQty'],
                'itemCompany':item['itemCompany'],
                'item_add_qty':item['item_add_qty']})
        print(output)
        return jsonify({'id':output,'status':201})
    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})



@delivery_shopper.route('/api/shop/orders',methods=['GET'])
@token_required
def getAllShopOrders(current_shop):
    try:
        shops=mongo.db.shop
        orders = mongo.db.order
        output=[]
        orders_list=current_shop['orders']

        if len(orders_list)==0:
            return jsonify({'id':'No orders exist','status':300})
        else:
            for order in orders_list:
                sorder=orders.find_one({'_id':ObjectId(order)})
                if sorder:
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
        
        result=orders.find_one_and_update({"_id":ObjectId(request.json['oid'])},{'$set':{'items':request.json['items'],'amount':request.json['amount']}})

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

        result=orders.find_one_and_update({"_id":ObjectId(request.json['oid'])},{'$set':{'status':request.json['status']}})

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