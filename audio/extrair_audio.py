import os
from moviepy.editor import VideoFileClip

def extrair_audio(video_path):
    os.makedirs("data/audio", exist_ok=True)
    audio_path = os.path.join("data/audio", "audio.wav")
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path)
    return audio_path
