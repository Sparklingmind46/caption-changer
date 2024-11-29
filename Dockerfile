# Add at the top of the Dockerfile
FROM python:3.9-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install a simple HTTP server
RUN pip install flask

# Copy the bot code
COPY main.py .


# Run both the bot and HTTP server
CMD python3 -u main.py
