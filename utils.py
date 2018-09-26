import json

from flask import Response

from db import get_token, find_one


def get_request_data(request):
    if request.form and len(request.form) > 0:
        data = request.form.to_dict()
    else:
        data = json.loads(request.data)
    return data


def json_response(dict_obj, code):
    if isinstance(dict_obj, (dict, list)):
        data = json.dumps(dict_obj)
    else:
        data = dict_obj
    resp = Response(response=data, status=code,
                    mimetype="application/json")
    return resp


def update_existing(collection, object_data):
    pass


def generate_single_post_url_response(collection):
    pass
