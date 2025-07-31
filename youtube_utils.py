import os
import re
from pytube import YouTube

def download_video(url, output_path="downloads"):
    yt = YouTube(url)
    stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by('resolution').desc().first()
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    filename = stream.download(output_path=output_path)
    return filename

def split_video(input_path, duration_sec=90, output_folder="clips"):
    from moviepy.editor import VideoFileClip
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    video = VideoFileClip(input_path)
    clips = []
    total = int(video.duration // duration_sec) + 1
    for i in range(total):
        start = i * duration_sec
        end = min((i + 1) * duration_sec, video.duration)
        clip = video.subclip(start, end)
        out_file = os.path.join(output_folder, f"part_{i+1}.mp4")
        clip.write_videofile(out_file, codec="libx264", audio_codec="aac")
        clips.append(out_file)
    return clips
