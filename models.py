import datetime
from dateutil import parser

import bcrypt
import rfc3339

from db import get_token, create_new_token, find_one, object_save, list_all
from utils import json_response


def get_user_by_token(collection, token):
    user_id = get_token(token)
    if user_id is None:
        return None

    user = find_one(collection, user_id)
    if user is None:
        return None
    return User(**user)


class User:

    def __init__(self, **kwargs):
        self._id = kwargs.get('_id')
        self.login = kwargs.get('login')
        self.password_hash = kwargs.get('password_hash')
        self.name = kwargs.get('name')

        if 'password' in kwargs:
            self.password_hash = bcrypt.hashpw(kwargs.get('password').encode('utf-8'), bcrypt.gensalt())

    def get_id(self):
        return self._id

    def password_match(self, password):
        return bcrypt.hashpw(password, self.password_hash) == self.password_hash

    def validate(self):
        for field in [self.login, self.password_hash, self.name]:
            if field is None:
                return False
        return True

    def authenticate(self, password):
        if not bcrypt.checkpw(password.encode('utf-8'), self.password_hash):
            return json_response({"message": "Invalid login or password"}, 403)

        token = get_token(self._id)
        if token is None:
            token = create_new_token(self._id)

        return json_response({"token": token}, 200)

    def create(self, collection):
        if find_one(collection, self.login, 'login') is not None:
            return json_response({"message": "User already exists"}, 409)

        return object_save(collection, self.to_dict())

    def update(self, collection, old_login):
        user = find_one(collection, old_login, 'login')
        if user is None:
            return json_response({"message": "User doesn't exist"}, 404)

        user = User(**user)
        if self.login != user.login:
            return json_response({"message": "You cannot change user login"}, 400)

        self._id = user._id
        return object_save(collection, self.to_dict())

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}


class Room:

    def __init__(self, **kwargs):
        self._id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.place = kwargs.get('place')

    def get_id(self):
        return self._id

    def validate(self):
        for field in [self.name, self.place]:
            if field is None:
                return False
        return True

    def create(self, collection):
        return object_save(collection, self.to_dict())

    def update(self, collection, old_id):
        old_room = find_one(collection, old_id)
        if old_room is None:
            return json_response({"message": "Room doesn't exist"}, 404)

        old_room = Room(**old_room)
        self._id = old_room._id
        return object_save(collection, self.to_dict())

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def available(self, meetings_collection, start, end, meeting_id=None):
        pass


class Meeting:

    def __init__(self, **kwargs):
        self._id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.start_time = kwargs.get('start_time')
        self.end_time = kwargs.get('end_time')
        self.room_id = kwargs.get('room_id')
        self.user_id = kwargs.get('user_id')

        if self.start_time is not None:
            self.start_time = rfc3339.rfc3339(parser(self.start_time), utc=True)
        if self.end_time is not None:
            self.end_time = rfc3339.rfc3339(parser(self.end_time), utc=True)

    def validate(self):
        for field in [self.name, self.start_time, self.end_time]:
            if field is None:
                return False
        return True

    def update(self, collection, meeting_id, rooms_collection, user):
        self.user_id = str(user.get_id())
        self._id = meeting_id

        old_meeting = find_one(collection, meeting_id)
        if old_meeting is None:
            return json_response({"message": "Meeting doesn't exist"}, 404)
        old_meeting = Meeting(**old_meeting)
        if self.room_id is None:
            self.room_id = old_meeting.room_id

        if self.room_id is not None:
            room_data = find_one(rooms_collection, self.room_id)
            if room_data is None:
                return json_response({"message": "Room doesn't exist"}, 400)
            room_data = Room(**room_data)
            if not room_data.available(collection, self.start_time, self.end_time, str(self._id)):
                return json_response({"message": "Room is not available for the specified time"}, 400)
        else:
            selected_room = None
            data = rooms_collection.find({})
            for x in data:
                x = Room(**x)
                if x.available(collection, self.start_time, self.end_time):
                    selected_room = x
                    break

            if selected_room is None:
                return json_response({"message": "There is no free room for the specified time"}, 400)
            self.room_id = str(selected_room.get_id())

        return object_save(collection, self.to_dict())

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}


class LoginData:

    def __init__(self, **kwargs):
        self.login = kwargs.get('login')
        self.password = kwargs.get('password')

    def validate(self):
        if self.login is None or self.password is None:
            return False
        return True

    def login_response(self, users_collection):
        user = find_one(users_collection, self.login, 'login')
        if user is None:
            return json_response({"message": "User do not exist"}, 404)
        user = User(**user)

        return user.authenticate(self.password)

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}


def list_meetings(collection, filters, args):
    if 'show_old' not in args:
        filters['start_time'] = {"$gt": rfc3339.rfc3339(datetime.datetime.now())}
    else:
        args.pop('show_old')
    filters['_temp'] = {"$exists": False}

    return list_all(collection, filters, args)


def meetings_change(collection, meeting_id_1, meeting_id_2):
    meeting_1 = find_one(collection, meeting_id_1)
    meeting_2 = find_one(collection, meeting_id_2)
    if meeting_1 is None or meeting_2 is None:
        return json_response({"message": "Meeting does not exist"}, 404)

    meeting_1 = Meeting(**meeting_1)
    meeting_2 = Meeting(**meeting_2)

    pass
