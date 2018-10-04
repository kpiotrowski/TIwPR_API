import pymongo
from flask import Flask, request, g

from models import User, LoginData, Room, Meeting, get_user_by_token, list_meetings
from utils import get_request_data, json_response
from db import list_all, delete_one_response, find_one_response, find_one, delete_many, \
    generate_single_post_url_response

app = Flask(__name__)
client = pymongo.MongoClient()
db = client.tiwpr


@app.before_request
def before_request():
    if request.method in ['PUT', 'POST'] and not (request.method == 'POST' and request.endpoint == 'meetings'):
        if not request.form and not request.data:
            return json_response({"message": "Missing request body"}, 400)

    if request.method == 'PUT' and not request.headers.get('If-Match'):
        return json_response({"message": "Missing If-Match header"}, 400)

    if request.endpoint == 'user_login' or (request.endpoint == 'users' and request.method == 'POST'):
        return

    token = request.headers.get('Authorization')
    user_d = get_user_by_token(db.users, token)
    if user_d is not None:
        g.logged_in = True
        g.user = user_d
    else:
        return json_response({"message": "You are not authorized"}, 401)


# ################################################### USERS ########################################################

# List or create users
@app.route('/users', methods=[
    # 'GET',
    'POST'
])
def users():
    if request.method == 'POST':
        user_data = User(**get_request_data(request))
        if not user_data.validate():
            return json_response({"message": "User form is invalid"}, 400)
        return user_data.create(db.users)
    # else:
    # return list_all(db.users, arguments=request.args)


# Get, update, delete user
@app.route('/users/<u_login>', methods=['GET', 'PUT', 'DELETE'])
def user(u_login):
    if u_login != g.user.login:
        return json_response({"message": "You are not allowed to see or modify different user"}, 403)

    if request.method == 'PUT':
        user_data = User(**get_request_data(request), e_tag=request.headers.get('If-Match'))
        if not user_data.validate():
            return json_response({"message": "User form is invalid"}, 400)

        return user_data.update(db.users, u_login)
    elif request.method == 'GET':
        return find_one_response(db.users, u_login, 'login')
    else:
        return delete_one_response(db.users, u_login, 'login')


# Login
@app.route('/tokens', methods=['POST'])
def user_login():
    login_data = LoginData(**get_request_data(request))
    if not login_data.validate():
        return json_response({"message": "Missing login or password"}, 400)

    return login_data.login_response(db.users)


# ################################################### ROOMS #######################################################

# List or create rooms
# Show only available rooms using query param
@app.route('/rooms', methods=['GET', 'POST'])
def rooms():
    if request.method == 'POST':
        room_data = Room(**get_request_data(request))
        if not room_data.validate():
            return json_response({"message": "Room form is invalid"}, 400)

        return room_data.create(db.rooms)
    else:
        return list_all(db.rooms, arguments=request.args)


# Get, update, delete room
@app.route('/rooms/<room_id>', methods=['GET', 'PUT', 'DELETE'])
def room(room_id):
    if request.method == 'PUT':
        room_data = Room(**get_request_data(request), e_tag=request.headers.get('If-Match'))
        if not room_data.validate():
            return json_response({"message": "Room form is invalid"}, 400)

        return room_data.update(db.rooms, room_id)
    elif request.method == 'GET':
        return find_one_response(db.rooms, room_id)
    else:
        if find_one(db.meetings, room_id, 'room_id'):
            return json_response({"message": "Cannot delete room because there is a meeting that is associated with "
                                             "that room"}, 400)
        return delete_one_response(db.rooms, room_id)


# ################################################## MEETINGS #####################################################

# Generates single POST url or list meetings
@app.route('/meetings', methods=['GET', 'POST'])
def meetings():
    if request.method == 'POST':
        return generate_single_post_url_response(db.meetings, g.user, "meetings")
    else:
        return list_meetings(db.meetings, {}, request.args)


# Get, update or delete meeting
@app.route('/meetings/<meeting_id>', methods=['GET', 'PUT', 'DELETE'])
def meeting(meeting_id):
    if request.method == 'PUT':
        meeting_data = Meeting(**get_request_data(request), e_tag=request.headers.get('If-Match'))
        if not meeting_data.validate():
            return json_response({"message": "Meeting form is invalid"}, 400)

        return meeting_data.update(db.meetings, meeting_id, db.rooms, g.user)

    elif request.method == 'GET':
        return find_one_response(db.meetings, meeting_id)
    else:
        return delete_one_response(db.meetings, meeting_id)


# List meetings for the room
@app.route('/rooms/<room_id>/meetings', methods=['GET'])
def room_meetings(room_id):
    if find_one(db.rooms, room_id) is None:
        return json_response({"message": "Room does not exist"}, 404)

    return list_all(db.meetings, {"room_id": room_id}, request.args)


# List or delete meetings for the user
@app.route('/users/<u_login>/meetings', methods=['GET', 'DELETE'])
def user_meetings(u_login):
    user_data = find_one(db.users, u_login, 'login')
    if user_data is None:
        return json_response({"message": "User does not exist"}, 404)

    user_data = User(**user_data)

    if request.method == 'DELETE':
        if g.user.get_id() != user_data.get_id():
            return json_response({"message": "You cannot delete different user meetings"}, 403)

        return delete_many(db.meetings, {'user_id': str(user_data.get_id())})
    else:
        return list_meetings(db.meetings, {'user_id': str(user_data.get_id())}, request.args)
