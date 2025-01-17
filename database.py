from pymongo import MongoClient
from config import cfg

# Initialize MongoDB Client
client = MongoClient(cfg.MONGO_URI)

# Define Collections
users = client['main']['users']
welcome_messages = client['main']['welcome_messages']
user_logs = client['main']['user_logs']


# User Functions
def already_db(user_id):
    return bool(users.find_one({"user_id": str(user_id)}))


def add_user(user_id, username=None):
    if not already_db(user_id):
        users.insert_one({
            "user_id": str(user_id),
            "username": username,
            "banned": False,
        })


def is_banned(user_id):
    user = users.find_one({"user_id": str(user_id)})
    return user.get("banned", False) if user else False


def log_user_data(user_id, username, log_channel):
    user_logs.insert_one({
        "user_id": str(user_id),
        "username": username,
        "log_channel": str(log_channel)
    })


def all_users():
    return list(users.find({"banned": False}))


# Welcome Message Functions
def set_welcome_message(chat_id, message):
    welcome_messages.update_one({"chat_id": str(chat_id)}, {"$set": {"welcome_message": message}}, upsert=True)


def get_welcome_message(chat_id):
    message_data = welcome_messages.find_one({"chat_id": str(chat_id)})
    return message_data.get("welcome_message", "Welcome!") if message_data else "Welcome!"
