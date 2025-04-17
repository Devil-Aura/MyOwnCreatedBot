import os
import asyncio
import logging
from datetime import datetime
from pyrogram.types import (Message, InlineKeyboardButton, 
                          InlineKeyboardMarkup, CallbackQuery, 
                          ChatMemberUpdated, ChatJoinRequest)
from pyrogram import filters, Client, enums
from pyrogram.errors import UserNotParticipant, FloodWait
from database import (
    add_user, add_group, all_users, all_groups, remove_user,
    disable_broadcast, enable_broadcast, is_broadcast_disabled,
    ban_user, unban_user, is_user_banned, get_banned_users,
    get_disabled_broadcast_users, set_welcome_message, 
    get_welcome_message, users_collection, groups_collection
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

LOG_CHANNEL = -1002446826368  # Make sure to add this to your config.py

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Welcome & Logging ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    user_id = m.from_user.id
    user_mention = m.from_user.mention

    if is_user_banned(user_id):
        await m.reply("🚫 You are banned from using this bot! Contact @Fastest_Bots_Support")
        return

    # Check if user has joined your channel (not if they've added bot as admin)
    try:
        member = await app.get_chat_member(cfg.CHID, user_id)
        if member.status in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]:
            raise UserNotParticipant
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
            await m.reply("**Make sure I am an admin in the update channel!**")
            return
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        await m.reply("⚠️ An error occurred while checking your channel membership. Please try again later.")
        return

    # Rest of your start handler remains the same...
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
        await m.reply("Welcome to the bot!")  # Fallback message

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Callback Query Handler ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_callback_query(filters.regex("^check_again$"))
async def check_again_callback(_, query: CallbackQuery):
    try:
        await query.message.delete()
        await query.message.reply("**Click /start To Check You Are Joined**")
    except Exception as e:
        logger.error(f"Callback error: {e}")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Approve Requests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_chat_join_request()
async def approve(_, join_request: ChatJoinRequest):
    chat = join_request.chat
    user = join_request.from_user

    try:
        # Try to get invite link
        try:
            invite_link = await app.export_chat_invite_link(chat.id)
        except:
            invite_link = "Not available"

        chat_type = "channel" if chat.type == enums.ChatType.CHANNEL else "group"
        username = f"@{user.username}" if user.username else f"User-{user.id}"

        await app.approve_chat_join_request(chat.id, user.id)
        logger.info(f"Approved join request for {username} in {chat.title}")

        welcome_msg = get_welcome_message(chat.id) or "🎉 Welcome, {user_mention}! Your request to join {chat_title} has been approved! 🚀 /start To Use Me"
        try:
            await app.send_message(
                user.id,
                welcome_msg.format(
                    user_mention=user.mention,
                    chat_title=chat.title
                )
            )
        except Exception as e:
            logger.warning(f"Couldn't send welcome message to {username}: {e}")

        add_user(user.id)
        add_group(
            chat.id,
            user.id,
            chat.title,
            invite_link,
            chat_type,
            username=username
        )

    except Exception as e:
        logger.error(f"Approval error in {chat.id}: {e}")
        try:
            await app.send_message(
                LOG_CHANNEL,
                f"⚠️ **Approval Failed**\n\n"
                f"**Chat:** {chat.title}\n"
                f"**ID:** `{chat.id}`\n"
                f"**User:** {user.mention}\n"
                f"**Error:** `{e}`"
            )
        except Exception as log_err:
            logger.error(f"Failed to send error log: {log_err}")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Bot Addition Logger ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_chat_member_updated()
async def log_bot_addition(_, update: ChatMemberUpdated):
    try:
        # Check if the update is about the bot being added as admin
        bot_id = (await app.get_me()).id
        if (update.new_chat_member and 
            update.new_chat_member.user.id == bot_id and 
            update.new_chat_member.status == enums.ChatMemberStatus.ADMINISTRATOR):
            
            chat = update.chat
            adder = update.from_user

            adder_name = adder.first_name if adder else "Unknown"
            adder_username = f"@{adder.username}" if adder and adder.username else "No Username"
            adder_id = adder.id if adder else "N/A"

            chat_title = chat.title or "Untitled"
            chat_id = chat.id
            chat_type = "Channel" if chat.type == enums.ChatType.CHANNEL else "Group"

            # Try to get an invite link
            invite_link = "Not available"
            try:
                result = await app.create_chat_invite_link(
                    chat.id,
                    name="Auto Log Invite",
                    creates_join_request=True
                )
                invite_link = result.invite_link
            except Exception as e:
                logger.warning(f"Invite link generation failed: {e}")

            # Fetch admin list
            admin_info = ""
            try:
                admins = await app.get_chat_members(chat_id=chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS)
                for admin in admins:
                    user = admin.user
                    admin_name = user.first_name or "Unknown"
                    admin_username = f"@{user.username}" if user.username else "No Username"
                    admin_info += f"• {admin_name} | {admin_username} | `{user.id}`\n"
            except Exception as e:
                admin_info = "Failed to fetch admin list."
                logger.warning(f"Couldn't fetch admin list: {e}")

            # Final log message
            log_message = (
                f"✅ **Bot Added to {chat_type}**\n\n"
                f"👤 **Added by:** {adder_name}\n"
                f"🆔 **User ID:** `{adder_id}`\n"
                f"🔗 **Username:** {adder_username}\n\n"
                f"📢 **{chat_type} Info:**\n"
                f"• Title: {chat_title}\n"
                f"• ID: `{chat_id}`\n"
                f"• Invite Link: {invite_link}\n\n"
                f"👮‍♂️ **Admins List:**\n{admin_info}\n"
                f"🕒 `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
            )

            # Send to log channel
            await app.send_message(LOG_CHANNEL, log_message, disable_web_page_preview=True)
            logger.info(f"Logged bot addition to {chat_title}")

            # Save to DB
            add_group(
                chat.id, 
                adder.id if adder else None, 
                chat_title, 
                invite_link,
                "channel" if chat.type == enums.ChatType.CHANNEL else "group",
                username=adder_username
            )

    except Exception as e:
        logger.error(f"Bot join handler failed: {e}")
        try:
            await app.send_message(
                LOG_CHANNEL,
                f"⚠️ **Bot Addition Log Failed**\n\n"
                f"**Error:** `{e}`"
            )
        except Exception as log_err:
            logger.error(f"Failed to send error log: {log_err}")

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

