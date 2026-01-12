from moviepy import VideoFileClip
import os

def extract_frames(video_path, output_dir, frame_duration=1.85): #Input Desired Frame Duration
    os.makedirs(output_dir, exist_ok=True)
    clip = VideoFileClip(video_path)
    total_duration = clip.duration
    times = [t for t in frange(0, total_duration, frame_duration)]
    for idx, t in enumerate(times):
        frame = clip.get_frame(t)
        frame_filename = os.path.join(output_dir, f"frame_{idx + 1:04d}.png")
        import imageio
        imageio.imwrite(frame_filename, frame)
        print(f"Saved {frame_filename}")

def frange(start, stop, step):
    t = start
    while t < stop:
        yield t
        t += step

video_path = "" #CHANGE
output_dir = "frames_output"   # Output folder

extract_frames(video_path, output_dir)