import logging
import asyncio
from pyrogram import Client, filters, errors
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors.exceptions.flood_420 import FloodWait
from database import (
    add_user, add_group, all_users, all_groups, users,
    remove_user, ban_user, unban_user, is_banned,
    disable_broadcast_for_user, is_broadcast_disabled,
    set_welcome_message, get_welcome_message
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

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Main Process ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_chat_join_request(filters.group | filters.channel)
async def approve(_, m: Message):
    if is_banned(m.from_user.id):
        return
    try:
        op = m.chat
        kk = m.from_user
        add_group(op.id)
        await app.approve_chat_join_request(op.id, kk.id)
        welcome_message = get_welcome_message(op.id) or "Welcome to {group}!"
        await app.send_message(
            kk.id,
            welcome_message.format(
                group=op.title,
                username=kk.username or "User",
                mention=kk.mention,
            ),
        )
        add_user(kk.id)
    except errors.PeerIdInvalid:
        logger.error("User hasn't started the bot.")
    except Exception as err:
        logger.error(f"Error in approving join request: {err}")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Start Command ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    if is_banned(m.from_user.id):
        await m.reply("🚫 You are banned from using this bot!")
        return

    try:
        await app.get_chat_member(cfg.CHID, m.from_user.id)
    except errors.UserNotParticipant:
        try:
            invite_link = await app.create_chat_invite_link(int(cfg.CHID))
        except Exception:
            await m.reply("**Make Sure I Am Admin In Your Channel**")
            return

        key = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🍿 Join Update Channel 🍿", url=invite_link.invite_link),
                    InlineKeyboardButton("🍀 Check Again 🍀", callback_data="chk"),
                ]
            ]
        )
        await m.reply_text(
            "**⚠️Access Denied!⚠️\n\nPlease Join My Update Channel To Use Me. If You Joined The Channel Then Click On Check Again Button To Confirm.**",
            reply_markup=key,
        )
        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🗯 Channel", url="https://t.me/World_Fastest_Bots"),
                InlineKeyboardButton("💬 Support", url="https://t.me/Fastest_Bots_Support"),
            ],
            [
                InlineKeyboardButton("➕ Add Me in Channel", url="https://t.me/Request_acceept_bot?startchannel"),
                InlineKeyboardButton("➕ Add Me in Group", url="https://t.me/Auto_Request_Accept_Fast_bot?startgroup"),
            ],
        ]
    )
    add_user(m.from_user.id)
    await m.reply_photo(
        "https://i.ibb.co/6wQZY57/photo-2024-12-30-17-57-41-7454266052625563676.jpg",
        caption=(
            f"**🙋🏻‍♂️Hello {m.from_user.mention}!\n"
            f"🚀 I am the FASTEST BOT, faster than light ⚡!"
            f" I approve join requests in just 0.5 seconds.\n\n**"
           <blockquote> "I'm an auto approve [Admin Join Requests](https://t.me/telegram/153) Bot.\n"
            "I can approve users in Groups/Channels. Add me to your chat and promote me to admin with add members permission.\n\n" </blockquote>
            "__Powered By : @World_Fastest_Bots __**"
        ),
        reply_markup=keyboard,
    )

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ New Features ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("stats") & filters.user(cfg.SUDO))
async def stats(_, m: Message):
    active_users = len(all_users())
    banned_users = len(users.get_banned_users())
    deactivated_users = len(users.get_deactivated_users())
    await m.reply_text(
        f"📊 **Bot Statistics:**\n\n"
        f"👤 **Active Users:** `{active_users}`\n"
        f"🚫 **Banned Users:** `{banned_users}`\n"
        f"🗿 **Deactivated Users:** `{deactivated_users}`"
    )

@app.on_message(filters.command("ban") & filters.user(cfg.SUDO))
async def ban_user_command(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/ban user_id`")
        return

    user_id = int(m.command[1])
    ban_user(user_id)
    await m.reply(f"🚫 User `{user_id}` has been banned from using this bot.")

@app.on_message(filters.command("welcome") & filters.user(cfg.SUDO))
async def set_welcome(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/welcome your_message`")
        return

    welcome_message = m.text.split(" ", 1)[1]
    set_welcome_message(cfg.CHID, welcome_message)
    await m.reply("✅ Welcome message has been updated.")

@app.on_message(filters.command("disable_broadcast") & filters.user(cfg.SUDO))
async def disable_broadcast(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/disable_broadcast user_id`")
        return

    user_id = int(m.command[1])
    disable_broadcast_for_user(user_id)
    await m.reply(f"🚫 Broadcasts have been disabled for user `{user_id}`.")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Broadcast ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("bcast") & filters.user(cfg.SUDO))
async def broadcast(_, m: Message):
    all_users_data = users
    reply = await m.reply_text("`⚡️ Processing broadcast...`")
    success, failed, deactivated, blocked = 0, 0, 0, 0

    for user in all_users_data.find():
        user_id = user["user_id"]
        if is_broadcast_disabled(user_id):
            continue
        try:
            await m.reply_to_message.copy(int(user_id))
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await m.reply_to_message.copy(int(user_id))
        except errors.InputUserDeactivated:
            remove_user(user_id)
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
