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

    START_PIC = os.environ.get("START_PIC", "https://i.ibb.co/6wQZY57/photo-2024-12-30-17-57-41-7454266052625563676.jpg")
    
    START_MSG = os.environ.get("START_MESSAGE", """<b>🤗 ʜᴇʟʟᴏ {first}!</b>\n\n
<b>🚀 ɪ ᴀᴍ ᴛʜᴇ <u>ꜰᴀꜱᴛᴇꜱᴛ ʙᴏᴛ</u>, ꜰᴀꜱᴛᴇʀ ᴛʜᴀɴ ʟɪɢʜᴛ ⚡! ɪ ᴀᴘᴘʀᴏᴠᴇ ᴊᴏɪɴ ʀᴇǫᴜᴇꜱᴛꜱ ɪɴ ᴊᴜꜱᴛ 0.5 ꜱᴇᴄᴏɴᴅꜱ.</b>\n
<blockquote><b>ɪ'ᴍ ᴀɴ ᴀᴜᴛᴏ-ᴀᴘᴘʀᴏᴠᴇ <a href="https://t.me/telegram/153">ᴀᴅᴍɪɴ ᴊᴏɪɴ ʀᴇǫᴜᴇꜱᴛꜱ</a> ʙᴏᴛ. ɪ ᴄᴀɴ ᴀᴘᴘʀᴏᴠᴇ ᴜꜱᴇʀꜱ ɪɴ ɢʀᴏᴜᴘꜱ/ᴄʜᴀɴɴᴇʟꜱ. ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ᴄʜᴀᴛ ᴀɴᴅ ᴘʀᴏᴍᴏᴛᴇ ᴍᴇ ᴛᴏ ᴀᴅᴍɪɴ ᴡɪᴛʜ 'ᴀᴅᴅ ᴍᴇᴍʙᴇʀꜱ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ.</b></blockquote>\n\n
<b>ᴘᴏᴡᴇʀᴇᴅ ʙʏ : <a href="https://t.me/World_Fastest_Bots">@World_Fastest_Bots</a></b>""")

cfg = Config()
