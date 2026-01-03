from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram import filters, Client, errors, enums, idle
from pyrogram.errors import UserNotParticipant, PeerIdInvalid, ChannelPrivate, UserIsBlocked, FloodWait
from database import (
    add_user, add_group, all_users, all_groups,
    ban_user, unban_user, is_user_banned, get_banned_users,
    get_disabled_broadcast_users, set_welcome_message, get_welcome_message,
    users_collection, channels_collection as groups_collection,
    disable_broadcast, enable_broadcast,
    add_persistent_broadcast, get_all_pending_broadcasts, get_expired_broadcasts, remove_temporary_broadcast
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
LOG_CHANNEL = -1002446826368  # Log channel for bot start messages
REQ_CHANNEL = -1002906408590  # Request approval channel

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
    """Background task to clean up expired broadcasts"""
    print("🔄 Starting temporary broadcast cleanup task...")
    
    # Check for pending broadcasts from previous sessions
    try:
        pending_broadcasts = get_all_pending_broadcasts()
        print(f"📊 Found {len(pending_broadcasts)} pending broadcasts from previous session")
        
        for broadcast in pending_broadcasts:
            user_id = broadcast["user_id"]
            message_id = broadcast["message_id"]
            delete_time = broadcast["delete_time"]
            
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
        await m.reply("🚫 You are banned from using this bot! Contact @Fastest_Bots_Support")  
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
            """**⚠️ ACCESS DENIED! ⚠️**

Please join my update channel to use me.**
    <blockquote><b>If you've already joined, click '<i>Check Again</i>' to confirm.</b></blockquote>""",
            reply_markup=key
        )  
        return

    # Logging user activity to LOG_CHANNEL
    try:  
        await app.send_message(  
            LOG_CHANNEL,  
            f"**👤 ɴᴇᴡ ᴜsᴇʀ sᴛᴀʀᴛᴇᴅ ʙᴏᴛ**\n\n"
            f"**ᴜsᴇʀ:** {user_mention}\n"
            f"**ɪᴅ:** `{user_id}`\n"
            f"**ᴜsᴇʀɴᴀᴍᴇ:** @{m.from_user.username if m.from_user.username else 'ɴᴏᴛ sᴇᴛ'}\n"
            f"**ᴛɪᴍᴇ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )  
    except Exception as e:  
        print(f"Failed to send log message: {e}")  

    add_user(user_id)  
    keyboard = InlineKeyboardMarkup([  
        [  
            InlineKeyboardButton("🗯 ᴄʜᴀɴɴᴇʟ", url="https://t.me/World_Fastest_Bots"),  
            InlineKeyboardButton("💬 sᴜᴘᴘᴏʀᴛ", url="https://t.me/Fastest_Bots_Support"),  
        ],  
        [  
            InlineKeyboardButton("➕ ᴀᴅᴅ ᴍᴇ ɪɴ ᴄʜᴀɴɴᴇʟ", url="https://t.me/Auto_Request_Accept_Fast_bot?startchannel"),  
            InlineKeyboardButton("➕ ᴀᴅᴅ ᴍᴇ ɪɴ ɢʀᴏᴜᴘ", url="https://t.me/Auto_Request_Accept_Fast_bot?startgroup"),  
        ],  
    ])  
    
    try:
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
    except Exception as e:
        print(f"Error sending start message: {e}")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Callback Query Handler ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_callback_query(filters.regex("^check_again$"))
async def check_again_callback(_, query: CallbackQuery):
    await query.message.delete()
    user_id = query.from_user.id
    
    try:  
        await app.get_chat_member(cfg.CHID, user_id)
        # User has joined, send start message
        await start(_, query.message)
    except UserNotParticipant:  
        try:  
            invite_link = await app.create_chat_invite_link(cfg.CHID)  
        except:  
            await query.message.reply("**Make sure I am an admin in your channel!**")  
            return  
        key = InlineKeyboardMarkup(  
            [[  
                InlineKeyboardButton("🍿 Join Update Channel 🍿", url=invite_link.invite_link),  
                InlineKeyboardButton("🍀 Check Again 🍀", callback_data="check_again")  
            ]]  
        )   
        await query.message.reply_text(
            """**⚠️ ACCESS DENIED! ⚠️**

Please join my update channel to use me.**
    <blockquote><b>If you've already joined, click '<i>Check Again</i>' to confirm.</b></blockquote>""",
            reply_markup=key
        )

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Approve Requests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_chat_join_request(filters.group | filters.channel)
async def approve(_, m: Message):
    chat = m.chat
    user = m.from_user

    try:  
        # Check if user is already in chat to avoid USER_ALREADY_PARTICIPANT error
        try:
            await app.get_chat_member(chat.id, user.id)
            # User is already participant, skip approval
            print(f"User {user.id} already in chat {chat.id}, skipping approval")
            return
        except UserNotParticipant:
            # User is not participant, proceed with approval
            pass

        # Fetch the private invite link for the group/channel  
        try:
            invite_link = await app.export_chat_invite_link(chat.id)
        except:
            invite_link = "Not Available"
            
        chat_type = "channel" if chat.type == enums.ChatType.CHANNEL else "group"  

        # Fetch user details  
        username = user.username or "ɴᴏᴛ sᴇᴛ"
        user_url = f"https://t.me/{username}" if user.username else f"tg://user?id={user.id}"

        # Add group/channel with user details  
        add_group(chat.id, user.id, chat.title, invite_link, chat_type, username=username, user_url=user_url)  

        # Approve the request
        await app.approve_chat_join_request(chat.id, user.id)  
        
        # Send approval log to REQ_CHANNEL
        try:
            await app.send_message(
                REQ_CHANNEL,
                f"**✅ ʀᴇǫᴜᴇsᴛ ᴀᴘᴘʀᴏᴠᴇᴅ**\n\n"
                f"**👤 ᴜsᴇʀ:** {user.mention}\n"
                f"**🆔 ɪᴅ:** `{user.id}`\n"
                f"**📱 ᴜsᴇʀɴᴀᴍᴇ:** @{username}\n"
                f"**📢 ᴄʜᴀᴛ:** {chat.title}\n"
                f"**🔗 ʟɪɴᴋ:** {invite_link if invite_link != 'Not Available' else 'ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ'}\n"
                f"**⏰ ᴛɪᴍᴇ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            print(f"Failed to send approval log: {e}")

        # Add user to database so bot 'meets' them before sending message
        add_user(user.id)
        
        # Small delay to allow Telegram to process the approval/new contact
        await asyncio.sleep(1)

        # Send welcome message with rate limiting
        from database import can_send_welcome, set_welcome_sent
        if can_send_welcome(user.id):
            welcome_msg = get_welcome_message(chat.id) or """**🎉 ᴡᴇʟᴄᴏᴍᴇ, {user_mention}!
            ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {chat_title} ʜᴀs ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ! 🚀
            /start ᴛᴏ ᴜsᴇ ᴍᴇ...!!**"""
            
            try:
                # Attempt to send message, handle peer id invalid by retrying once after a longer delay
                try:
                    await app.send_message(user.id, welcome_msg.format(user_mention=user.mention, chat_title=chat.title))
                except (PeerIdInvalid, PeerIdInvalid):
                    print(f"PeerIdInvalid for {user.id}, retrying after 3s...")
                    await asyncio.sleep(3)
                    await app.send_message(user.id, welcome_msg.format(user_mention=user.mention, chat_title=chat.title))
                
                set_welcome_sent(user.id)
                # Log successful welcome message to REQ_CHANNEL
                try:
                    await app.send_message(
                        REQ_CHANNEL,
                        f"**💌 ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ sᴇɴᴛ**\n\n"
                        f"**👤 ᴛᴏ:** {user.mention}\n"
                        f"**🆔 ɪᴅ:** `{user.id}`\n"
                        f"**📱 ᴜsᴇʀɴᴀᴍᴇ:** @{username}\n"
                        f"**📢 ᴄʜᴀᴛ:** {chat.title}\n"
                        f"**🔗 ʟɪɴᴋ:** {invite_link if invite_link != 'Not Available' else 'ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ'}"
                    )
                except:
                    pass
            except UserIsBlocked:
                # Log blocked user to REQ_CHANNEL
                try:
                    await app.send_message(
                        REQ_CHANNEL,
                        f"**🚫 ᴜsᴇʀ ʙʟᴏᴄᴋᴇᴅ ʙᴏᴛ**\n\n"
                        f"**👤 ᴜsᴇʀ:** {user.mention}\n"
                        f"**🆔 ɪᴅ:** `{user.id}`\n"
                        f"**📱 ᴜsᴇʀɴᴀᴍᴇ:** @{username}\n"
                        f"**📢 ᴄʜᴀᴛ:** {chat.title}\n"
                        f"**❌ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ ɴᴏᴛ sᴇɴᴛ**"
                    )
                except:
                    pass
            except Exception as e:
                print(f"Error sending welcome message: {e}")
        else:
            print(f"Welcome message skipped for {user.id} (rate limited)")

        add_user(user.id)  
        
    except errors.UserAlreadyParticipant:
        print(f"User {user.id} already participant in {chat.id}")
    except errors.PeerIdInvalid:  
        print("User hasn't started the bot")
    except Exception as e:  
        print(f"Error in approval: {e}")

@app.on_message(filters.command("stats") & filters.user(cfg.SUDO))
async def stats(_, m: Message):
    from database import all_users, all_groups, get_banned_users, get_disabled_broadcast_users, get_all_pending_broadcasts, users_collection
    
    total_users = all_users()
    total_groups = all_groups()
    banned_users = len(get_banned_users())
    disabled_broadcasts = len(get_disabled_broadcast_users())
    pending_broadcasts = len(get_all_pending_broadcasts())
    
    db_status = "MongoDB ✅" if users_collection is not None else "SQLite 📁 (MongoDB Failed)"

    await m.reply_text(  
        f"**📊 ʙᴏᴛ sᴛᴀᴛs ({db_status})**\n\n"  
        f"**👥 ᴛᴏᴛᴀʟ ᴜsᴇʀs:** `{total_users}`\n"  
        f"**📢 ᴛᴏᴛᴀʟ ɢʀᴏᴜᴘs:** `{total_groups}`\n"  
        f"**🚫 ʙᴀɴɴᴇᴅ ᴜsᴇʀs:** `{banned_users}`\n"  
        f"**🔕 ᴅɪsᴀʙʟᴇᴅ ʙʀᴏᴀᴅᴄᴀsᴛs:** `{disabled_broadcasts}`\n"
        f"**⏰ ᴘᴇɴᴅɪɴɢ ᴛᴇᴍᴘ ʙʀᴏᴀᴅᴄᴀsᴛs:** `{pending_broadcasts}`"  
    )

@app.on_message(filters.command("status") & filters.user(cfg.SUDO))
async def show_status(_, m: Message):
    # Count pending temporary broadcasts
    pending_broadcasts = len(get_all_pending_broadcasts())
    
    await m.reply_text(
        f"**⚙️ sʏsᴛᴇᴍ sᴛᴀᴛᴜs**\n\n"
        f"{get_system_stats()}\n"
        f"**⏱ ᴜᴘᴛɪᴍᴇ:** `{format_uptime(time.time() - START_TIME)}`\n"
        f"**🕒 sᴛᴀʀᴛᴇᴅ:** `{datetime.fromtimestamp(START_TIME).strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"**⏰ ᴘᴇɴᴅɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛs:** `{pending_broadcasts}`"
    )

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Broadcast Commands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("broadcast") & filters.user(cfg.SUDO) & filters.reply)
async def broadcast_message(_, m: Message):
    if not m.reply_to_message:
        await m.reply("**⚠️ ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪᴛ!**")
        return

    broadcast_msg = m.reply_to_message  
    processing_msg = await m.reply("**🔄 sᴛᴀʀᴛɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ...**")

    # Get all users
    all_users_list = get_all_users()
    
    if not all_users_list:
        await processing_msg.edit("**❌ No users found in database.**")
        return

    disabled_users = get_disabled_broadcast_users()  
    banned_users = get_banned_users()  

    success = 0  
    failed = 0  
    blocked = 0

    await processing_msg.edit(f"**📤 ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴛᴏ {len(all_users_list)} ᴜsᴇʀs...**")

    for user_id in all_users_list:  
        if user_id not in disabled_users and user_id not in banned_users:  
            try:  
                await broadcast_msg.copy(user_id)  
                success += 1  
            except UserIsBlocked:
                blocked += 1
            except Exception as e:  
                failed += 1
            
            # Update progress every 50 users
            if (success + failed + blocked) % 50 == 0:
                try:
                    await processing_msg.edit(
                        f"**📤 ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ...**\n"
                        f"**✅ sᴜᴄᴄᴇss:** {success} | **❌ ғᴀɪʟᴇᴅ:** {failed} | **🚫 ʙʟᴏᴄᴋᴇᴅ:** {blocked}"
                    )
                except:
                    pass
            
            await asyncio.sleep(0.1)  # Prevent flooding

    await processing_msg.edit(
        f"**📢 ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!**\n\n"
        f"**✅ sᴜᴄᴄᴇss:** `{success}`\n"
        f"**❌ ғᴀɪʟᴇᴅ:** `{failed}`\n"
        f"**🚫 ʙʟᴏᴄᴋᴇᴅ:** `{blocked}`"
    )

@app.on_message(filters.command("dbroadcast") & filters.user(cfg.SUDO) & filters.reply)
async def temporary_broadcast(_, m: Message):
    if not m.reply_to_message:
        await m.reply("**⚠️ ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪᴛ ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ!**")
        return

    if len(m.command) < 2:
        await m.reply("**⚠️ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛɪᴍᴇ ᴅᴜʀᴀᴛɪᴏɴ (ᴇ.ɢ., 1ʜ, 30ᴍ, 2ᴅ)**")
        return

    time_str = m.command[1]
    duration_seconds = parse_time(time_str)
    
    if not duration_seconds:
        await m.reply("**❌ ɪɴᴠᴀʟɪᴅ ᴛɪᴍᴇ ғᴏʀᴍᴀᴛ! ᴜsᴇ: 1ʜ, 30ᴍ, 2ᴅ, ᴇᴛᴄ.**")
        return

    original_broadcast_time = datetime.now()
    delete_time = original_broadcast_time + timedelta(seconds=duration_seconds)
    broadcast_msg = m.reply_to_message
    processing_msg = await m.reply("**🔄 sᴛᴀʀᴛɪɴɢ ᴛᴇᴍᴘᴏʀᴀʀʏ ʙʀᴏᴀᴅᴄᴀsᴛ...**")

    # Get all users
    all_users_list = get_all_users()
    
    if not all_users_list:
        await processing_msg.edit("**❌ No users found in database.**")
        return

    disabled_users = get_disabled_broadcast_users()  
    banned_users = get_banned_users()  

    success = 0  
    failed = 0  
    blocked = 0

    await processing_msg.edit(f"**📤 ᴛᴇᴍᴘᴏʀᴀʀʏ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴛᴏ {len(all_users_list)} ᴜsᴇʀs...**")

    for user_id in all_users_list:  
        if user_id not in disabled_users and user_id not in banned_users:  
            try:  
                # copy() preserves everything: text, media, captions, formatting, and inline keyboards
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
            except UserIsBlocked:
                blocked += 1
            except Exception as e:  
                failed += 1
            
            # Update progress
            if (success + failed + blocked) % 50 == 0:
                try:
                    await processing_msg.edit(
                        f"**📤 ᴛᴇᴍᴘᴏʀᴀʀʏ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ...**\n"
                        f"**✅ sᴜᴄᴄᴇss:** {success} | **❌ ғᴀɪʟᴇᴅ:** {failed} | **🚫 ʙʟᴏᴄᴋᴇᴅ:** {blocked}"
                    )
                except:
                    pass
            
            await asyncio.sleep(0.1)

    stats_msg = await processing_msg.edit(
        f"**⏰ ᴛᴇᴍᴘᴏʀᴀʀʏ ʙʀᴏᴀᴅᴄᴀsᴛ sᴇɴᴛ!**\n\n"
        f"**✅ sᴜᴄᴄᴇss:** `{success}`\n"
        f"**❌ ғᴀɪʟᴇᴅ:** `{failed}`\n"
        f"**🚫 ʙʟᴏᴄᴋᴇᴅ:** `{blocked}`\n"
        f"**⏳ ᴡɪʟʟ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ɪɴ:** `{time_str}`\n"
        f"**💾 ᴘᴇʀsɪsᴛᴇɴᴛ:** sᴜʀᴠɪᴠᴇs ʙᴏᴛ ʀᴇsᴛᴀʀᴛ! ✅"
    )

    # Schedule deletion of stats message
    await asyncio.sleep(min(300, duration_seconds))
    try:
        await stats_msg.delete()
    except:
        pass

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Broadcast Toggle Commands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("disable_broadcast") & filters.user(cfg.SUDO))
async def disable_broadcast_cmd(_, m: Message):
    if len(m.command) < 2:
        await m.reply("**⚠️ Provide User ID to disable broadcast.**")
        return
    try:
        user_id = int(m.command[1])
        from database import disable_broadcast
        disable_broadcast(user_id)
        await m.reply(f"**✅ Broadcast/DBroadcast disabled for user `{user_id}`.**")
    except ValueError:
        await m.reply("**❌ Invalid User ID.**")

