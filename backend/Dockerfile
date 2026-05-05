FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2 and pdfplumber (if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory content
COPY . ./backend

# Copy the .env from the root if needed (though we'll pass env vars via docker-compose)
# COPY ../.env .

# Set PYTHONPATH so that it can find the backend package
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
