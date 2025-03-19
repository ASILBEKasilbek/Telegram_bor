import requests
import yt_dlp
from shazamio import Shazam
import os
from config import FAST_SAVER_API, FAST_SAVER_API_KEY
from database import get_channels

def download_social_media_video(url):
    headers = {"Authorization": f"Bearer {FAST_SAVER_API_KEY}"}
    response = requests.post(FAST_SAVER_API, json={"url": url}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("video_url")
    return None

def process_youtube_video(url):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": "video.%(ext)s",
        "merge_output_format": "mp4",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info["filesize_approx"] / (1024 * 1024) < 50:
            ydl.download([url])
            return "video.mp4"
        else:
            return info["url"]

async def shazam_video(video_path):
    shazam = Shazam()
    result = await shazam.recognize_song(video_path)
    if result and "track" in result:
        return result["track"]["title"], result["track"]["subtitle"]
    return None, None

async def shazam_audio(audio_path):
    shazam = Shazam()
    result = await shazam.recognize_song(audio_path)
    if result and "track" in result:
        return result["track"]["title"], result["track"]["subtitle"]
    return None, None

async def check_membership(bot, user_id):
    channels = get_channels()
    if not channels:
        return True  # Agar kanal/guruh qo‘shilmagan bo‘lsa, tekshiruv o‘tkazilmaydi
    try:
        for chat_id, _ in channels:
            status = (await bot.get_chat_member(chat_id, user_id)).status
            if status not in ["member", "administrator", "creator"]:
                return False
        return True
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False