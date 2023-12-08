from flask import Flask, render_template, request, send_file, url_for, redirect
from tasks import download_images_task, download_youtube_audio_task, combine_images_and_video_task, delayed_delete_path
from celery_config import celery_app, logger
import os

app = Flask(__name__)

# Define absolute paths for Docker volume
output_directory = "/app/downloaded_images"
output_video_path = os.path.join(output_directory, "final_combined_video.mp4")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            board_url = request.form.get('board_url')
            youtube_url = request.form.get('youtube_url')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')

            logger.info(f"Received form data: board_url={board_url}, youtube_url={youtube_url}, start_time={start_time}, end_time={end_time}")

            chain = (download_images_task.si(board_url, output_directory) |
                     download_youtube_audio_task.si(youtube_url, start_time, end_time, os.path.join(output_directory, "youtube_audio.mp3")) |
                     combine_images_and_video_task.si(output_directory, os.path.join(output_directory, "youtube_audio.mp3"), output_video_path))
            result = chain.apply_async()

            return redirect(url_for('status', task_id=result.id))

        except Exception as e:
            logger.error(f"Failed to dispatch task chain: {e}", exc_info=True)
            return render_template('index.html', message="An error occurred while processing your request.")

    return render_template('index.html')

@app.route('/status/<task_id>')
def status(task_id):
    task = celery_app.AsyncResult(task_id)
    download_link = None  # Initialize download_link to None

    if task.state == 'PENDING':
        message = "Your request is still being processed..."
    elif task.state == 'SUCCESS':
        if task.result:  # assuming the task returns True on success
            message = "Your request was processed successfully!"
            download_link = url_for('download')
        else:
            message = "An error occurred during processing."
    else:
        # Handle other states like FAILURE, RETRY, etc.
        message = f"An error occurred: {str(task.info)}"

    return render_template('status.html', message=message, task_id=task_id, download_link=download_link)


@app.route('/download')
def download():
    file_path = os.path.join(output_directory, "final_combined_video.mp4")
    if os.path.exists(file_path):
        response = send_file(file_path, as_attachment=True)

        # Schedule deletion of resources after a delay (e.g., 5 minutes)
        delayed_delete_path.apply_async(args=[output_directory], countdown=300)
        return response
    else:
        return "Video not ready yet. Please try again later."



if __name__ == "__main__":
    app.run(host='0.0.0.0')
