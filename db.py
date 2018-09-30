import secrets
import uuid

import redis
from bson import ObjectId
from bson.errors import InvalidId

import config
from utils import json_response

tokens_db = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
EXPIRE_TIME = 3600


def get_token(key):
    token = tokens_db.get(key)
    if token is not None:
        return token.decode("utf-8")
    return token


def create_new_token(user_id):
    token = secrets.token_hex(32)

    tokens_db.set(user_id, token)
    tokens_db.set(token, user_id)

    tokens_db.expire(user_id, EXPIRE_TIME)
    tokens_db.expire(token, EXPIRE_TIME)

    return token


def list_all(collection, filters=None, arguments=None):
    if filters is None:
        filters = {}

    page, items = int(arguments.get('page', 0)), int(arguments.get('items', 25))
    for argument in arguments:
        if argument not in ['page', 'items']:
            filters[argument] = arguments[argument]

    count = collection.find(filters).count()
    data = collection.find(filters).skip(page*items).limit(items)

    result = [x for x in data]
    for x in result:
        x['_id'] = str(x['_id'])

    return json_response({"items": result, "page": page, "all_count": count}, 200)


def find_one(collection, object_id, filter_key='_id'):
    if filter_key == '_id':
        key = ObjectId(object_id)
    else:
        key = object_id

    try:
        return collection.find_one({filter_key: key})
    except InvalidId:
        return None


def find_one_response(collection, object_id, filter_key='_id'):
    data = find_one(collection, object_id, filter_key)

    if data is None:
        return json_response({"message": "Not found", "status": "404"}, 404)
    data['_id'] = str(data['_id'])
    for k, v in data.items():
        if isinstance(v, bytes):
            data[k] = v.decode('utf-8')
        if 'hash' in k:
            data[k] = "***"

    return json_response(data, 200)


def object_save(collection, object_data):
    if '_id' not in object_data:
        status = 201
        msg = "Successfully created object"
    else:
        status = 200
        msg = "Successfully updated object"

    key = str(collection.save(object_data))
    return json_response({"_id": key, "message": msg}, status)


def delete_one_response(collection, object_id,  filter_key='_id'):
    if find_one(collection, object_id, filter_key) is None:
        return json_response({"message": "Not found", "status": "404"}, 404)

    if filter_key == '_id':
        key = ObjectId(object_id)
    else:
        key = object_id

    collection.delete_one({filter_key: key})
    return json_response("", 204)


def delete_many(collection, filters):
    collection.delete_many(filters)
    return json_response("", 204)


def generate_single_post_url_response(collection):
    key = str(collection.save({'_temp': True}))

    return json_response({
        "url": f"{config.HOST}/meetings/{key}",
        "_id": key,
        "method": "PUT",
        "Message:": "Created temporary object. Use put method to update it."
    }, 202)
