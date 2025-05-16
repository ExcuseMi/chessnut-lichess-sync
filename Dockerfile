FROM python:3.13-slim

# Create a non-root user and switch to it
RUN useradd -m appuser && \
    mkdir -p /app && \
    chown appuser:appuser /app

WORKDIR /app
USER appuser

# Create and activate virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create needed directories
RUN mkdir -p /app/data /app/logs && \
    touch /app/logs/main.log

# Copy application files
COPY --chown=appuser:appuser . .

CMD ["python", "main.py"]