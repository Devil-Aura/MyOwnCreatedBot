from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram import filters, Client, errors
from pyrogram.errors import UserNotParticipant, FloodWait
from database import add_user, add_group, all_users, all_groups, users, remove_user
from config import cfg
import random
import asyncio
import logging

# Initialize Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize Pyrogram Bot Client
app = Client(
    "approver_bot",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN
)

# Auto-Approve Chat Join Requests
@app.on_chat_join_request(filters.group | filters.channel)
async def approve_requests(_, message: Message):
    try:
        chat = message.chat
        user = message.from_user
        add_group(chat.id)
        await app.approve_chat_join_request(chat.id, user.id)
        await app.send_message(
            user.id,
            f"Hello {user.mention}!\nWelcome to {chat.title}.\n\nPowered By: @World_Fastest_Bots"
        )
        add_user(user.id)
    except errors.PeerIdInvalid:
        logging.warning("User hasn't started the bot yet.")
    except Exception as err:
        logging.error(f"Error approving request: {err}")

# Start Command
@app.on_message(filters.private & filters.command("start"))
async def start(_, message: Message):
    user = message.from_user
    try:
        await app.get_chat_member(cfg.CHID, user.id)
    except UserNotParticipant:
        try:
            invite_link = await app.create_chat_invite_link(cfg.CHID)
        except errors.ChatAdminRequired:
            await message.reply("Make sure I am an admin in your channel.")
            return
        
        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("Join Updates Channel", url=invite_link.invite_link),
                InlineKeyboardButton("Check Again", callback_data="check_subscription")
            ]]
        )
        await message.reply(
            "⚠️ Access Denied! ⚠️\n\nPlease join my updates channel to use this bot. After joining, click 'Check Again'.",
            reply_markup=keyboard
        )
        return
    
    # Welcome Message
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Channel", url="https://t.me/World_Fastest_Bots"),
            InlineKeyboardButton("Support", url="https://t.me/Fastest_Bots_Support")
        ]]
    )
    add_user(user.id)
    await message.reply_photo(
        "https://i.ibb.co/6wQZY57/photo-2024-12-30-17-57-41-7454266052625563676.jpg",
        caption=f"Hello {user.mention}!\nI am an auto-approve bot. Add me to your group or channel as an admin with the 'Add Members' permission.",
        reply_markup=keyboard
    )

# Check Subscription Callback
@app.on_callback_query(filters.regex("check_subscription"))
async def check_subscription(_, callback: CallbackQuery):
    user = callback.from_user
    try:
        await app.get_chat_member(cfg.CHID, user.id)
        await callback.edit_message_text(
            f"Hello {user.mention}!\nSubscription verified. You can now use this bot."
        )
    except UserNotParticipant:
        await callback.answer("You have not joined the updates channel.", show_alert=True)

# User Stats Command
@app.on_message(filters.command("users") & filters.user(cfg.SUDO))
async def user_stats(_, message: Message):
    total_users = all_users()
    total_groups = all_groups()
    await message.reply_text(
        f"📊 Bot Stats:\n🙋‍♂️ Users: {total_users}\n👥 Groups: {total_groups}\n🚀 Total: {total_users + total_groups}"
    )

# Broadcast Message
@app.on_message(filters.command("bcast") & filters.user(cfg.SUDO))
async def broadcast(_, message: Message):
    broadcast_message = message.reply_to_message
    if not broadcast_message:
        await message.reply("Reply to a message to broadcast.")
        return
    
    total, success, failed = 0, 0, 0
    for user in users.find():
        total += 1
        try:
            await broadcast_message.copy(int(user["user_id"]))
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except errors.UserIsBlocked:
            remove_user(user["user_id"])
        except Exception:
            failed += 1
    
    await message.reply(f"✅ Sent: {success}\n❌ Failed: {failed}\n👥 Total: {total}")

if __name__ == "__main__":
    logging.info("Bot started.")
    app.run()
