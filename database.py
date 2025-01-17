from pymongo import MongoClient
from config import cfg

client = MongoClient(cfg.MONGO_URI)
db = client["bot_database"]

# Collections
users = db["users"]
user_channels = db["user_channels"]

# Functions
def add_user(user_id, username=None):
    if not users.find_one({"user_id": str(user_id)}):
        users.insert_one({"user_id": str(user_id), "username": username, "banned": False})

def is_banned(user_id):
    user = users.find_one({"user_id": str(user_id)})
    return user.get("banned", False) if user else False

def ban_user(user_id):
    users.update_one({"user_id": str(user_id)}, {"$set": {"banned": True}})

def unban_user(user_id):
    users.update_one({"user_id": str(user_id)}, {"$set": {"banned": False}})

def all_banned_users():
    return list(users.find({"banned": True}))

def disable_broadcast_for_user(user_id):
    users.update_one({"user_id": str(user_id)}, {"$set": {"broadcast_disabled": True}})

def enable_broadcast(user_id):
    users.update_one({"user_id": str(user_id)}, {"$set": {"broadcast_disabled": False}})

def is_broadcast_disabled(user_id):
    user = users.find_one({"user_id": str(user_id)})
    return user.get("broadcast_disabled", False) if user else False

def all_users():
    return list(users.find())

def log_user_data(user_id, username, log_channel):
    pass  # Add your logging logic here

def get_user_channels(user_id):
    return list(user_channels.find({"user_id": str(user_id)}))
