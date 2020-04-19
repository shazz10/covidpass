from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import jwt
from functools import wraps
from notification import createSpecificNotification
from bucket import get_bucket

delivery_shopper = Blueprint('delivery_shopper', __name__)


SECRET_KEY = "keepitsecret!!"

status_map ={
    0:"Pending",
    1:"Accepted and Waiting for Approval",
    2:"Approved",
    3:"Out for Delivery",
    4:"Delivered"
}

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

        statuses = [int(status)]

        if int(status)==2:
            statuses.append(3)

        if int(status)==4:
            orders_list=current_shop['history']
        else:
            orders_list=current_shop['orders']

        if len(orders_list)==0:
            return jsonify({'id':[],'status':300})
        else:
            for order in orders_list:
                sorder=orders.find_one({'_id':ObjectId(order)})
                if sorder and sorder["status"] in statuses:
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
        users = mongo.db.user
        result=orders.find_one_and_update({"_id":ObjectId(request.json['oid'])},
            {'$set':{'items':request.json['items'],'amount':request.json['amount'],'delivery_time':request.json["delivery_time"],'status':1}})

        if result:
            order = orders.find_one({"_id":ObjectId(request.json['oid'])},{"uid":1})
            user = users.find_one({"_id":ObjectId(order["uid"])},{"player_id":1})
            createSpecificNotification([user["player_id"]],"Order Accepted by Shopkeeper","Please check the order in history tab of homepage and Approve. Thanks!!")
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
        users = mongo.db.user

        result = orders.find_one_and_update({"_id":ObjectId(request.json['oid'])},{'$set':{'status':int(request.json["status"])}})
        if int(request.json["status"])==4 and result:
            shops.find_one_and_update({"_id":current_shop["_id"]},{"$pull":{"orders":request.json['oid']}})
            shops.find_one_and_update({"_id":current_shop["_id"]},{"$push":{"history":request.json['oid']}})

        if result:
            order = orders.find_one({"_id":ObjectId(request.json['oid'])},{"uid":1})
            user = users.find_one({"_id":ObjectId(order["uid"])},{"player_id":1})
            createSpecificNotification([user["player_id"]],"Order Status Updated!!","Order is {}!! Please check the order in history tab of homepage. Thanks!!",format(status_map[int(request.json["status"])]))
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
        users = mongo.db.user

        result=orders.find_one_and_update({"_id":ObjectId(request.json['oid'])},{'$set':{'status':-1}})
        shops.find_one_and_update({"_id":current_shop["_id"]},{'$pull':{'orders':request.json['oid']}})

        if result:
            order = orders.find_one({"_id":ObjectId(request.json['oid'])},{"uid":1})
            user = users.find_one({"_id":ObjectId(order["uid"])},{"player_id":1})
            createSpecificNotification([user["player_id"]],"Order Rejected!!","Sorry but your Order is Rejected due to some reason. Please contact the Shopkeeper in case of Queries. Thanks!!")
            return jsonify({'id':"updated successfully",'status':201})
        else:
            return jsonify({'id':'No orders exist','status':300})
            
    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})



@delivery_shopper.route('/api/shop/get_prescription_image',methods=['POST'])
@token_required
def get_prescription_image(current_user):
    try:
        my_bucket = get_bucket()
        ob=my_bucket.Object(request.json["filename"]).get()
        return ob["Body"].read()

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})
