from flask import Blueprint, request, jsonify, session
from flask_pymongo import PyMongo
import bcrypt
import json
from bson.objectid import ObjectId
from database import mongo
import jwt
import datetime
from functools import wraps

quarantine = Blueprint('quarantine', __name__)

SECRET_KEY = "keepitsecret!!"





