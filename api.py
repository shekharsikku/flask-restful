from flask import Flask, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
from nanoid import generate
import json


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sqlite.db"

db = SQLAlchemy(app)
api = Api(app)


# def api_response(message: str, code: int, data: any = None):
#     success = True if code < 400 else False
#     if data is not None:
#         return make_response(jsonify({"message": message, "success": success, "data": data}), code)
#     return make_response(jsonify({"message": message, "success": success}), code)


def api_response(message, code, data=None):
    response = {
        'code': code,
        'message': message,
        'data': data
    }
    return jsonify(response)


class UserModel(db.Model):
    id = db.Column(db.String(21), primary_key=True, default=lambda: generate(size=21))
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f"User(name = {self.name}, email = {self.email});"
    

user_args = reqparse.RequestParser()
user_args.add_argument("name", type=str, required=True, help="Name is required!")
user_args.add_argument("email", type=str, required=True, help="Email is required!")
user_args.add_argument("password", type=str, required=True, help="Password is required!")


user_fields = {
    "id": fields.String,
    "name": fields.String,
    "email": fields.String,
    "password": fields.String,
}


class Users(Resource):
    @marshal_with(user_fields)
    def get(self):
        all_users = UserModel.query.all()

        if len(all_users) <= 0:
            abort(404, message="No any user available!")

        return api_response("Users fetched!", 200, all_users)
    

    @marshal_with(user_fields)
    def post(self):
        args = user_args.parse_args()

        existed_email = UserModel.query.filter_by(email=args["email"]).first()

        if existed_email:
            abort(409, message="Email already exists!")

        new_user = UserModel(name=args["name"], email=args["email"], password=args["password"])
        db.session.add(new_user)
        db.session.commit()
        # users = UserModel.query.all()
        return new_user, 201
    

class User(Resource):
    @marshal_with(user_fields)
    def get(self, id):
        user = UserModel.query.filter_by(id=id).first()
        if not user:
            abort(404, message="User not found!")
        return user
    
    @marshal_with(user_fields)
    def patch(self, id):
        args = user_args.parse_args()
        user = UserModel.query.filter_by(id=id).first() 
        if not user: 
            abort(404, message="User not found!")
        user.name = args["name"]
        user.email = args["email"]
        user.password = args["password"]
        db.session.commit()
        return user 
    
    @marshal_with(user_fields)
    def delete(self, id):
        user = UserModel.query.filter_by(id=id).first() 
        if not user: 
            abort(404, message="User not found!")
        db.session.delete(user)
        db.session.commit()
        # users = UserModel.query.all()
        return user, 301


api.add_resource(Users, "/api/users/")
api.add_resource(User, "/api/users/<id>")


@app.route("/")
def home():
    return "<h1>Flask REST API</h1>"


# Basic Error/Exception Handling!

@app.errorhandler(Exception)
@app.errorhandler(SQLAlchemyError)
def handle_generic_exception(error):
    return api_response(f"Error: {error}!", 400)


@app.errorhandler(HTTPException)
def handle_http_exception(error):
    return api_response(f"{error.description}", error.code)


if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=8070)
