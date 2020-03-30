from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo

helper = Blueprint('helper', __name__)

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

@helper.route('/api/shop/register',methods=['POST'])
def registerShop():
    try:
        shops = mongo.db.shop
        existing_shop = shops.find_one({'shopname':request.json['shopname'],'zone':request.json['zone']})
        if existing_shop is None:
            id = shops.insert({
            'shopname':request.json['shopname'],
            'zone':request.json['zone'],
            'type':request.json['type'],
            'address':request.json['address'],
            'phone':request.json['phone'],
            'items':[],
            'orders':[]
            })

            return jsonify({'id':str(id),'status':201})
        else:
            return jsonify({'id':"shop exists!!",'status':401})

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})

@user_side.route('/api/shop/login',methods=['POST'])
def loginShop():
    try:
        shops = mongo.db.shop
        login_shop = shops.find_one({'email':request.json['email']})

        if login_shop:
            if login_shop['password'] == bcrypt.hashpw(request.json['password'].encode('utf-8'),login_user['password']):
                login_user['_id']=str(login_user['_id'])
                token = jwt.encode({'uid':login_user['_id'],'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},SECRET_KEY)
                login_user['token']=token.decode('UTF-8')
                del login_user['password']
                return jsonify({'id':login_user,"status":200})
            else:
                return jsonify({'id':"password wrong","status":404})
        else:
            return jsonify({'id':"user not exists!!","status":403})
    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})



@helper.route('/api/shop/insert_item',methods=['POST'])
def insertItem():
    try:
        items = mongo.db.item
        existing_item = items.find_one({'itemname':request.json['itemname'],'price':request.json['price']})
        if existing_item is None:
            id = items.insert({
            'itemname':request.json['itemname'],
            'type':request.json['type'],
            'price':request.json['price'],
            'unitqty':request.json['unitqty'],
            })

            return jsonify({'id':str(id),'status':201})
        else:
            return jsonify({'id':"item exists!!",'status':401})

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})