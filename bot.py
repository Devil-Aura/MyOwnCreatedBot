import os
import asyncio
import logging
from datetime import datetime
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ChatMemberUpdated
from pyrogram import filters, Client, errors, enums
from pyrogram.errors import UserNotParticipant, FloodWait
from database import (
    add_user, add_group, all_users, all_groups, remove_user,
    disable_broadcast, enable_broadcast, is_broadcast_disabled,
    ban_user, unban_user, is_user_banned, get_banned_users,
    get_disabled_broadcast_users, set_welcome_message, get_welcome_message,
    get_user_channels, users_collection
)
from config import cfg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure session directory exists
os.makedirs("sessions", exist_ok=True)

app = Client(
    "approver",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN,
    workdir="sessions",
    plugins=dict(root="plugins")
)

LOG_CHANNEL = -1002446826368  # Your actual log channel ID

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Welcome & Logging ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    user_id = m.from_user.id
    user_mention = m.from_user.mention

    if is_user_banned(user_id):
        await m.reply("🚫 You are banned from using this bot! (@Fastest_Bots_Support)")
        return

    try:
        await app.get_chat_member(cfg.CHID, user_id)
    except UserNotParticipant:
        try:
            invite_link = await app.create_chat_invite_link(cfg.CHID)
            key = InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("🍿 Join Update Channel 🍿", url=invite_link.invite_link),
                    InlineKeyboardButton("🍀 Check Again 🍀", callback_data="check_again")
                ]]
            )
            await m.reply_text(
                "**⚠️ Access Denied! ⚠️**\n\n"
                "Please join my update channel to use me. If you have already joined, click 'Check Again' to confirm.",
                reply_markup=key
            )
            return
        except Exception as e:
            logger.error(f"Failed to create invite link: {e}")
            await m.reply("**Make sure I am an admin in your channel!**")
            return

    try:
        if not users_collection.find_one({"user_id": user_id}):
            username = f"@{m.from_user.username}" if m.from_user.username else "No Username"
            await app.send_message(
                LOG_CHANNEL,
                f"**New User Started the Bot!**\n\n"
                f"👤 **User:** {user_mention}\n"
                f"🆔 **ID:** `{user_id}`\n"
                f"📛 **Username:** {username}"
            )
    except Exception as e:
        logger.error(f"Failed to send log message: {e}")

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
    
    try:
        await m.reply_photo(
            "https://i.ibb.co/6wQZY57/photo-2024-12-30-17-57-41-7454266052625563676.jpg",
            caption=(
                f"**🤗 Hello {m.from_user.mention}!\n\n"
                f"🚀 I am the FASTEST BOT, faster than light ⚡! "
                f"I approve join requests in just 0.5 seconds.\n"
                f"<blockquote>I'm an auto-approve [Admin Join Requests](https://t.me/telegram/153) Bot.\n"
                f"I can approve users in Groups/Channels. Add me to your chat and promote me to admin with 'Add Members' permission.</blockquote>\n\n"
                f"Powered By: @World_Fastest_Bots**"
            ),
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Failed to send welcome message: {e}")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Callback Query Handler ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_callback_query(filters.regex("^check_again$"))
async def check_again_callback(_, query: CallbackQuery):
    try:
        await query.message.delete()
        await query.message.reply("**Click /start To Check You Are Joined**")
    except Exception as e:
        logger.error(f"Callback error: {e}")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Approve Requests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_chat_member_updated()
async def log_bot_addition(_, update: ChatMemberUpdated):
    try:
        # Debugging: Print raw update
        logger.info(f"Received chat member update: {update}")
        
        # Get bot's own ID
        me = await app.get_me()
        bot_id = me.id
        logger.info(f"Bot ID: {bot_id}")
        
        # Check if this update is about our bot being added as admin
        if (update.new_chat_member and 
            update.new_chat_member.user.id == bot_id and 
            update.new_chat_member.status == enums.ChatMemberStatus.ADMINISTRATOR):
            
            logger.info("Bot was added as admin")
            
            chat = update.chat
            adder = update.from_user

            adder_name = adder.first_name if adder else "Unknown"
            adder_username = f"@{adder.username}" if adder and adder.username else "No Username"
            adder_id = adder.id if adder else "N/A"
            
            chat_type = "Private Channel" if chat.type == enums.ChatType.CHANNEL else "Private Group"
            chat_title = chat.title or "Untitled"
            chat_id = chat.id
            
            # Try to create invite link
            invite_link = "Not available"
            try:
                result = await app.create_chat_invite_link(
                    chat.id,
                    name="Bot-Auto-Link",
                    creates_join_request=True
                )
                invite_link = result.invite_link
                logger.info(f"Created invite link: {invite_link}")
            except Exception as e:
                logger.error(f"Failed to create invite link: {e}")

            # Prepare log message
            log_message = (
                f"🔒 **Bot Added to {chat_type}**\n\n"
                f"👤 **Added by:** {adder_name}\n"
                f"🆔 **User ID:** `{adder_id}`\n"
                f"📛 **Username:** {adder_username}\n\n"
                f"📢 **Chat Details:**\n"
                f"• Name: {chat_title}\n"
                f"• ID: `{chat_id}`\n"
                f"• Invite Link: {invite_link}\n\n"
                f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Send to log channel
            try:
                logger.info(f"Sending to log channel: {LOG_CHANNEL}")
                await app.send_message(
                    LOG_CHANNEL,
                    log_message,
                    disable_web_page_preview=True
                )
                logger.info("Log message sent successfully")
                
                # Add to database
                add_group(chat.id, adder.id if adder else None, chat_title, 
                          invite_link, 
                          "channel" if chat.type == enums.ChatType.CHANNEL else "group",
                          username=adder_username)
            except Exception as e:
                logger.error(f"Failed to send log message: {e}")

    except Exception as e:
        logger.error(f"Error in log_bot_addition: {e}", exc_info=True)

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Bot Addition Logger ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_chat_member_updated()
async def log_bot_addition(client: Client, update: ChatMemberUpdated):
    try:
        # First get the bot's ID safely
        try:
            me = await client.get_me()
            bot_id = me.id
        except Exception as e:
            logger.error(f"Failed to get bot ID: {e}")
            return

        # Check if this update is relevant to our bot
        if not (update.new_chat_member and update.new_chat_member.user.id == bot_id):
            return

        # Verify it's an admin promotion event
        if update.new_chat_member.status != enums.ChatMemberStatus.ADMINISTRATOR:
            return

        logger.info(f"Bot was promoted to admin in {update.chat.id}")

        # Get chat and adder info with proper error handling
        try:
            chat = update.chat
            adder = update.from_user
            
            # Basic info collection with fallbacks
            adder_info = {
                'name': adder.first_name if adder else "Unknown",
                'username': f"@{adder.username}" if adder and adder.username else "No Username",
                'id': adder.id if adder else "N/A"
            }
            
            chat_info = {
                'type': "Channel" if chat.type == enums.ChatType.CHANNEL else "Group",
                'title': chat.title or "Untitled",
                'id': chat.id,
                'is_private': not bool(chat.username)  # Best way to check if private
            }
            
        except Exception as e:
            logger.error(f"Failed to get chat/adder info: {e}")
            return

        # Handle invite link creation
        invite_link = "Not available"
        if chat_info['is_private']:
            try:
                # Check if bot has permission to create invite links
                chat_member = await client.get_chat_member(chat_info['id'], bot_id)
                if chat_member.privileges and chat_member.privileges.can_invite_users:
                    result = await client.create_chat_invite_link(
                        chat_info['id'],
                        name="Bot-Generated-Link",
                        creates_join_request=True
                    )
                    invite_link = result.invite_link
                    logger.info(f"Created invite link for {chat_info['id']}")
            except Exception as e:
                logger.error(f"Invite link creation failed: {e}")

        # Prepare and send log message
        try:
            log_message = (
                f"🤖 **Bot Added to {chat_info['type']}**\n\n"
                f"👤 **Added by:** {adder_info['name']}\n"
                f"🆔 **User ID:** `{adder_info['id']}`\n"
                f"📛 **Username:** {adder_info['username']}\n\n"
                f"📢 **Chat Details:**\n"
                f"• Name: {chat_info['title']}\n"
                f"• Type: {'Private' if chat_info['is_private'] else 'Public'}\n"
                f"• ID: `{chat_info['id']}`\n"
                f"• Link: {invite_link}\n\n"
                f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            await client.send_message(
                LOG_CHANNEL,
                log_message,
                disable_web_page_preview=True
            )
            logger.info(f"Logged addition to {chat_info['id']}")

            # Database operations
            try:
                add_group(
                    chat_info['id'],
                    adder_info['id'],
                    chat_info['title'],
                    invite_link,
                    "channel" if chat.type == enums.ChatType.CHANNEL else "group",
                    username=adder_info['username']
                )
            except Exception as e:
                logger.error(f"Database update failed: {e}")

        except Exception as e:
            logger.error(f"Log message failed: {e}")

    except Exception as e:
        logger.error(f"Unexpected error in log_bot_addition: {e}", exc_info=True)

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

@app.on_message(filters.command("User_Channels") & filters.user(cfg.SUDO))
async def user_channels(_, m: Message):
    channels = get_user_channels()
    if not channels:
        await m.reply("No users have added the bot to any channels/groups yet.")
        return

    text = "**📋 Users & Their Channels/Groups:**\n"
    for user_id, details in channels.items():
        user_name = details.get("username", f"User-{user_id}")  # Fetch user name
        user_url = details.get("user_url", f"https://t.me/{user_name}")  # Fetch user URL

        # Fetch user's actual name and username from Telegram
        try:
            user = await app.get_users(user_id)
            user_name = user.first_name or "Unknown"  # Use first name or "Unknown" if not available
            username = user.username or f"User-{user_id}"  # Use username or fallback to User-<ID>
            user_tag = f"@{username}" if username else user_name  # Use @username if available, else use name
            user_mention = user.mention  # Use user mention (e.g., @username or name)
        except Exception:
            user_name = "Unknown"
            user_tag = f"User-{user_id}"
            user_mention = f"User-{user_id}"

        text += f"\n👤 **User Name:** {user_name}\n"
        text += f"      **User ID:** `{user_id}`\n"
        text += f"      **Username Tag:** {user_tag}\n"
        text += f"      **User Mention:** {user_mention}\n"

        if details["channels"]:
            text += "  📢 **Channels:**\n"
            for channel in details["channels"]:
                text += f"    - [{channel['chat_title']}]({channel['chat_url']})\n"

        if details["groups"]:
            text += "  📢 **Groups:**\n"
            for group in details["groups"]:
                text += f"    - [{group['chat_title']}]({group['chat_url']})\n"
        else:
            text += "  ❌ No channels/groups added.\n"

    await m.reply(text, disable_web_page_preview=True)

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
    text = "🔕 **Users with Disabled Broadcasts:**\n" + "\n".join(f"👤 `{user}`" for user in users)
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
    text = "🚫 **Banned Users:**\n" + "\n".join(f"👤 `{user}`" for user in users)
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
