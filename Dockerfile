FROM python:3.9-slim-buster

WORKDIR /app

# Install FFmpeg and build dependencies
RUN apt-get update && apt-get install -y ffmpeg build-essential libffi-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY .env .
COPY . .

CMD ["python", "Deploy.py"]
