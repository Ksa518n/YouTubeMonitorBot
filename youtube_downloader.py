import os
from pytube import YouTube
import moviepy.editor as mp
import datetime

last_video_id = ""

def download_and_split_video(url, title):
    yt = YouTube(url)
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    video_path = stream.download(filename='full_video.mp4')

    clip = mp.VideoFileClip(video_path)
    duration = clip.duration
    segment_length = 90  # 1:30

    parts = []
    for i in range(0, int(duration), segment_length):
        start = i
        end = min(i + segment_length, duration)
        part = clip.subclip(start, end)
        part_title = f"{title} - Part {i // segment_length + 1}"
        filename = f"part_{i // segment_length + 1}.mp4"
        part.write_videofile(filename)
        parts.append(filename)

    return parts

def check_new_video_and_process(channel_id):
    from youtube_search_python import Channel

    global last_video_id
    channel = Channel(channel_id)
    latest_video = channel.videos[0]
    video_id = latest_video['id']
    
    if video_id != last_video_id:
        last_video_id = video_id
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        title = latest_video['title']
        parts = download_and_split_video(video_url, title)
        # TODO: Add upload to your YouTube channel function here
        return {"id": video_id, "title": title, "parts": parts}
    return None
