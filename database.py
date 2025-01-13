from pymongo import MongoClient
from config import cfg

client = MongoClient(cfg.MONGO_URI)

# Define collections
users = client['main']['users']
groups = client['main']['groups']
welcome_messages = client['main']['welcome_messages']

# Check if a user exists in the database
def already_db(user_id):
    user = users.find_one({"user_id": str(user_id)})
    return bool(user)

# Check if a group exists in the database
def already_dbg(chat_id):
    group = groups.find_one({"chat_id": str(chat_id)})
    return bool(group)

# Add a user to the database
def add_user(user_id):
    if not already_db(user_id):
        users.insert_one({"user_id": str(user_id), "banned": False, "deactivated": False, "broadcast_disabled": False})

# Remove a user from the database
def remove_user(user_id):
    if already_db(user_id):
        users.delete_one({"user_id": str(user_id)})

# Add a group to the database
def add_group(chat_id):
    if not already_dbg(chat_id):
        groups.insert_one({"chat_id": str(chat_id)})

# Get the total count of users
def all_users():
    return users.count_documents({"banned": False, "deactivated": False})

# Get the total count of groups
def all_groups():
    return groups.count_documents({})

# Mark a user as banned
def ban_user(user_id):
    if already_db(user_id):
        users.update_one({"user_id": str(user_id)}, {"$set": {"banned": True}})

# Unban a user
def unban_user(user_id):
    if already_db(user_id):
        users.update_one({"user_id": str(user_id)}, {"$set": {"banned": False}})

# Check if a user is banned
def is_banned(user_id):
    user = users.find_one({"user_id": str(user_id)})
    return user.get("banned", False) if user else False

# Mark a user as deactivated
def mark_deactivated(user_id):
    if already_db(user_id):
        users.update_one({"user_id": str(user_id)}, {"$set": {"deactivated": True}})

# Get the total count of deactivated users
def count_deactivated_users():
    return users.count_documents({"deactivated": True})

# Disable broadcast for a user
def disable_broadcast(user_id):
    if already_db(user_id):
        users.update_one({"user_id": str(user_id)}, {"$set": {"broadcast_disabled": True}})

# Enable broadcast for a user
def enable_broadcast(user_id):
    if already_db(user_id):
        users.update_one({"user_id": str(user_id)}, {"$set": {"broadcast_disabled": False}})

# Check if broadcast is disabled for a user
def is_broadcast_disabled(user_id):
    user = users.find_one({"user_id": str(user_id)})
    return user.get("broadcast_disabled", False) if user else False

# Set welcome message for a group
def set_welcome_message(chat_id, message):
    if already_dbg(chat_id):
        welcome_messages.update_one({"chat_id": str(chat_id)}, {"$set": {"welcome_message": message}}, upsert=True)
    else:
        welcome_messages.insert_one({"chat_id": str(chat_id), "welcome_message": message})

# Get welcome message for a group
def get_welcome_message(chat_id):
    message_data = welcome_messages.find_one({"chat_id": str(chat_id)})
    return message_data.get("welcome_message", "Welcome!") if message_data else "Welcome!"

# Get the total count of banned users
def count_banned_users():
    return users.count_documents({"banned": True})