@app.on_message(filters.command("enable_broadcast") & filters.user(cfg.SUDO))
async def enable_broadcast_cmd(_, m: Message):
    if len(m.command) < 2:
        await m.reply("**⚠️ Provide User ID to enable broadcast.**")
        return
    try:
        user_id = int(m.command[1])
        from database import enable_broadcast
        enable_broadcast(user_id)
        await m.reply(f"**✅ Broadcast/DBroadcast enabled for user `{user_id}`.**")
    except ValueError:
        await m.reply("**❌ Invalid User ID.**")

@app.on_message(filters.command("clean_broadcasts") & filters.user(cfg.SUDO))
async def clean_broadcasts(_, m: Message):
    """Manually clean up all temporary broadcast records"""
    try:
        expired = get_expired_broadcasts()
        for broadcast in expired:
            remove_temporary_broadcast(broadcast["message_id"], broadcast["user_id"])
        
        await m.reply(f"**🧹 ᴄʟᴇᴀɴᴇᴅ ᴜᴘ {len(expired)} ᴇxᴘɪʀᴇᴅ ʙʀᴏᴀᴅᴄᴀsᴛ ʀᴇᴄᴏʀᴅs**")
    except Exception as e:
        await m.reply(f"**❌ ᴄʟᴇᴀɴᴜᴘ ғᴀɪʟᴇᴅ:** {e}")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Welcome Message Management ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("set_welcome") & filters.user(cfg.SUDO))
