import logging
import asyncio
from pyrogram import Client, filters, errors
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors.exceptions.flood_420 import FloodWait
from database import (
    add_user, add_group, all_users, all_groups,
    remove_user, ban_user, unban_user, is_banned,
    disable_broadcast_for_user, is_broadcast_disabled,
    set_welcome_message, get_welcome_message,
    log_user_data, get_user_channels
)
from config import cfg

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

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Start Command ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    if is_banned(m.from_user.id):
        await m.reply("🚫 You are banned from using this bot!")
        return

    add_user(m.from_user.id, m.from_user.username)
    log_user_data(m.from_user.id, m.from_user.username, LOG_CHANNEL)

    await app.send_message(
        LOG_CHANNEL,
        f"🆕 **New User Alert!**\n"
        f"**Username:** @{m.from_user.username or 'N/A'}\n"
        f"**User ID:** `{m.from_user.id}`",
    )

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
             f"**🙋🏻‍♂️Hello {m.from_user.mention}!\n"
            f"🚀 I am the FASTEST BOT, faster than light ⚡!"
            f" I approve join requests in just 0.5 seconds.\n\n"
            f" <blockquote> I'm an auto-approve [Admin Join Requests](https://t.me/telegram/153) Bot.\n"
            f"I can approve users in Groups/Channels. Add me to your chat and promote me to admin with 'Add Members' permission.</blockquote>\n\n"
            f"Powered By : @World_Fastest_Bots**"
       ),
        reply_markup=keyboard,
    )

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ User Commands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("stats") & filters.user(cfg.SUDO))
async def stats(_, m: Message):
    active_users = len(all_users())
    banned_users = users.count_documents({"banned": True})
    disabled_broadcast_users = len([user for user in all_users() if is_broadcast_disabled(user["user_id"])])
    await m.reply_text(
        f"📊 **Bot Statistics:**\n\n"
        f"👤 **Active Users:** `{active_users}`\n"
        f"🚫 **Banned Users:** `{banned_users}`\n"
        f"🔕 **Disabled Broadcast Users:** `{disabled_broadcast_users}`"
    )

@app.on_message(filters.command("ban") & filters.user(cfg.SUDO))
async def ban_user_command(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/ban user_id`")
        return

    try:
        user_id = int(m.command[1])
        ban_user(user_id)
        
        # Disable broadcast for banned user
        disable_broadcast_for_user(user_id)
        
        await m.reply(f"🚫 User `{user_id}` has been banned from using this bot and their broadcast has been disabled.")
    except ValueError:
        await m.reply("❌ Invalid user ID. Please provide a numeric value.")

@app.on_message(filters.command("user_channels") & filters.user(cfg.SUDO))
async def user_channels(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/user_channels user_id`")
        return

    try:
        user_id = int(m.command[1])
        channels = get_user_channels(user_id)
        if not channels:
            await m.reply(f"🚫 No channels/groups found for user `{user_id}`.")
            return

        text = "\n".join([f"• `{c['chat_id']}`: {c['chat_name']} ({c['chat_url']})" for c in channels])
        await m.reply_text(f"📚 **Channels/Groups for User `{user_id}`:**\n\n{text}")
    except ValueError:
        await m.reply("❌ Invalid user ID. Please provide a numeric value.")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Broadcast ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("bcast") & filters.user(cfg.SUDO))
async def broadcast(_, m: Message):
    active_users = all_users()
    reply = await m.reply_text("`⚡️ Processing broadcast...`")
    success, failed, deactivated, blocked = 0, 0, 0, 0

    for user in active_users:
        if is_broadcast_disabled(user["user_id"]):
            deactivated += 1
            continue  # Skip disabled users

        try:
            await m.reply_to_message.copy(int(user["user_id"]))
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await m.reply_to_message.copy(int(user["user_id"]))
        except errors.InputUserDeactivated:
            remove_user(user["user_id"])
            deactivated += 1
        except errors.UserIsBlocked:
            blocked += 1
        except Exception:
            failed += 1

    await reply.edit(
        f"✅ Successfully broadcasted to `{success}` users.\n"
        f"❌ Failed to send to `{failed}` users.\n"
        f"👾 `{blocked}` users blocked the bot.\n"
        f"👻 `{deactivated}` accounts were deactivated."
    )

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Main Run ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

logger.info("🚀 Bot is alive and running faster than light!")
app.run()
