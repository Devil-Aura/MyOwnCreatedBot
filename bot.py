from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram import filters, Client, errors, enums
from pyrogram.errors import UserNotParticipant, PeerIdInvalid, ChannelPrivate
from database import (
    add_user, add_group, all_users, all_groups,
    ban_user, unban_user, is_user_banned, get_banned_users,
    get_disabled_broadcast_users, set_welcome_message, get_welcome_message,
    users_collection, channels_collection as groups_collection
)
from config import cfg
import asyncio
import time
import psutil
from datetime import datetime
import sys
import os
from config import *

app = Client(
    "approver",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN
)

# Global variables
START_TIME = time.time()
LOG_CHANNEL = -1002446826368 # Replace with your actual log channel ID

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Helper Functions ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_uptime(seconds):
    """Convert seconds to human-readable format"""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def get_system_stats():
    """Get lightweight system metrics"""
    try:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        return f"🖥 CPU: {cpu}% | RAM: {mem}%"
    except:
        return "⚠️ System stats unavailable"
        
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Welcome & Logging ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    user_id = m.from_user.id
    user_mention = m.from_user.mention

    if is_user_banned(user_id):  
        await m.reply("🚫 You are banned from using this bot!(@Fastest_Bots_Support)")  
        return  

    try:  
        await app.get_chat_member(cfg.CHID, user_id)  
    except UserNotParticipant:  
        try:  
            invite_link = await app.create_chat_invite_link(cfg.CHID)  
        except:  
            await m.reply("**Make sure I am an admin in your channel!**")  
            return  
        key = InlineKeyboardMarkup(  
            [[  
                InlineKeyboardButton("🍿 Join Update Channel 🍿", url=invite_link.invite_link),  
                InlineKeyboardButton("🍀 Check Again 🍀", callback_data="check_again")  
            ]]  
        )  
        await m.reply_text(  
            "**⚠️ Access Denied! ⚠️**\n\n"  
            "<b>Please join my update channel to use me.</b>/n <blockquote><b>If you have already joined, click 'Check Again' to confirm.</b></blockqoute>",  
            reply_markup=key  
        )  
        return  

    # Logging user activity  
    try:  
        await app.send_message(  
            LOG_CHANNEL,  
            f"**New User Started the Bot!**\n\n"  
            f"👤 **User:** {user_mention}\n"  
            f"🆔 **User ID:** `{user_id}`"  
        )  
    except Exception as e:  
        print(f"Failed to send log message: {e}")  

    add_user(user_id)  
    keyboard = InlineKeyboardMarkup([  
        [  
            InlineKeyboardButton("🗯 Channel", url="https://t.me/World_Fastest_Bots"),  
            InlineKeyboardButton("💬 Support", url="https://t.me/Fastest_Bots_Support"),  
        ],  
        [  
            InlineKeyboardButton("➕ Add Me in Channel", url="https://t.me/Auto_Request_Accept_Fast_bot?startchannel"),  
            InlineKeyboardButton("➕ Add Me in Group", url="https://t.me/Auto_Request_Accept_Fast_bot?startgroup"),  
        ],  
    ])  
    await m.reply_photo(
        "https://i.ibb.co/6wQZY57/photo-2024-12-30-17-57-41-7454266052625563676.jpg",
        caption=(
            f"**🤗 Hello {m.from_user.mention}!\n\n"
            f"🚀 I am the FASTEST BOT, faster than light ⚡!"
            f"I approve join requests in just 0.5 seconds.\n"
            f"<blockquote> I'm an auto-approve [Admin Join Requests](https://t.me/telegram/153) Bot.\n"
            f"I can approve users in Groups/Channels. Add me to your chat and promote me to admin with 'Add Members' permission.</blockquote>\n\n"
            f"Powered By : @World_Fastest_Bots**"
        ),
        reply_markup=keyboard,
    )
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Callback Query Handler ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_callback_query(filters.regex("^check_again$"))
async def check_again_callback(_, query: CallbackQuery):
    await query.message.delete()
    await query.message.reply("<b>ᴄʟɪᴄᴋ /start ᴛᴏ ᴄʜᴇᴄᴋ ʏᴏᴜ ᴀʀᴇ ᴊᴏɪɴᴇᴅ</b>")
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ pic ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#START_MSG = """<b>🤗 Hello {first}!</b>

