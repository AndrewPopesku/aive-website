# AIVE Backend - Modern Python Architecture

Modern AI Video Editor Backend built with FastAPI, SQLModel, and domain-driven design principles.

## 🏗️ Architecture

This project follows a **domain-driven design (DDD)** approach with clean architecture principles:

```
src/
├── base/                    # Core utilities & base classes
├── projects/                # Project domain (video projects)
├── render/                  # Render domain (video rendering)
├── video_processing/        # Video processing services
├── database/                # Database configuration
└── server_api.py           # FastAPI application entry point
```

### Key Features

- **Modern Python 3.13+** with async/await patterns
- **FastAPI** for high-performance API development
- **SQLModel/SQLAlchemy** for type-safe database operations
- **PostgreSQL** with async driver (AsyncPG)
- **UV** as modern package manager
- **Domain-driven design** with clear separation of concerns
- **Comprehensive testing** with pytest
- **Docker** containerization support

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- UV package manager
- PostgreSQL (or use Docker)
- FFmpeg (for video processing)

### Installation

1. **Clone and navigate to the backend directory**
   ```bash
   cd backend
   ```

2. **Install dependencies**
   ```bash
   make install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start development database**
   ```bash
   make rundb
   ```

5. **Run database migrations**
   ```bash
   make upgrade
   ```

6. **Start the development server**
   ```bash
   make run
   ```

The API will be available at `http://localhost:8000`

## 📋 Available Commands

```bash
# Development
make install    # Install dependencies with UV
make run        # Start development server
make rundb      # Start database services with Docker

# Code Quality
make format     # Format code with ruff
make lint       # Lint code with ruff

# Testing
make test       # Run tests
make coverage   # Run tests with coverage

# Database
make migrate    # Create new database migration
make upgrade    # Apply database migrations

# Utilities
make clean      # Clean cache and temp files
make help       # Show available commands
```

## 🏗️ Domain Structure

### Projects Domain (`src/projects/`)
Handles video project management:
- **Models**: Project, Sentence, FootageChoice, MusicRecommendation
- **API Endpoints**: CRUD operations for projects
- **Features**: Audio transcription, footage selection, music recommendations

### Render Domain (`src/render/`)
Manages video rendering tasks:
- **Models**: RenderTask
- **API Endpoints**: Render management and status tracking
- **Features**: Background task processing, progress tracking

### Video Processing (`src/video_processing/`)
Core video processing services:
- **Audio transcription** using Groq API
- **Video footage search** via Pexels API
- **Translation services** for multi-language support
- **File download and processing utilities**

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

## 🐳 Docker Support

### Development with Docker

```bash
# Start database services
make rundb

# Build and run the application
docker build -t aive-backend .
docker run -p 8000:8000 aive-backend
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
make coverage
```

For detailed documentation and troubleshooting, see the full documentation in the project.