from flask import request
from flask_restful import Resource
from src.model.pre_config import PreConfig
import requests
import mongoengine as me


class PreConfigs(Resource):
    def post(self):
        data = request.get_json(force=True)

        try:
            pre_config = PreConfig(**data).save()
        except me.errors.NotUniqueError:
            return {
                "error": "The pre config name is already in use"
            }, requests.codes.unprocessable_entity

        return pre_config.to_json(), requests.codes.created

    def get(self):
        pre_config = []

        for db_pre_config in PreConfig.objects():
            pre_config.append(db_pre_config.to_lean_json())
        return pre_config

    def get(self):
        pre_config_goal = []

        for db_pre_config_goal in PreConfig.objects():
            pre_config_goal.append(db_pre_config_goal.to_goal_json())
        return pre_config_goal


class PreConfigsWithID(Resource):
    def get(self, pre_config_id):
        try:
            pre_config = PreConfig.objects.with_id(pre_config_id)
            if pre_config is None:
                return{
                    "Error": f"There is no pre configurations with ID {pre_config_id}"
                }, requests.codes.not_found

            return pre_config.to_json()
        except me.errors.ValidationError:
            return {
                "Error": f"{pre_config_id} is not a valid ID"
            }, requests.codes.not_found


class PreConfigsGoals(Resource):
    def get(self, pre_config2):
        try:
            pre_config_goal = PreConfig.objects.goals(pre_config2)
            if pre_config_goal is None:
                return{
                    "Error": f"There is no goals for that pre-config{pre_config2}"
                }, requests.codes.not_found

            return pre_config_goal.to_json()
        except me.errors.ValidationError:
            return{
                "Error": f"{pre_config2} is not a valid goal"
            }, requests.codes.not_found
