from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import flask
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import jwt
from functools import wraps
import datetime
from bucket import get_bucket
import uuid
from notification import createSpecificNotification
import json

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
        output=[]
        res = restricted.find_one({
            "state":current_user["state"],
            "district":current_user["district"],
            "city":current_user["city"],
            "zone":current_user["zone"],
            "subzone":current_user["subzone"],
            "sector":current_user["sector"]
            })

        if res:
            shops_in_zone=shops.find({
                    'zone_address.state':current_user["state"],
                    'zone_address.district':current_user["district"],
                    'zone_address.city':current_user["city"],
                    'zone_address.zone':current_user["zone"],
                    'zone_address.subzone':current_user["subzone"],
                    'zone_address.sector':current_user["sector"]
                },
                {"_id":1,"address":1,"email":1,"shop_name":1,"phone":1,"type":1})

            for shop in shops_in_zone:
                shop['_id']=str(shop["_id"])
                shop['items'] = None
                output.append(shop)
        else:
            shops_in_zone=shops.find({
                    'zone.state':current_user["state"],
                    'zone.district':current_user["district"],
                    'zone.city':current_user["city"],
                    'zone.zone':current_user["zone"],
                    'zone.subzone':current_user["subzone"],
                    'zone.sector':current_user["sector"]
                },
                {"_id":1,"address":1,"email":1,"shop_name":1,"phone":1,"type":1,"zone_address":1})
            
            for shop in shops_in_zone:
                r = restricted.find_one({
                        "state":current_user["state"],
                        "district":current_user["district"],
                        "city":shop["zone_address"]["city"],
                        "zone":shop["zone_address"]["zone"],
                        "subzone":shop["zone_address"]["subzone"],
                        "sector":shop["zone_address"]["sector"]
                    })
                if r:
                    continue
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
                    {"_id":1,"shop_name":1,"email":1,"address":1,"phone":1})
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
                    {"_id":1,"shop_name":1,"email":1,"address":1,"phone":1})
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

        filename = ""
        items=[]
        sid = ""
        address = ""

        if request.headers["Content-Type"] == "multipart/form-data":
            filename = 'prescription/'+str(current_user["_id"])+'/'+str(uuid.uuid4())+'.png'
            my_bucket = get_bucket()
            my_bucket.Object(filename).put(Body=request.files['pic'])
            filename = "https://surakhsa-storage.s3.ap-south-1.amazonaws.com/"+filename

            data = json.loads(request.form["data"])

            items = data['items']
            sid = data['sid']
            address = data['address']

        else:
            items= request.json['items']
            sid = request.json['sid']
            address = request.json['address']




        time = datetime.datetime.utcnow()
        time+= datetime.timedelta(minutes=330)
        time = str(time).split('.')[0]

        id = orders.insert({
        'items':items,
        'uid':str(current_user["_id"]),
        'img':filename,
        'sid':sid,
        'time':time,
        'address':address,
        'phone':current_user["phone"],
        'status':0,
        })

        

        result1=users.find_one_and_update({"_id":current_user["_id"]},{'$push':{'orders':str(id)}})
        result2=shops.find_one_and_update({"_id":ObjectId(request.json["sid"])},{'$push':{'orders':str(id)}})

        if not result1 or not result2:
            orders.remove({"_id":ObjectId(id)})
            return jsonify({'id':"user or shop not present!!",'status':404})


        shop = shops.find_one({"_id":ObjectId(request.json['sid'])},{"player_id":1})
        createSpecificNotification([shop["player_id"]],"New Order placed!!","Please got to your Orders: Check, Edit and Accept Order soon. Thanks!!")
            
        return jsonify({'id':str(id),'status':201})
    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


# @delivery_user.route('/api/upload_prescript',methods=['POST'])

# def upload_prescription():
#     try:
        

#         #print(request.files)
#         #file.save("abc.png")
#         # imagefile = request.files["pic"]

#         # imagefile.save("abc.png")

#         print(request.files)
#         print(request.form)
#         print(request.json)
#         print(request.args)

#         # filename = ""
#         # if "img" in request.json.keys() and request.json["img"] :

#         #     filename = 'prescription/'+str(current_user["_id"])+'/'+str(uuid.uuid4())+'.txt'

#         #     my_bucket = get_bucket()
#         #     my_bucket.Object(filename).put(Body=request.json['img'])
#         #print("hello")

#         return jsonify({'id':"filename.jpg",'status':201})
#     except Exception as e:
#         raise(e)
#         return jsonify({'id':"failed",'status':500})


# @delivery_user.route('/api/push_medicine_orders',methods=['POST'])
# @token_required
# def pushOrder(current_user):
#     try:
#         orders = mongo.db.order
#         users = mongo.db.user
#         shops = mongo.db.shop

#         time = datetime.datetime.utcnow()
#         time+= datetime.timedelta(minutes=330)
#         time = str(time).split('.')[0]

#         id = orders.insert({
#         'items':request.json['items'],
#         'uid':str(current_user["_id"]),
#         'sid':request.json['sid'],
#         'time':time,
#         'address':request.json['address'],
#         'phone':current_user["phone"],
#         'status':0,
#         })

#         result1=users.find_one_and_update({"_id":current_user["_id"]},{'$push':{'orders':str(id)}})
#         result2=shops.find_one_and_update({"_id":ObjectId(request.json["sid"])},{'$push':{'orders':str(id)}})

#         if not result1 or not result2:
#             orders.remove({"_id":ObjectId(id)})
#             return jsonify({'id':"user or shop not present!!",'status':404})
#         return jsonify({'id':str(id),'status':201})
#     except Exception as e:
#         print(e)
#         return jsonify({'id':"failed",'status':500})


@delivery_user.route('/api/update_order',methods=['POST'])
@token_required
def update_order(current_user):
    try:
        orders = mongo.db.order
        users = mongo.db.user
        shops = mongo.db.shop

        shop = shops.find_one({"_id":ObjectId(request.json['sid'])},{"player_id":1})
        order = orders.find_one({"_id":ObjectId(request.json["oid"])},{"status":1})

        if order["status"] <3 and int(request.json["status"])==-2:
            orders.find_one_and_update({"_id":ObjectId(request.json["oid"])},{'$set':{'status':-2}})
            shops.find_one_and_update({"_id":ObjectId(request.json["sid"])},{"$pull":{"orders":request.json["oid"]}})     
            
            createSpecificNotification([shop["player_id"]],"Order Cancelled!!","Sorry but one of your Order is Cancelled due to some reason. Please check your orders. Thanks!!")

            return jsonify({'id':"rejected",'status':202})
        elif int(request.json["status"])==2:
            orders.find_one_and_update({"_id":ObjectId(request.json["oid"])},{'$set':{'status':2}})

            createSpecificNotification([shop["player_id"]],"Order Approved from User!!","Your accepted order has been Approved by User!! Please check your Approved orders. Thanks!!")

            return jsonify({'id':"accepted!!",'status':201})

        return jsonify({'id':"error",'status':404})
    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})