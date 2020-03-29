from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo

helper = Blueprint('helper', __name__)


@helper.route('/api/shop',methods=['POST'])
def insertShop():
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
            'items':[]
            })

            return jsonify({'id':str(id),'status':201})
        else:
            return jsonify({'id':"shop exists!!",'status':401})

    except Exception as e:
        print(e)
        return jsonify({'id':"failed",'status':500})


@helper.route('/api/item',methods=['POST'])
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