#<b>🚀 I am the <u>FASTEST BOT</u>, faster than light ⚡! I approve join requests in just 0.5 seconds.</b>

#<blockquote><b>I'm an auto-approve <a href="https://t.me/telegram/153">Admin Join Requests</a> Bot. I can approve users in Groups/Channels. Add me to your chat and promote me to admin with 'Add Members' permission.</b></blockquote>

#<b>Powered By : <a href="https://t.me/World_Fastest_Bots">@World_Fastest_Bots</a></b>"""
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Approve Requests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_chat_join_request(filters.group | filters.channel)
async def approve(_, m: Message):
    chat = m.chat
    user = m.from_user

    try:  
        # Fetch the private invite link for the group/channel  
        invite_link = await app.export_chat_invite_link(chat.id)  # Fetch private invite link  
        chat_type = "channel" if chat.type == enums.ChatType.CHANNEL else "group"  

        # Fetch user details  
        user_name = user.first_name or "Unknown"  
        username = user.username or f"User-{user.id}"  
        user_url = f"https://t.me/{username}" if username else f"https://t.me/User-{user.id}"  

        # Add group/channel with user details  
        add_group(chat.id, user.id, chat.title, invite_link, chat_type, username=username, user_url=user_url)  

        await app.approve_chat_join_request(chat.id, user.id)  

        welcome_msg = get_welcome_message(chat.id) or "**<b>🎉 Welcome, {user_mention}! Your request to join {chat_title} has been approved! 🚀</b>/n <blockquote><b>/start To Use Me...!!</b></blockqoute>**"  
        await app.send_message(user.id, welcome_msg.format(user_mention=user.mention, chat_title=chat.title))  

        add_user(user.id)  
    except errors.PeerIdInvalid:  
        print("User hasn't started the bot (group issue)")  
    except Exception as e:  
        print(str(e))

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ New Fretures  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("restart") & filters.user(cfg.SUDO))
async def restart_bot(_, m: Message):
    await m.reply("♻️ Restarting bot...")
    await app.send_message(
        LOG_CHANNEL,
        f"🔄 Bot restarted by {m.from_user.mention}\n"
        f"⏱ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    os.execl(sys.executable, sys.executable, *sys.argv)

@app.on_message(filters.command("status") & filters.user(cfg.SUDO))
async def show_status(_, m: Message):
    await m.reply_text(
        f"⚙️ **System Status**\n\n"
        f"{get_system_stats()}\n"
        f"⏱ Uptime: `{format_uptime(time.time() - START_TIME)}`\n"
        f"🕒 Started: `{datetime.fromtimestamp(START_TIME).strftime('%Y-%m-%d %H:%M')}`"
    )
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Admin Commands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("stats") & filters.user(cfg.SUDO))
async def stats(_, m: Message):
    total_users = all_users()
    total_groups = all_groups()
    banned_users = len(get_banned_users())
    disabled_broadcasts = len(get_disabled_broadcast_users())

    await m.reply_text(  
        f"📊 **Bot Stats**\n\n"  
        f"👥 Users: `{total_users}`\n"  
        f"📢 Groups: `{total_groups}`\n"  
        f"🚫 Banned Users: `{banned_users}`\n"  
        f"🔕 Disabled Broadcasts: `{disabled_broadcasts}`"  
    )

