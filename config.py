class Config:
    API_ID = int(getenv("API_ID", "22768311"))
    API_HASH = getenv("API_HASH", "702d8884f48b42e865425391432b3794")
    BOT_TOKEN = getenv("BOT_TOKEN", "")
    CHID = int(getenv("CHID", "-1002432405855"))  # Channel ID
    SUDO = list(map(int, getenv("SUDO", "6040503076").split()))
    MONGO_URI = getenv("MONGO_URI", "mongodb+srv://<tyuvie>:<lxYx2uM6elNxd9BR>@cluster0.ybi1b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    FLASK_PORT = int(getenv("FLASK_PORT", 5000))  # Default Flask port
cfg = Config()
