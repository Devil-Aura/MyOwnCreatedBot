from pymongo import MongoClient
from config import cfg

# Initialize MongoDB Client
client = MongoClient(cfg.MONGO_URI)

# Define Collections
users = client['main']['users']
groups = client['main']['groups']
welcome_messages = client['main']['welcome_messages']
user_logs = client['main']['user_logs']
user_channels = client['main']['user_channels']

# User Functions
def already_db(user_id):
    return bool(users.find_one({"user_id": str(user_id)}))

def add_user(user_id, username=None):
    if not already_db(user_id):
        users.insert_one({
            "user_id": str(user_id),
            "username": username,
            "banned": False,
            "deactivated": False,
            "broadcast_disabled": False
        })

def remove_user(user_id):
    users.delete_one({"user_id": str(user_id)})

def ban_user(user_id):
    users.update_one({"user_id": str(user_id)}, {"$set": {"banned": True}}, upsert=True)

def unban_user(user_id):
    users.update_one({"user_id": str(user_id)}, {"$set": {"banned": False}}, upsert=True)

def is_banned(user_id):
    user = users.find_one({"user_id": str(user_id)})
    return user.get("banned", False) if user else False

def disable_broadcast_for_user(user_id):
    users.update_one({"user_id": str(user_id)}, {"$set": {"broadcast_disabled": True}}, upsert=True)

def enable_broadcast(user_id):
    users.update_one({"user_id": str(user_id)}, {"$set": {"broadcast_disabled": False}}, upsert=True)

def is_broadcast_disabled(user_id):
    user = users.find_one({"user_id": str(user_id)})
    return user.get("broadcast_disabled", False) if user else False

def log_user_data(user_id, username, log_channel):
    user_logs.insert_one({
        "user_id": str(user_id),
        "username": username,
        "log_channel": str(log_channel)
    })

def all_users():
    return list(users.find({"banned": False, "deactivated": False}))

def count_banned_users():
    return users.count_documents({"banned": True})

def count_deactivated_users():
    return users.count_documents({"deactivated": True})

# Group Functions
def already_dbg(chat_id):
    return bool(groups.find_one({"chat_id": str(chat_id)}))

def add_group(chat_id):
    if not already_dbg(chat_id):
        groups.insert_one({"chat_id": str(chat_id)})

def all_groups():
    return list(groups.find())

# Welcome Message Functions
def set_welcome_message(chat_id, message):
    """
    Sets a custom welcome message for a chat.
    """
    welcome_messages.update_one(
        {"chat_id": str(chat_id)},
        {"$set": {"welcome_message": message}},
        upsert=True
    )

def get_welcome_message(chat_id):
    """
    Gets the custom welcome message for a chat. Returns a default message if not set.
    """
    message_data = welcome_messages.find_one({"chat_id": str(chat_id)})
    return message_data.get("welcome_message", "Welcome!") if message_data else "Welcome!"

# User-Channel Functions
def add_user_channel(user_id, chat_id, chat_name, chat_url):
    user_channels.insert_one({
        "user_id": str(user_id),
        "chat_id": str(chat_id),
        "chat_name": chat_name,
        "chat_url": chat_url
    })

def get_user_channels(user_id):
    return list(user_channels.find({"user_id": str(user_id)}))

def get_all_user_channels():
    return list(user_channels.find())