async def set_welcome(_, m: Message):
    if len(m.command) < 2:
        await m.reply("**⚠️ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ!**\n**ᴇxᴀᴍᴘʟᴇ:** `/set_welcome ᴡᴇʟᴄᴏᴍᴇ {user_mention} ᴛᴏ {chat_title}!`")
        return

    chat_id = m.chat.id
    welcome_msg = m.text.split(None, 1)[1]

    set_welcome_message(chat_id, welcome_msg)  
    await m.reply("**✅ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ ᴜᴘᴅᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**\n**ᴜsᴇ** `{user_mention}` **ғᴏʀ ᴜsᴇʀ ᴍᴇɴᴛɪᴏɴ ᴀɴᴅ** `{chat_title}` **ғᴏʀ ᴄʜᴀᴛ ᴛɪᴛʟᴇ.**")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Broadcast Control Commands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("disable_broadcast") & filters.user(cfg.SUDO))
async def disable_broadcast_cmd(_, m: Message):
    if len(m.command) < 2:
        await m.reply("**⚠️ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ɪᴅ!**")
        return

    try:
        user_id = int(m.command[1])  
        disable_broadcast(user_id)  
        await m.reply(f"**🚫 ʙʀᴏᴀᴅᴄᴀsᴛs ᴅɪsᴀʙʟᴇᴅ ғᴏʀ ᴜsᴇʀ** `{user_id}`")
    except ValueError:
        await m.reply("**❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ!**")

