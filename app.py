from flask import Flask, render_template, request, send_file
import logging
import os
from tasks import download_images_task, download_youtube_audio_task, combine_images_and_video_task, delayed_delete_path
from celery_config import logger

# Create a Flask application instance
app = Flask(__name__)

# Define absolute paths for Docker volume
output_directory = "/app/downloaded_images"  # Directory for downloaded images
output_video_path = "/app/downloaded_images/final_combined_video.mp4"  # Path for the final combined video

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Extract form data
            board_url = request.form.get('board_url')
            youtube_url = request.form.get('youtube_url')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')

            logger.info(f"Received form data: board_url={board_url}, youtube_url={youtube_url}, start_time={start_time}, end_time={end_time}")

            # Offload tasks to Celery workers using a task chain
            chain = (download_images_task.si(board_url, output_directory) |
                     download_youtube_audio_task.si(youtube_url, start_time, end_time, "/app/downloaded_images/youtube_audio.mp3") |
                     combine_images_and_video_task.si(output_directory, "/app/downloaded_images/youtube_audio.mp3", output_video_path, 10))
            result = chain.apply_async()
            logger.info(f"Task chain with id {result.id} dispatched successfully.")

            return render_template('index.html', message="Your request is being processed. You will be able to download the video shortly.")

        except Exception as e:
            logger.error(f"Failed to dispatch task chain: {e}", exc_info=True)
            return render_template('index.html', message="An error occurred while processing your request.")

    return render_template('index.html', message="Enter a Pinterest board URL and YouTube details")

@app.route('/download')
def download():
    if os.path.exists(output_video_path):
        # Send the final video as an attachment for download
        response = send_file(output_video_path, as_attachment=True)
        
        # Schedule delayed deletion of temporary files and directories
        delayed_delete_path.apply_async(args=[output_video_path], countdown=300)
        delayed_delete_path.apply_async(args=["/app/downloaded_images/youtube_audio.mp3"], countdown=300)
        delayed_delete_path.apply_async(args=[output_directory], countdown=300)
        
        return response
    else:
        return "Video not ready yet. Please try again later."

if __name__ == "__main__":
    app.run(host='0.0.0.0')  # Run the Flask application
