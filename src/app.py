from flask import Flask
from flask_restful import Api
from src.resources.hello_world import HelloWorld, HelloWorld2
from src.resources.available import AvailablePreConfigs


app = Flask(__name__)
api = Api(app)

api.add_resource(HelloWorld, "/hello")

api.add_resource(HelloWorld2, "/hello-world")

api.add_resource(AvailablePreConfigs, "/available-pre-configs")
