FROM python:3.13-slim

WORKDIR /app

# Create a non-root user with the same UID/GID as host
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID appuser && \
    useradd -u $UID -g $GID -m appuser && \
    mkdir -p /data && \
    chown appuser:appuser /data

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY --chown=appuser:appuser . .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

USER appuser

CMD ["python", "main.py"]