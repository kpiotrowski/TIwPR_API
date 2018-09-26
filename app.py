import pymongo
from flask import Flask, request
from flask.ext.login import login_user, logout_user, current_user, login_required

from models import User, LoginData, Room, Meeting, get_user_by_token
from utils import get_request_data, json_response, generate_single_post_url_response
from db import list_all, delete_one_response, find_one_response, find_one, delete_many

app = Flask(__name__)
client = pymongo.MongoClient('localhost', 27017)
db = client.tiwpr


@app.before_request
def before_request():
    if request.endpoint == '/tokens' or (request.endpoint == '/users' and request.method == 'POST'):
        return

    token = " TODO GET TOKEN "
    user = get_user_by_token(db.users, token)
    if user is not None:
        login_user(user)


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
@app.route('/users/<user_id>', methods=['GET', 'PUT', 'DELETE'])
def user(user_id):
    if request.method == 'PUT':
        user_data = User(**get_request_data(request))
        if not user_data.validate():
            return json_response({"message": "User form is invalid"}, 400)

        return user_data.update(db.users, user_id)
    elif request.method == 'GET':
        return find_one_response(db.users, user_id)
    else:
        return delete_one_response(db.users, user_id)


# List or delete meetings for the user
@app.route('/users/<user_id>/meetings', methods=['GET', 'DELETE'])
def user_meetings(user_id):
    if find_one(db.users, user_id) is None:
        return json_response({"message": "User does not exist"}, 404)

    if request.method == 'DELETE':
        return delete_many(db.meetings, {'user_id': user_id})
    else:
        return list_all(db.meetings, {'user_id': user_id}, request.args)


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
        room_data = Room(**get_request_data(request))
        if not room_data.validate():
            return json_response({"message": "Room form is invalid"}, 400)

        return room_data.update(db.rooms)
    elif request.method == 'GET':
        return find_one_response(db.rooms, room_id)
    else:
        return delete_one_response(db.rooms, room_id)


# List meetings for the room
@app.route('/rooms/<room_id>/meetings', methods=['GET'])
def room_meetings(room_id):
    if find_one(db.rooms, room_id) is None:
        return json_response({"message": "Room does not exist"}, 404)

    return list_all(db.meetings, {"room_id": room_id}, request.args)


# ################################################## MEETINGS #####################################################

# Generates single POST url or list meetings
@app.route('/meetings', methods=['GET', 'POST'])
def meetings():
    if request.method == 'POST':
        return generate_single_post_url_response(db.new_meetings)
    else:
        return list_all(db.meetings, arguments=request.args)


# Creates new user using PUT request
@app.route('/new_meetings/<meetings_uuid>', methods=['PUT'])
def new_meetings(meetings_uuid):
    if find_one(db.new_meetings, meetings_uuid) is None:
        return json_response({"message": "Single POST URL doesn't exist"}, 404)

    meeting_data = Meeting(**get_request_data(request))
    if not meeting_data.validate():
        return json_response({"message": "Meeting form is invalid"}, 400)

    response = meeting_data.create(db.meetings)
    delete_one_response(db.new_meetings, meetings_uuid)
    return response


# Get, update or delete meeting
@app.route('/meetings/<meeting_id>', methods=['GET', 'PUT', 'DELETE'])
def meeting(meeting_id):
    if request.method == 'PUT':
        meeting_data = Meeting(**get_request_data(request))
        if not meeting_data.validate():
            return json_response({"message": "Meeting form is invalid"}, 400)

        return meeting_data.update(db.meetings)

    elif request.method == 'GET':
        return find_one_response(db.meetings, meeting_id)
    else:
        return delete_one_response(db.meetings, meeting_id)


# Moves meeting to the different room
@app.route('/meetings/<meeting_id>/rooms/<room_id>', methods=['PUT'])
def meeting_move(meeting_id, room_id):
    pass
