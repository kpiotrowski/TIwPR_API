import json

from flask import Response


def get_request_data(request):
    if request.form and len(request.form) > 0:
        data = request.form.to_dict(flat=False)
    else:
        data = json.loads(request.data)

    return data


def json_response(dict_obj, code, headers=None):
    if isinstance(dict_obj, (dict, list)):
        data = json.dumps(dict_obj)
    else:
        data = dict_obj
    resp = Response(response=data, status=code,
                    mimetype="application/json")

    if headers is not None:
        for header_key in headers:
            resp.headers[header_key] = headers[header_key]

    return resp
