import redis
import secrets

from bson import json_util, ObjectId
from bson.errors import InvalidId

import config
from utils import json_response

tokens_db = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
EXPIRE_TIME = 3600


def get_token(key):
    return tokens_db.get(key)


def create_new_token(login):
    token = secrets.token_hex(32)

    tokens_db.set(login, token)
    tokens_db.set(token, login)

    tokens_db.expire(login, EXPIRE_TIME)
    tokens_db.expire(token, EXPIRE_TIME)

    return token


def list_all(collection, filters=None, arguments=None):
    if filters is None:
        filters = {}

    page, items = arguments.get('page'), arguments.get('items')
    for argument in arguments:
        if argument not in ['page', 'items']:
            filters[argument] = arguments[argument]

    if page is not None and items is not None:
        data = collection.find(filters).skip(page*items).limit(items)
    else:
        data = collection.find(filters)

    return json_response(json_util.dumps(data), 200)


def find_one(collection, object_id, filter_key='_id'):
    try:
        return collection.find_one({filter_key: ObjectId(object_id)})
    except InvalidId:
        return None


def find_one_response(collection, object_id):
    data = find_one(collection, object_id)

    if data is None:
        return json_response({"message": "Not found", "status": "404"}, 404)
    return json_response(data, 200)


def object_save(collection, object_data):
    if '_id' not in object_data:
        status = 201
        msg = "Successfully created object"
    else:
        status = 200
        msg = "Successfully updated object"

    output = collection.save(object_data)
    key = str(output['_id'])
    return json_response({"_id": key, "message": msg}, status)


def delete_one_response(collection, object_id):
    if find_one(collection, object_id) is None:
        return json_response({"message": "Not found", "status": "404"}, 404)

    collection.delete_one({"_id": ObjectId(object_id)})
    return json_response("", 204)


def delete_many(collection, filters):
    collection.delete_many(filters)
    return json_response("", 204)

