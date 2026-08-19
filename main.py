import os
import threading
import asyncio
import logging
import re
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# ----------------- FLASK SERVER (Render Keep-Alive) -----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "VIP Proxy Bot is Running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ----------------- BOT CONFIGURATION -----------------
TOKEN = "8628179351:AAHOlbKJTDbsAUPN2nH409VQbCVpCnD57KE"
PRIMARY_ADMIN_ID = 8991828975      # মূল অ্যাডমিন (আপনার আইডি)
ALL_ADMINS = [PRIMARY_ADMIN_ID]

CHANNEL_USERNAME = "@personel_3452"   # রিকোয়ার্ড চ্যানেল

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

PRODUCTS = {
    "Owl Proxy 200MB": {"price": 5, "stock_list": [], "type": "proxy"},
    "Owl Proxy 600MB": {"price": 25, "type": "proxy_bundle", "count": 3}
}

USER_BALANCES = {} 
USER_STATES = {}   
USER_TEMP_DATA = {} 
ALL_USERS = set()
BANNED_USERS = set()

async def check_subscription(user_id, context):
    if user_id in ALL_ADMINS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except TelegramError:
        return False

# কিবোর্ড মেনু
def get_main_keyboard(user_id):
    keyboard = [
        [KeyboardButton("🛍️ 𝘽𝙐𝙔 𝙋𝙍𝙊𝙓𝙔 / 𝙎𝙀𝙍𝙑𝙄𝘾𝙀"), KeyboardButton("💳 𝘿𝙀𝙋𝙊𝙎𝙄𝙏 𝙈𝙊𝙉𝙀𝙔")],
        [KeyboardButton("💎 𝙈𝙔 𝘼𝘾𝘾𝙊𝙐𝙉𝙏 & 𝘽𝘼𝙇𝘼𝙉𝘾𝙀"), KeyboardButton("⚡ 𝙇𝙄𝙑𝙀 𝙎𝙐𝙋𝙋𝙊𝙍𝙏")]
    ]
    if user_id in ALL_ADMINS:
        keyboard.append([KeyboardButton("👑 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇")])
        
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_reply_keyboard():
    keyboard = [
        [KeyboardButton("📦 𝘼𝘿𝘿 𝙋𝙍𝙊𝙓𝙔 𝙎𝙏𝙊𝘾𝙆"), KeyboardButton("🏷️ 𝙀𝘿𝙄𝙏 𝙋𝙍𝙄𝘾𝙀")],
        [KeyboardButton("🛠️ 𝘼𝘿𝘿 𝙉𝙀𝙒 𝙎𝙀𝙍𝙑𝙄𝘾𝙀"), KeyboardButton("📢 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏 𝙈𝙀𝙎𝙎𝘼𝙂𝙀")],
        [KeyboardButton("🚫 𝘽𝘼𝙉 / 𝙐𝙉𝘽𝘼𝙉 𝙐𝙎𝙀𝙍"), KeyboardButton("🔙 𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝙀𝙉𝙐")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    ALL_USERS.add(user_id)

    if user_id in BANNED_USERS:
        await update.message.reply_text("🚫 অ্যাক্সেস ডিনাইড! আপনি এই বট থেকে ব্যান আছেন।")
        return

    is_joined = await check_subscription(user_id, context)
    
    if not is_joined:
        join_alert = (
            "╭━━━━━━━━━━━━━━━━━━━━━━━━╮\n"
            "   ⚠️  আমাদের চ্যানেলে জয়েন করুন  ⚠️\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"👋 হ্যালো {user_name}!\n\n"
            "বটটি ব্যবহার করতে হলে আমাদের অফিশিয়াল চ্যানেলে যুক্ত হতে হবে।\n\n"
            f"📢 অফিশিয়াল চ্যানেল: {CHANNEL_USERNAME}\n\n"
            "👇 নিচের বাটনে ক্লিক করে জয়েন করে ভেরিফাই করুন:"
        )
        join_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 𝙅𝙊𝙄𝙉 𝘾𝙃𝘼𝙉𝙉𝙀𝙇", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("⚡ 𝙑𝙀𝙍𝙄𝙁𝙔 𝙅𝙊𝙄𝙉", callback_data="verify_join")]
        ])
        await update.message.reply_text(join_alert, reply_markup=join_markup)
        return

    welcome_text = (
        "╔═════════════════════════╗\n"
        "   👑  𝙏𝙀𝘼𝙈 𝙀𝙇𝙄𝙏𝙀 𝙓 𝙋𝙍𝙊𝙓𝙔  👑\n"
        "╚═════════════════════════╝\n\n"
        f"🔥 স্বাগতম, {user_name}!\n"
        "সবচেয়ে ফাস্ট ও প্রিমিয়াম প্রক্সি এবং সার্ভিস কিনুন এক ক্লিকে। ⚡\n\n"
        "💳 পেমেন্ট মাধ্যম (ট্যাপ করে কপি করুন):\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 বিকাশ (Personal): `01317404705`\n"
        "🔸 নগদ (Personal): `01917404724`\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "☎️ সাপোর্ট: @owner_joshim\n\n"
        "👇 নিচের কিবোর্ড মেনু থেকে আপনার অপশন সিলেক্ট করুন:"
    )
    await update.message.reply_text(
        welcome_text, 
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown"
    )