@app.on_message(filters.command("Set_Welcome_Mgs") & filters.user(cfg.SUDO))
async def set_welcome(_, m: Message):
    chat_id = m.chat.id
    welcome_msg = m.text.split(None, 1)[1] if len(m.text.split()) > 1 else None

    if not welcome_msg:  
        await m.reply("⚠️ Please provide a welcome message!")  
        return  

    set_welcome_message(chat_id, welcome_msg)  
    await m.reply("✅ Welcome message updated successfully!")

@app.on_message(filters.command("Disable_Boardcast") & filters.user(cfg.SUDO))
async def disable_broadcast_cmd(_, m: Message):
    if len(m.command) < 2:
        await m.reply("⚠️ Please provide a user ID!")
        return

    user_id = int(m.command[1])  
    disable_broadcast(user_id)  
    await m.reply(f"🚫 Broadcasts disabled for `{user_id}`.")

@app.on_message(filters.command("Unable_Boardcast") & filters.user(cfg.SUDO))
async def enable_broadcast_cmd(_, m: Message):
    if len(m.command) < 2:
        await m.reply("⚠️ Please provide a user ID!")
        return

    user_id = int(m.command[1])  
    enable_broadcast(user_id)  
    await m.reply(f"🔔 Broadcasts enabled for `{user_id}`.")

@app.on_message(filters.command("Shows_Disable_Boardcast_Users") & filters.user(cfg.SUDO))
async def show_disabled_broadcasts(_, m: Message):
    users = get_disabled_broadcast_users()
    text = "🔕 Users with Disabled Broadcasts:\n" + "\n".join(f"👤 {user}" for user in users)
    await m.reply(text)

@app.on_message(filters.command("Ban") & filters.user(cfg.SUDO))
async def ban(_, m: Message):
    if len(m.command) < 2:
        await m.reply("⚠️ Please provide a user ID!")
        return

    user_id = int(m.command[1])  
    ban_user(user_id)  
    await m.reply(f"🚫 User `{user_id}` has been banned!")

@app.on_message(filters.command("Unban") & filters.user(cfg.SUDO))
async def unban(_, m: Message):
    if len(m.command) < 2:
        await m.reply("⚠️ Please provide a user ID!")
        return

    user_id = int(m.command[1])  
    unban_user(user_id)  
    await m.reply(f"✅ User `{user_id}` has been unbanned!")

@app.on_message(filters.command("Shows_Banusers") & filters.user(cfg.SUDO))
async def show_banned_users(_, m: Message):
    users = get_banned_users()
    text = "🚫 Banned Users:\n" + "\n".join(f"👤 {user}" for user in users)
    await m.reply(text)

@app.on_message(filters.command("broadcast") & filters.user(cfg.SUDO) & filters.reply)
async def broadcast_message(_, m: Message):
    # Check if the command is used as a reply
    if not m.reply_to_message:
        await m.reply("⚠️ Please reply to a message to broadcast it!")
        return

    # Get the replied message  
    broadcast_msg = m.reply_to_message  

    # Get all users except banned and disabled broadcast users  
    all_users_list = list(set([user["user_id"] for user in users_collection.find({})]))  # Fetch all unique user IDs from MongoDB  
    disabled_users = get_disabled_broadcast_users()  # Fetch disabled broadcast users  
    banned_users = get_banned_users()  # Fetch banned users  

    success = 0  
    failed = 0  

    # Send the message to all users  
    for user_id in all_users_list:  
        if user_id not in disabled_users and user_id not in banned_users:  
            try:  
                await broadcast_msg.copy(user_id)  # Send the message only once  
                success += 1  
            except Exception as e:  
                print(f"Failed to send message to {user_id}: {e}")  
                failed += 1  
        await asyncio.sleep(0.1)  # To avoid flooding  

    # Send broadcast stats to the admin  
    await m.reply(  
        f"📢 **Broadcast Completed!**\n\n"  
        f"✅ Success: `{success}`\n"  
        f"❌ Failed: `{failed}`"  
    )

print("Bot is running!")
app.run()
