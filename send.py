#!/usr/bin/env python3
import sys, os, subprocess, tempfile
from pathlib import Path, PurePath
from argparse import ArgumentParser

#print('\n'.join(sys.path))

from telegram import ParseMode
from telegram.ext import Updater
import logging
import sys, socket

from config import token, base_url, chat_id_admin

# General
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# https://stackoverflow.com/a/3844467
def get_video_info(path):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    info = result.stdout.split()
    return {'width': int(info[0]),
            'height': int(info[1]),
            'duration': float(info[2])}

def send_video(bot, chat, path):
    info = get_video_info(path)

    # Create a thumbnail
    tmp_fd, thumb = tempfile.mkstemp('.jpg')
    os.close(tmp_fd)
    os.system(f"ffmpeg -i {path} -vframes 1 -an -vf scale=320:-1 -y {thumb}")

    # Upload to server and send video
    os.system(f"rsync --progress -au {path} vps:/data/tmp/")
    #os.system(f"rsync --progress -au {path} {thumb} vps:/data/tmp/")
    video_server=f"/data/tmp/{PurePath(path).name}"
    video_data=f"file://{video_server}"
    #thumb_server=f"/data/tmp/{PurePath(thumb).name}"
    #video_data=Path(path).read_bytes()
    thumb_data=Path(thumb).read_bytes()
    bot.send_video(chat_id=chat,
            video=video_data, thumb=thumb_data,
            #video=f"file://{server_video}", thumb=thumb_bytes,
            width=info['width'], height=info['height'], duration=round(info['duration']),
            supports_streaming=True, disable_notification=True, timeout=300)

    os.system(f"ssh vps rm {video_server}")
    os.remove(thumb)

def send_md(bot, chat, text):
    bot.send_message(chat_id=chat, text=text, parse_mode=ParseMode.MARKDOWN)

def main():
    parser = ArgumentParser()
    parser.add_argument('-c', '--chat', type=int, default=chat_id_admin,
                        help='Chat ID')
    parser.add_argument('-v', '--video', type=str,
                        help='Send video file')

    args, msg = parser.parse_known_args()
    print(args)

    updater = Updater(token=token, base_url=base_url, use_context=True)

    if args.video:
        send_video(updater.bot, args.chat, args.video)

    else:
        text = "_%s_\n%s"%(socket.gethostname(), "\n".join(msg))
        send_md(updater.bot, args.chat, text)

    #updater.start_polling()
    #updater.idle()

if __name__ == '__main__':
    main()
