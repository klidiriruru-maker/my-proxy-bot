import asyncio
import logging
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

TOKEN = "8628179351:AAHOlbKJTDbsAUPN2nH409VQbCVpCnD57KE"
PRIMARY_ADMIN_ID = 8991828975      # মূল অ্যাডমিন
PARTNER_ADMIN_ID = 7746201403      # পার্টনার অ্যাডমিন
ALL_ADMINS = [PRIMARY_ADMIN_ID, PARTNER_ADMIN_ID]

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
BANNED_USERS = set()  # ব্যান করা ইউজারদের আইডি সংরক্ষণ করার জন্য

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

def get_main_keyboard(user_id):
    keyboard = [
        [KeyboardButton("🛒 Buy Services / Proxy"), KeyboardButton("💰 Deposit")],
        [KeyboardButton("📦 My Stock & Balance"), KeyboardButton("📞 Support")]
    ]
    if user_id in ALL_ADMINS:
        keyboard.append([KeyboardButton("⚙️ Admin Panel")])
        
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# অ্যাডমিন প্যানেলের কিবোর্ড মেনু (Ban/Unban অপশন যুক্ত করা হয়েছে)
def get_admin_reply_keyboard():
    keyboard = [
        [KeyboardButton("➕ Add Proxy Stock"), KeyboardButton("💰 Change Price")],
        [KeyboardButton("🛠️ Add New Service"), KeyboardButton("📢 Broadcast Message")],
        [KeyboardButton("🚫 Ban / Unban User"), KeyboardButton("⬅️ Back to Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    ALL_USERS.add(user_id)

    if user_id in BANNED_USERS:
        await update.message.reply_text("❌ দুঃখিত! আপনি এই বট থেকে ব্যান (Banned) হয়েছেন।")
        return

    is_joined = await check_subscription(user_id, context)
    
    if not is_joined:
        join_alert = (
            "===============================\n"
            "          ⚠️ ALERT! ⚠️\n"
            "===============================\n\n"
            f"Hello {user_name} Vhai!\n"
            f"বট ব্যবহার করতে হলে অবশ্যই আমাদের নিচের চ্যানেলে জয়েন করতে হবে:\n{CHANNEL_USERNAME}\n\n"
            "চ্যানেলে জয়েন করার পর নিচের ইনলাইন বাটন থেকে ভেরিফাই করুন।"
        )
        join_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("✅ Verify Join", callback_data="verify_join")]
        ])
        await update.message.reply_text(join_alert, reply_markup=join_markup)
        return

    welcome_text = (
        "===============================\n"
        "   ✨ WELCOME TO FASTWORK_SELL\n"
        "===============================\n\n"
        f"Hello, {user_name} Vhai!\n"
        "Welcome to our official selling bot. 🚀\n\n"
        "💳 Payment Methods (Tap to Copy):\n"
        "🔹 Bkash (Personal): `01317404705`\n"
        "🔸 Nagad (Personal): `01917404724`\n\n"
        "📞 Support: @owner_joshim\n\n"
        "Please choose an option from the keyboard below:"
    )
    await update.message.reply_text(
        welcome_text, 
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    if data == "verify_join":
        is_joined = await check_subscription(user_id, context)
        if is_joined:
            await query.message.delete()
            welcome_text = (
                "✅ Verification Successful! 🎉\n\n"
                "===============================\n"
                "   ✨ WELCOME TO FASTWORK_SELL\n"
                "===============================\n\n"
                "Please choose an option from the keyboard below:"
            )
            await context.bot.send_message(
                chat_id=user_id,
                text=welcome_text,
                reply_markup=get_main_keyboard(user_id)
            )
        else:
            await query.answer("❌ আপনি এখনো নির্দিষ্ট চ্যানেলে জয়েন করেননি! আগে চ্যানেলে জয়েন করুন।", show_alert=True)

    elif data.startswith("approve_"):
        if user_id != PRIMARY_ADMIN_ID:
            return
        parts = data.split("_")
        target_user = int(parts[1])
        amount = int(parts[2])

        if target_user not in USER_BALANCES:
            USER_BALANCES[target_user] = 0
        USER_BALANCES[target_user] += amount

        new_caption = f"{query.message.caption}\n\n✅ Status: Approved by Admin\n💰 Added: {amount} BDT"
        try:
            await query.edit_message_caption(caption=new_caption)
        except Exception as e:
            print(f"Caption edit error: {e}")

        try:
            await context.bot.send_message(
                chat_id=target_user,
                text=f"🎉 আপনার ডিপোজিট সফলভাবে অনুমোদিত হয়েছে!\n\n💰 আপনার অ্যাকাউন্টে {amount} BDT যোগ করা হয়েছে।"
            )
        except:
            pass

    elif data.startswith("reject_"):
        if user_id != PRIMARY_ADMIN_ID:
            return
        parts = data.split("_")
        target_user = int(parts[1])

        new_caption = f"{query.message.caption}\n\n❌ Status: Rejected by Admin"
        try:
            await query.edit_message_caption(caption=new_caption)
        except Exception as e:
            print(f"Caption edit error: {e}")

        try:
            await context.bot.send_message(
                chat_id=target_user,
                text="❌ আপনার ডিপোজিট রিকোয়েস্টটি অ্যাডমিন কর্তৃক বাতিল (Rejected) করা হয়েছে!\n\nদয়া করে সঠিক তথ্য দিয়ে পুনরায় চেষ্টা করুন।"
            )
        except:
            pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text if update.message else ""
    ALL_USERS.add(user_id)

    if user_id in BANNED_USERS:
        await update.message.reply_text("❌ দুঃখিত! আপনি এই বট থেকে ব্যান (Banned) হয়েছেন।")
        return

    if text == "❌ Cancel & Back":
        USER_STATES[user_id] = None
        if user_id in USER_TEMP_DATA:
            del USER_TEMP_DATA[user_id]
        await update.message.reply_text("🏠 প্রসেস বাতিল করা হয়েছে। মূল মেনুতে ফিরে এসেছেন:", reply_markup=get_main_keyboard(user_id))
        return

    # অ্যাডমিন প্যানেল কিবোর্ড বাটন হ্যান্ডলিং
    if user_id in ALL_ADMINS:
        if text == "⚙️ Admin Panel":
            await update.message.reply_text(
                "==============================+\n"
                "       ⚙️ ADMIN PANEL\n"
                "==============================+\n\n"
                "নিচের কিবোর্ড মেনু থেকে আপনার প্রয়োজনীয় অপশন সিলেক্ট করুন 👇",
                reply_markup=get_admin_reply_keyboard()
            )
            return

        elif text == "➕ Add Proxy Stock":
            USER_STATES[user_id] = "waiting_for_admin_proxy_stock"
            await update.message.reply_text(
                "📦 **প্রক্সি স্টক অ্যাড করুন:**\n\n"
                "নিচের ফরম্যাটে প্রক্সিগুলো লিখে পাঠিয়ে দিন (এক বা একাধিক):\n\n"
                "Host: your_ip\nPort: your_port\nUsername: your_user\nPassword: your_pass",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel & Back")]], resize_keyboard=True),
                parse_mode="Markdown"
            )
            return

        elif text == "💰 Change Price":
            USER_STATES[user_id] = "waiting_for_admin_price_change"
            await update.message.reply_text(
                "💰 **প্রাইস পরিবর্তন করুন:**\n\n"
                "প্রোডাক্টের নাম এবং নতুন দাম লিখে পাঠান।\n"
                "উদাহরণ: `200MB 5` বা `600MB 20`",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel & Back")]], resize_keyboard=True),
                parse_mode="Markdown"
            )
            return

        elif text == "🛠️ Add New Service":
            USER_STATES[user_id] = "waiting_for_admin_new_service"
            await update.message.reply_text(
                "🛠️ **নতুন সার্ভিস অ্যাড করুন:**\n\n"
                "প্রথম লাইনে নাম এবং দাম লিখুন, আর পরের লাইনে স্টক/ডিটেইলস দিন।\n"
                "উদাহরণ:\n"
                "NordVPN 50\n"
                "Account: user@gmail.com pass123",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel & Back")]], resize_keyboard=True),
                parse_mode="Markdown"
            )
            return

        elif text == "📢 Broadcast Message":
            USER_STATES[user_id] = "waiting_for_admin_broadcast_msg"
            await update.message.reply_text(
                "📢 **ব্রডকাস্ট মেসেজ:**\n\n"
                "আপনি সব ব্যবহারকারীকে যে মেসেজটি পাঠাতে চান তা লিখে পাঠিয়ে দিন:",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel & Back")]], resize_keyboard=True),
                parse_mode="Markdown"
            )
            return

        elif text == "🚫 Ban / Unban User":
            USER_STATES[user_id] = "waiting_for_ban_action"
            await update.message.reply_text(
                "🚫 **ইউজার ব্যান বা আনব্যান করুন:**\n\n"
                "কমান্ড ও ইউজারের আইডি এভাবে লিখে পাঠান:\n"
                "• ব্যান করতে: `ban ইউজার_আইডি` (যেমন: `ban 123456789`)\n"
                "• আনব্যান করতে: `unban ইউজার_আইডি` (যেমন: `unban 123456789`)",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel & Back")]], resize_keyboard=True),
                parse_mode="Markdown"
            )
            return

    # অ্যাডমিন স্টেট ইনপুট প্রসেসিং
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
                    await update.message.reply_text(f"✅ সফলভাবে **{added_count}টি** প্রক্সি স্টকে যোগ করা হয়েছে!\n📦 মোট স্টক (200MB): {total_stock} টি", reply_markup=get_admin_reply_keyboard())
                else:
                    await update.message.reply_text("⚠️ ফরম্যাট সঠিক হয়নি!", reply_markup=get_admin_reply_keyboard())
            except Exception as e:
                await update.message.reply_text(f"⚠️ ত্রুটি: {e}", reply_markup=get_admin_reply_keyboard())
            return

        elif current_state == "waiting_for_admin_price_change":
            try:
                args = text.split(" ")
                if len(args) < 2:
                    await update.message.reply_text("⚠️ সঠিক নিয়মে লিখুন। যেমন: `200MB 5`", reply_markup=get_admin_reply_keyboard())
                    return
                target_key = args[0].lower()
                new_price = int(args[1])
                
                updated = False
                for p_name in PRODUCTS:
                    if target_key in p_name.lower():
                        PRODUCTS[p_name]["price"] = new_price
                        updated = True
                        await update.message.reply_text(f"✅ সফলভাবে **{p_name}**-এর নতুন দাম নির্ধারণ করা হয়েছে: {new_price} BDT", reply_markup=get_admin_reply_keyboard())
                        break
                if not updated:
                    await update.message.reply_text("❌ এই নামের কোনো প্রডাক্ট পাওয়া যায়নি!", reply_markup=get_admin_reply_keyboard())
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
                    await update.message.reply_text("⚠️ প্রথম লাইনে নাম ও দাম দিন। যেমন:\n`NordVPN 50`", reply_markup=get_admin_reply_keyboard())
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
                await update.message.reply_text(f"✅ নতুন সার্ভিস **{service_name}** ({service_price} BDT) সফলভাবে যোগ করা হয়েছে!", reply_markup=get_admin_reply_keyboard())
            except Exception as e:
                await update.message.reply_text(f"⚠️ ত্রুটি: {e}", reply_markup=get_admin_reply_keyboard())
            return

        elif current_state == "waiting_for_admin_broadcast_msg":
            USER_STATES[user_id] = None
            sent_count = 0
            fail_count = 0
            status_msg = await update.message.reply_text("📢 ব্রডকাস্ট পাঠানো শুরু হয়েছে, অপেক্ষা করুন...")
            
            for uid in ALL_USERS:
                try:
                    await context.bot.send_message(chat_id=uid, text=f"📢 **অফিশিয়াল ঘোষণা:**\n\n{text}", parse_mode="Markdown")
                    sent_count += 1
                    await asyncio.sleep(0.1)
                except:
                    fail_count += 1
            await status_msg.edit_text(f"✅ ব্রডকাস্ট সম্পন্ন!\n\n📤 সফলভাবে পাঠানো হয়েছে: {sent_count} জন\n❌ ফেইল করেছে: {fail_count} জন", reply_markup=get_admin_reply_keyboard())
            return

        elif current_state == "waiting_for_ban_action":
            try:
                parts = text.split(" ")
                if len(parts) < 2:
                    await update.message.reply_text("⚠️ সঠিক ফরম্যাটে লিখুন। যেমন: `ban 123456789` অথবা `unban 123456789`", reply_markup=get_admin_reply_keyboard())
                    return
                
                action = parts[0].lower()
                target_uid = int(parts[1])
                USER_STATES[user_id] = None

                if action == "ban":
                    if target_uid in ALL_ADMINS:
                        await update.message.reply_text("❌ কোনো অ্যাডমিনকে ব্যান করা যাবে না!", reply_markup=get_admin_reply_keyboard())
                        return
                    BANNED_USERS.add(target_uid)
                    await update.message.reply_text(f"✅ সফলভাবে ইউজার আইডি `{target_uid}`-কে ব্যান করা হয়েছে।", reply_markup=get_admin_reply_keyboard(), parse_mode="Markdown")
                elif action == "unban":
                    if target_uid in BANNED_USERS:
                        BANNED_USERS.remove(target_uid)
                        await update.message.reply_text(f"✅ সফলভাবে ইউজার আইডি `{target_uid}`-কে আনব্যান করা হয়েছে।", reply_markup=get_admin_reply_keyboard(), parse_mode="Markdown")
                    else:
                        await update.message.reply_text(f"⚠️ এই ইউজার আইডি (`{target_uid}`) ব্যান লিস্টে পাওয়া যায়নি!", reply_markup=get_admin_reply_keyboard(), parse_mode="Markdown")
                else:
                    await update.message.reply_text("❌ কমান্ড ভুল হয়েছে! `ban` অথবা `unban` লিখে ইউজার আইডি দিন।", reply_markup=get_admin_reply_keyboard())
            except Exception as e:
                await update.message.reply_text(f"⚠️ ত্রুটি: {e}", reply_markup=get_admin_reply_keyboard())
            return

    # সাধারণ ইউজার স্টেট হ্যান্ডলিং
    if USER_STATES.get(user_id) == "waiting_for_deposit_amount":
        if not text or not text.isdigit():
            await update.message.reply_text("⚠️ দয়া করে সঠিক সংখ্যায় টাকার পরিমাণ লিখুন (যেমন: 10 বা 50)", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel & Back")]], resize_keyboard=True))
            return
        
        amount_val = int(text)
        if amount_val < 10:
            await update.message.reply_text("❌ সর্বনিম্ন ডিপোজিট পরিমাণ ১০ টাকা (10 BDT)।", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel & Back")]], resize_keyboard=True))
            return

        USER_TEMP_DATA[user_id] = text
        USER_STATES[user_id] = "waiting_for_deposit_screenshot"
        
        await update.message.reply_text(
            f"✅ আপনি লিখেছেন: {text} BDT\n\n📸 এখন আপনার পেমেন্টের **স্ক্রিনশট (Screenshot)** বা ছবি এই চ্যাটে পাঠিয়ে দিন।",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel & Back")]], resize_keyboard=True)
        )
        return

    elif USER_STATES.get(user_id) == "waiting_for_deposit_screenshot":
        if not update.message.photo:
            await update.message.reply_text("⚠️ দয়া করে একটি পেমেন্টের **স্ক্রিনশট বা ছবি** আপলোড করুন।", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel & Back")]], resize_keyboard=True))
            return
        
        amount_sent = USER_TEMP_DATA.get(user_id, "Unknown")
        photo_file_id = update.message.photo[-1].file_id
        user_mention = f"@{update.effective_user.username}" if update.effective_user.username else update.effective_user.first_name

        USER_STATES[user_id] = None  
        if user_id in USER_TEMP_DATA:
            del USER_TEMP_DATA[user_id]

        admin_alert = (
            "===============================\n"
            "    🔔 NEW DEPOSIT REQUEST\n"
            "===============================\n\n"
            f"👤 User: {user_mention} ({user_id})\n"
            f"💰 Amount: {amount_sent} BDT\n\n"
            "⚠️ নিচের বাটন থেকে অ্যাপ্রুভ বা রিজেক্ট করুন:"
        )
        
        admin_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"✅ Approve {amount_sent}৳", callback_data=f"approve_{user_id}_{amount_sent}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
            ]
        ])

        try:
            await context.bot.send_photo(
                chat_id=PRIMARY_ADMIN_ID, 
                photo=photo_file_id, 
                caption=admin_alert, 
                reply_markup=admin_markup
            )
        except Exception as e:
            print(f"Admin send error: {e}")

        await update.message.reply_text(
            "⏳ আপনার ডিপোজিট রিকোয়েস্ট এবং স্ক্রিনশট অ্যাডমিনের কাছে পাঠানো হয়েছে! অনুগ্রহ করে অপেক্ষা করুন। ✨",
            reply_markup=get_main_keyboard(user_id)
        )
        return

    is_joined = await check_subscription(user_id, context)
    if not is_joined:
        join_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("✅ Verify Join", callback_data="verify_join")]
        ])
        await update.message.reply_text("❌ বট ব্যবহার করতে হলে প্রথমে নির্দিষ্ট চ্যানেলে জয়েন করতে হবে!", reply_markup=join_markup)
        return

    if user_id not in USER_BALANCES:
        USER_BALANCES[user_id] = 0

    if text == "🛒 Buy Services / Proxy":
        shop_text = (
            "===============================\n"
            "     🛒 SHOP SERVICES & PROXY\n"
            "===============================\n\n"
        )
        kb_buttons = []
        for p_name, p_info in PRODUCTS.items():
            if p_info["type"] == "proxy":
                stock_count = len(p_info["stock_list"])
                shop_text += f"🔹 {p_name}\n   💰 Price: {p_info['price']} BDT | 📦 Stock: {stock_count} units\n\n"
                kb_buttons.append([KeyboardButton(f"📦 Buy {p_name} ({p_info['price']}৳)")])
            elif p_info["type"] == "proxy_bundle":
                stock_count = len(PRODUCTS.get("Owl Proxy 200MB", {}).get("stock_list", [])) // 3
                shop_text += f"🔹 {p_name}\n   💰 Price: {p_info['price']} BDT | 📦 Stock Packs: {stock_count}\n\n"
                kb_buttons.append([KeyboardButton(f"📦 Buy {p_name} ({p_info['price']}৳)")])
            elif p_info["type"] == "custom_service":
                stock_count = len(p_info["stock_list"])
                shop_text += f"🔹 {p_name}\n   💰 Price: {p_info['price']} BDT | 📦 Stock: {stock_count} units\n\n"
                kb_buttons.append([KeyboardButton(f"📦 Buy {p_name} ({p_info['price']}৳)")])

        shop_text += "নিচের বাটনগুলো থেকে আপনার পছন্দমতো প্যাকেজ সিলেক্ট করুন 👇"
        kb_buttons.append([KeyboardButton("⬅️ Back to Menu")])
        
        await update.message.reply_text(shop_text, reply_markup=ReplyKeyboardMarkup(kb_buttons, resize_keyboard=True))

    elif text.startswith("📦 Buy "):
        bought = False
        for p_name, p_info in PRODUCTS.items():
            buy_btn_text = f"📦 Buy {p_name} ({p_info['price']}৳)"
            if text == buy_btn_text:
                bought = True
                p_price = p_info["price"]
                
                if USER_BALANCES[user_id] < p_price:
                    await update.message.reply_text("❌ পর্যাপ্ত ব্যালেন্স নেই! আগে ডিপোজিট করুন।", reply_markup=get_main_keyboard(user_id))
                    return

                if p_info["type"] == "proxy":
                    if len(p_info["stock_list"]) <= 0:
                        await update.message.reply_text("⚠️ স্টক খালি আছে!", reply_markup=get_main_keyboard(user_id))
                        return
                    USER_BALANCES[user_id] -= p_price
                    proxy_info = p_info["stock_list"].pop(0)
                    delivery_text = (
                        f"📦 Product: {p_name}\n"
                        "────────────────────────\n"
                        f"🆔 ID: {proxy_info['id']}\n"
                        f"🌐 Host: {proxy_info['host']}\n"
                        f"🔌 Port: {proxy_info['port']}\n"
                        f"👤 UN: {proxy_info['user']}\n"
                        f"🔑 PASS: {proxy_info['pwd']}\n\n"
                        f"💰 বর্তমান ব্যালেন্স: {USER_BALANCES[user_id]} BDT\n"
                        "✅ Ready to Connect"
                    )
                    await update.message.reply_text(delivery_text, reply_markup=get_main_keyboard(user_id))

                elif p_info["type"] == "proxy_bundle":
                    stock_list = PRODUCTS["Owl Proxy 200MB"]["stock_list"]
                    if len(stock_list) < 3:
                        await update.message.reply_text("⚠️ পর্যাপ্ত স্টক নেই (কমপক্ষে ৩টি প্রয়োজন)!", reply_markup=get_main_keyboard(user_id))
                        return
                    USER_BALANCES[user_id] -= p_price
                    p1 = stock_list.pop(0)
                    p2 = stock_list.pop(0)
                    p3 = stock_list.pop(0)
                    
                    for i, p_info_item in enumerate([p1, p2, p3], 1):
                        extra = f"\n💰 বর্তমান ব্যালেন্স: {USER_BALANCES[user_id]} BDT\n✅ Ready to Connect" if i == 3 else "\n✅ Ready to Connect"
                        d_text = (
                            f"📦 Bundle Item {i}/3 — {p_name}\n"
                            "────────────────────────\n"
                            f"🆔 ID: {p_info_item['id']}\n"
                            f"🌐 Host: {p_info_item['host']}\n"
                            f"🔌 Port: {p_info_item['port']}\n"
                            f"👤 UN: {p_info_item['user']}\n"
                            f"🔑 PASS: {p_info_item['pwd']}{extra}"
                        )
                        await update.message.reply_text(d_text)
                        await asyncio.sleep(0.5)
                    await update.message.reply_text("🎉 সফলভাবে ডেলিভারি সম্পন্ন হয়েছে!", reply_markup=get_main_keyboard(user_id))

                elif p_info["type"] == "custom_service":
                    if len(p_info["stock_list"]) <= 0:
                        await update.message.reply_text("⚠️ স্টক খালি আছে!", reply_markup=get_main_keyboard(user_id))
                        return
                    USER_BALANCES[user_id] -= p_price
                    item_data = p_info["stock_list"].pop(0)
                    await update.message.reply_text(
                        f"📦 Service: {p_name}\n────────────────────────\n{item_data}\n\n💰 বর্তমান ব্যালেন্স: {USER_BALANCES[user_id]} BDT",
                        reply_markup=get_main_keyboard(user_id)
                    )
                break

    elif text == "⬅️ Back to Menu":
        USER_STATES[user_id] = None
        await update.message.reply_text("🏠 মূল মেনুতে ফিরে এসেছেন:", reply_markup=get_main_keyboard(user_id))

    elif text == "💰 Deposit":
        USER_STATES[user_id] = "waiting_for_deposit_amount"
        deposit_text = (
            "===============================\n"
            "       💳 DEPOSIT MONEY\n"
            "===============================\n\n"
            "টাকা পাঠানোর জন্য নিচের পার্সোনাল নম্বরগুলোতে সেন্ড মনি করুন:\n\n"
            "🔹 Bkash (Personal): `01317404705`\n"
            "🔸 Nagad (Personal): `01917404724`\n\n"
            "⚠️ **মিনিমাম ডিপোজিট ১০ টাকা (10 BDT)**\n\n"
            "✍️ আপনি কত টাকা পাঠিয়েছেন তা সংখ্যায় এখানে লিখে পাঠান:"
        )
        await update.message.reply_text(deposit_text, reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel & Back")]], resize_keyboard=True), parse_mode="Markdown")

    elif text == "📦 My Stock & Balance":
        bal = USER_BALANCES.get(user_id, 0)
        status_text = (
            "===============================\n"
            "     👤 ACCOUNT STATUS\n"
            "===============================\n\n"
            f"💰 Current Balance: {bal} BDT\n"
            "📦 Purchased Items: History Clean"
        )
        await update.message.reply_text(status_text)

    elif text == "📞 Support":
        await update.message.reply_text("📞 For any issue, contact directly: @owner_joshim")

    else:
        if USER_STATES.get(user_id) is None:
            await update.message.reply_text("Please select a valid option from the keyboard menu below.", reply_markup=get_main_keyboard(user_id))

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO & (~filters.COMMAND), handle_message))

    print("🤖 Bot is running with Ban/Unban Admin Features...")
    application.run_polling()

if __name__ == '__main__':
    main()
