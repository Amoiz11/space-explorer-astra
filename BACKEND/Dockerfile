FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BOOTSTRAP_ON_START=true \
    PORT=8080

# Create a non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python dependencies first for caching
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the rest of the application files with ownership
COPY --chown=appuser:appuser . .

# Ensure storage directories exist and appuser can write database and storage
RUN mkdir -p storage/raw storage/processed storage/kernels && \
    chown -R appuser:appuser /app && \
    chmod -R u+rwX /app

USER appuser

EXPOSE 8080

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
