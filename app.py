from flask import Flask
from config import cfg

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'TechVJ Bot is Running!'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=cfg.FLASK_PORT)
