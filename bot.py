import logging
from pyrogram import Client, filters, errors
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import cfg
from database import (
    add_user, log_user_data, is_banned, all_users, disable_broadcast_for_user,
    enable_broadcast, is_broadcast_disabled, set_welcome_message, get_welcome_message,
    get_user_channels, ban_user, unban_user, all_banned_users, all_disabled_broadcast_users
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Pyrogram Client
app = Client(
    "approver",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN,
)

LOG_CHANNEL = cfg.LOG_CHANNEL
FORCE_SUB_CHANNEL = cfg.FORCE_SUB_CHANNEL  # Add channel username in config.py without '@'


# Function to check if user is subscribed
async def is_user_subscribed(client: Client, user_id: int, channel_username: str) -> bool:
    try:
        user = await client.get_chat_member(channel_username, user_id)
        return user.status in ["member", "administrator", "creator"]
    except errors.UserNotParticipant:
        return False
    except errors.ChatAdminRequired:
        logger.warning(f"Bot is not an admin in the channel: {channel_username}")
        return False
    except Exception as e:
        logger.error(f"Error checking subscription status: {e}")
        return False


# Start Command
@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    # Check force subscription
    if not await is_user_subscribed(app, m.from_user.id, FORCE_SUB_CHANNEL):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
        ])
        await m.reply(
            f"🔒 You must join [this channel](https://t.me/{FORCE_SUB_CHANNEL}) to use this bot!\n\n"
            f"⚡ I approve requests faster than light!",
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )
        return

    # Check if user is banned
    if is_banned(m.from_user.id):
        await m.reply("🚫 You are banned from using this bot!")
        return

    # Add user and log data
    add_user(m.from_user.id, m.from_user.username)
    log_user_data(m.from_user.id, m.from_user.username, LOG_CHANNEL)

    # Send welcome message with the keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🗯 Channel", url="https://t.me/World_Fastest_Bots"),
            InlineKeyboardButton("💬 Support", url="https://t.me/Fastest_Bots_Support"),
        ],
        [
            InlineKeyboardButton("➕ Add Me in Channel", url="https://t.me/Request_acceept_bot?startchannel"),
            InlineKeyboardButton("➕ Add Me in Group", url="https://t.me/Auto_Request_Accept_Fast_bot?startgroup"),
        ],
    ])
    
    await m.reply_photo(
        "https://i.ibb.co/6wQZY57/photo-2024-12-30-17-57-41-7454266052625563676.jpg",
        caption=(
            f"**🙋🏻‍♂️ Hello {m.from_user.mention}!\n\n"
            f"🚀 I am the FASTEST BOT, faster than light ⚡!\n"
            f"I approve join requests in just 0.5 seconds.\n"
            f" <blockquote> I'm an auto-approve [Admin Join Requests](https://t.me/telegram/153) Bot.\n"
            f"I can approve users in Groups/Channels. Add me to your chat and promote me to admin with 'Add Members' permission.</blockquote>\n\n"
            f"Powered By : @World_Fastest_Bots**"
        ),
        reply_markup=keyboard,
    )


# Ban Command
@app.on_message(filters.command("ban") & filters.user(cfg.SUDO))
async def ban_command(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/ban user_id`")
        return
    user_id = int(m.command[1])
    ban_user(user_id)
    disable_broadcast_for_user(user_id)
    await m.reply(f"🚫 User `{user_id}` has been banned.")


# Unban Command
@app.on_message(filters.command("unban") & filters.user(cfg.SUDO))
async def unban_command(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/unban user_id`")
        return
    user_id = int(m.command[1])
    unban_user(user_id)
    await m.reply(f"✅ User `{user_id}` has been unbanned.")


# Show Banned Users Command
@app.on_message(filters.command("show_banned_users") & filters.user(cfg.SUDO))
async def show_banned_users(_, m: Message):
    banned_users = all_banned_users()
    if not banned_users:
        await m.reply("🚫 No banned users found.")
        return
    text = "\n".join([f"• `{user['user_id']}`" for user in banned_users])
    await m.reply(f"📜 **Banned Users:**\n\n{text}")


# Disable Broadcast Command
@app.on_message(filters.command("disable_broadcast") & filters.user(cfg.SUDO))
async def disable_broadcast(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/disable_broadcast user_id`")
        return
    user_id = int(m.command[1])
    disable_broadcast_for_user(user_id)
    await m.reply(f"🚫 Broadcast disabled for user `{user_id}`.")


# Enable Broadcast Command
@app.on_message(filters.command("enable_broadcast") & filters.user(cfg.SUDO))
async def enable_broadcast(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/enable_broadcast user_id`")
        return
    user_id = int(m.command[1])
    enable_broadcast(user_id)
    await m.reply(f"✅ Broadcast enabled for user `{user_id}`.")


# Show Disabled Broadcast Users Command
@app.on_message(filters.command("show_disable_broadcast_users") & filters.user(cfg.SUDO))
async def show_disabled_broadcast_users(_, m: Message):
    disabled_users = all_disabled_broadcast_users()
    if not disabled_users:
        await m.reply("🚫 No disabled broadcast users found.")
        return
    text = "\n".join([f"• `{user['user_id']}`" for user in disabled_users])
    await m.reply(f"📜 **Disabled Broadcast Users:**\n\n{text}")


# User Channels Command
@app.on_message(filters.command("user_channels") & filters.user(cfg.SUDO))
async def user_channels(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/user_channels user_id`")
        return
    user_id = int(m.command[1])
    channels = get_user_channels(user_id)
    if not channels:
        await m.reply(f"🚫 No channels found for user `{user_id}`.")
        return
    text = "\n".join([f"• `{c['chat_id']}`: {c['chat_name']}" for c in channels])
    await m.reply(f"📜 **User Channels:**\n\n{text}")


# Stats Command
@app.on_message(filters.command("stats") & filters.user(cfg.SUDO))
async def stats(_, m: Message):
    active_users = len(all_users())
    await m.reply(f"📊 **Active Users:** `{active_users}`")


# Run the Bot
logger.info("🚀 Bot is alive and running!")
app.run()
