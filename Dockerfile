# Lightweight Python Base
FROM python:3.10-slim

# Set the working directory inside the cloud container
WORKDIR /app

# Copy your entire folder into the container
COPY . /app

# Install your libraries
RUN pip install --no-cache-dir -r requirements.txt

# Hugging Face Spaces explicitly expects the web app to bind to port 7860
ENV PORT=7860
# Set up internal communication for the Bot
ENV API_BASE_URL=http://127.0.0.1:7860

# Boot up the backend in the background and the bot in the foreground!
CMD uvicorn main:app --host 0.0.0.0 --port $PORT & sleep 5 && exec python -u bot.py
