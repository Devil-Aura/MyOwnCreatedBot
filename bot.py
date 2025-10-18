from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram import filters, Client, errors, enums
from pyrogram.errors import UserNotParticipant, PeerIdInvalid, ChannelPrivate
from database import (
    add_user, add_group, all_users, all_groups,
    ban_user, unban_user, is_user_banned, get_banned_users,
    get_disabled_broadcast_users, set_welcome_message, get_welcome_message,
    users_collection, channels_collection as groups_collection,
    add_persistent_broadcast, get_all_pending_broadcasts, get_expired_broadcasts, remove_temporary_broadcast,
    store_user_message, get_user_message_info
)
from config import cfg
import asyncio
import time
import psutil
from datetime import datetime, timedelta
import sys
import os
from config import *
import re

app = Client(
    "approver",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN
)

# Global variables
START_TIME = time.time()
LOG_CHANNEL = -1002446826368  # Replace with your actual log channel ID

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

def parse_time(time_str):
    """Parse time string like 1h, 30m, 2d into seconds"""
    time_units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }
    
    match = re.match(r'^(\d+)([smhd])$', time_str.lower())
    if match:
        value, unit = match.groups()
        return int(value) * time_units[unit]
    return None

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Background Tasks ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def cleanup_temporary_broadcasts():
    """Background task to clean up expired broadcasts - SURVIVES BOT RESTART"""
    print("🔄 Starting temporary broadcast cleanup task...")
    
    # Check for pending broadcasts from previous sessions
    try:
        pending_broadcasts = get_all_pending_broadcasts()
        print(f"📊 Found {len(pending_broadcasts)} pending broadcasts from previous session")
        
        for broadcast in pending_broadcasts:
            user_id = broadcast["user_id"]
            message_id = broadcast["message_id"]
            delete_time = broadcast["delete_time"]
            original_time = broadcast["original_broadcast_time"]
            
            # Calculate remaining time
            now = datetime.now()
            time_remaining = (delete_time - now).total_seconds()
            
            if time_remaining > 0:
                print(f"⏰ Rescheduling deletion for message {message_id} in {time_remaining:.0f}s")
                # Schedule deletion for remaining time
                asyncio.create_task(delete_single_broadcast(user_id, message_id, time_remaining))
            else:
                # Immediate deletion if time already passed
                asyncio.create_task(delete_single_broadcast(user_id, message_id, 0))
                
    except Exception as e:
        print(f"❌ Error loading pending broadcasts: {e}")
    
    # Continuous cleanup loop
    while True:
        try:
            expired_broadcasts = get_expired_broadcasts()
            for broadcast in expired_broadcasts:
                user_id = broadcast["user_id"]
                message_id = broadcast["message_id"]
                
                print(f"🕒 Deleting expired broadcast: {message_id} for user {user_id}")
                await delete_single_broadcast(user_id, message_id, 0)
                
        except Exception as e:
            print(f"❌ Error in cleanup task: {e}")
        
        await asyncio.sleep(30)  # Check every 30 seconds

