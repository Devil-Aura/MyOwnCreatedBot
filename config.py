from os import getenv

class Config:
    API_ID = int(getenv("API_ID", "22768311"))
    API_HASH = getenv("API_HASH", "702d8884f48b42e865425391432b3794")
    BOT_TOKEN = getenv("BOT_TOKEN", "")
    
    # Your Force Subscribe Channel ID (Make Bot Admin In This Channel)
    CHID = int(getenv("CHID", "-1002432405855"))  

    
    # Admin Or Owner IDs (Multiple Admins Can Be Added)
    SUDO = list(map(int, getenv("SUDO", "6040503076").split()))

    # MongoDB Database URI
    MONGO_URI = getenv(
        "MONGO_URI",
        "mongodb+srv://yoyoyoyo2:yoyoyoyo2@cluster0.aq4zsrb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    )
    FLASK_PORT = int(getenv("FLASK_PORT", "9068"))
    # Default Welcome Message
    DEFAULT_WELCOME_MSG = "🎉 Welcome, {user_mention}!\nYour request to join {chat_title} has been approved! 🚀In 0.5 Seconds, This Is World Fastest Request Approval Bot.\n/start (For Use Me)"
    
    WELCOME_TEXT = (
    "<b>🤗 Hello {user_mention}!</b>\n\n"
    "🚀 I am the <b>FASTEST BOT</b>, faster than light ⚡!<br>"
    "I approve join requests in just <b>0.5 seconds</b>.<br><br>"
    "<blockquote>"
    "I'm an auto-approve <a href='https://t.me/telegram/153'>Admin Join Requests</a> Bot.<br>"
    "I can approve users in Groups/Channels.<br>"
    "Add me to your chat and promote me to admin with 'Add Members' permission."
    "</blockquote><br><br>"
    "<b>Powered By :</b> <a href='https://t.me/World_Fastest_Bots'>@World_Fastest_Bots</a>"
)


cfg = Config()
