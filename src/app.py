from flask import Flask
from flask_restful import Api
from src.resources.hello_world import HelloWorld, HelloWorld2
from src.resources.available import AvailablePreConfigs
from flask_mongoengine import MongoEngine
from .config import MONGO_SETTINGS

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = MONGO_SETTINGS
api = Api(app)
db = MongoEngine(app)

api.add_resource(HelloWorld, "/hello")

api.add_resource(HelloWorld2, "/hello-world")

api.add_resource(AvailablePreConfigs, "/available-pre-configs")
