from pyrogram.types import (
    Message, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    CallbackQuery,
    ChatMemberUpdated,  # Added this import
    ChatJoinRequest     # Added this import
)
from pyrogram import filters, Client, errors, enums
from pyrogram.errors import UserNotParticipant
from pyrogram.errors.exceptions.flood_420 import FloodWait
from database import (
    add_user, add_group, all_users, all_groups, remove_user,
    disable_broadcast, enable_broadcast, is_broadcast_disabled,
    ban_user, unban_user, is_user_banned, get_banned_users,
    get_disabled_broadcast_users, set_welcome_message, get_welcome_message,
    users_collection
)
from config import cfg
import asyncio
from datetime import datetime  # Make sure this is imported

app = Client(
    "approver",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN
)

LOG_CHANNEL = -1002446826368  # Your log channel ID

# [Rest of your bot code remains the same, including all the handler functions]

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Welcome & Logging ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    user_id = m.from_user.id
    user_mention = m.from_user.mention

    if is_user_banned(user_id):
        await m.reply("🚫 You are banned from using this bot!")
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
    await app.send_message(
        LOG_CHANNEL,
        f"**New User Started the Bot!**\n\n"
        f"👤 **User:** {user_mention}\n"
        f"🆔 **User ID:** `{user_id}`"
    )

    add_user(user_id)  # Corrected indentation
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
            f"**🙋🏻‍♂️ Hello {m.from_user.mention}!\n\n"
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
    # Delete the previous message
    await query.message.delete()

    # Send the /start command from the user's side
    await query.message.reply("/start")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Approve Requests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_chat_join_request(filters.group | filters.channel)
async def approve(_, m: Message):
    chat = m.chat
    user = m.from_user

    try:
        # Fetch chat invite link if the bot has permission
        invite_link = await app.export_chat_invite_link(chat.id) if chat.username is None else f"https://t.me/{chat.username}"
        chat_type = "channel" if chat.type == enums.ChatType.CHANNEL else "group"
        add_group(chat.id, user.id, chat.title, invite_link, chat_type)
        await app.approve_chat_join_request(chat.id, user.id)

        welcome_msg = get_welcome_message(chat.id) or "🎉 Welcome, {user_mention}! Your request to join {chat_title} has been approved! 🚀"
        await app.send_message(user.id, welcome_msg.format(user_mention=user.mention, chat_title=chat.title))

        add_user(user.id)
    except errors.PeerIdInvalid:
        print("User hasn't started the bot (group issue)")
    except Exception as e:
        print(str(e))

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Bot Addition Logger ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_chat_member_updated()
async def log_bot_addition(_, update: ChatMemberUpdated):
    if (update.new_chat_member and 
        update.new_chat_member.user.id == app.id and 
        update.new_chat_member.status == enums.ChatMemberStatus.ADMINISTRATOR):
        
        chat = update.chat
        adder = update.from_user

        try:
            # 1. Get adder info (handles anonymous admins)
            adder_info = "👤 **Added By:** "
            if adder:
                if adder.is_anonymous:
                    adder_info += "Anonymous Admin"
                else:
                    adder_info += f"{adder.mention} (ID: `{adder.id}`)"
                
                if adder.username:
                    adder_info += f"\n🔗 **Username:** @{adder.username}"
            else:
                adder_info += "Unknown (possibly via invite link)"

            # 2. Get chat info (works for private channels/groups)
            chat_type = "Channel" if chat.type == enums.ChatType.CHANNEL else "Group"
            
            # 3. Get invite link (using bot's invite permission)
            try:
                if chat.username:
                    invite_link = f"https://t.me/{chat.username}"
                else:
                    invite_link = await app.export_chat_invite_link(chat.id)
            except Exception as e:
                invite_link = f"No link available (Error: {str(e)})"

            # 4. Get member count (works for private chats)
            try:
                members_count = await app.get_chat_members_count(chat.id)
            except:
                members_count = "Unknown (no access)"

            # 5. Get admin list (handles private chats)
            admin_list = []
            try:
                async for member in app.get_chat_members(chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                    if member.user.is_bot:
                        continue
                    
                    admin_entry = f"• {member.user.mention if not member.user.is_anonymous else 'Anonymous Admin'}"
                    admin_entry += f" (ID: `{member.user.id}`)"
                    
                    if member.status == enums.ChatMemberStatus.OWNER:
                        admin_entry += " 👑"
                    if member.custom_title:
                        admin_entry += f" [{member.custom_title}]"
                    
                    admin_list.append(admin_entry)
            except Exception as e:
                admin_list = [f"⚠️ Admin list unavailable: {str(e)}"]

            # Compose the log message
            log_msg = (
                f"🤖 **Bot Added to Private {chat_type}**\n\n"
                f"{adder_info}\n\n"
                f"📢 **Chat Details**\n"
                f"▫️ Name: {chat.title}\n"
                f"▫️ ID: `{chat.id}`\n"
                f"▫️ Type: {'Private' if chat.invite_link else 'Public'} {chat_type}\n"
                f"▫️ Members: `{members_count}`\n"
                f"▫️ Invite Link: {invite_link}\n\n"
                f"👮 **Admins ({len(admin_list)})**:\n" + "\n".join(admin_list) + 
                f"\n\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            await app.send_message(LOG_CHANNEL, log_msg, disable_web_page_preview=True)
            
        except Exception as e:
            error_msg = (
                f"⚠️ **Failed to Log Bot Addition**\n\n"
                f"Chat: {chat.title if chat else 'Unknown'}\n"
                f"ID: `{chat.id if chat else 'N/A'}`\n"
                f"Error: `{str(e)}`"
            )
            try:
                await app.send_message(LOG_CHANNEL, error_msg)
            except:
                pass

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

@app.on_message(filters.command("User_Channels") & filters.user(cfg.SUDO))
async def user_channels(_, m: Message):
    channels = get_user_channels()
    if not channels:
        await m.reply("No users have added the bot to any channels/groups yet.")
        return

    text = "**📋 Users & Their Channels/Groups:**\n"
    for user_id, details in channels.items():
        username = details["username"]
        text += f"\n👤 **User:** [{username}](tg://user?id={user_id}) (ID: `{user_id}`)\n"  # Mention username and user ID
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
