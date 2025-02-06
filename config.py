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
        "mongodb+srv://iamrealdevil098:M7UXF0EL3M352q0H@cluster0.257nd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    )
    FLASK_PORT = int(getenv("FLASK_PORT", "9068"))
    # Default Welcome Message
    DEFAULT_WELCOME_MSG = "🎉 Welcome, {user_mention}!\nYour request to join {chat_title} has been approved! 🚀In 0.5 Seconds, This Is World Fastest Request Approval Bot.\n/start (For Use Me)"

cfg = Config()
