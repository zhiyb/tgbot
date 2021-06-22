#!/usr/bin/env python3
import os, traceback
import subprocess
from pathlib import Path
from telegram.ext import CommandHandler
from config import hls_url

# HLS archive
hls_dir = '/var/www/hls'
hls_adapt_dir = '/var/www/hls_adapt'
hls_timer = 3
# File size threshold, 1.9 GiB
hls_size = (1946 * 1024 * 1024)

# General
tmp_dir = '/data/tmp'

# HLS archive
class HlsArchive:
    key = "stream"
    chat_id = 0
    archive_url = None
    hls_last = ""
    hls_count = 0
    hls_running = False
    hls_adapt = False
    hls_dir = ""
    hls_url = ""
    file_index = 0
    max_file_size = 0

    def __init__(self, updater, key = "stream", chat_id = 0, archive_url = None, adapt = None, max_file_size = hls_size):
        self.key = key + adapt if adapt else key
        self.chat_id = chat_id
        self.archive_url = archive_url
        self.hls_dir = hls_adapt_dir if adapt else hls_dir
        self.hls_url = hls_url if key == "stream" else f"{hls_url}?key={key}"
        self.max_file_size = max_file_size
        self.file_index = 0
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler(key, self.hls_stream))
        updater.job_queue.run_repeating(self.hls_poll, hls_timer)

    def fname_base(self):
        return f"{tmp_dir}/hls_{self.key}_{self.file_index}"

    def fname_live(self):
        return f"{self.fname_base()}_live.ts"

    def fname_base_push(self):
        return f"{self.fname_base()}_push"

    def hls_append(self, bot, fname):
        with open(os.path.join(self.hls_dir, fname), 'rb') as fsrc:
            with open(self.fname_live(), 'wb' if self.hls_count == 0 else 'ab') as fdst:
                fdst.write(fsrc.read())
                print(self.key, self.hls_count, fsrc.name)
                return 1
        return 0

    # https://stackoverflow.com/a/3844467
    def get_video_length(self, filename):
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of",
                                "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        return float(result.stdout)

    def hls_push_async(self, context):
        bot = context.bot
        src,push = context.job.context
        ext = ".mp4" #".ts"
        thumb = f"{push}.jpg"
        if ext == ".mp4":
            dst = f"{push}{ext}"
            os.system("ffmpeg -i %s -c copy -movflags faststart -y %s"%(src, dst))
            os.unlink(src)
            src = dst
        os.system("ffmpeg -i %s -vframes 1 -an -s 400x225 -y %s"%(src, thumb))
        #time.sleep(18)
        bot.send_video(chat_id=self.chat_id,
                video="file://%s"%src, thumb=Path(thumb),
                width=1920, height=1080, duration=round(self.get_video_length(src)),
                supports_streaming=True, disable_notification=True, timeout=300)
        os.unlink(src)
        os.unlink(thumb)

    def hls_push(self, context):
        src = self.fname_live()
        push = self.fname_base_push()
        self.file_index += 1
        context.job_queue.run_once(self.hls_push_async, 0, (src, push))

    # Messages
    def hls_stream(self, update, context):
        text = f"Stream is running at {self.hls_url}" if self.hls_running else "Stream is dead"
        if self.archive_url:
            text += f"\nArchive: {self.archive_url}"
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    def hls_poll(self, context):
        bot = context.bot
        try:
            with open(os.path.join(self.hls_dir, self.key + '.m3u8'), 'r') as f:
                playlist = f.read()
                files = list(filter(lambda f: f.endswith('.ts'), playlist.split("\n")))
                last = files[-1]
                if last == self.hls_last:
                    return

                first = 0
                try:
                    first = files.index(self.hls_last) + 1
                except:
                    pass
                self.hls_last = last

                for i in range(first, len(files)):
                    fname = files[i]
                    if self.hls_append(bot, fname):
                        self.hls_count += 1
                        if not self.hls_running:
                            self.hls_running = True
                            bot.send_message(chat_id=self.chat_id,
                                    text="Stream running:\n%s"%self.hls_url)

                        size = os.path.getsize(self.fname_live())
                        if size >= self.max_file_size:
                            self.hls_count = 0
                            self.hls_push(context)
        except:
            if self.hls_running:
                traceback.print_exc()
                self.hls_running = False
                if self.hls_count != 0:
                    self.hls_count = 0
                    self.hls_push(context)
                bot.send_message(chat_id=self.chat_id, text="Stream stopped")
