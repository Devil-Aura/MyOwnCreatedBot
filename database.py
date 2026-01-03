from pymongo import MongoClient
from os import getenv
from datetime import datetime, timedelta

# Load MongoDB URI from environment variables
MONGO_URI = getenv("MONGO_URI", "mongodb+srv://request:Requestbot0123@cluster0.zncwjjj.mongodb.net/?appName=Cluster0")

class MongoDB:
    def __init__(self, uri):
        try:
            self.client = MongoClient(
                uri, 
                tls=True,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                serverSelectionTimeoutMS=30000
            )
            self.client.admin.command('ping')
            self.db = self.client.get_database("Cluster0")
            print("✅ MongoDB connected successfully!")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            self.client = None
            self.db = None

        if self.db is not None:
            self.users = self.db["users"]
            self.channels = self.db["channels"]
            self.temp_broadcasts = self.db["temporary_broadcasts"]
            self.user_messages = self.db["user_messages"]
            self.welcome_limit = self.db["welcome_limit"]
            self.banned_users = self.db["banned_users"]
            self.welcome_messages = self.db["welcome_messages"]
        else:
            self.users = None
            self.channels = None
            self.temp_broadcasts = None
            self.user_messages = None
            self.welcome_limit = None
            self.banned_users = None
            self.welcome_messages = None

mongo = MongoDB(MONGO_URI)
users_collection = mongo.users
channels_collection = mongo.channels

#━━━━━━━━━━━━━━━━━━━━━━━ User Management ━━━━━━━━━━━━━━━━━━━━━━━

def add_user(user_id):
    if mongo.users is not None:
        try:
            mongo.users.update_one(
                {"user_id": user_id},
                {"$set": {"user_id": user_id, "joined_at": datetime.now()}},
                upsert=True
            )
        except Exception as e:
            print(f"MongoDB error in add_user: {e}")

def remove_user(user_id):
    if mongo.users is not None:
        try:
            mongo.users.delete_one({"user_id": user_id})
        except Exception as e:
            print(f"MongoDB error in remove_user: {e}")

def all_users():
    if mongo.users is not None:
        try:
            return mongo.users.count_documents({})
        except:
            return 0
    return 0

def get_all_users():
    if mongo.users is not None:
        try:
            return [user["user_id"] for user in mongo.users.find({})]
        except:
            return []
    return []

#━━━━━━━━━━━━━━━━━━━━━━━ Group/Channel Management ━━━━━━━━━━━━━━━━━━━━━━━