@app.on_message(filters.command(["set_welcome", "set_welcome_msg"]) & filters.user(cfg.SUDO))
async def set_welcome(_, m: Message):
    if len(m.command) < 2:
        await m.reply("⚠️ Usage: /set_welcome <message>")
        return

    chat_id = m.chat.id
    welcome_msg = m.text.split(None, 1)[1]
    
    set_welcome_message(chat_id, welcome_msg)
    await m.reply("✅ Welcome message updated successfully!")

@app.on_message(filters.command("disable_broadcast") & filters.user(cfg.SUDO))
async def disable_broadcast_cmd(_, m: Message):
    if len(m.command) < 2:
        await m.reply("⚠️ Usage: /disable_broadcast <user_id>")
        return

    try:
        user_id = int(m.command[1])
        disable_broadcast(user_id)
        await m.reply(f"🚫 Broadcasts disabled for user `{user_id}`.")
    except ValueError:
        await m.reply("⚠️ Invalid user ID!")

@app.on_message(filters.command("enable_broadcast") & filters.user(cfg.SUDO))
async def enable_broadcast_cmd(_, m: Message):
    if len(m.command) < 2:
        await m.reply("⚠️ Usage: /enable_broadcast <user_id>")
        return

    try:
        user_id = int(m.command[1])
        enable_broadcast(user_id)
        await m.reply(f"🔔 Broadcasts enabled for user `{user_id}`.")
    except ValueError:
        await m.reply("⚠️ Invalid user ID!")

@app.on_message(filters.command("disabled_users") & filters.user(cfg.SUDO))
async def show_disabled_broadcasts(_, m: Message):
    users = get_disabled_broadcast_users()
    if not users:
        await m.reply("No users have disabled broadcasts.")
        return
        
    text = "🔕 **Users with Disabled Broadcasts:**\n" + "\n".join(f"👤 `{user}`" for user in users)
    await m.reply(text)

@app.on_message(filters.command("ban") & filters.user(cfg.SUDO))
async def ban(_, m: Message):
    if len(m.command) < 2:
        await m.reply("⚠️ Usage: /ban <user_id>")
        return

    try:
        user_id = int(m.command[1])
        ban_user(user_id)
        await m.reply(f"🚫 User `{user_id}` has been banned!")
    except ValueError:
        await m.reply("⚠️ Invalid user ID!")

@app.on_message(filters.command("unban") & filters.user(cfg.SUDO))
async def unban(_, m: Message):
    if len(m.command) < 2:
        await m.reply("⚠️ Usage: /unban <user_id>")
        return

    try:
        user_id = int(m.command[1])
        unban_user(user_id)
        await m.reply(f"✅ User `{user_id}` has been unbanned!")
    except ValueError:
        await m.reply("⚠️ Invalid user ID!")

@app.on_message(filters.command("banned_users") & filters.user(cfg.SUDO))
async def show_banned_users(_, m: Message):
    users = get_banned_users()
    if not users:
        await m.reply("No users are currently banned.")
        return
        
    text = "🚫 **Banned Users:**\n" + "\n".join(f"👤 `{user}`" for user in users)
    await m.reply(text)

@app.on_message(filters.command("broadcast") & filters.user(cfg.SUDO) & filters.reply)
async def broadcast_message(_, m: Message):
    if not m.reply_to_message:
        await m.reply("⚠️ Please reply to a message to broadcast it!")
        return

    broadcast_msg = m.reply_to_message
    processing_msg = await m.reply("📢 Starting broadcast...")

    all_users_list = [user["user_id"] for user in users_collection.find({})]
    disabled_users = get_disabled_broadcast_users()
    banned_users = get_banned_users()

    success = 0
    failed = 0
    blocked = 0

    for user_id in all_users_list:
        if user_id in disabled_users or user_id in banned_users:
            continue
            
        try:
            await broadcast_msg.copy(user_id)
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except errors.UserIsBlocked:
            blocked += 1
            remove_user(user_id)
        except Exception as e:
            logger.error(f"Failed to send to {user_id}: {e}")
            failed += 1
            
        await asyncio.sleep(0.1)  # Small delay to prevent flooding

        # Update progress every 50 sends
        if (success + failed) % 50 == 0:
            try:
                await processing_msg.edit_text(
                    f"📢 Broadcasting in progress...\n\n"
                    f"✅ Success: {success}\n"
                    f"❌ Failed: {failed}\n"
                    f"🚫 Blocked: {blocked}"
                )
            except:
                pass

    await processing_msg.edit_text(
        f"📢 **Broadcast Completed!**\n\n"
        f"✅ Success: `{success}`\n"
        f"❌ Failed: `{failed}`\n"
        f"🚫 Blocked: `{blocked}`"
    )

if __name__ == "__main__":
    print("Bot is starting...")
    app.run()
