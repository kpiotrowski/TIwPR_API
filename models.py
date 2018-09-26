import bcrypt

from db import get_token, create_new_token, find_one, object_save
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
        self._id = kwargs.get('id')
        self.login = kwargs.get('login')
        self.password_hash = kwargs.get('password_hash')
        self.name = kwargs.get('name')

        if 'password' in kwargs:
            self.password_hash = bcrypt.hashpw(kwargs.get('password'), bcrypt.gensalt())

    def password_match(self, password):
        return bcrypt.hashpw(password, self.password_hash) == self.password_hash

    def validate(self):
        for field in [self.login, self.password_hash, self.name]:
            if field is None:
                return False
        return True

    def authenticate(self, password):
        if not bcrypt.checkpw(password, self.password_hash):
            return json_response({"message": "Invalid login or password"}, 403)

        token = get_token(self.login)
        if token is None:
            token = create_new_token(self.login)

        return json_response({"token": token}, 200)

    def create(self, collection):
        if find_one(collection, self.login, 'login') is not None:
            return json_response({"message": "User already exists"}, 409)

        return object_save(collection, self.__dict__)

    def update(self, collection, old_id):
        user = find_one(collection, old_id)
        if user is None:
            return json_response({"message": "User doesn't exist"}, 404)

        user = User(**user)
        if self.login != user.login:
            return json_response({"message": "You cannot change user login"}, 400)

        return object_save(collection, self.__dict__)


class Room:

    def __init__(self, **kwargs):
        self._id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.place = kwargs.get('place')

    def validate(self):
        for field in [self.name, self.place]:
            if field is None:
                return False
        return True

    def create(self, collection):
        return object_save(collection, self.__dict__)

    def update(self, collection, old_id):
        if find_one(collection, old_id) is None:
            return json_response({"message": "Room doesn't exist"}, 404)

        return object_save(collection, self.__dict__)


class Meeting:

    def __init__(self, **kwargs):
        self._id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.start_time = kwargs.get('start_time')
        self.end_time = kwargs.get('end_time')
        self.room_id = kwargs.get('room_id')
        self.user_id = kwargs.get('user_id')

    def validate(self):
        for field in [self.name, self.start_time, self.end_time, self.room_id, self.user_id]:
            if field is None:
                return False
        return True

    def create(self, collection):
        pass

    def update(self, collection):
        pass


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
