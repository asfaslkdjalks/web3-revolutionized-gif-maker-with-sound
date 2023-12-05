
# web<sub>3</sub> revolutionized gif<sub>(mp4)</sub> maker<sub>(with sound)</sub>

what you'll need:
- **erlang**: [Erlang Official Website](https://www.erlang.org/)
- **rabbitMQ**: [RabbitMQ Official Website](https://www.rabbitmq.com/)
- **ffmpeg**: [FFmpeg Official Website](https://ffmpeg.org/)
- **yt-dlp**: [yt-dlp on GitHub](https://github.com/yt-dlp/yt-dlp)
- **flask**: [Flask Official Website](https://flask.palletsprojects.com/en/2.0.x/)
- **celery**: [Celery Official Website](https://docs.celeryproject.org/en/stable/index.html)
- ... other stuff


envision a medium that transcends mere entertainment to critically engage with the intricacies of internet culture—a collage that's less a random patchwork and more a deliberate mosaic of the zeitgeist. each segment is curated with the precision of an artisan, echoing the spirit of abstract, multi-layered narratives that captivate the cybernetic soul. imagine the essence of a story that delves deep into the fabric of virtual existence, questioning the very nature of reality and self—themes that resonate with those who find solace and identity in their data streams.

**the collage becomes an arena where the philosophical undercurrents that flow through subterranean digital cultures come to the fore.** it's a place where visuals from the annals of the internet are woven together, hinting at a reality where identity is fluid, and existence is as much virtual as it is physical. it's a digital landscape that subtly nods to the complexity of a world where the **‘wired’** and the **'real'** blur, reflecting a narrative that is etched into the collective memory of an entire generation that has grown up with the hum of the of a pc fan as a lullaby.

## a confluence of visual and auditory exploration

sound marries the visual in a dance as old as time, yet as fresh as the latest trend. the integration of auditory elements isn't merely an addition—it's an essential layer that complements the visual—creating an immersive experience that invites introspection and connection. this isn't just a collage; it's a dialogue, a contemplative exploration of the enigmatic relationship between humanity and the ever-expanding digital universe.

---

the simple act of submitting a form morphs your inputs into a unique creative process:
```python
chain = (
    download_images_task.si(board_url, output_directory) |
    download_youtube_audio_task.si(youtube_url, start_time, end_time, "/app/downloaded_images/youtube_audio.mp3") |
    combine_images_and_video_task.si(output_directory, "/app/downloaded_images/youtube_audio.mp3", output_video_path, 10)
)
result = chain.apply_async()
```

remember, if you plan on running this on you're own, you'll need a `celery_config.py` file that looks something like this:
```python
celery_app = Celery(
    __name__,
    broker='amqp://guest:guest@rabbitmq:5672//',
    backend='rpc://',
    include=['tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/London',
    enable_utc=True,
)

celery_app.log.setup_task_loggers()

__all__ = ['celery_app', 'logger']
```
---
you may choose to run this application in Docker, in which case you'll need to attach a Dockerfile that may look something like this:
```Dockerfile
# WARNING: THE CONFIGURATIONS IN THIS DOCKERFILE ARE NOT DESIGNED FOR SECURITY.
# PLEASE ENSURE TO REVIEW AND MODIFY THEM ACCORDING TO YOUR SECURITY REQUIREMENTS.

# WARNING: THE CONFIGURATIONS IN THIS DOCKERFILE ARE NOT DESIGNED FOR SECURITY.
# PLEASE ENSURE TO REVIEW AND MODIFY THEM ACCORDING TO YOUR SECURITY REQUIREMENTS.

# WARNING: THE CONFIGURATIONS IN THIS DOCKERFILE ARE NOT DESIGNED FOR SECURITY.
# PLEASE ENSURE TO REVIEW AND MODIFY THEM ACCORDING TO YOUR SECURITY REQUIREMENTS.


# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Install FFmpeg
RUN apt-get update \
    && apt-get install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV NAME World

# Set broad permissions on /app directory to avoid potential permission issues
RUN chmod -R 777 /app

# Run app.py when the container launches
CMD ["python", "app.py"]
```
---
and a docker-compose file which may look like this:
```yaml
# WARNING: THE CONFIGURATIONS IN THIS DOCKERFILE ARE NOT DESIGNED FOR SECURITY.
# PLEASE ENSURE TO REVIEW AND MODIFY THEM ACCORDING TO YOUR SECURITY REQUIREMENTS.

# WARNING: THE CONFIGURATIONS IN THIS DOCKERFILE ARE NOT DESIGNED FOR SECURITY.
# PLEASE ENSURE TO REVIEW AND MODIFY THEM ACCORDING TO YOUR SECURITY REQUIREMENTS.

# WARNING: THE CONFIGURATIONS IN THIS DOCKERFILE ARE NOT DESIGNED FOR SECURITY.
# PLEASE ENSURE TO REVIEW AND MODIFY THEM ACCORDING TO YOUR SECURITY REQUIREMENTS.

version: '3'

services:
  rabbitmq:
    image: "rabbitmq:3-management"
    ports:
      - "5672:5672"
      - "15672:15672"
    hostname: rabbitmq

  worker:
    build: .
    command: celery -A celery_config worker --loglevel=info
    environment:
      - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
    depends_on:
      - rabbitmq
    volumes:
      - shared_data:/app/downloaded_images

  web:
    build: .
    ports:
      - "5000:5000"
    command: python app.py
    depends_on:
      - rabbitmq
    volumes:
      - shared_data:/app/downloaded_images

volumes:
  shared_data:
```
---
