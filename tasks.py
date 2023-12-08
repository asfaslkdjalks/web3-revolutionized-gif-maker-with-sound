from celery_config import celery_app, logger
import subprocess
from PIL import Image
import shutil
import os
import re
import time
from time import sleep

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
    
def clear_directory(directory):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")

@celery_app.task(bind=True)
def download_images_task(self, board_url, output_directory):
    clear_directory(output_directory)
    if not os.path.exists(output_directory):
        try:
            os.makedirs(output_directory)
            logger.info(f"Created directory: {output_directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {output_directory}: {e}")
            return False

    command = ["gallery-dl", "--dest", output_directory, board_url]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            logger.info("Download completed successfully.")
        else:
            logger.error(f"Download failed with return code {result.returncode}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired as e:
        logger.error(f"Download timed out: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error executing gallery-dl command: {e}")
        return False

    # Log the directory structure after download
    logger.info(f"Directory contents of {output_directory} after download:")
    for root, dirs, files in os.walk(output_directory):
        for name in files:
            logger.info(os.path.join(root, name))

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

# Additional function to clear existing files
def clear_existing_files(*file_paths):
    for path in file_paths:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            logger.info(f"Cleared existing file or directory: {path}")

@celery_app.task(bind=True)
def combine_images_and_video_task(self, image_directory, audio_path, output_video_path, frame_rate=10, max_canvas_size=(1920, 1080)):
    # Clear existing files before starting
    video_temp_path = output_video_path.replace('.mp4', '_temp.mp4')
    clear_existing_files(output_video_path, video_temp_path)
    # Clear previous temporary files
    temp_dir = os.path.join(image_directory, "temp_frames")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    # Combine images and audio into a video
    temp_dir = os.path.join(image_directory, "temp_frames")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    logger.info(f"Combining images from {image_directory} and audio from {audio_path} into video {output_video_path}")

    # Log directory contents for debugging
    logger.info(f"Contents of '{image_directory}': {os.listdir(image_directory)}")
    if os.path.exists(temp_dir):
        logger.info(f"Contents of '{temp_dir}': {os.listdir(temp_dir)}")
    else:
        logger.error(f"Directory not found: {temp_dir}")
        return False

    # Stacking images
    if not stack_images(image_directory, temp_dir, max_canvas_size):
        logger.error(f"Failed to stack images in {temp_dir}")
        return False

    frame_pattern = os.path.join(temp_dir, "%05d.png")

    # Creating video from images using ffmpeg
    ffmpeg_command = [
        "ffmpeg",
        "-y",  # Automatically overwrite existing files
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

    # Adding audio to the video if audio file exists
    if audio_path and os.path.exists(audio_path):
        add_audio_command = [
            "ffmpeg",
            "-y",  # Automatically overwrite existing files
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

    # Clean up temporary frame directory
    shutil.rmtree(temp_dir)
    return True


def find_deepest_subdirectory_with_images(directory):
    for root, _, files in os.walk(directory, topdown=True):
        if any(file.lower().endswith((".jpg", ".jpeg", ".png")) for file in files):
            return root
    return None

def stack_images(image_directory, temp_dir, max_canvas_size):
    # Dynamically find the deepest subdirectory with images
    subdirectory = find_deepest_subdirectory_with_images(image_directory)
    if not subdirectory:
        logger.error(f"No image files found in any subdirectory of {image_directory}")
        return False

    image_files = [os.path.join(subdirectory, img) for img in sorted(os.listdir(subdirectory)) if img.endswith((".jpg", ".jpeg", ".png"))]
    
    # Initialize a transparent base image
    base_image = Image.new('RGBA', max_canvas_size, (0, 0, 0, 0))

    for idx, image_path in enumerate(image_files):
        try:
            with Image.open(image_path) as img:
                img.thumbnail(max_canvas_size, Image.Resampling.LANCZOS)
                left = (max_canvas_size[0] - img.width) // 2
                top = (max_canvas_size[1] - img.height) // 2

                # Create a new image for the current frame
                current_frame = Image.new('RGBA', max_canvas_size, (0, 0, 0, 0))
                current_frame.paste(base_image, (0, 0))
                current_frame.paste(img, (left, top), img if img.mode == 'RGBA' else None)

                # Update the base image for the next iteration
                base_image = current_frame

                # Save the current state of the base image
                frame_path = os.path.join(temp_dir, f"{idx:05d}.png")
                current_frame.save(frame_path, format='PNG')
                logger.info(f"Saved frame: {frame_path}")
        except Exception as e:
            logger.error(f"Failed to process image {image_path}: {e}")
            return False

    return True

@celery_app.task(bind=True)
def delayed_delete_path(self, path, max_retries=5, sleep_interval=10):
    logger.info(f"Deleting path after delay: {path}")

    for attempt in range(max_retries):
        try:
            if os.path.isdir(path):
                # Delete individual files first
                for filename in os.listdir(path):
                    file_path = os.path.join(path, filename)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                # Attempt to remove the directory
                os.rmdir(path)
                logger.info(f"Successfully deleted directory: {path}")
                break
            elif os.path.exists(path):
                # Delete the file directly if it's not a directory
                os.remove(path)
                logger.info(f"Successfully deleted file: {path}")
                break
        except OSError as e:
            logger.error(f"Error deleting {path}: {e}. Retrying...")
            sleep(sleep_interval)
    else:
        logger.error(f"Failed to delete {path} after {max_retries} attempts.")






def find_images_in_directory(directory):
    image_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_files.append(os.path.join(root, file))
    return image_files