@app.on_message(filters.command("enable_broadcast") & filters.user(cfg.SUDO))
async def enable_broadcast_cmd(_, m: Message):
    if len(m.command) < 2:
        await m.reply("**⚠️ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ɪᴅ!**")
        return

    try:
        user_id = int(m.command[1])  
        enable_broadcast(user_id)  
        await m.reply(f"**🔔 ʙʀᴏᴀᴅᴄᴀsᴛs ᴇɴᴀʙʟᴇᴅ ғᴏʀ ᴜsᴇʀ** `{user_id}`")
    except ValueError:
        await m.reply("**❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ!**")

@app.on_message(filters.command("show_disabled") & filters.user(cfg.SUDO))
async def show_disabled_broadcasts(_, m: Message):
    users = get_disabled_broadcast_users()
    if users:
        text = "**🔕 ᴜsᴇʀs ᴡɪᴛʜ ᴅɪsᴀʙʟᴇᴅ ʙʀᴏᴀᴅᴄᴀsᴛs:**\n" + "\n".join(f"**👤** `{user}`" for user in users)
    else:
        text = "**✅ ɴᴏ ᴜsᴇʀs ʜᴀᴠᴇ ᴅɪsᴀʙʟᴇᴅ ʙʀᴏᴀᴅᴄᴀsᴛs.**"
    await m.reply(text)

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Ban Management Commands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("ban") & filters.user(cfg.SUDO))
async def ban_user_cmd(_, m: Message):
    if len(m.command) < 2:
        await m.reply("**⚠️ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ɪᴅ!**")
        return

    try:
        user_id = int(m.command[1])  
        ban_user(user_id)  
        await m.reply(f"**🚫 ᴜsᴇʀ** `{user_id}` **ʜᴀs ʙᴇᴇɴ ʙᴀɴɴᴇᴅ!**")
    except ValueError:
        await m.reply("**❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ!**")

