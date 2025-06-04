import os
import subprocess

def baixar_video(video_url):
    os.makedirs("data/videos", exist_ok=True)
    output_path = os.path.join("data/videos", "video.mp4")
    subprocess.run([
        "yt-dlp", "-f", "mp4", "-o", output_path, video_url
    ], check=True)
    return output_path
