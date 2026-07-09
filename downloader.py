import instaloader
import os
import re
import time
import yt_dlp

def download_instagram_post(url):
    """
    دانلود از اینستاگرام با روش ترکیبی:
    - اول با instaloader (برای عکس‌ها و ویدیوها)
    - اگه instaloader جواب نداد، با yt-dlp (برای ویدیوها)
    """
    download_dir = "downloads"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # پاک کردن فایل‌های قبلی
    for f in os.listdir(download_dir):
        os.remove(os.path.join(download_dir, f))

    # استخراج shortcode
    match = re.search(r"/(?:p|reel|tv)/([^/?]+)", url)
    if not match:
        return None, "❌ لینک اینستاگرام معتبر نیست."
    shortcode = match.group(1)

    # ========== روش اول: instaloader ==========
    try:
        loader = instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,
            save_metadata=False,
            post_metadata_txt_pattern="",
            filename_pattern="{shortcode}",
            quiet=True,
        )
        
        # بارگذاری کوکی (اگه وجود داره)
        cookies_path = os.path.join(os.getcwd(), "cookies.txt")
        if os.path.exists(cookies_path):
            try:
                loader.load_session_from_file(cookies_path)
            except:
                pass

        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        caption = post.caption if post.caption else "بدون کپشن"

        loader.download_post(post, target=download_dir)
        time.sleep(1)

        files = os.listdir(download_dir)
        media_files = []
        for f in sorted(files):
            if f.endswith((".mp4", ".jpg", ".png", ".jpeg")):
                media_files.append(os.path.join(download_dir, f))

        if media_files:
            return media_files, caption

    except Exception as e:
        print(f"⚠️ instaloader failed: {e}")

    # ========== روش دوم: yt-dlp ==========
    try:
        ydl_opts = {
            'outtmpl': os.path.join(download_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'format': 'best[ext=mp4]/best[ext=jpg]/best',
            'ignoreerrors': True,
        }
        
        # استفاده از کوکی
        cookies_path = os.path.join(os.getcwd(), "cookies.txt")
        if os.path.exists(cookies_path):
            ydl_opts['cookiefile'] = cookies_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                return None, "❌ لینک معتبر نیست یا محتوایی یافت نشد."

            caption = info.get('description') or info.get('title') or "بدون کپشن"
            files = os.listdir(download_dir)
            media_files = []
            for f in sorted(files):
                if f.endswith((".mp4", ".jpg", ".png", ".jpeg")):
                    media_files.append(os.path.join(download_dir, f))

            if media_files:
                return media_files, caption

    except Exception as e:
        print(f"⚠️ yt-dlp failed: {e}")

    return None, "❌ هیچ فایلی دانلود نشد."
