from os import getenv  

class Config:
    API_ID = int(getenv("API_ID", "22768311"))
    API_HASH = getenv("API_HASH", "702d8884f48b42e865425391432b3794")
    BOT_TOKEN = getenv("BOT_TOKEN", "")  # Add your bot token here
    FORCE_SUB_CHANNEL = getenv("FORCE_SUB_CHANNEL", "World_Fastest_Bots")  
    SUDO = list(map(int, getenv("SUDO", "6040503076 1234567890 9876543210").split()))  
    MONGO_URI = getenv("MONGO_URI", "mongodb+srv://iamrealdevil098:M7UXF0EL3M352q0H@cluster0.257nd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")  
    LOG_CHANNEL = int(getenv("LOG_CHANNEL", "-1002446826368"))  
    FLASK_PORT = int(getenv("FLASK_PORT", 9007))  
    
    # New additions:
    DEFAULT_WELCOME_MESSAGE = getenv("DEFAULT_WELCOME_MESSAGE", "🚀 Welcome to the fastest bot!")
    BROADCAST_ENABLED = bool(int(getenv("BROADCAST_ENABLED", "1")))

cfg = Config()
