FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DOCKER_ENV true

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/data
RUN mkdir -p /app/logs
# Copy application
COPY . .

# Create log directory
RUN touch /app/logs/main.log

CMD ["python", "main.py"]