def add_group(chat_id, user_id, chat_title, chat_url, chat_type, username=None, user_url=None):
    if mongo.channels is not None:
        try:
            mongo.channels.update_one(
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
    if mongo.channels is not None:
        try:
            return mongo.channels.count_documents({})
        except:
            return 0
    return 0

#━━━━━━━━━━━━━━━━━━━━━━━ Persistent Temporary Broadcast Management ━━━━━━━━━━━━━━━━━━━━━━━

def add_persistent_broadcast(user_id, message_id, delete_time, original_broadcast_time):
    if mongo.temp_broadcasts is not None:
        try:
            mongo.temp_broadcasts.update_one(
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
    if mongo.temp_broadcasts is None:
        return []
    try:
        now = datetime.now()
        return list(mongo.temp_broadcasts.find({"delete_time": {"$gt": now}}))
    except Exception as e:
        print(f"MongoDB error in get_all_pending_broadcasts: {e}")
        return []

def get_expired_broadcasts():
    if mongo.temp_broadcasts is None:
        return []
    try:
        now = datetime.now()
        return list(mongo.temp_broadcasts.find({"delete_time": {"$lte": now}}))
    except Exception as e:
        print(f"MongoDB error in get_expired_broadcasts: {e}")
        return []

def remove_temporary_broadcast(message_id, user_id=None):
    if mongo.temp_broadcasts is not None:
        try:
            if user_id:
                mongo.temp_broadcasts.delete_one({"message_id": message_id, "user_id": user_id})
            else:
                mongo.temp_broadcasts.delete_one({"message_id": message_id})
        except Exception as e:
            print(f"MongoDB error in remove_temporary_broadcast: {e}")

#━━━━━━━━━━━━━━━━━━━━━━━ User Message Management ━━━━━━━━━━━━━━━━━━━━━━━

def store_user_message(user_id, message_id, log_message_id):
    if mongo.user_messages is not None:
        try:
            mongo.user_messages.insert_one({
                "user_id": user_id,
                "user_message_id": message_id,
                "log_message_id": log_message_id,
                "timestamp": datetime.now()
            })
        except Exception as e:
            print(f"MongoDB error in store_user_message: {e}")

def get_user_message_info(log_message_id):
    if mongo.user_messages is None:
        return None
    try:
        return mongo.user_messages.find_one({"log_message_id": log_message_id})
    except Exception as e:
        print(f"MongoDB error in get_user_message_info: {e}")
        return None

#━━━━━━━━━━━━━━━━━━━━━━━ Welcome Limit Management ━━━━━━━━━━━━━━━━━━━━━━━

def can_send_welcome(user_id):
    if mongo.welcome_limit is None:
        return True
    try:
        limit = mongo.welcome_limit.find_one({"user_id": user_id})
        if not limit:
            return True
        last_sent = limit["last_sent"]
        if datetime.now() - last_sent > timedelta(hours=3):
            return True
        return False
    except:
        return True

def set_welcome_sent(user_id):
    if mongo.welcome_limit is not None:
        try:
            mongo.welcome_limit.update_one(
                {"user_id": user_id},
                {"$set": {"last_sent": datetime.now()}},
                upsert=True
            )
        except:
            pass

#━━━━━━━━━━━━━━━━━━━━━━━ Broadcast Control ━━━━━━━━━━━━━━━━━━━━━━━

def disable_broadcast(user_id):
    if mongo.users is not None:
        try:
            mongo.users.update_one({"user_id": user_id}, {"$set": {"broadcast_disabled": True}}, upsert=True)
        except: pass

def enable_broadcast(user_id):
    if mongo.users is not None:
        try:
            mongo.users.update_one({"user_id": user_id}, {"$set": {"broadcast_disabled": False}}, upsert=True)
        except: pass

def is_broadcast_disabled(user_id):
    if mongo.users is not None:
        try:
            user = mongo.users.find_one({"user_id": user_id})
            if user and user.get("broadcast_disabled"):
                return True
        except: pass
    return False

def get_disabled_broadcast_users():
    if mongo.users is not None:
        try:
            return [user["user_id"] for user in mongo.users.find({"broadcast_disabled": True})]
        except:
            return []
    return []

#━━━━━━━━━━━━━━━━━━━━━━━ Ban Management ━━━━━━━━━━━━━━━━━━━━━━━

def ban_user(user_id):
    if mongo.banned_users is not None:
        try:
            mongo.banned_users.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)
        except: pass

def unban_user(user_id):
    if mongo.banned_users is not None:
        try:
            mongo.banned_users.delete_one({"user_id": user_id})
        except: pass

def is_user_banned(user_id):
    if mongo.banned_users is not None:
        try:
            return mongo.banned_users.find_one({"user_id": user_id}) is not None
        except:
            return False
    return False

def get_banned_users():
    if mongo.banned_users is not None:
        try:
            return [user["user_id"] for user in mongo.banned_users.find({})]
        except:
            return []
    return []

#━━━━━━━━━━━━━━━━━━━━━━━ Welcome Message Management ━━━━━━━━━━━━━━━━━━━━━━━

def set_welcome_message(chat_id, message):
    if mongo.welcome_messages is not None:
        try:
            mongo.welcome_messages.update_one(
                {"chat_id": chat_id},
                {"$set": {"message": message}},
                upsert=True
            )
        except: pass

def get_welcome_message(chat_id):
    if mongo.welcome_messages is not None:
        try:
            res = mongo.welcome_messages.find_one({"chat_id": chat_id})
            return res["message"] if res else None
        except:
            return None
    return None

#━━━━━━━━━━━━━━━━━━━━━━━ User-Channel Tracking ━━━━━━━━━━━━━━━━━━━━━━━

def get_user_channels():
    if not mongo.channels:
        return {}
    try:
        user_channels = mongo.channels.find({})
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
                channels[user_id]["channels"].append({"chat_title": chat_title, "chat_url": chat_url})
            elif chat_type == "group":
                channels[user_id]["groups"].append({"chat_title": chat_title, "chat_url": chat_url})
        return channels
    except Exception as e:
        print(f"MongoDB error in get_user_channels: {e}")
        return {}

#━━━━━━━━━━━━━━━━━━━━━━━ Initialize Database ━━━━━━━━━━━━━━━━━━━━━━━

print("✅ Bot is now using MongoDB 100% with improved reliability!")