# ডিপোজিট অ্যাপ্রুভ / রিজেক্ট বাটন হ্যান্ডলার
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    if data == "verify_join":
        is_joined = await check_subscription(user_id, context)
        if is_joined:
            try:
                await query.message.delete()
            except:
                pass
            welcome_text = (
                "╔═════════════════════════╗\n"
                "   👑  𝙏𝙀𝘼𝙈 𝙀𝙇𝙄𝙏𝙀 𝙓 𝙋𝙍𝙊𝙓𝙔  👑\n"
                "╚═════════════════════════╝\n\n"
                "✅ ভেরিফিকেশন সফল হয়েছে! 🎉\n\n"
                "👇 নিচের মেনু থেকে আপনার সেবাটি বেছে নিন:"
            )
            await context.bot.send_message(
                chat_id=user_id,
                text=welcome_text,
                reply_markup=get_main_keyboard(user_id)
            )
        else:
            await query.answer("❌ আপনি এখনো চ্যানেলে জয়েন করেননি! আগে জয়েন করুন।", show_alert=True)

    elif data.startswith("approve_"):
        if user_id not in ALL_ADMINS:
            await query.answer("❌ আপনি অ্যাডমিন নন!", show_alert=True)
            return
        parts = data.split("_")
        target_user = int(parts[1])
        amount = int(parts[2])

        if target_user not in USER_BALANCES:
            USER_BALANCES[target_user] = 0
        USER_BALANCES[target_user] += amount

        new_caption = f"{query.message.caption}\n\n━━━━━━━━━━━━━━━━━━━━\n✅ স্ট্যাটাস: Approved by Admin\n💰 যোগ করা হয়েছে: ৳{amount} BDT"
        try:
            await query.edit_message_caption(caption=new_caption)
        except Exception as e:
            print(f"Caption error: {e}")

        try:
            await context.bot.send_message(
                chat_id=target_user,
                text=(
                    "╔═════════════════════════╗\n"
                    "   🎉  ডিপোজিট সফল হয়েছে  🎉\n"
                    "╚═════════════════════════╝\n\n"
                    f"💎 জমা হয়েছে: ৳{amount} BDT\n"
                    f"💰 বর্তমান ব্যালেন্স: ৳{USER_BALANCES[target_user]} BDT\n\n"
                    "✨ ধন্যবাদ আমাদের সাথে থাকার জন্য!"
                )
            )
        except:
            pass
        await query.answer("✅ ব্যালেন্স সফলভাবে যোগ করা হয়েছে!")

    elif data.startswith("reject_"):
        if user_id not in ALL_ADMINS:
            await query.answer("❌ আপনি অ্যাডমিন নন!", show_alert=True)
            return
        parts = data.split("_")
        target_user = int(parts[1])

        new_caption = f"{query.message.caption}\n\n━━━━━━━━━━━━━━━━━━━━\n❌ স্ট্যাটাস: Rejected by Admin"
        try:
            await query.edit_message_caption(caption=new_caption)
        except Exception as e:
            print(f"Caption error: {e}")

        try:
            await context.bot.send_message(
                chat_id=target_user,
                text=(
                    "╭━━━━━━━━━━━━━━━━━━━━━━━━╮\n"
                    "   ❌  ডিপোজিট বাতিল হয়েছে  ❌\n"
                    "╰━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
                    "⚠️ দুঃখিত! আপনার পেমেন্ট ভেরিফাই করা সম্ভব হয়নি।\n"
                    "অনুগ্রহ করে সঠিক তথ্য দিয়ে পুনরায় চেষ্টা করুন অথবা সাপোর্টে যোগাযোগ করুন।"
                )
            )
        except:
            pass
        await query.answer("❌ ডিপোজিট বাতিল করা হয়েছে!")

