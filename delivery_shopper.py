from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import jwt
from functools import wraps

delivery_shopper = Blueprint('delivery_shopper', __name__)

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


@delivery_shopper.route('/api/orders/<sid>',methods=['GET'])
def getAllShopOrders(sid):
    try:
        shops=mongo.db.shop
        orders = mongo.db.order
        output=[]
        current_shop=shops.find_one({'_id':ObjectId(sid)})
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


@delivery_shopper.route('/api/orderedit',methods=['POST'])
def editOrders():
    try:
        orders = mongo.db.order
        current_order=orders.find_one({'_id':ObjectId(request.json['oid'])})
        if current_order is None:
            return jsonify({'result':'No orders exist','status':300})
        else:
            orders.find_one_and_update({"_id":ObjectId(request.json['oid'])},{'$set':{'items':request.json['items']}})
            return jsonify({'result':"updated successfully",'status':201})
    except Exception as e:
        print(e)
        return jsonify({'result':"failed",'status':500})

@delivery_shopper.route('/api/orderstatus',methods=['POST'])
def editStatusOrders():
    try:
        orders = mongo.db.order
        current_order=orders.find_one({'_id':ObjectId(request.json['oid'])})
        if current_order is None:
            return jsonify({'result':'No orders exist','status':300})
        else:
            orders.find_one_and_update({"_id":ObjectId(request.json['oid'])},{'$set':{'status':request.json['status']}})
            return jsonify({'result':"updated successfully",'status':201})
    except Exception as e:
        print(e)
        return jsonify({'result':"failed",'status':500})
