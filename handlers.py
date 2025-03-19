from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import ADMIN_IDS
from database import add_user, update_request_count, get_stats, get_users, add_admin, get_admins, remove_admin, add_channel, remove_channel, get_channels
from utils import download_social_media_video, process_youtube_video, shazam_video, shazam_audio, check_membership
import os

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    if not await check_membership(context.bot, user_id):
        channels = get_channels()
        keyboard = []
        for chat_id, chat_type in channels:
            keyboard.append([InlineKeyboardButton(f"{chat_type.capitalize()}ga qo‘shilish", url=f"https://t.me/{chat_id[1:]}")])
        keyboard.append([InlineKeyboardButton("Tekshirish", callback_data="check_membership")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Iltimos, quyidagi kanal va guruhlarga a'zo bo'ling!",
            reply_markup=reply_markup
        )
        return
    keyboard = [
        [InlineKeyboardButton("URL yuborish", callback_data="send_url")],
        [InlineKeyboardButton("Video yuklash", callback_data="upload_video")],
        [InlineKeyboardButton("Audio yuklash", callback_data="upload_audio")],
    ]
    if user_id in ADMIN_IDS or user_id in get_admins():
        keyboard.append([InlineKeyboardButton("Admin panel", callback_data="admin_panel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Salom! Quyidagi tugmalardan foydalaning:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "check_membership":
        if await check_membership(context.bot, user_id):
            keyboard = [
                [InlineKeyboardButton("URL yuborish", callback_data="send_url")],
                [InlineKeyboardButton("Video yuklash", callback_data="upload_video")],
                [InlineKeyboardButton("Audio yuklash", callback_data="upload_audio")],
            ]
            if user_id in ADMIN_IDS or user_id in get_admins():
                keyboard.append([InlineKeyboardButton("Admin panel", callback_data="admin_panel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Tabriklaymiz! Endi botdan foydalanishingiz mumkin:", reply_markup=reply_markup)
        else:
            await query.edit_message_text("Hali ham kanal yoki guruhga a’zo bo‘lmagansiz. Qo‘shiling va qayta tekshiring.")
    elif query.data == "send_url":
        await query.edit_message_text("URL yuboring:")
    elif query.data == "upload_video":
        await query.edit_message_text("Video faylni yuboring:")
    elif query.data == "upload_audio":
        await query.edit_message_text("Audio faylni yuboring:")
    elif query.data == "admin_panel":
        if user_id in ADMIN_IDS or user_id in get_admins():
            keyboard = [
                [InlineKeyboardButton("Reklama yuborish", callback_data="send_ad")],
                [InlineKeyboardButton("Foydalanuvchilarni ko‘rish", callback_data="list_users")],
                [InlineKeyboardButton("Admin qo‘shish", callback_data="add_admin")],
                [InlineKeyboardButton("Admin o‘chirish", callback_data="remove_admin")],
                [InlineKeyboardButton("Adminlarni ko‘rish", callback_data="list_admins")],
                [InlineKeyboardButton("Statistika", callback_data="stats")],
                [InlineKeyboardButton("Kanal/Guruh qo‘shish", callback_data="add_channel")],
                [InlineKeyboardButton("Kanal/Guruh o‘chirish", callback_data="remove_channel")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Admin panel:", reply_markup=reply_markup)
        else:
            await query.edit_message_text("Siz admin emassiz!")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(context.bot, user_id):
        await update.message.reply_text("Kanal va guruhga a'zo bo'ling!")
        return
    url = update.message.text
    update_request_count(user_id)
    
    if "youtube.com" in url or "youtu.be" in url:
        result = process_youtube_video(url)
        if os.path.exists(result):
            with open(result, "rb") as video:
                await update.message.reply_video(video)
            os.remove(result)
        else:
            await update.message.reply_text(f"Yuklab olish uchun URL: {result}")
    else:
        video_url = download_social_media_video(url)
        if video_url:
            await update.message.reply_video(video_url)
        else:
            await update.message.reply_text("Video yuklab olinmadi, URLni tekshiring.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(context.bot, user_id):
        await update.message.reply_text("Kanal va guruhga a'zo bo'ling!")
        return
    update_request_count(user_id)
    file = await update.message.video.get_file()
    await file.download_to_drive("temp_video.mp4")
    title, artist = await shazam_video("temp_video.mp4")
    os.remove("temp_video.mp4")
    if title and artist:
        await update.message.reply_text(f"Qo'shiq: {title}\nMuallif: {artist}")
    else:
        await update.message.reply_text("Musiqa topilmadi.")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(context.bot, user_id):
        await update.message.reply_text("Kanal va guruhga a'zo bo'ling!")
        return
    update_request_count(user_id)
    file = await update.message.audio.get_file()
    await file.download_to_drive("temp_audio.mp3")
    title, artist = await shazam_audio("temp_audio.mp3")
    os.remove("temp_audio.mp3")
    if title and artist:
        await update.message.reply_text(f"Qo'shiq: {title}\nMuallif: {artist}")
    else:
        await update.message.reply_text("Musiqa topilmadi.")

# Admin handlers
async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        await query.edit_message_text("Siz admin emassiz!")
        return

    if query.data == "send_ad":
        await query.edit_message_text("Reklama uchun xabarni yuboring (reply qilib yoki to‘g‘ridan-to‘g‘ri):")
    elif query.data == "list_users":
        users = get_users()
        text = "\n".join([f"ID: {u[0]}, So'rovlar: {u[1]}" for u in users])
        await query.edit_message_text(text or "Foydalanuvchilar yo'q.")
    elif query.data == "add_admin":
        await query.edit_message_text("Yangi admin ID’sini yuboring:")
    elif query.data == "remove_admin":
        admins = get_admins()
        keyboard = [[InlineKeyboardButton(str(admin), callback_data=f"rm_admin_{admin}")] for admin in admins]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("O‘chiriladigan adminni tanlang:", reply_markup=reply_markup)
    elif query.data == "list_admins":
        admins = get_admins()
        text = "\n".join([str(admin) for admin in admins])
        await query.edit_message_text(text or "Qo'shimcha adminlar yo'q.")
    elif query.data == "stats":
        daily, monthly, yearly = get_stats()
        await query.edit_message_text(f"Kunlik: {daily}\nOylik: {monthly}\nYillik: {yearly}")
    elif query.data.startswith("rm_admin_"):
        admin_id = int(query.data.split("_")[2])
        remove_admin(admin_id)
        await query.edit_message_text(f"Admin {admin_id} o‘chirildi.")
    elif query.data == "add_channel":
        await query.edit_message_text("Kanal yoki guruh nomini yuboring (masalan, @MyChannel):")
    elif query.data == "remove_channel":
        channels = get_channels()
        keyboard = [[InlineKeyboardButton(chat_id, callback_data=f"rm_channel_{chat_id}")] for chat_id, _ in channels]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("O‘chiriladigan kanal/guruhni tanlang:", reply_markup=reply_markup)
    elif query.data.startswith("rm_channel_"):
        chat_id = query.data.split("_")[2]
        remove_channel(chat_id)
        await query.edit_message_text(f"{chat_id} o‘chirildi.")

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        return
    text = update.message.text
    if text.startswith("@"):
        chat_type = "channel" if "channel" in text.lower() else "group"
        add_channel(text, chat_type)
        await update.message.reply_text(f"{text} qo‘shildi ({chat_type}).")
    elif text.isdigit():
        add_admin(int(text))
        await update.message.reply_text(f"Admin {text} qo‘shildi.")

async def send_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        return
    if update.message.reply_to_message:
        msg = update.message.reply_to_message
        keyboard = [
            [InlineKeyboardButton("Hammaga yuborish", callback_data="ad_all")],
            [InlineKeyboardButton("Faqat aktivlarga", callback_data="ad_active")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Reklama qayerda tarqatilsin?", reply_markup=reply_markup)
        context.user_data["ad_message"] = msg.message_id
    else:
        await update.message.reply_text("Reklamani reply qilib yuboring!")

async def ad_distribution_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        return
    ad_msg_id = context.user_data.get("ad_message")
    if not ad_msg_id:
        await query.edit_message_text("Xatolik: Reklama xabari topilmadi.")
        return
    users = get_users()
    active_users = [u[0] for u in users if u[1] > 0]
    target_users = [u[0] for u in users] if query.data == "ad_all" else active_users
    for user_id in target_users:
        try:
            await context.bot.copy_message(user_id, update.effective_chat.id, ad_msg_id)
        except:
            continue
    await query.edit_message_text(f"Reklama {len(target_users)} foydalanuvchiga yuborildi!")

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    app.add_handler(CallbackQueryHandler(admin_button_handler, pattern="^(send_ad|list_users|add_admin|remove_admin|list_admins|stats|add_channel|remove_channel|rm_admin_.*|rm_channel_.*)$"))
    app.add_handler(MessageHandler(filters.REPLY & filters.User(ADMIN_IDS), send_ad))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_IDS), handle_admin_input))
    app.add_handler(CallbackQueryHandler(ad_distribution_handler, pattern="^ad_"))