# মেসেজ ও ফটো হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ALL_USERS.add(user_id)

    if user_id in BANNED_USERS:
        await update.message.reply_text("🚫 অ্যাক্সেস ডিনাইড! আপনি এই বট থেকে ব্যান আছেন।")
        return

    # --- ফটো হ্যান্ডলিং (স্ক্রিনশট গ্রহণ) ---
    if update.message.photo:
        if USER_STATES.get(user_id) == "waiting_for_deposit_screenshot":
            amount_sent = USER_TEMP_DATA.get(user_id, "0")
            photo_file_id = update.message.photo[-1].file_id
            user_mention = f"@{update.effective_user.username}" if update.effective_user.username else update.effective_user.first_name

            USER_STATES[user_id] = None  
            if user_id in USER_TEMP_DATA:
                del USER_TEMP_DATA[user_id]

            admin_alert = (
                "╔═════════════════════════╗\n"
                "   🔔  নতুন ডিপোজিট রিকোয়েস্ট  🔔\n"
                "╚═════════════════════════╝\n\n"
                f"👤 ইউজার: {user_mention} (`{user_id}`)\n"
                f"💰 টাকার পরিমাণ: ৳{amount_sent} BDT\n\n"
                "👇 নিচের বাটন চেপে অ্যাপ্রুভ বা রিজেক্ট করুন:"
            )
            
            admin_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"✅ Approve ৳{amount_sent}", callback_data=f"approve_{user_id}_{amount_sent}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
                ]
            ])

            # অ্যাডমিনের কাছে স্ক্রিনশট পাঠানো
            try:
                await context.bot.send_photo(
                    chat_id=PRIMARY_ADMIN_ID, 
                    photo=photo_file_id, 
                    caption=admin_alert, 
                    reply_markup=admin_markup,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logging.error(f"Error sending photo to admin: {e}")

            await update.message.reply_text(
                "⏳ আপনার ডিপোজিট রিকোয়েস্টটি অ্যাডমিনের কাছে পাঠানো হয়েছে! অ্যাডমিন ভেরিফাই করে দ্রুত ব্যালেন্স যুক্ত করে দেবেন। ✨",
                reply_markup=get_main_keyboard(user_id)
            )
            return
        else:
            return

    text = update.message.text if update.message.text else ""

    if text in ["❌ 𝘾𝘼𝙉𝘾𝙀𝙇 & 𝘽𝘼𝘾𝙆", "❌ Cancel & Back", "🔙 𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝙀𝙉𝙐", "⬅️ Back to Menu"]:
        USER_STATES[user_id] = None
        if user_id in USER_TEMP_DATA:
            del USER_TEMP_DATA[user_id]
        await update.message.reply_text("🏠 প্রধান মেনুতে ফিরে আসা হয়েছে:", reply_markup=get_main_keyboard(user_id))
        return

    # অ্যাডমিন মেনু
    if user_id in ALL_ADMINS:
        if text in ["👑 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇", "⚙️ Admin Panel"]:
            await update.message.reply_text(
                "╔═════════════════════════╗\n"
                "   👑  এডমিন কন্ট্রোল সেন্টার  👑\n"
                "╚═════════════════════════╝\n\n"
                "নিচের অপশনগুলো থেকে আপনার কাজ সিলেক্ট করুন 👇",
                reply_markup=get_admin_reply_keyboard()
            )
            return

        elif text in ["📦 𝘼𝘿𝘿 𝙋𝙍𝙊𝙓𝙔 𝙎𝙏𝙊𝘾𝙆", "➕ Add Proxy Stock"]:
            USER_STATES[user_id] = "waiting_for_admin_proxy_stock"
            await update.message.reply_text(
                "📦 নতুন প্রক্সি স্টক যোগ করুন:\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "নিচের ফরমেটে লিখে পাঠান:\n\n"
                "`Host: your_ip`\n`Port: your_port`\n`Username: your_user`\n`Password: your_pass`",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇 & 𝘽𝘼𝘾𝙆")]], resize_keyboard=True),
                parse_mode="Markdown"
            )
            return

        elif text in ["🏷️ 𝙀𝘿𝙄𝙏 𝙋𝙍𝙄𝘾𝙀", "💰 Change Price"]:
            USER_STATES[user_id] = "waiting_for_admin_price_change"
            await update.message.reply_text(
                "🏷️ প্রাইস পরিবর্তন করুন:\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "নাম এবং নতুন দাম লিখে পাঠান।\n"
                "উদাহরণ: `200MB 6` অথবা `600MB 20`",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇 & 𝘽𝘼𝘾𝙆")]], resize_keyboard=True),
                parse_mode="Markdown"
            )
            return

        elif text in ["🛠️ 𝘼𝘿𝘿 𝙉𝙀𝙒 𝙎𝙀𝙍𝙑𝙄𝘾𝙀", "🛠️ Add New Service"]:
            USER_STATES[user_id] = "waiting_for_admin_new_service"
            await update.message.reply_text(
                "🛠️ নতুন সার্ভিস যুক্ত করুন:\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "প্রথম লাইনে নাম ও দাম এবং পরের লাইনে তথ্য দিন:\n\n"
                "উদাহরণ:\n`NordVPN 50`\n`user:pass | Expire: 30 days`",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇 & 𝘽𝘼𝘾𝙆")]], resize_keyboard=True),
                parse_mode="Markdown"
            )
            return

        elif text in ["📢 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏 𝙈𝙀𝙎𝙎𝘼𝙂𝙀", "📢 Broadcast Message"]:
            USER_STATES[user_id] = "waiting_for_admin_broadcast_msg"
            await update.message.reply_text(
                "📢 ব্রডকাস্ট নোটিশ পাঠান:\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "সকল ইউজারকে যে নোটিশ পাঠাতে চান তা লিখে পাঠান:",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇 & 𝘽𝘼𝘾𝙆")]], resize_keyboard=True)
            )
            return

        elif text in ["🚫 𝘽𝘼𝙉 / 𝙐𝙉𝘽𝘼𝙉 𝙐𝙎𝙀𝙍", "🚫 Ban / Unban User"]:
            USER_STATES[user_id] = "waiting_for_ban_action"
            await update.message.reply_text(
                "🚫 ইউজার ব্যান/আনব্যান করুন:\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "• ব্যান করতে: `ban 123456789`\n"
                "• আনব্যান করতে: `unban 123456789`",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇 & 𝘽𝘼𝘾𝙆")]], resize_keyboard=True),
                parse_mode="Markdown"
            )
            return

    # অ্যাডমিন স্টেট প্রসেসিং
    current_state = USER_STATES.get(user_id)
    if user_id in ALL_ADMINS and current_state:
        if current_state == "waiting_for_admin_proxy_stock":
            try:
                blocks = re.split(r'\n\s*\d+\.\s*\n', text)
                if len(blocks) <= 1:
                    blocks = [text]

                added_count = 0
                for block in blocks:
                    host_match = re.search(r'(?:SERVER|Host|🌐.*?Host|🌐.*?SERVER)\s*[:\-]?\s*([^\n]+)', block, re.IGNORECASE)
                    port_match = re.search(r'(?:PORT|Port|🔌.*?Port|🔌.*?PORT)\s*[:\-]?\s*([^\n]+)', block, re.IGNORECASE)
                    user_match = re.search(r'(?:UN|Username|👤.*?Username|👤.*?UN)\s*[:\-]?\s*([^\n]+)', block, re.IGNORECASE)
                    pwd_match = re.search(r'(?:PASS|Password|🔑.*?Password|🔑.*?PASS)\s*[:\-]?\s*([^\n]+)', block, re.IGNORECASE)

                    if host_match and port_match and user_match and pwd_match:
                        proxy_data = {
                            "id": f"OWL-{added_count+len(PRODUCTS['Owl Proxy 200MB']['stock_list'])+1}",
                            "host": host_match.group(1).strip(),
                            "port": port_match.group(1).strip(),
                            "user": user_match.group(1).strip(),
                            "pwd": pwd_match.group(1).strip()
                        }
                        PRODUCTS["Owl Proxy 200MB"]["stock_list"].append(proxy_data)
                        added_count += 1

                USER_STATES[user_id] = None
                if added_count > 0:
                    total_stock = len(PRODUCTS["Owl Proxy 200MB"]["stock_list"])
                    await update.message.reply_text(f"✅ {added_count}টি প্রক্সি সফলভাবে স্টকে যোগ হয়েছে!\n📦 মোট স্টক: {total_stock} টি", reply_markup=get_admin_reply_keyboard())
                else:
                    await update.message.reply_text("⚠️ ফরম্যাট সঠিক হয়নি! দয়া করে সঠিক নিয়মে দিন।", reply_markup=get_admin_reply_keyboard())
            except Exception as e:
                await update.message.reply_text(f"⚠️ ত্রুটি: {e}", reply_markup=get_admin_reply_keyboard())
            return

        elif current_state == "waiting_for_admin_price_change":
            try:
                args = text.split(" ")
                if len(args) < 2:
                    await update.message.reply_text("⚠️ উদাহরণ অনুযায়ী লিখুন: `200MB 5`", reply_markup=get_admin_reply_keyboard())
                    return
                target_key = args[0].lower()
                new_price = int(args[1])
                
                updated = False
                for p_name in PRODUCTS:
                    if target_key in p_name.lower():
                        PRODUCTS[p_name]["price"] = new_price
                        updated = True
                        await update.message.reply_text(f"✅ {p_name} এর নতুন দাম: ৳{new_price} BDT", reply_markup=get_admin_reply_keyboard())
                        break
                if not updated:
                    await update.message.reply_text("❌ এই নামের কোনো প্রোডাক্ট পাওয়া যায়নি!", reply_markup=get_admin_reply_keyboard())
                USER_STATES[user_id] = None
            except Exception as e:
                await update.message.reply_text(f"⚠️ ত্রুটি: {e}", reply_markup=get_admin_reply_keyboard())
            return

        elif current_state == "waiting_for_admin_new_service":
            try:
                text_lines = text.split("\n")
                first_line = text_lines[0].strip()
                parts = first_line.rsplit(" ", 1)
                
                if len(parts) < 2:
                    await update.message.reply_text("⚠️ সঠিক ফরম্যাটে লিখুন:\n`NordVPN 50`", reply_markup=get_admin_reply_keyboard())
                    return
                    
                service_name = parts[0].strip()
                service_price = int(parts[1])
                service_stock_item = "\n".join(text_lines[1:]).strip()
                
                full_service_name = f"Service: {service_name}"
                if full_service_name not in PRODUCTS:
                    PRODUCTS[full_service_name] = {
                        "price": service_price,
                        "stock_list": [],
                        "type": "custom_service"
                    }
                if service_stock_item:
                    PRODUCTS[full_service_name]["stock_list"].append(service_stock_item)
                
                USER_STATES[user_id] = None
                await update.message.reply_text(f"✅ নতুন সার্ভিস {service_name} (৳{service_price} BDT) সফলভাবে তৈরি হয়েছে!", reply_markup=get_admin_reply_keyboard())
            except Exception as e:
                await update.message.reply_text(f"⚠️ ত্রুটি: {e}", reply_markup=get_admin_reply_keyboard())
            return

        elif current_state == "waiting_for_admin_broadcast_msg":
            USER_STATES[user_id] = None
            sent_count = 0
            fail_count = 0
            status_msg = await update.message.reply_text("📢 ব্রডকাস্ট পাঠানো হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন...")
            
            for uid in ALL_USERS:
                try:
                    await context.bot.send_message(
                        chat_id=uid, 
                        text=f"╔═════════════════════════╗\n   📢  অফিসিয়াল নোটিশ  📢\n╚═════════════════════════╝\n\n{text}"
                    )
                    sent_count += 1
                    await asyncio.sleep(0.1)
                except:
                    fail_count += 1
            await status_msg.edit_text(f"✅ ব্রডকাস্ট সম্পন্ন!\n\n📤 পাঠানো হয়েছে: {sent_count} জন\n❌ ব্যর্থ: {fail_count} জন", reply_markup=get_admin_reply_keyboard())
            return

        elif current_state == "waiting_for_ban_action":
            try:
                parts = text.split(" ")
                if len(parts) < 2:
                    await update.message.reply_text("⚠️ ফরম্যাট: `ban 123456789`", reply_markup=get_admin_reply_keyboard())
                    return
                
                action = parts[0].lower()
                target_uid = int(parts[1])
                USER_STATES[user_id] = None

                if action == "ban":
                    if target_uid in ALL_ADMINS:
                        await update.message.reply_text("❌ অ্যাডমিনকে ব্যান করা যাবে না!", reply_markup=get_admin_reply_keyboard())
                        return
                    BANNED_USERS.add(target_uid)
                    await update.message.reply_text(f"✅ ইউজার আইডি {target_uid} ব্যান করা হয়েছে।", reply_markup=get_admin_reply_keyboard())
                elif action == "unban":
                    if target_uid in BANNED_USERS:
                        BANNED_USERS.remove(target_uid)
                        await update.message.reply_text(f"✅ ইউজার আইডি {target_uid} আনব্যান করা হয়েছে।", reply_markup=get_admin_reply_keyboard())
                    else:
                        await update.message.reply_text(f"⚠️ ইউজার আইডি {target_uid} ব্যান তালিকায় নেই!", reply_markup=get_admin_reply_keyboard())
            except Exception as e:
                await update.message.reply_text(f"⚠️ ত্রুটি: {e}", reply_markup=get_admin_reply_keyboard())
            return

    # ইউজার ডিপোজিট অ্যামাউন্ট ইনপুট
    if USER_STATES.get(user_id) == "waiting_for_deposit_amount":
        if not text or not text.isdigit():
            await update.message.reply_text("⚠️ দয়া করে সঠিক সংখ্যায় অ্যামাউন্ট লিখুন (যেমন: 20 বা 50):", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇 & 𝘽𝘼𝘾𝙆")]], resize_keyboard=True))
            return
        
        amount_val = int(text)
        if amount_val < 10:
            await update.message.reply_text("❌ সর্বনিম্ন ডিপোজিট ৳১০ BDT!", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇 & 𝘽𝘼𝘾𝙆")]], resize_keyboard=True))
            return

        USER_TEMP_DATA[user_id] = text
        USER_STATES[user_id] = "waiting_for_deposit_screenshot"
        
        await update.message.reply_text(
            f"✅ আপনি লিখেছেন: ৳{text} BDT\n\n📸 এবার আপনার পেমেন্টের স্ক্রিনশট (Screenshot) এই চ্যাটে পাঠান।",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇 & 𝘽𝘼𝘾𝙆")]], resize_keyboard=True)
        )
        return

    is_joined = await check_subscription(user_id, context)
    if not is_joined:
        join_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 𝙅𝙊𝙄𝙉 𝘾𝙃𝘼𝙉𝙉𝙀𝙇", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("⚡ 𝙑𝙀𝙍𝙄𝙁𝙔 𝙅𝙊𝙄𝙉", callback_data="verify_join")]
        ])
        await update.message.reply_text("❌ বট ব্যবহার করতে হলে প্রথমে চ্যানেলে জয়েন করতে হবে!", reply_markup=join_markup)
        return

    if user_id not in USER_BALANCES:
        USER_BALANCES[user_id] = 0

    # শপ মেনু
    if text in ["🛍️ 𝘽𝙐𝙔 𝙋𝙍𝙊𝙓𝙔 / 𝙎𝙀𝙍𝙑𝙄𝘾𝙀", "🛍️ BUY PROXY / SERVICE"]:
        shop_text = (
            "╔═════════════════════════╗\n"
            "   🛒  𝙋𝙍𝙊𝙓𝙔 & 𝙎𝙀𝙍𝙑𝙄𝘾𝙀 𝙎𝙏𝙊𝙍𝙀  🛒\n"
            "╚═════════════════════════╝\n\n"
        )
        kb_buttons = []
        for p_name, p_info in PRODUCTS.items():
            if p_info["type"] == "proxy":
                stock_count = len(p_info["stock_list"])
                shop_text += f"🔹 {p_name}\n   💰 প্রাইস: ৳{p_info['price']} BDT | 📦 স্টক: {stock_count} টি\n\n"
                kb_buttons.append([KeyboardButton(f"⚡ 𝘽𝙪𝙮 {p_name} (৳{p_info['price']})")])
            elif p_info["type"] == "proxy_bundle":
                stock_count = len(PRODUCTS.get("Owl Proxy 200MB", {}).get("stock_list", [])) // 3
                shop_text += f"🔹 {p_name} (৩টি প্যাক)\n   💰 প্রাইস: ৳{p_info['price']} BDT | 📦 স্টক: {stock_count} প্যাক\n\n"
                kb_buttons.append([KeyboardButton(f"⚡ 𝘽𝙪𝙮 {p_name} (৳{p_info['price']})")])
            elif p_info["type"] == "custom_service":
                stock_count = len(p_info["stock_list"])
                shop_text += f"🔹 {p_name}\n   💰 প্রাইস: ৳{p_info['price']} BDT | 📦 স্টক: {stock_count} টি\n\n"
                kb_buttons.append([KeyboardButton(f"⚡ 𝘽𝙪𝙮 {p_name} (৳{p_info['price']})")])

        shop_text += "👇 নিচের বাটন চেপে প্যাকেজ অর্ডার করুন:"
        kb_buttons.append([KeyboardButton("🔙 𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝙀𝙉𝙐")])
        
        await update.message.reply_text(shop_text, reply_markup=ReplyKeyboardMarkup(kb_buttons, resize_keyboard=True))

    elif "Buy" in text or "𝘽𝙪𝙮" in text:
        bought = False
        for p_name, p_info in PRODUCTS.items():
            if p_name in text:
                bought = True
                p_price = p_info["price"]
                
                if USER_BALANCES[user_id] < p_price:
                    await update.message.reply_text(
                        "❌ আপনার পর্যাপ্ত ব্যালেন্স নেই! অনুগ্রহ করে প্রথমে ডিপোজিট করুন।", 
                        reply_markup=get_main_keyboard(user_id)
                    )
                    return

                if p_info["type"] == "proxy":
                    if len(p_info["stock_list"]) <= 0:
                        await update.message.reply_text("⚠️ দুঃখিত! এই প্রক্সিটি বর্তমানে স্টক আউট।", reply_markup=get_main_keyboard(user_id))
                        return
                    USER_BALANCES[user_id] -= p_price
                    proxy_info = p_info["stock_list"].pop(0)
                    delivery_text = (
                        "╔═════════════════════════╗\n"
                        "   🚀  𝙋𝙍𝙊𝙓𝙔 𝘿𝙀𝙇𝙄𝙑𝙀𝙍𝙀𝘿  🚀\n"
                        "╚═════════════════════════╝\n\n"
                        f"📦 প্যাকেজ: {p_name}\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        f"🆔 ID: `{proxy_info['id']}`\n"
                        f"🌐 Host: `{proxy_info['host']}`\n"
                        f"🔌 Port: `{proxy_info['port']}`\n"
                        f"👤 User: `{proxy_info['user']}`\n"
                        f"🔑 Pass: `{proxy_info['pwd']}`\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        f"💰 অবশিষ্ট ব্যালেন্স: ৳{USER_BALANCES[user_id]} BDT\n\n"
                        "⚡ সরাসরি কানেক্ট করে ব্যবহার করুন।"
                    )
                    await update.message.reply_text(delivery_text, reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")

                elif p_info["type"] == "proxy_bundle":
                    stock_list = PRODUCTS["Owl Proxy 200MB"]["stock_list"]
                    if len(stock_list) < 3:
                        await update.message.reply_text("⚠️ দুঃখিত! বান্ডেলের জন্য পর্যাপ্ত স্টক নেই।", reply_markup=get_main_keyboard(user_id))
                        return
                    USER_BALANCES[user_id] -= p_price
                    p1 = stock_list.pop(0)
                    p2 = stock_list.pop(0)
                    p3 = stock_list.pop(0)
                    
                    for i, p_info_item in enumerate([p1, p2, p3], 1):
                        d_text = (
                            f"📦 বান্ডেল আইটেম ({i}/3):\n"
                            "━━━━━━━━━━━━━━━━━━━━\n"
                            f"🆔 ID: `{p_info_item['id']}`\n"
                            f"🌐 Host: `{p_info_item['host']}`\n"
                            f"🔌 Port: `{p_info_item['port']}`\n"
                            f"👤 User: `{p_info_item['user']}`\n"
                            f"🔑 Pass: `{p_info_item['pwd']}`"
                        )
                        await update.message.reply_text(d_text, parse_mode="Markdown")
                        await asyncio.sleep(0.4)
                    await update.message.reply_text(f"🎉 ৩টি প্রক্সি ডেলিভারি সম্পন্ন!\n💰 বর্তমান ব্যালেন্স: ৳{USER_BALANCES[user_id]} BDT", reply_markup=get_main_keyboard(user_id))

                elif p_info["type"] == "custom_service":
                    if len(p_info["stock_list"]) <= 0:
                        await update.message.reply_text("⚠️ দুঃখিত! সার্ভিসটি বর্তমানে স্টক আউট।", reply_markup=get_main_keyboard(user_id))
                        return
                    USER_BALANCES[user_id] -= p_price
                    item_data = p_info["stock_list"].pop(0)
                    await update.message.reply_text(
                        f"🎉 সার্ভিস ডেলিভারি সম্পন্ন:\n━━━━━━━━━━━━━━━━━━━━\n📦 {p_name}\n\n`{item_data}`\n━━━━━━━━━━━━━━━━━━━━\n💰 বর্তমান ব্যালেন্স: ৳{USER_BALANCES[user_id]} BDT",
                        reply_markup=get_main_keyboard(user_id),
                        parse_mode="Markdown"
                    )
                break

    elif text in ["💳 𝘿𝙀𝙋𝙊𝙎𝙄𝙏 𝙈𝙊𝙉𝙀𝙔", "💳 DEPOSIT MONEY"]:
        USER_STATES[user_id] = "waiting_for_deposit_amount"
        deposit_text = (
            "╔═════════════════════════╗\n"
            "   💳  ডিপোজিট / অ্যাড মানি  💳\n"
            "╚═════════════════════════╝\n\n"
            "টাকা পাঠানোর পার্সোনাল নম্বরসমূহ:\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔹 বিকাশ (Personal): `01317404705`\n"
            "🔸 নগদ (Personal): `01917404724`\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ সর্বনিম্ন ডিপোজিট: ৳১০ BDT\n\n"
            "✍️ টাকা পাঠিয়ে কত টাকা পাঠিয়েছেন তা সংখ্যায় লিখে পাঠান (যেমন: 50):"
        )
        await update.message.reply_text(deposit_text, reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇 & 𝘽𝘼𝘾𝙆")]], resize_keyboard=True), parse_mode="Markdown")

    elif text in ["💎 𝙈𝙔 𝘼𝘾𝘾𝙊𝙐𝙉𝙏 & 𝘽𝘼𝙇𝘼𝙉𝘾𝙀", "💎 MY ACCOUNT & BALANCE"]:
        bal = USER_BALANCES.get(user_id, 0)
        status_text = (
            "╔═════════════════════════╗\n"
            "   👤  ইউজার ড্যাশবোর্ড  👤\n"
            "╚═════════════════════════╝\n\n"
            f"🆔 আপনার আইডি: `{user_id}`\n"
            f"💰 বর্তমান ব্যালেন্স: ৳{bal} BDT\n"
            f"💎 ইউজার স্ট্যাটাস: Verified (VIP)\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🚀 সবচেয়ে ফাস্ট সার্ভিসের জন্য আমাদের সাথেই থাকুন!"
        )
        await update.message.reply_text(status_text, parse_mode="Markdown")

    elif text in ["⚡ 𝙇𝙄𝙑𝙀 𝙎𝙐𝙋𝙋𝙊𝙍𝙏", "⚡ LIVE SUPPORT"]:
        support_text = (
            "╔═════════════════════════╗\n"
            "   ☎️  অফিসিয়াল সাপোর্ট  ☎️\n"
            "╚═════════════════════════╝\n\n"
            "যে কোনো সমস্যা বা তথ্যের জন্য যোগাযোগ করুন:\n\n"
            "👤 অ্যাডমিন: @owner_joshim"
            "⏰ সাপোর্ট টাইম: ২৪/৭ একটিভ"
        )
        await update.message.reply_text(support_text)

    else:
        if USER_STATES.get(user_id) is None:
            await update.message.reply_text("👇 অনুগ্রহ করে নিচের কিবোর্ড মেনু থেকে অপশন নির্বাচন করুন।", reply_markup=get_main_keyboard(user_id))

def main():
    threading.Thread(target=run_web_server, daemon=True).start()

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    # টেক্সট ও ফটো দুটোই যেন সঠিকভাবে রিসিভ হয়
    application.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))

    print("👑 VIP Proxy Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
