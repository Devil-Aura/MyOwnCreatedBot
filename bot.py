from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ChatMemberUpdated
from pyrogram import filters, Client, errors, enums
from pyrogram.errors import UserNotParticipant
from pyrogram.errors.exceptions.flood_420 import FloodWait
from database import (
    add_user, add_group, all_users, all_groups, remove_user,
    disable_broadcast, enable_broadcast, is_broadcast_disabled,
    ban_user, unban_user, is_user_banned, get_banned_users,
    get_disabled_broadcast_users, set_welcome_message, get_welcome_message, users_collection
)
from config import cfg
import asyncio

app = Client(
    "approver",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN
)

LOG_CHANNEL = -1002446826368  # Replace with your actual log channel ID

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
            "Please join my update channel to use me. If you have already joined, click 'Check Again' to confirm.",  
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
    await query.message.reply("Click /start To Check You Are Joined")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Approve Requests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

        welcome_msg = get_welcome_message(chat.id) or "**🎉 Welcome, {user_mention}! Your request to join {chat_title} has been approved! 🚀    /start To Use Me**"  
        await app.send_message(user.id, welcome_msg.format(user_mention=user.mention, chat_title=chat.title))  

        add_user(user.id)  
    except errors.PeerIdInvalid:  
        print("User hasn't started the bot (group issue)")  
    except Exception as e:  
        print(str(e))

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Log Bot Added to Channel/Group ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_chat_member_updated()
async def chat_member_updated(_, update: ChatMemberUpdated):
    if update.new_chat_member and update.new_chat_member.user.id == app.id:
        print("Bot was added to a chat!")  # Debugging log
        chat = update.chat
        user = update.from_user

        # Fetch user details  
        user_name = user.first_name or "Unknown"  
        username = user.username or f"User-{user.id}"  
        user_url = f"https://t.me/{username}" if username else f"https://t.me/User-{user.id}"  
        user_mention = user.mention  

        # Fetch chat invite link if the bot has permission  
        try:  
            invite_link = await app.export_chat_invite_link(chat.id) if chat.username is None else f"https://t.me/{chat.username}"  
        except Exception:  
            invite_link = "No invite link available"  

        # Customize log message based on chat type  
        if chat.type == enums.ChatType.CHANNEL:  
            log_message = (  
                f"**Bot Added to Channel!**\n\n"  
                f"👤 **Added By:** {user_mention}\n"  
                f"🆔 **User ID:** `{user.id}`\n"  
                f"📛 **Username:** @{username}\n"  
                f"📢 **Channel Name:** {chat.title}\n"  
                f"🆔 **Channel ID:** `{chat.id}`\n"  
                f"🔗 **Channel Link:** {invite_link}"  
            )  
        elif chat.type == enums.ChatType.GROUP or chat.type == enums.ChatType.SUPERGROUP:  
            log_message = (  
                f"**Bot Added to Group!**\n\n"  
                f"👤 **Added By:** {user_mention}\n"  
                f"🆔 **User ID:** `{user.id}`\n"  
                f"📛 **Username:** @{username}\n"  
                f"📢 **Group Name:** {chat.title}\n"  
                f"🆔 **Group ID:** `{chat.id}`\n"  
                f"🔗 **Group Link:** {invite_link}"  
            )  
        else:  
            return  

        # Send log message to the log channel  
        try:  
            await app.send_message(LOG_CHANNEL, log_message)  
        except Exception as e:  
            print(f"Failed to send log message: {e}")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Admin Commands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("fetchadmins") & filters.user(cfg.SUDO))
async def fetch_admins(_, m: Message):
    if len(m.command) < 2:
        await m.reply("⚠️ Please provide a channel/group ID!\nUsage: `/fetchadmins channel_id`")
        return
    
    try:
        chat_id = int(m.command[1]) if m.command[1].startswith('-') else m.command[1]
        admins = await app.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS)
        
        if not admins:
            await m.reply("❌ No admins found or I don't have permission to view admins.")
            return
        
        admin_list = "**👥 Admins List:**\n\n"
        for admin in admins:
            user = admin.user
            admin_list += (
                f"👤 **Name:** {user.first_name or 'Unknown'}\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"📛 **Username:** @{user.username}\n"
                f"🔹 **Status:** {admin.status.value}\n\n"
            )
        
        # Send to both the requester and log channel
        await m.reply(admin_list)
        try:
            await app.send_message(
                LOG_CHANNEL,
                f"**Admin List Fetched**\n\n"
                f"📢 **Chat ID:** `{chat_id}`\n"
                f"👤 **Requested By:** {m.from_user.mention}\n"
                f"🆔 **User ID:** `{m.from_user.id}`\n\n"
                f"{admin_list}"
            )
        except Exception as e:
            print(f"Failed to send admin list to log channel: {e}")
            
    except Exception as e:
        await m.reply(f"❌ Error fetching admins: {str(e)}")

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
        user_name = details.get("username", f"User-{user_id}")  
        user_url = details.get("user_url", f"https://t.me/{user_name}")  

        try:  
            user = await app.get_users(user_id)  
            user_name = user.first_name or "Unknown"  
            username = user.username or f"User-{user_id}"  
            user_tag = f"@{username}" if username else user_name  
            user_mention = user.mention  
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
    all_users_list = list(set([user["user_id"] for user in users_collection.find({})]))  
    disabled_users = get_disabled_broadcast_users()  
    banned_users = get_banned_users()  

    success = 0  
    failed = 0  

    # Send the message to all users  
    for user_id in all_users_list:  
        if user_id not in disabled_users and user_id not in banned_users:  
            try:  
                await broadcast_msg.copy(user_id)  
                success += 1  
            except Exception as e:  
                print(f"Failed to send message to {user_id}: {e}")  
                failed += 1  
        await asyncio.sleep(0.1)  

    # Send broadcast stats to the admin  
    await m.reply(  
        f"📢 **Broadcast Completed!**\n\n"  
        f"✅ Success: `{success}`\n"  
        f"❌ Failed: `{failed}`"  
    )

print("Bot is running!")
app.run()
