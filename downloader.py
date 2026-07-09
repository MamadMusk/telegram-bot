"""
downloader.py — Instagram downloader with manual cookies.
Works for photos, videos, and carousels.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from typing import List, Optional, Tuple

import instaloader

logger = logging.getLogger(__name__)

# ============================================================
#  URL patterns
# ============================================================

URL_PATTERNS = {
    "instagram": re.compile(
        r"(?:https?://)?(?:www\.)?(?:instagram\.com|instagr\.am)/"
        r"(?:p|reel|reels|tv|share/v)/([^/?#&]+)",
        re.IGNORECASE,
    ),
}


def detect_platform(url: str) -> Optional[str]:
    for platform, pattern in URL_PATTERNS.items():
        if pattern.search(url):
            return platform
    return None


def extract_instagram_shortcode(url: str) -> Optional[str]:
    m = URL_PATTERNS["instagram"].search(url)
    return m.group(1) if m else None


# ============================================================
#  Result dataclass
# ============================================================

@dataclass
class DownloadResult:
    files: List[str]
    caption: str
    platform: str
    shortcode: Optional[str]
    tempdir: str
    file_size_kb: int

    def cleanup(self) -> None:
        if self.tempdir and os.path.isdir(self.tempdir):
            shutil.rmtree(self.tempdir, ignore_errors=True)


# ============================================================
#  Cookies file path
# ============================================================

COOKIES_FILE = os.path.join(os.getcwd(), "cookies.txt")


# ============================================================
#  Main download function (only instaloader + cookies)
# ============================================================

def download(url: str) -> DownloadResult:
    platform = detect_platform(url)
    if not platform:
        raise ValueError("لینک پشتیبانی نمی‌شود.")

    shortcode = extract_instagram_shortcode(url)
    if not shortcode:
        raise ValueError("لینک اینستاگرام معتبر نیست.")

    workdir = tempfile.mkdtemp(prefix="tb_", dir=None)

    try:
        logger.info("🔍 Trying instaloader for %s", shortcode)

        loader = instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,
            download_video_thumbnails=False,
            save_metadata=False,
            post_metadata_txt_pattern="",
            filename_pattern="{shortcode}",
            quiet=True,
        )

        # Load cookies
        if os.path.exists(COOKIES_FILE):
            try:
                loader.load_session_from_file(COOKIES_FILE)
                logger.info("✅ Loaded cookies from %s", COOKIES_FILE)
            except Exception as e:
                logger.warning("⚠️ Cookie load failed: %s", e)
        else:
            logger.warning("⚠️ cookies.txt not found at %s", COOKIES_FILE)
            raise RuntimeError("فایل cookies.txt پیدا نشد. لطفاً آن را از مرورگر بگیرید.")

        # Get post
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        caption = post.caption or "بدون کپشن"

        # Download
        loader.download_post(post, target=workdir)

        # Find files
        files = []
        for f in sorted(os.listdir(workdir)):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".mp4")):
                files.append(os.path.join(workdir, f))

        if not files:
            raise RuntimeError("هیچ فایلی دانلود نشد.")

        total_bytes = sum(os.path.getsize(f) for f in files if os.path.exists(f))
        file_size_kb = total_bytes // 1024

        if caption and len(caption) > 1000:
            caption = caption[:997] + "..."

        logger.info("✅ Downloaded %d files, %d KB total", len(files), file_size_kb)

        return DownloadResult(
            files=files,
            caption=caption,
            platform=platform,
            shortcode=shortcode,
            tempdir=workdir,
            file_size_kb=file_size_kb,
        )

    except Exception as e:
        shutil.rmtree(workdir, ignore_errors=True)
        raise RuntimeError(f"خطا: {e}")


def is_file_too_large(file_path: str) -> bool:
    from config import settings
    if not os.path.exists(file_path):
        return False
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    return os.path.getsize(file_path) > max_bytes


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python downloader.py <url>")
        sys.exit(1)
    logging.basicConfig(level=logging.INFO)
    result = download(sys.argv[1])
    print(f"Got {len(result.files)} files, {result.file_size_kb} KB")
    for f in result.files:
        print(f"  - {f}")
    result.cleanup()