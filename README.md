# web<sub>3</sub> revolutionized gif<sub>(mp4)</sub> maker with-sound
the easiest interface to create captivating collages.

envision a medium that transcends mere entertainment to critically engage with the intricacies of internet culture—a collage that's less a random patchwork and more a deliberate mosaic of the zeitgeist. each segment is curated with the precision of an artisan, echoing the spirit of abstract, multi-layered narratives that captivate the cybernetic soul. imagine the essence of a story that delves deep into the fabric of virtual existence, questioning the very nature of reality and self—themes that resonate with those who find solace and identity in the realms of pixels and data streams.

the collage becomes an arena where the philosophical undercurrents that flow through subterranean digital cultures come to the fore. it's a place where visuals from the annals of the internet are woven together, hinting at a reality where identity is fluid, and existence is as much virtual as it is physical. it's a digital landscape that subtly nods to the complexity of a world where the ‘wired’ and the 'real' blur, reflecting a narrative that is etched into the collective memory of an entire generation that has grown up with the hum of the of a pc fan as a lullaby.

in this realm, sound marries the visual in a dance that is as old as time, yet as fresh as the latest trend. the integration of auditory elements is not just an addition—but an essential layer that complements the visual—creating an immersive experience that invites introspection and connection. this isn't just a collage; it's a dialogue, a contemplative exploration of the enigmatic relationship between humanity and the ever-expanding digital universe.

## witness it in action

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
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='Europe/London',
    enable_utc=True,
)

celery_app.log.setup_task_loggers()

__all__ = ['celery_app', 'logger']
```

you may choose to run this application in Docker, in which case you'll need to attach a Dockerfile that may look something like this:
```docker
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

## real-time testing

we're in the thick of prepping a live testing zone for this tool, so u can jump right into it on your own. it won't be long till you're getting hands-on, experimenting with its tricks and really getting the full picture, all going down in real time.

## performance that astounds

our tool is built on a foundation of cutting-edge technology, utilizing rabbitmq as a message broker. this architecture empowers the application to handle exceptional levels of throughput and scalability, ensuring your creative endeavors are never limited by technical constraints.

- maximum throughput: up to a staggering 40,000 messages per second.
- maximum queue size: support for up to 50,000 messages.

## take the leap

if you're keen to dive into what's possible, we're all for you getting your hands dirty with setting up and running web3-revolutionized-gif-maker-5000-with-sound on your own

what you'll need:

- erlang
- rabbitmq
- ffmpeg
- yt-dlp
- flask
- celery
- other stuff..


bingus
