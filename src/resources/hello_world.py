from flask import jsonify, request
from flask_restful import Resource
from datetime import datetime


class HelloWorld(Resource):
    def get(self):
        return jsonify({"Hello": "World!"})


class HelloWorld2(Resource):
    def get(self):
        now = datetime.now()
        return now.strftime("%m/%d/%Y, %H:%M:%S")

    def post(self):
        a = request.get_json()
        print(a)
        return jsonify({"Status": "OK"})
