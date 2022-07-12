import os

MONGO_SETTINGS = {
    "host": os.getenv("DB_HOST", "measuresoftgram-db"),
    "port": int(os.getenv("DB_PORT", "27017")),
    "db": os.getenv("DB_NAME", "measuresoftgram"),
    "username": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "example"),
}
