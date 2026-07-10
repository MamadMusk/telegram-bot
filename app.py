@app.route('/', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') != 'application/json':
            return 'Unsupported content type', 400

        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)

        # ============================================================
        #  1️⃣ پردازش Callback Query (دکمه‌های شیشه‌ای)
        # ============================================================
        if update.callback_query:
            call = update.callback_query
            user_id = call.from_user.id
            chat_id = call.message.chat.id
            message_id = call.message.message_id
            data = call.data

            logging.info(f"📞 Callback: {data} from {user_id}")

            # ===== بررسی دسترسی ادمین =====
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "⛔ شما دسترسی ادمین ندارید!", show_alert=True)
                return 'OK', 200

            bot.answer_callback_query(call.id)  # پاسخ اولیه

            # ─── 1. بروزرسانی آمار ───
            if data == "refresh_stats":
                bot.answer_callback_query(call.id, "🔄 آمار بروزرسانی شد!", show_alert=False)
                show_stats(chat_id, message_id)

            # ─── 2. مدیریت ادمین‌ها ───
            elif data == "admin_add":
                bot.answer_callback_query(call.id, "➕ لطفاً آیدی عددی را وارد کنید", show_alert=False)
                bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
                msg = bot.send_message(chat_id, MESSAGES["admin_add_prompt"])
                bot.user_data[chat_id] = {'step': 'add_admin', 'message_id': msg.message_id}

            elif data.startswith("admin_remove_"):
                admin_id = int(data.replace("admin_remove_", ""))
                if admin_id == user_id:
                    bot.answer_callback_query(call.id, "❌ نمی‌توانید خودتان را حذف کنید!", show_alert=True)
                    return 'OK', 200
                remove_admin(admin_id)
                bot.answer_callback_query(call.id, f"✅ ادمین {admin_id} حذف شد!", show_alert=True)
                show_admin_list(chat_id, message_id)

            # ─── 3. قفل اسپانسر ───
            elif data == "force_sub_add":
                bot.answer_callback_query(call.id, "➕ لطفاً آیدی کانال را با @ وارد کنید", show_alert=False)
                bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
                msg = bot.send_message(chat_id, MESSAGES["force_sub_add_prompt"])
                bot.user_data[chat_id] = {'step': 'add_force_channel', 'message_id': msg.message_id}

            elif data.startswith("force_sub_remove_"):
                channel = data.replace("force_sub_remove_", "")
                if remove_force_channel(channel):
                    bot.answer_callback_query(call.id, f"✅ کانال {channel} حذف شد!", show_alert=True)
                else:
                    bot.answer_callback_query(call.id, f"❌ کانال {channel} پیدا نشد!", show_alert=True)
                show_force_sub_settings(chat_id, message_id)

            # ─── 4. تنظیمات ───
            elif data == "setting_quota":
                bot.answer_callback_query(call.id, "📊 عدد مورد نظر را وارد کنید", show_alert=False)
                bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
                msg = bot.send_message(chat_id, MESSAGES["settings_quota_prompt"])
                bot.user_data[chat_id] = {'step': 'set_daily_quota', 'message_id': msg.message_id}

            elif data == "setting_size":
                bot.answer_callback_query(call.id, "📦 عدد مورد نظر را وارد کنید", show_alert=False)
                bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
                msg = bot.send_message(chat_id, MESSAGES["settings_size_prompt"])
                bot.user_data[chat_id] = {'step': 'set_max_file_size', 'message_id': msg.message_id}

            elif data == "setting_active":
                current = get_setting("is_active", "True")
                new_value = "False" if current == "True" else "True"
                set_setting("is_active", new_value)
                bot.answer_callback_query(call.id, f"✅ وضعیت تغییر کرد: {'فعال' if new_value == 'True' else 'غیرفعال'}", show_alert=True)
                show_settings(chat_id, message_id)

            # ─── 5. ارسال همگانی ───
            elif data == "broadcast_confirm":
                bot.answer_callback_query(call.id, "📨 در حال ارسال...", show_alert=False)
                data_obj = bot.user_data.get(user_id, {})
                broadcast_text = data_obj.get('broadcast_message', '')
                if not broadcast_text:
                    bot.send_message(user_id, "❌ پیامی برای ارسال وجود ندارد.")
                    return 'OK', 200
                users = get_all_users()
                success_count = 0
                for user in users:
                    try:
                        bot.send_message(user['user_id'], broadcast_text)
                        success_count += 1
                        time.sleep(0.05)
                    except Exception as e:
                        logging.error(f"Failed to send to {user['user_id']}: {e}")
                try:
                    bot.edit_message_reply_markup(chat_id, data_obj.get('message_id'), reply_markup=None)
                except:
                    pass
                bot.send_message(user_id, MESSAGES["broadcast_success"].format(count=success_count))
                if user_id in bot.user_data:
                    del bot.user_data[user_id]

            elif data == "broadcast_cancel":
                bot.answer_callback_query(call.id, "❌ لغو شد", show_alert=False)
                data_obj = bot.user_data.get(user_id, {})
                try:
                    bot.edit_message_reply_markup(chat_id, data_obj.get('message_id'), reply_markup=None)
                except:
                    pass
                bot.send_message(user_id, MESSAGES["broadcast_cancelled"])
                if user_id in bot.user_data:
                    del bot.user_data[user_id]

            # ─── 6. تأیید عضویت ───
            elif data == "force_sub_verify":
                is_subscribed, not_subscribed = check_user_subscription(user_id)
                if is_subscribed:
                    bot.answer_callback_query(call.id, "✅ عضویت شما تأیید شد!", show_alert=True)
                    bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
                    if is_admin(user_id):
                        keyboard = get_admin_keyboard()
                    else:
                        keyboard = get_user_keyboard()
                    bot.send_message(user_id, MESSAGES["force_sub_verified"], reply_markup=keyboard)
                else:
                    channels_text = "\n".join([f"• {ch}" for ch in not_subscribed])
                    bot.answer_callback_query(call.id, "❌ هنوز در همه کانال‌ها عضو نشدی!", show_alert=True)
                    bot.send_message(user_id, MESSAGES["force_sub_required"].format(channels=channels_text), parse_mode='HTML')

            # ─── 7. بازگشت ───
            elif data == "admin_back":
                bot.answer_callback_query(call.id, "🔙 بازگشت", show_alert=False)
                bot.edit_message_text("🛠 پنل مدیریت", chat_id, message_id, reply_markup=get_admin_keyboard())

            return 'OK', 200

        # ============================================================
        #  2️⃣ پردازش پیام
        # ============================================================
        elif update.message:
            chat_id = update.message.chat.id
            user_id = update.message.from_user.id
            text = update.message.text
            username = update.message.from_user.username
            first_name = update.message.from_user.first_name
            last_name = update.message.from_user.last_name

            logging.info(f"📨 Message from {chat_id}: {text}")

            # ثبت کاربر
            add_user(user_id, username, first_name, last_name)

            # بررسی عضویت اجباری
            if not is_admin(user_id):
                is_subscribed, not_subscribed = check_user_subscription(user_id)
                if not is_subscribed:
                    channels_text = "\n".join([f"• {ch}" for ch in not_subscribed])
                    keyboard = get_force_sub_keyboard(not_subscribed)
                    bot.send_message(
                        chat_id,
                        MESSAGES["force_sub_required"].format(channels=channels_text),
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                    return 'OK', 200

            # ===== پردازش مراحل (step) =====
            step_data = bot.user_data.get(chat_id, {})
            step = step_data.get('step')

            if step == 'add_admin':
                try:
                    new_admin_id = int(text.strip())
                    if new_admin_id == user_id:
                        bot.send_message(chat_id, "❌ نمی‌توانید خودتان را دوباره اضافه کنید!")
                    else:
                        add_admin(new_admin_id, "moderator")
                        bot.send_message(chat_id, MESSAGES["admin_add_success"].format(role="moderator"))
                        show_admin_list(chat_id)
                except ValueError:
                    bot.send_message(chat_id, MESSAGES["admin_invalid_id"])
                if chat_id in bot.user_data:
                    del bot.user_data[chat_id]
                return 'OK', 200

            elif step == 'add_force_channel':
                channel = text.strip()
                if not channel.startswith('@'):
                    channel = f"@{channel}"
                add_force_channel(channel)
                bot.send_message(chat_id, MESSAGES["force_sub_added"].format(channel=channel))
                show_force_sub_settings(chat_id)
                if chat_id in bot.user_data:
                    del bot.user_data[chat_id]
                return 'OK', 200

            elif step == 'set_daily_quota':
                try:
                    value = int(text.strip())
                    set_setting("daily_quota", str(value))
                    bot.send_message(chat_id, MESSAGES["settings_updated"])
                    show_settings(chat_id)
                except ValueError:
                    bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
                    msg = bot.send_message(chat_id, MESSAGES["settings_quota_prompt"])
                    bot.user_data[chat_id] = {'step': 'set_daily_quota', 'message_id': msg.message_id}
                if chat_id in bot.user_data:
                    del bot.user_data[chat_id]
                return 'OK', 200

            elif step == 'set_max_file_size':
                try:
                    value = int(text.strip())
                    set_setting("max_file_size", str(value))
                    bot.send_message(chat_id, MESSAGES["settings_updated"])
                    show_settings(chat_id)
                except ValueError:
                    bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
                    msg = bot.send_message(chat_id, MESSAGES["settings_size_prompt"])
                    bot.user_data[chat_id] = {'step': 'set_max_file_size', 'message_id': msg.message_id}
                if chat_id in bot.user_data:
                    del bot.user_data[chat_id]
                return 'OK', 200

            elif step == 'broadcast':
                process_broadcast_message(chat_id, text)
                if chat_id in bot.user_data:
                    del bot.user_data[chat_id]
                return 'OK', 200

            # ===== /start =====
            if text and text.startswith('/start'):
                if is_admin(user_id):
                    keyboard = get_admin_keyboard()
                    bot.send_message(chat_id, MESSAGES["start"], reply_markup=keyboard)
                else:
                    keyboard = get_user_keyboard()
                    bot.send_message(chat_id, MESSAGES["start"], reply_markup=keyboard)
                return 'OK', 200

            # ===== دکمه‌های ادمین =====
            if is_admin(user_id):
                if text == "📊 آمار ربات":
                    show_stats(chat_id)
                    return 'OK', 200
                elif text == "📨 ارسال همگانی":
                    start_broadcast(chat_id)
                    return 'OK', 200
                elif text == "🔒 قفل اسپانسر":
                    show_force_sub_settings(chat_id)
                    return 'OK', 200
                elif text == "📋 مدیریت ادمین‌ها":
                    show_admin_list(chat_id)
                    return 'OK', 200
                elif text == "⚙️ تنظیمات ربات":
                    show_settings(chat_id)
                    return 'OK', 200

            # ===== لینک اینستاگرام =====
            if text and 'instagram.com' in text:
                msg = bot.send_message(chat_id, MESSAGES["downloading"])
                files, error = download_instagram_post(text, user_id)

                if not files:
                    bot.edit_message_text(f"❌ {error}", chat_id, msg.message_id)
                    return 'OK', 200

                for f in files:
                    try:
                        with open(f, 'rb') as media:
                            if f.endswith('.mp4'):
                                bot.send_video(chat_id, media, caption=MESSAGES["caption"])
                            else:
                                bot.send_photo(chat_id, media, caption=MESSAGES["caption"])
                            os.remove(f)
                    except Exception as e:
                        logging.error(f"خطا در ارسال فایل: {e}")
                        bot.send_message(chat_id, MESSAGES["send_error"].format(error=str(e)))

                bot.delete_message(chat_id, msg.message_id)
            else:
                if not is_admin(user_id):
                    bot.send_message(chat_id, MESSAGES["invalid_link"])

        return 'OK', 200

    except Exception as e:
        logging.error(f"❌ Webhook error: {e}")
        return 'Error', 500
