from pymongo import MongoClient
from config import cfg

client = MongoClient(cfg.MONGO_URI)

# Define collections
users = client['main']['users']
groups = client['main']['groups']

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
        users.insert_one({"user_id": str(user_id)})

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
    return users.count_documents({})

# Get the total count of groups
def all_groups():
    return groups.count_documents({})
