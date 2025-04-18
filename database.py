import sqlite3
from pymongo import MongoClient
from os import getenv
from datetime import datetime

# Database Configuration
MONGO_URI = getenv("MONGO_URI", "mongodb+srv://yoyoyoyo2:yoyoyoyo2@cluster0.aq4zsrb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = "bot_database.db"

# Connect to databases
client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
mongo_db = client["Cluster0"]

# Collections
users_collection = mongo_db["users"]
groups_collection = mongo_db["groups"]  # Changed from channels_collection for consistency
disabled_broadcast_collection = mongo_db["disabled_broadcast"]
banned_users_collection = mongo_db["banned_users"]
welcome_messages_collection = mongo_db["welcome_messages"]

# Initialize SQLite
def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    tables = [
        """CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )""",
        """CREATE TABLE IF NOT EXISTS groups (
            chat_id INTEGER PRIMARY KEY
        )""",
        """CREATE TABLE IF NOT EXISTS disabled_broadcast (
            user_id INTEGER PRIMARY KEY
        )""",
        """CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY
        )""",
        """CREATE TABLE IF NOT EXISTS welcome_messages (
            chat_id INTEGER PRIMARY KEY,
            message TEXT
        )"""
    ]

    for table in tables:
        cursor.execute(table)
    conn.commit()
    conn.close()

#━━━━━━━━━━━━━━━━━━━━━━━ User Management ━━━━━━━━━━━━━━━━━━━━━━━

def add_user(user_id):
    # SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    # MongoDB
    users_collection.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {"user_id": user_id, "created_at": datetime.now()}},
        upsert=True
    )

def remove_user(user_id):
    # SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    # MongoDB
    users_collection.delete_one({"user_id": user_id})

def all_users():
    # Using MongoDB count for better performance
    return users_collection.count_documents({})

#━━━━━━━━━━━━━━━━━━━━━━━ Group/Channel Management ━━━━━━━━━━━━━━━━━━━━━━━

def add_group(chat_id, user_id, chat_title, chat_url, chat_type, username=None):
    # SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO groups (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

    # MongoDB
    groups_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {
            "user_id": user_id,
            "username": username or f"User-{user_id}",
            "chat_title": chat_title,
            "chat_url": chat_url,
            "type": chat_type,
            "last_updated": datetime.now()
        }},
        upsert=True
    )

def all_groups():
    return groups_collection.count_documents({})

#━━━━━━━━━━━━━━━━━━━━━━━ Broadcast Control ━━━━━━━━━━━━━━━━━━━━━━━

def disable_broadcast(user_id):
    # SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO disabled_broadcast (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    # MongoDB
    disabled_broadcast_collection.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {"user_id": user_id}},
        upsert=True
    )

def enable_broadcast(user_id):
    # SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM disabled_broadcast WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    # MongoDB
    disabled_broadcast_collection.delete_one({"user_id": user_id})

def is_broadcast_disabled(user_id):
    # Using MongoDB for faster lookup
    return disabled_broadcast_collection.find_one({"user_id": user_id}) is not None

def get_disabled_broadcast_users():
    return [user["user_id"] for user in disabled_broadcast_collection.find({}, {"user_id": 1})]

#━━━━━━━━━━━━━━━━━━━━━━━ Ban Management ━━━━━━━━━━━━━━━━━━━━━━━

def ban_user(user_id):
    # SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    # MongoDB
    banned_users_collection.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {"user_id": user_id, "banned_at": datetime.now()}},
        upsert=True
    )

def unban_user(user_id):
    # SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    # MongoDB
    banned_users_collection.delete_one({"user_id": user_id})

def is_user_banned(user_id):
    return banned_users_collection.find_one({"user_id": user_id}) is not None

def get_banned_users():
    return [user["user_id"] for user in banned_users_collection.find({}, {"user_id": 1})]

#━━━━━━━━━━━━━━━━━━━━━━━ Welcome Message Management ━━━━━━━━━━━━━━━━━━━━━━━

def set_welcome_message(chat_id, message):
    # SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO welcome_messages (chat_id, message) VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET message = ?
    """, (chat_id, message, message))
    conn.commit()
    conn.close()

    # MongoDB
    welcome_messages_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"message": message, "updated_at": datetime.now()}},
        upsert=True
    )

def get_welcome_message(chat_id):
    # Using MongoDB for faster access
    result = welcome_messages_collection.find_one({"chat_id": chat_id})
    return result["message"] if result else None

# Initialize the database
create_tables()
