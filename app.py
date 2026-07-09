def download_instagram_post(url):
    """
    دانلود پست اینستاگرام (هم ویدیو و هم عکس) با اولویت yt-dlp
    و در صورت نیاز، fallback به instaloader با کوکی درست
    """
    files = []
    caption = ""
    
    # استخراج shortcode
    shortcode_match = re.search(r'/(?:p|reel|tv|stories)/([^/?]+)', url)
    if not shortcode_match:
        return None, "لینک معتبر اینستاگرام نیست."
    shortcode = shortcode_match.group(1)
    
    # ========== مرحله ۱: yt-dlp (برای همه چیز، هم عکس هم ویدیو) ==========
    try:
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'cookies.txt',
            'format': 'best',  # بهترین کیفیت رو بگیر، فرقی نمیکنه عکس یا ویدیو
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info and 'entries' in info:  # پست چندتایی
                for entry in info['entries']:
                    if entry:
                        filename = ydl.prepare_filename(entry)
                        if os.path.exists(filename):
                            files.append(filename)
                caption = info.get('description', '')
            else:
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    files.append(filename)
                caption = info.get('description', '')
        if files:
            return files, caption
    except Exception as e:
        logging.error(f"yt-dlp failed: {e}")
        # اگه ارور داد، برو سراغ instaloader
    
    # ========== مرحله ۲: instaloader با کوکی درست (برای عکس‌ها) ==========
    try:
        loader = instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,  # بذار True باشه برای احتیاط
            download_video_thumbnails=False,
            compress_json=False,
            save_metadata=False,
            post_metadata_txt_pattern='',
            max_connection_attempts=3
        )
        
        # ✅ اینجا مهمه: کوکی رو با متد درست برای فایل Netscape لود کن
        loader.load_cookies_from_txt("cookies.txt")  # <-- این خط جادوییه
        
        # حالا پست رو بگیر
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=shortcode)
        
        # فایل‌های دانلود شده رو پیدا کن
        for file in os.listdir('.'):
            if file.startswith(shortcode) and (file.endswith('.jpg') or file.endswith('.png') or file.endswith('.mp4')):
                files.append(os.path.join('.', file))
        caption = post.caption if post.caption else ""
        
        if files:
            return files, caption
        else:
            return None, "هیچ فایلی دانلود نشد."
    except Exception as e:
        logging.error(f"instaloader failed: {e}")
        return None, f"دانلود با مشکل مواجه شد: {str(e)}"
