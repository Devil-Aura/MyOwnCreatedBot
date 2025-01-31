from os import getenv  # Add this line to fix the error

class Config:
    API_ID = int(getenv("API_ID", "22768311"))
    API_HASH = getenv("API_HASH", "702d8884f48b42e865425391432b3794")
    BOT_TOKEN = getenv("BOT_TOKEN", "")  # Add your bot token here
    FORCE_SUB_CHANNEL = getenv("FORCE_SUB_CHANNEL", "World_Fastest_Bots")  # Force subscription channel
    SUDO = list(map(int, getenv("SUDO", "6040503076").split()))  # List of sudo user IDs
    MONGO_URI = getenv("MONGO_URI", "mongodb+srv://iamrealdevil098:M7UXF0EL3M352q0H@cluster0.257nd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")  # MongoDB URI (if using MongoDB)
    LOG_CHANNEL = int(getenv("LOG_CHANNEL", "-1002446826368"))  # Log channel to track user and group activities
    FLASK_PORT = int(getenv("FLASK_PORT", 9823))  # Port for Flask (changed to 9643 as per your configuration)

cfg = Config()
