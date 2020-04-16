from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import jwt
from functools import wraps
import datetime

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

@delivery_user.route('/api/set_delivery_address',methods=['POST'])
@token_required
def set_delivery_address(current_user):
    try:
        users = mongo.db.user
        result=users.find_one_and_update({"_id":current_user["_id"]},{"$set":
            {
                "city":request.json["city"],
                "zone":request.json["zone"],
                "subzone":request.json["subzone"],
                "sector":request.json["sector"],
                "area":request.json["area"]

            }})
        
        if result:
            return jsonify({'id':"updated",'status':201})
        else:
            return jsonify({'id':"failure",'status':400})

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


@delivery_user.route('/api/get_shops',methods=['GET'])
@token_required
def getAllShop(current_user):
    try:
        shops = mongo.db.shop
        restricted = mongo.db.restricted

        res = restricted.find_one({
            "city":current_user["city"],
            "zone":current_user["zone"],
            "subzone":current_user["subzone"],
            "sector":current_user["sector"]
            })
        if res:
            return jsonify({'id':"Your location is restricted for delivery!!",'status':300})

        output=[]
        shops_in_zone=shops.find({'zone':current_user["zone"]},
            {"_id":1,"address":1,"email":1,"name":1,"phone":1})
        
        for shop in shops_in_zone:
            shop['_id']=str(shop["_id"])
            shop['items'] = None
            output.append(shop)

        if len(output)>0:
            return jsonify({'id':output,'status':200})
        else:
            return jsonify({'id':"no shops exists!!",'status':400})


    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


@delivery_user.route('/api/get_shop_items',methods=['POST'])
@token_required
def get_shop_items(current_user):
    try:
        shops = mongo.db.shop
        
        shop = shops.find_one({"_id":ObjectId(request.json['sid'])},
                              {"items":1})
        
        
        items = shop['items']

        if shop:
            return jsonify({'id':items,'status':200})
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
        #print(current_user["orders"])
        for oid in current_user["orders"]:
            o = orders.find_one({"_id":ObjectId(oid)})
            # print(o)
            if o:
                o["_id"]=str(o["_id"])
                shop = shops.find_one({"_id":ObjectId(o['sid'])},
                    {"_id":1,"name":1,"email":1,"address":1,"phone":1})
                if shop:
                    shop["_id"]=str(shop["_id"])
                o["shop_details"]=shop
                output.append(o)
            else:
                dead_orders.append(oid)
        #print(output)
        if len(dead_orders)>0:
            for oid in dead_orders:
                users.find_one_and_update({"_id":current_user["_id"]},{"$pull":{'orders':oid}})

        return jsonify({'id':output,'status':200})
        
    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


@delivery_user.route('/api/get_order',methods=['POST'])
@token_required
def get_order(current_user):
    try:
        orders = mongo.db.order
        users = mongo.db.user
        shops = mongo.db.shop

        
        o = orders.find_one({"_id":ObjectId(request.json['oid'])})

        if o:
            o["_id"]=str(o["_id"])
            shop = shops.find_one({"_id":ObjectId(o['sid'])},
                    {"_id":1,"name":1,"email":1,"address":1,"phone":1})
            if shop:
                shop["_id"]=str(shop["_id"])
            o["shop_details"]=shop
            return jsonify({'id':o,'status':200})
        else:
            return jsonify({'id':'No such order!!','status':404})

        
    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


@delivery_user.route('/api/push_orders',methods=['POST'])
@token_required
def pushOrder(current_user):
    try:
        orders = mongo.db.order
        users = mongo.db.user
        shops = mongo.db.shop

        time = datetime.datetime.utcnow()
        time+= datetime.timedelta(minutes=330)
        time = str(time).split('.')[0]

        id = orders.insert({
        'items':request.json['items'],
        'uid':str(current_user["_id"]),
        'sid':request.json['sid'],
        'time':time,
        'address':request.json['address'],
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


@delivery_user.route('/api/update_order',methods=['POST'])
@token_required
def update_order(current_user):
    try:
        orders = mongo.db.order
        users = mongo.db.user
        shops = mongo.db.shop

        if int(request.json["status"])==-1:
            orders.find_one_and_update({"_id":ObjectId(request.json["oid"])},{'$set':{'status':-1}})
            shops.find_one_and_update({"_id":ObjectId(request.json["sid"])},{"$pull":{"orders":request.json["oid"]}})
            return jsonify({'id':"rejected",'status':202})
        elif int(request.json["status"])==2:
            orders.find_one_and_update({"_id":ObjectId(request.json["oid"])},{'$set':{'status':2}})
            return jsonify({'id':"accepted!!",'status':201})

        return jsonify({'id':"error",'status':404})
    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})