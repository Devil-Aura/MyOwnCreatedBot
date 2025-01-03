from pymongo import MongoClient
from config import cfg

# Establish a connection to the MongoDB database
client = MongoClient(cfg.MONGO_URI)

# Define collections for users and groups
db = client['my_bot_database']  # Use a specific database name
users_collection = db['users']
groups_collection = db['groups']

# Check if a user already exists in the database
def user_exists(user_id):
    return users_collection.find_one({"user_id": str(user_id)}) is not None

# Check if a group already exists in the database
def group_exists(chat_id):
    return groups_collection.find_one({"chat_id": str(chat_id)}) is not None

# Add a user to the database
def add_user(user_id):
    if not user_exists(user_id):
        users_collection.insert_one({"user_id": str(user_id)})
        print(f"User {user_id} added to the database.")

# Remove a user from the database
def remove_user(user_id):
    if user_exists(user_id):
        users_collection.delete_one({"user_id": str(user_id)})
        print(f"User {user_id} removed from the database.")

# Add a group to the database
def add_group(chat_id):
    if not group_exists(chat_id):
        groups_collection.insert_one({"chat_id": str(chat_id)})
        print(f"Group {chat_id} added to the database.")

# Count the total number of users in the database
def count_users():
    return users_collection.count_documents({})

# Count the total number of groups in the database
def count_groups():
    return groups_collection.count_documents({})

# Retrieve all users from the database
def get_all_users():
    return [user["user_id"] for user in users_collection.find()]

# Retrieve all groups from the database
def get_all_groups():
    return [group["chat_id"] for group in groups_collection.find()]

# Example usage
if __name__ == "__main__":
    print("Total Users:", count_users())
    print("Total Groups:", count_groups())
