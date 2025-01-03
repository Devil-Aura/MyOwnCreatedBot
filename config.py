from os import getenv

class Config:
    API_ID = int(getenv("API_ID", "22768311"))
    API_HASH = getenv("API_HASH", "702d8884f48b42e865425391432b3794")
    BOT_TOKEN = getenv("BOT_TOKEN", "")
    CHID = int(getenv("CHID", "-1002432405855"))  # Ensure bot is admin here
    SUDO = list(map(int, getenv("SUDO", "6040503076").split()))
    MONGO_URI = getenv("MONGO_URI", "mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true")

cfg = Config()
