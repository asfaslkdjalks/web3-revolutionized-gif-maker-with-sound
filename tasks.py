from celery_config import celery_app, logger
import subprocess
from PIL import Image
import shutil
import os
import re
import time

def parse_time(time_str):
    match = re.match(r'(\d+):(\d+):(\d+)', time_str)
    if match:
        hours, minutes, seconds = map(int, match.groups())
        return hours * 3600 + minutes * 60 + seconds
    elif time_str.isdigit():
        return int(time_str)
    else:
        logger.error(f"Invalid time format: {time_str}")
        return None

@celery_app.task(bind=True)
def download_images_task(self, board_url, output_directory):
    output_directory = os.path.abspath(output_directory)  # Use absolute path
    logger.info(f"Downloading images from {board_url} to {output_directory}")

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        logger.info(f"Created directory: {output_directory}")

    command = ["gallery-dl", "--dest", output_directory, board_url]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            logger.info("Download completed successfully.")
        else:
            logger.error(f"Download failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error executing gallery-dl command: {e}")
        return False

    return True

@celery_app.task(bind=True)
def download_youtube_audio_task(self, video_url, start_time, end_time, output_path):
    output_path = os.path.abspath(output_path)  # Use absolute path
    logger.info(f"Downloading YouTube audio: {video_url}, from {start_time} to {end_time}, to {output_path}")

    start_seconds = parse_time(start_time)
    end_seconds = parse_time(end_time)
    if start_seconds is None or end_seconds is None:
        logger.error("Invalid start or end time provided.")
        return False

    yt_dlp_command = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--postprocessor-args", f"-ss {start_seconds} -to {end_seconds}",
        "--output", output_path,
        video_url
    ]
    try:
        result = subprocess.run(yt_dlp_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            logger.info("YouTube audio download completed successfully.")
        else:
            logger.error(f"YT-DLP failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error executing yt-dlp command: {e}")
        return False

    return True

@celery_app.task(bind=True)
def combine_images_and_video_task(self, image_directory, audio_path, output_video_path, frame_rate=10, max_canvas_size=(1920, 1080)):
    # Combine images and audio into a video
    temp_dir = os.path.join(image_directory, "temp_frames")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    logger.info(f"Combining images from {image_directory} and audio from {audio_path} into video {output_video_path}")

    # Stacking images
    stack_images(image_directory, temp_dir, max_canvas_size)

    # Verify that frame files exist before running ffmpeg
    if not os.listdir(temp_dir):
        logger.error(f"No frames found in {temp_dir}")
        return False
    
    video_temp_path = output_video_path.replace('.mp4', '_temp.mp4')
    frame_pattern = os.path.join(temp_dir, "%05d.png")

    # Verify that frame files exist before running ffmpeg
    if not os.listdir(temp_dir):
        logger.error(f"No frames found in {temp_dir}")
        return False

    ffmpeg_command = [
        "ffmpeg",
        "-framerate", str(frame_rate),
        "-i", frame_pattern,
        "-c:v", "libx264",
        "-vf", "scale=1920:1080,format=yuv420p",
        "-preset", "veryfast",
        video_temp_path
    ]
    try:
        subprocess.run(ffmpeg_command, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create video from images: {e}")
        return False

    if audio_path and os.path.exists(audio_path):
        add_audio_command = [
            "ffmpeg",
            "-i", video_temp_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_video_path
        ]
        try:
            subprocess.run(add_audio_command, check=True)
            os.remove(video_temp_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add audio to video: {e}")
            return False

    shutil.rmtree(temp_dir)
    return True

def stack_images(image_directory, temp_dir, max_canvas_size):
    image_files = [os.path.join(image_directory, img) for img in sorted(os.listdir(image_directory)) if img.endswith((".jpg", ".jpeg", ".png"))]
    
    if not image_files:
        logger.error(f"No image files found in {image_directory}")
        return False

    # Start with a transparent base image
    base_image = Image.new('RGBA', max_canvas_size, (0, 0, 0, 0))

    for idx, image_path in enumerate(image_files):
        try:
            with Image.open(image_path) as img:
                img.thumbnail(max_canvas_size, Image.Resampling.LANCZOS)
                left = (max_canvas_size[0] - img.width) // 2
                top = (max_canvas_size[1] - img.height) // 2
                base_image.paste(img, (left, top), img if img.mode == 'RGBA' else None)

                # Save the current state of the base image
                frame_path = os.path.join(temp_dir, f"{idx:05d}.png")
                base_image.save(frame_path, format='PNG')
                logger.info(f"Saved frame: {frame_path}")
        except Exception as e:
            logger.error(f"Failed to process image {image_path}: {e}")
            return False

    return True


@celery_app.task(bind=True)
def delayed_delete_path(self, path):
    logger.info(f"Deleting path after delay: {path}")

    
    time.sleep(60)  # Sleep is used here for simplicity, but should be replaced with a more robust solution
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)