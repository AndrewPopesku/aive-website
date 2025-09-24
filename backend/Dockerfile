FROM python:3.13-slim

# Copy UV installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Set Python path
ENV PYTHONPATH=/app/src

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy project configuration files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv venv && uv sync

# Copy source code
COPY src/ /app/src/
COPY alembic.ini run.sh ./

# Create necessary directories
RUN mkdir -p /app/static/{temp,output,audio}

# Make run script executable
RUN chmod +x run.sh

# Expose port
EXPOSE 8000

# Run the application
CMD ["./run.sh"]