FROM python:3.13-alpine

# Set the working directory
COPY . /app
WORKDIR /app

RUN mkdir /data
VOLUME "/data"

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENV IS_CONTAINERIZED=true
ENV REMOTE_CHROMIUM=http://selenium:4444/wd/hub

CMD ["python", "amazon-deals-telegram-bot"]