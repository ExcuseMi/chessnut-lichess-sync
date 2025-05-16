FROM python:3.13-slim

WORKDIR /app

# Install dependencies first (cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Then copy the rest of the code (changes frequently)
COPY . .

# Create needed directories
RUN mkdir -p /app/data /app/logs

CMD ["python", "main.py"]