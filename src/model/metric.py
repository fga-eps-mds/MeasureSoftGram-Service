from flask import Flask, request, jsonify
import json
import mongoengine as me


class Metrics(me.Document):

    comment_lines_density = me.FloatField()
    complexity = me.FloatField()
    coverage = me.FloatField()
    duplicated_lines_density = me.FloatField()
    files = me.FloatField()
    functions = me.FloatField()
    ncloc = me.FloatField()
    security_rating = me.FloatField()
    test_errors = me.FloatField()
    test_execution_time = me.FloatField()
    test_failures = me.FloatField()
    tests = me.FloatField()

    def to_json(self):
        return {"comment_lines_density": self.comment_lines_density,
                "complexity": self.complexity,
                "coverage": self.coverage,
                "duplicated_lines_density": self.duplicated_lines_density,
                "files": self.files,
                "functions": self.functions,
                "ncloc": self.ncloc,
                "security_rating": self.security_rating,
                "test_errors": self.test_errors,
                "test_execution_time": self.test_execution_time,
                "test_failures": self.test_failures,
                "tests": self.tests
                }
