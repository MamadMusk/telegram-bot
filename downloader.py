import yt_dlp
import os
import re
import logging
from database import add_download

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def download_media(url, user_id):
    """
    دانلود از پلتفرم‌های مختلف با استفاده از yt-dlp
    پشتیبانی از: Instagram, YouTube, Spotify, X (Twitter), TikTok, Pinterest,
    Snapchat, Facebook, SoundCloud, Threads, Reddit, Likee
    """
    try:
        logging.info(f"📥 Downloading from: {url}")
        
        # تشخیص پلتفرم
        platform = detect_platform(url)
        logging.info(f"📌 Platform detected: {platform}")
        
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s-%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': False,
            'ignoreerrors': True,
            'extract_flat': False,
        }
        
        # تنظیمات خاص برای هر پلتفرم
        if platform in ["spotify", "soundcloud"]:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            ydl_opts['format'] = 'best[ext=mp4]/best'
        
        # برای پلتفرم‌هایی که نیاز به کوکی دارند
        if platform in ["instagram", "twitter", "facebook"]:
            ydl_opts['cookiefile'] = 'cookies.txt' if os.path.exists('cookies.txt') else None
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            files = []
            
            if info:
                if 'entries' in info and info['entries']:
                    for entry in info['entries']:
                        if entry:
                            filename = ydl.prepare_filename(entry)
                            if os.path.exists(filename):
                                files.append(filename)
                            # برای فایل‌های صوتی
                            base = os.path.splitext(filename)[0]
                            for ext in ['.mp3', '.m4a', '.webm']:
                                if os.path.exists(base + ext):
                                    files.append(base + ext)
                else:
                    filename = ydl.prepare_filename(info)
                    if os.path.exists(filename):
                        files.append(filename)
                    base = os.path.splitext(filename)[0]
                    for ext in ['.mp3', '.m4a', '.webm']:
                        if os.path.exists(base + ext):
                            files.append(base + ext)
            
            if files:
                # ثبت در دیتابیس
                file_size = 0
                for f in files:
                    try:
                        file_size += os.path.getsize(f) // 1024  # تبدیل به کیلوبایت
                    except:
                        pass
                add_download(user_id, url, platform, "success", file_size)
                return files, info.get('description', '') if info else ''
            else:
                add_download(user_id, url, platform, "failed", error_message="هیچ فایلی دانلود نشد")
                return None, "هیچ فایلی دانلود نشد."
                
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Download error: {error_msg}")
        add_download(user_id, url, detect_platform(url), "failed", error_message=error_msg)
        return None, error_msg

def detect_platform(url):
    """تشخیص پلتفرم از روی لینک"""
    url_lower = url.lower()
    if 'instagram.com' in url_lower or 'instagr.am' in url_lower:
        return 'instagram'
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'spotify.com' in url_lower:
        return 'spotify'
    elif 'x.com' in url_lower or 'twitter.com' in url_lower:
        return 'twitter'
    elif 'tiktok.com' in url_lower:
        return 'tiktok'
    elif 'pinterest.com' in url_lower or 'pin.it' in url_lower:
        return 'pinterest'
    elif 'snapchat.com' in url_lower:
        return 'snapchat'
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
        return 'facebook'
    elif 'soundcloud.com' in url_lower:
        return 'soundcloud'
    elif 'threads.net' in url_lower:
        return 'threads'
    elif 'reddit.com' in url_lower or 'redd.it' in url_lower:
        return 'reddit'
    elif 'likee.com' in url_lower or 'likee.video' in url_lower:
        return 'likee'
    else:
        return 'unknown'

def get_platform_icon(platform):
    """دریافت آیکون پلتفرم"""
    icons = {
        'instagram': '📸',
        'youtube': '▶️',
        'spotify': '🎧',
        'twitter': '🐦',
        'tiktok': '📱',
        'pinterest': '📌',
        'snapchat': '👻',
        'facebook': '🌐',
        'soundcloud': '🎵',
        'threads': '💬',
        'reddit': '🔗',
        'likee': '🎥',
        'unknown': '🔗'
    }
    return icons.get(platform, '🔗')
