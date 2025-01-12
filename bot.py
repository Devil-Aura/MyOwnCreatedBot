import logging
import random
import asyncio
from pyrogram import Client, filters, errors
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import UserNotParticipant
from pyrogram.errors.exceptions.flood_420 import FloodWait
from database import add_user, add_group, all_users, all_groups, users, remove_user
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
    try:
        op = m.chat
        kk = m.from_user
        add_group(op.id)
        await app.approve_chat_join_request(op.id, kk.id)
        await app.send_message(
            kk.id,
            f"**Hello {kk.mention}!\nWelcome To {op.title}\n\n__Powered By : @World_Fastest_Bots __**",
        )
        add_user(kk.id)
    except errors.PeerIdInvalid:
        logger.error("User hasn't started the bot.")
    except Exception as err:
        logger.error(f"Error in approving join request: {err}")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Start Command ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
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

    # Keyboard with updated buttons
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
            f"**🦊 Hello {m.from_user.mention}!\n"
            f"🚀 I am the **FASTEST BOT**, faster than light! 🌠\n"
            f"⏱ I approve join requests in just **0.5 seconds**.\n\n"
            "I'm an auto approve [Admin Join Requests](https://t.me/telegram/153) Bot.\n"
            "I can approve users in Groups/Channels. Add me to your chat and promote me to admin with add members permission.\n\n"
            "__Powered By : @World_Fastest_Bots __**"
        ),
        reply_markup=keyboard,
    )

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Callback Handling ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_callback_query(filters.regex("chk"))
async def check_again(_, cb: CallbackQuery):
    try:
        await app.get_chat_member(cfg.CHID, cb.from_user.id)
    except errors.UserNotParticipant:
        await cb.answer(
            "🙅‍♂️ You are not joined my channel. First join the channel, then check again. 🙅‍♂️",
            show_alert=True,
        )
        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🗯 Channel", url="https://t.me/World_Fastest_Bots"),
                InlineKeyboardButton("💬 Support", url="https://t.me/Fastest_Bots_Support"),
            ]
        ]
    )
    await cb.edit_message_text(
        text=(
            f"**🦊 Hello {cb.from_user.mention}!\n"
            f"I'm an auto approve [Admin Join Requests](https://t.me/telegram/153) Bot.\n"
            "I can approve users in Groups/Channels. Add me to your chat and promote me to admin with add members permission.\n\n"
            "__Powered By : @World_Fastest_Bots __**"
        ),
        reply_markup=keyboard,
    )

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Database Stats ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("users") & filters.user(cfg.SUDO))
async def show_stats(_, m: Message):
    num_users = len(all_users())
    num_groups = len(all_groups())
    total = num_users + num_groups
    await m.reply_text(
        text=(
            f"🍀 **Chat Stats:** 🍀\n\n"
            f"🙋‍♂️ Users: `{num_users}`\n"
            f"👥 Groups: `{num_groups}`\n"
            f"🚧 Total Users & Groups: `{total}`"
        )
    )

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Broadcast ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_message(filters.command("bcast") & filters.user(cfg.SUDO))
async def broadcast(_, m: Message):
    all_users_data = users
    reply = await m.reply_text("`⚡️ Processing broadcast...`")
    success, failed, deactivated, blocked = 0, 0, 0, 0

    for user in all_users_data.find():
        user_id = user["user_id"]
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
