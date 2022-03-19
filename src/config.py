import os

MONGO_SETTINGS = {
    "host": "mongo",
    "port": 27017,
    "db": os.getenv("DB_NAME", "measuresoftgram"),
    "username": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "example"),
}