async def delete_single_broadcast(user_id, message_id, delay_seconds=0):
    """Delete a single broadcast message after delay"""
    try:
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)
        
        # Try to delete the message
        await app.delete_messages(user_id, message_id)
        print(f"✅ Successfully deleted temporary broadcast: {message_id}")
        
    except errors.MessageDeleteForbidden:
        print(f"⚠️ Cannot delete message {message_id} (may be too old)")
    except errors.MessageIdInvalid:
        print(f"⚠️ Message {message_id} not found (may be already deleted)")
    except Exception as e:
        print(f"❌ Failed to delete message {message_id}: {e}")
    
    # Always remove from database - CLEANUP LOGS
    finally:
        remove_temporary_broadcast(message_id, user_id)
        print(f"🗑️ Cleared database record for message: {message_id}")

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
            """**⚠️ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ! ⚠️

            ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴍʏ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍᴇ.**
    <blockquote><b>ɪғ ʏᴏᴜ'ᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴊᴏɪɴᴇᴅ, ᴄʟɪᴄᴋ '<i>ᴄʜᴇᴄᴋ ᴀɢᴀɪɴ</i>' ᴛᴏ ᴄᴏɴғɪʀᴍ.</b></blockquote>""",
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
        f"**🤗 ʜᴇʟʟᴏ {m.from_user.mention}!\n\n"
        f"🚀 ɪ ᴀᴍ ᴛʜᴇ ғᴀsᴛᴇsᴛ ʙᴏᴛ, ғᴀsᴛᴇʀ ᴛʜᴀɴ ʟɪɢʜᴛ ⚡!"
        f"ɪ ᴀᴘᴘʀᴏᴠᴇ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛs ɪɴ ᴊᴜsᴛ 0.5 sᴇᴄᴏɴᴅs.\n"
        f"<blockquote>ɪ ᴄᴀɴ ᴀᴘᴘʀᴏᴠᴇ ᴜsᴇʀs ɪɴ ɢʀᴏᴜᴘs/ᴄʜᴀɴɴᴇʟs. ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ᴄʜᴀᴛ ᴀɴᴅ ᴘʀᴏᴍᴏᴛᴇ ᴍᴇ ᴛᴏ ᴀᴅᴍɪɴ ᴡɪᴛʜ 'ᴀᴅᴅ ᴍᴇᴍʙᴇʀs' ᴘᴇʀᴍɪssɪᴏɴ.</blockquote>\n\n"
        f"ᴘᴏᴡᴇʀᴇᴅ ʙʏ : @World_Fastest_Bots**"
    ),
    reply_markup=keyboard,
    )

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Callback Query Handler ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_callback_query(filters.regex("^check_again$"))
async def check_again_callback(_, query: CallbackQuery):
    await query.message.delete()
    await query.message.reply("<b>ᴄʟɪᴄᴋ /start ᴛᴏ ᴄʜᴇᴄᴋ ʏᴏᴜ ᴀʀᴇ ᴊᴏɪɴᴇᴅ</b>")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Approve Requests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_chat_join_request(filters.group | filters.channel)
