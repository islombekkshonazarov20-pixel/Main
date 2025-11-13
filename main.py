import os
import asyncio
from yt_dlp import YoutubeDL
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from telegram.error import Forbidden

TELEGRAM_TOKEN = "8454214201:AAF2l1po3Etal89x-ZkcuBEn0Xy3GVhbC14"
CHANNEL_ID = "@attackboy_pubgm"  # obuna tekshiriladigan kanal

TMP_DIR = "tmp_media"
os.makedirs(TMP_DIR, exist_ok=True)

video_opts = {
    "format": "best",
    "outtmpl": os.path.join(TMP_DIR, "%(id)s.%(ext)s"),
    "quiet": True,
    "no_warnings": True,
}

audio_opts = {
    "format": "bestaudio/best",
    "outtmpl": os.path.join(TMP_DIR, "%(id)s.%(ext)s"),
    "quiet": True,
    "no_warnings": True,
    "postprocessors": [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
    ],
}


# 🔒 OBUNA TEKSHIRISH FUNKSIYASI
async def check_subscription(user_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Forbidden:
        return False
    except Exception:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Link yuboring (Instagram, YouTube, TikTok, Facebook...) — men uni video, rasm yoki audio qilib qaytaraman.\n"
        "🎵 Faqat musiqa yuklash uchun: /music <link>\n\n"
        f"📢 Yuklashdan oldin kanalga obuna bo‘ling: {CHANNEL_ID}"
    )


def download_media(url, opts):
    """Oddiy sinxron yuklab olish funksiyasi"""
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if opts is audio_opts:
            filename = os.path.splitext(filename)[0] + ".mp3"
        return filename, info


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text = msg.text or msg.caption or ""
    user_id = msg.from_user.id

    # 🔒 OBUNA TEKSHIRUV
    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        await msg.reply_text(
            f"📢 Iltimos, kanalga obuna bo‘ling: {CHANNEL_ID}\n"
            "✅ Obuna bo‘lgach, qayta urinib ko‘ring."
        )
        return

    if not text or not text.startswith("http"):
        await msg.reply_text("❌ Iltimos, to‘liq media link yuboring.")
        return

    url = text.strip()
    status_msg = await msg.reply_text("⏳ Yuklanmoqda...")

    try:
        loop = asyncio.get_running_loop()
        filename, info = await loop.run_in_executor(None, lambda: download_media(url, video_opts))

        if not os.path.exists(filename):
            await status_msg.edit_text("⚠️ Fayl topilmadi yoki qo‘llab-quvvatlanmaydi.")
            return

        description = info.get("description", "")
        title = info.get("title", "Media")
        caption = f"📥 Yuklandi: {title}"
        if description:
            caption += f"\n\n📝 {description}"
        caption = caption[:1024]

        ext = os.path.splitext(filename)[1].lower()
        if ext in [".mp4", ".mov", ".avi", ".mkv"]:
            with open(filename, "rb") as f:
                await msg.reply_video(video=InputFile(f), caption=caption)
        elif ext in [".jpg", ".jpeg", ".png", ".webp"]:
            with open(filename, "rb") as f:
                await msg.reply_photo(photo=InputFile(f), caption=caption)
        else:
            with open(filename, "rb") as f:
                await msg.reply_document(document=InputFile(f), caption=caption)

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"⚠️ Xatolik yuz berdi: {e}")
    finally:
        try:
            for fname in os.listdir(TMP_DIR):
                os.remove(os.path.join(TMP_DIR, fname))
        except:
            pass


async def handle_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text = msg.text or msg.caption or ""
    user_id = msg.from_user.id

    # 🔒 OBUNA TEKSHIRUV
    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        await msg.reply_text(
            f"📢 Iltimos, kanalga obuna bo‘ling: {CHANNEL_ID}\n"
            "✅ Obuna bo‘lgach, qayta urinib ko‘ring."
        )
        return

    if not text or not text.startswith("http"):
        await msg.reply_text("🎵 Iltimos, musiqa link yuboring (YouTube, TikTok...).")
        return

    url = text.strip()
    status_msg = await msg.reply_text("🎧 Musiqa yuklanmoqda...")

    try:
        loop = asyncio.get_running_loop()
        filename, info = await loop.run_in_executor(None, lambda: download_media(url, audio_opts))

        if not os.path.exists(filename):
            await status_msg.edit_text("⚠️ Musiqa topilmadi.")
            return

        title = info.get("title", "Audio")
        artist = info.get("uploader", "Noma'lum")
        caption = f"🎵 {title}\n👤 {artist}"

        with open(filename, "rb") as f:
            await msg.reply_audio(audio=InputFile(f, filename=os.path.basename(filename)), caption=caption)

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"⚠️ Xatolik: {e}")
    finally:
        try:
            for fname in os.listdir(TMP_DIR):
                os.remove(os.path.join(TMP_DIR, fname))
        except:
            pass


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("music", handle_music))
    app.add_handler(MessageHandler(filters.TEXT | filters.Caption(), handle_message))
    print("✅ Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()