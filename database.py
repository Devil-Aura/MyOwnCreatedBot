import sqlite3
from pymongo import MongoClient
from os import getenv
from datetime import datetime, timedelta

# Load MongoDB URI from environment variables
MONGO_URI = getenv("MONGO_URI", "mongodb+srv://ajedvwess_db_user:pU3egnmZuEuHvWsd@cluster0.bflbyzu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Connect to MongoDB with SSL disabled
try:
    client = MongoClient(
        MONGO_URI, 
        ssl=False,  # Disable SSL
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        serverSelectionTimeoutMS=30000
    )
    # Test connection
    client.admin.command('ismaster')
    print("✅ MongoDB connected successfully!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    client = None

if client:
    db = client["Cluster0"]
else:
    db = None

# Collections
if db:
    users_collection = db["users"]
    channels_collection = db["channels"]
    temporary_broadcasts_collection = db["temporary_broadcasts"]
    user_messages_collection = db["user_messages"]
else:
    # Fallback to empty collections if MongoDB fails
    users_collection = None
    channels_collection = None
    temporary_broadcasts_collection = None
    user_messages_collection = None

# Define DB Name for SQLite
DB_NAME = "bot_database.db"

# Create Tables
def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)

    # Groups/Channels Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            chat_id INTEGER PRIMARY KEY
        )
    """)

    # Disabled Broadcast Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disabled_broadcast (
            user_id INTEGER PRIMARY KEY
        )
    """)

    # Banned Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY
        )
    """)

    # Welcome Messages Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS welcome_messages (
            chat_id INTEGER PRIMARY KEY,
            message TEXT
        )
    """)

    conn.commit()
    conn.close()

#━━━━━━━━━━━━━━━━━━━━━━━ User Management ━━━━━━━━━━━━━━━━━━━━━━━

def add_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    # Add to MongoDB if available
    if users_collection:
        try:
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"user_id": user_id, "joined_at": datetime.now()}},
                upsert=True
            )
        except Exception as e:
            print(f"MongoDB error in add_user: {e}")

def remove_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def all_users():
    # Try MongoDB first, fallback to SQLite
    if users_collection:
        try:
            return users_collection.count_documents({})
        except:
            pass
    
    # Fallback to SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_users():
    """Get all user IDs from both databases"""
    users = []
    
    # Try MongoDB first
    if users_collection:
        try:
            users = list(set([user["user_id"] for user in users_collection.find({})]))
        except:
            pass
    
    # If MongoDB fails or empty, use SQLite
    if not users:
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            users = [row[0] for row in cursor.fetchall()]
            conn.close()
        except:
            pass
    
    return users

#━━━━━━━━━━━━━━━━━━━━━━━ Group/Channel Management ━━━━━━━━━━━━━━━━━━━━━━━

def add_group(chat_id, user_id, chat_title, chat_url, chat_type, username=None, user_url=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO groups (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

    # Add to MongoDB if available
    if channels_collection:
        try:
            channels_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {
                    "user_id": user_id,
                    "username": username or f"User-{user_id}",
                    "user_url": user_url or f"https://t.me/{username}",
                    "chat_id": chat_id,
                    "chat_title": chat_title,
                    "chat_url": chat_url,
                    "type": chat_type,
                    "added_at": datetime.now()
                }},
                upsert=True
            )
        except Exception as e:
            print(f"MongoDB error in add_group: {e}")

def all_groups():
    # Try MongoDB first, fallback to SQLite
    if channels_collection:
        try:
            return channels_collection.count_documents({})
        except:
            pass
    
    # Fallback to SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM groups")
    count = cursor.fetchone()[0]
    conn.close()
    return count

#━━━━━━━━━━━━━━━━━━━━━━━ Persistent Temporary Broadcast Management ━━━━━━━━━━━━━━━━━━━━━━━

def add_persistent_broadcast(user_id, message_id, delete_time, original_broadcast_time):
    """Store broadcast with original time to survive bot restarts"""
    if temporary_broadcasts_collection:
        try:
            temporary_broadcasts_collection.update_one(
                {"user_id": user_id, "message_id": message_id},
                {"$set": {
                    "user_id": user_id,
                    "message_id": message_id,
                    "delete_time": delete_time,
                    "original_broadcast_time": original_broadcast_time,
                    "created_at": datetime.now()
                }},
                upsert=True
            )
        except Exception as e:
            print(f"MongoDB error in add_persistent_broadcast: {e}")