@app.on_message(filters.command("unban") & filters.user(cfg.SUDO))
async def unban_user_cmd(_, m: Message):
    if len(m.command) < 2:
        await m.reply("**⚠️ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ɪᴅ!**")
        return

    try:
        user_id = int(m.command[1])  
        unban_user(user_id)  
        await m.reply(f"**✅ ᴜsᴇʀ** `{user_id}` **ʜᴀs ʙᴇᴇɴ ᴜɴʙᴀɴɴᴇᴅ!**")
    except ValueError:
        await m.reply("**❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ!**")

@app.on_message(filters.command("show_banned") & filters.user(cfg.SUDO))
async def show_banned_users(_, m: Message):
    users = get_banned_users()
    if users:
        text = "**🚫 ʙᴀɴɴᴇᴅ ᴜsᴇʀs:**\n" + "\n".join(f"**👤** `{user}`" for user in users)
    else:
        text = "**✅ ɴᴏ ᴜsᴇʀs ᴀʀᴇ ᴄᴜʀʀᴇɴᴛʟʏ ʙᴀɴɴᴇᴅ.**"
    await m.reply(text)

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Start Bot ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def main():
    await app.start()
    print("✅ Bot started successfully!")
    
    # Start background tasks for dbroadcast
    asyncio.create_task(cleanup_temporary_broadcasts())
    print("✅ Background tasks started!")
    
    # Send startup message to LOG_CHANNEL
    try:
        await app.send_message(
            LOG_CHANNEL,
            f"**🤖 ʙᴏᴛ sᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**\n"
            f"**⏰** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"**👥 ᴜsᴇʀs:** {all_users()}\n"
            f"**📢 ɢʀᴏᴜᴘs:** {all_groups()}"
        )
    except:
        pass
    
    print("🔧 All features loaded and ready!")
    print("\n" + "="*50)
    print("🤖 BOT COMMANDS LIST:")
    print("="*50)
    print("👤 User Commands:")
    print("• /start - Start the bot")
    print("\n🛠️ Admin Commands:")
    print("• /stats - Show bot statistics")
    print("• /status - Show system status")
    print("• /broadcast - Broadcast message (reply)")
    print("• /dbroadcast - Temporary broadcast (reply with time)")
    print("• /clean_broadcasts - Clean expired broadcasts")
    print("• /set_welcome - Set welcome message")
    print("• /ban - Ban a user")
    print("• /unban - Unban a user")
    print("• /show_banned - Show banned users")
    print("• /disable_broadcast - Disable broadcast for user")
    print("• /enable_broadcast - Enable broadcast for user")
    print("• /show_disabled - Show users with disabled broadcasts")
    print("="*50)
    
    # Keep the bot running
    await idle()

if __name__ == "__main__":
    try:
        app.run(main())
    except KeyboardInterrupt:
        print("❌ Bot stopped by user!")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
