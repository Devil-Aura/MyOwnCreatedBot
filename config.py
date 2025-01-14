from os import getenv  # Add this line to fix the error

class Config:
    API_ID = int(getenv("API_ID", "22768311"))
    API_HASH = getenv("API_HASH", "702d8884f48b42e865425391432b3794")
    BOT_TOKEN = getenv("BOT_TOKEN", "")
    CHID = int(getenv("CHID", "-1002432405855"))
    SUDO = list(map(int, getenv("SUDO", "6040503076").split()))
    MONGO_URI = getenv("MONGO_URI", "mongodb+srv://iamrealdevil098:M7UXF0EL3M352q0H@cluster0.257nd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    LOG_CHANNEL = int(getenv("LOG_CHANNEL", "-1002446826368"))  # Log channel to track user and group activities
    FLASK_PORT = int(getenv("FLASK_PORT", 9398))  # Changed port to 8080
cfg = Config()