def get_all_pending_broadcasts():
    """Get all broadcasts that haven't been deleted yet"""
    if not temporary_broadcasts_collection:
        return []
    
    try:
        now = datetime.now()
        return list(temporary_broadcasts_collection.find({"delete_time": {"$gt": now}}))
    except Exception as e:
        print(f"MongoDB error in get_all_pending_broadcasts: {e}")
        return []

def get_expired_broadcasts():
    """Get broadcasts that are ready for deletion"""
    if not temporary_broadcasts_collection:
        return []
    
    try:
        now = datetime.now()
        return list(temporary_broadcasts_collection.find({"delete_time": {"$lte": now}}))
    except Exception as e:
        print(f"MongoDB error in get_expired_broadcasts: {e}")
        return []

def remove_temporary_broadcast(message_id, user_id=None):
    """Remove broadcast record after deletion - CLEANS DATABASE LOGS"""
    if temporary_broadcasts_collection:
        try:
            if user_id:
                temporary_broadcasts_collection.delete_one({"message_id": message_id, "user_id": user_id})
            else:
                temporary_broadcasts_collection.delete_one({"message_id": message_id})
            print(f"🗑️ Database record cleaned for message: {message_id}")
        except Exception as e:
            print(f"MongoDB error in remove_temporary_broadcast: {e}")

#━━━━━━━━━━━━━━━━━━━━━━━ User Message Management ━━━━━━━━━━━━━━━━━━━━━━━

def store_user_message(user_id, message_id, log_message_id):
    if user_messages_collection:
        try:
            user_messages_collection.insert_one({
                "user_id": user_id,
                "user_message_id": message_id,
                "log_message_id": log_message_id,
                "timestamp": datetime.now()
            })
        except Exception as e:
            print(f"MongoDB error in store_user_message: {e}")

def get_user_message_info(log_message_id):
    if not user_messages_collection:
        return None
    
    try:
        return user_messages_collection.find_one({"log_message_id": log_message_id})
    except Exception as e:
        print(f"MongoDB error in get_user_message_info: {e}")
        return None

#━━━━━━━━━━━━━━━━━━━━━━━ Broadcast Control ━━━━━━━━━━━━━━━━━━━━━━━

def disable_broadcast(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO disabled_broadcast (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def enable_broadcast(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM disabled_broadcast WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_broadcast_disabled(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM disabled_broadcast WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_disabled_broadcast_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM disabled_broadcast")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

#━━━━━━━━━━━━━━━━━━━━━━━ Ban Management ━━━━━━━━━━━━━━━━━━━━━━━

def ban_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_user_banned(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM banned_users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_banned_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM banned_users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

#━━━━━━━━━━━━━━━━━━━━━━━ Welcome Message Management ━━━━━━━━━━━━━━━━━━━━━━━

def set_welcome_message(chat_id, message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO welcome_messages (chat_id, message) VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET message = ?
    """, (chat_id, message, message))
    conn.commit()
    conn.close()

def get_welcome_message(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT message FROM welcome_messages WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

#━━━━━━━━━━━━━━━━━━━━━━━ User-Channel Tracking ━━━━━━━━━━━━━━━━━━━━━━━

def get_user_channels():
    if not channels_collection:
        return {}
    
    try:
        user_channels = channels_collection.find({})
        channels = {}

        for channel in user_channels:
            user_id = channel["user_id"]
            chat_title = channel["chat_title"]
            chat_url = channel["chat_url"]
            chat_type = channel.get("type", "unknown")
            username = channel.get("username", f"User-{user_id}")
            user_url = channel.get("user_url", f"https://t.me/{username}")

            if user_id not in channels:
                channels[user_id] = {
                    "username": username,
                    "user_url": user_url,
                    "user_id": user_id,
                    "username_tag": f"@{username}" if username else f"User-{user_id}",
                    "channels": [],
                    "groups": []
                }

            if chat_type == "channel":
                channels[user_id]["channels"].append({
                    "chat_title": chat_title,
                    "chat_url": chat_url
                })
            elif chat_type == "group":
                channels[user_id]["groups"].append({
                    "chat_title": chat_title,
                    "chat_url": chat_url
                })

        return channels
    except Exception as e:
        print(f"MongoDB error in get_user_channels: {e}")
        return {}

#━━━━━━━━━━━━━━━━━━━━━━━ Initialize Database ━━━━━━━━━━━━━━━━━━━━━━━

create_tables()
print("✅ Database initialized successfully!")