async def approve(_, m: Message):
    chat = m.chat
    user = m.from_user

    try:  
        # Fetch the private invite link for the group/channel  
        invite_link = await app.export_chat_invite_link(chat.id)
        chat_type = "channel" if chat.type == enums.ChatType.CHANNEL else "group"  

        # Fetch user details  
        user_name = user.first_name or "Unknown"  
        username = user.username or f"User-{user.id}"  
        user_url = f"https://t.me/{username}" if username else f"https://t.me/User-{user.id}"  

        # Add group/channel with user details  
        add_group(chat.id, user.id, chat.title, invite_link, chat_type, username=username, user_url=user_url)  

        await app.approve_chat_join_request(chat.id, user.id)  

        welcome_msg = get_welcome_message(chat.id) or """**<b>🎉 ᴡᴇʟᴄᴏᴍᴇ, {user_mention}!
        ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {chat_title} ʜᴀs ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ! 🚀</b>
        <blockquote><b>/start ᴛᴏ ᴜsᴇ ᴍᴇ...!!</b></blockqoute>**"""
        await app.send_message(user.id, welcome_msg.format(user_mention=user.mention, chat_title=chat.title))  

        add_user(user.id)  
    except errors.PeerIdInvalid:  
        print("User hasn't started the bot (group issue)")  
    except Exception as e:  
        print(str(e))

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ New Features ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
    # Count pending temporary broadcasts
    pending_broadcasts = get_all_pending_broadcasts()
    
    await m.reply_text(
        f"⚙️ **System Status**\n\n"
        f"{get_system_stats()}\n"
        f"⏱ Uptime: `{format_uptime(time.time() - START_TIME)}`\n"
        f"🕒 Started: `{datetime.fromtimestamp(START_TIME).strftime('%Y-%m-%d %H:%M')}`\n"
        f"⏰ Pending Temporary Broadcasts: `{len(pending_broadcasts)}`"
    )

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Temporary Broadcast Feature (PERSISTENT) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("dbroadcast") & filters.user(cfg.SUDO) & filters.reply)
async def temporary_broadcast(_, m: Message):
    if not m.reply_to_message:
        await m.reply("⚠️ Please reply to a message to broadcast it temporarily!")
        return

    if len(m.command) < 2:
        await m.reply("⚠️ Please provide time duration (e.g., 1h, 30m, 2d)")
        return

    time_str = m.command[1]
    duration_seconds = parse_time(time_str)
    
    if not duration_seconds:
        await m.reply("❌ Invalid time format! Use: 1h, 30m, 2d, etc.")
        return

    original_broadcast_time = datetime.now()
    delete_time = original_broadcast_time + timedelta(seconds=duration_seconds)
    broadcast_msg = m.reply_to_message

    # Get all users from both MongoDB and SQLite as fallback
    all_users_list = []
    
    # Try MongoDB first
    if users_collection:
        try:
            all_users_list = list(set([user["user_id"] for user in users_collection.find({})]))
        except:
            pass
    
    # If MongoDB fails, use SQLite
    if not all_users_list:
        try:
            import sqlite3
            conn = sqlite3.connect("bot_database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            all_users_list = [row[0] for row in cursor.fetchall()]
            conn.close()
        except:
            await m.reply("❌ Failed to get user list from database")
            return

    disabled_users = get_disabled_broadcast_users()  
    banned_users = get_banned_users()  

    success = 0  
    failed = 0  

    # Send the message to all users  
    for user_id in all_users_list:  
        if user_id not in disabled_users and user_id not in banned_users:  
            try:  
                sent_msg = await broadcast_msg.copy(user_id)  
                
                # Store in database with deletion time - SURVIVES BOT RESTART
                add_persistent_broadcast(
                    user_id=user_id,
                    message_id=sent_msg.id,
                    delete_time=delete_time,
                    original_broadcast_time=original_broadcast_time
                )
                
                # Schedule deletion
                asyncio.create_task(delete_single_broadcast(user_id, sent_msg.id, duration_seconds))
                
                success += 1  
            except Exception as e:  
                print(f"Failed to send message to {user_id}: {e}")  
                failed += 1  
            await asyncio.sleep(0.1)

    # Send broadcast stats to the admin  
    stats_msg = await m.reply(  
        f"⏰ **Temporary Broadcast Sent!**\n\n"  
        f"✅ Success: `{success}`\n"  
        f"❌ Failed: `{failed}`\n"  
        f"⏳ Will auto-delete in: `{time_str}`\n"
        f"💾 **Persistent**: Survives bot restart! ✅"  
    )

    # Schedule deletion of stats message
    await asyncio.sleep(min(300, duration_seconds))
    try:
        await stats_msg.delete()
    except:
        pass

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ User Message Forwarding & Reply System ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.private & ~filters.command(["start", "stats", "broadcast", "dbroadcast", "ban", "unban", "restart", "status"]))
async def forward_user_message(_, m: Message):
    user_id = m.from_user.id
    
    if is_user_banned(user_id):
        return

    # Forward user message to log channel
    try:
        forwarded_msg = await m.forward(LOG_CHANNEL)
        
        # Store message info for reply system
        store_user_message(user_id, m.id, forwarded_msg.id)
        
        # Send info about the user
        user_info = f"**💬 New Message from User**\n\n"
        user_info += f"👤 **User:** {m.from_user.mention}\n"
        user_info += f"🆔 **ID:** `{m.from_user.id}`\n"
        if m.from_user.username:
            user_info += f"📱 **Username:** @{m.from_user.username}\n"
        user_info += f"⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        user_info += "**💡 Reply to this message to respond to the user!**"
        
        await app.send_message(LOG_CHANNEL, user_info, reply_to_message_id=forwarded_msg.id)
        
    except Exception as e:
        print(f"Failed to forward user message: {e}")

@app.on_message(filters.chat(LOG_CHANNEL) & filters.reply & filters.user(cfg.SUDO))
async def reply_to_user(_, m: Message):
    try:
        replied_msg = m.reply_to_message
        
        # Get user message info from database
        user_message_info = get_user_message_info(replied_msg.id)
        
        if user_message_info:
            user_id = user_message_info["user_id"]
            
            # Send the reply to the user
            if m.text:
                await app.send_message(user_id, f"**💌 Admin Reply:**\n\n{m.text}")
            elif m.media:
                await m.copy(user_id, caption=f"**💌 Admin Reply:**\n\n{m.caption}" if m.caption else None)
            
            await m.reply("✅ Reply sent to user!")
        else:
            await m.reply("❌ Could not find user information for this message.")
            
    except Exception as e:
        await m.reply(f"❌ Failed to send reply: {e}")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Admin Commands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("stats") & filters.user(cfg.SUDO))
async def stats(_, m: Message):
    total_users = all_users()
    total_groups = all_groups()
    banned_users = len(get_banned_users())
    disabled_broadcasts = len(get_disabled_broadcast_users())
    pending_broadcasts = len(get_all_pending_broadcasts())

    await m.reply_text(  
        f"📊 **Bot Stats**\n\n"  
        f"👥 Users: `{total_users}`\n"  
        f"📢 Groups: `{total_groups}`\n"  
        f"🚫 Banned Users: `{banned_users}`\n"  
        f"🔕 Disabled Broadcasts: `{disabled_broadcasts}`\n"
        f"⏰ Pending Temp Broadcasts: `{pending_broadcasts}`"  
    )

@app.on_message(filters.command("clean_broadcasts") & filters.user(cfg.SUDO))
async def clean_broadcasts(_, m: Message):
    """Manually clean up all temporary broadcast records"""
    try:
        expired = get_expired_broadcasts()
        for broadcast in expired:
            remove_temporary_broadcast(broadcast["message_id"], broadcast["user_id"])
        
        await m.reply(f"🧹 Cleaned up {len(expired)} expired broadcast records")
    except Exception as e:
        await m.reply(f"❌ Cleanup failed: {e}")

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
    if not m.reply_to_message:
        await m.reply("⚠️ Please reply to a message to broadcast it!")
        return

    broadcast_msg = m.reply_to_message  

    # Get all users from both MongoDB and SQLite as fallback
    all_users_list = []
    
    # Try MongoDB first
    if users_collection:
        try:
            all_users_list = list(set([user["user_id"] for user in users_collection.find({})]))
        except:
            pass
    
    # If MongoDB fails, use SQLite
    if not all_users_list:
        try:
            import sqlite3
            conn = sqlite3.connect("bot_database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            all_users_list = [row[0] for row in cursor.fetchall()]
            conn.close()
        except:
            await m.reply("❌ Failed to get user list from database")
            return

    disabled_users = get_disabled_broadcast_users()  
    banned_users = get_banned_users()  

    success = 0  
    failed = 0  

    for user_id in all_users_list:  
        if user_id not in disabled_users and user_id not in banned_users:  
            try:  
                await broadcast_msg.copy(user_id)  
                success += 1  
            except Exception as e:  
                print(f"Failed to send message to {user_id}: {e}")  
                failed += 1  
            await asyncio.sleep(0.1)

    await m.reply(  
        f"📢 **Broadcast Completed!**\n\n"  
        f"✅ Success: `{success}`\n"  
        f"❌ Failed: `{failed}`"  
    )

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Start Bot ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def main():
    await app.start()
    print("✅ Bot started successfully!")
    
    # Start background tasks
    asyncio.create_task(cleanup_temporary_broadcasts())
    print("✅ Background tasks started!")
    
    # Keep the bot running
    await idle()

if __name__ == "__main__":
    try:
        app.run(main())
    except KeyboardInterrupt:
        print("❌ Bot stopped by user!")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
