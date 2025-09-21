# Video Creator Backend API

A FastAPI backend service for an interactive video creation platform with AI-powered footage recommendations and automated video rendering.

## Overview

This API provides a complete video creation workflow:

1. **Upload & Transcribe**: Upload voiceover audio files and get AI-powered transcription with timestamps
2. **AI Recommendations**: Get AI-recommended video footage for each sentence using semantic analysis
3. **Default Selections**: Backend automatically selects recommended footage as defaults
4. **Music Integration**: Get curated background music recommendations
5. **Video Rendering**: Render final videos with chosen footage, voiceover, and background music
6. **Database Persistence**: All project data is stored in SQLite for reliable state management

## Key Features

- **AI-Powered Transcription**: Uses Groq's Whisper model for accurate speech-to-text
- **Smart Footage Matching**: Semantic analysis to find relevant video content from Pexels
- **Automatic Defaults**: Backend pre-selects recommended footage to streamline user experience
- **Background Music**: Curated music recommendations from Pixabay
- **Video Processing**: MoviePy-based rendering with subtitle support
- **Database Persistence**: SQLite database for reliable project state management
- **Async Processing**: Background task processing for video rendering

## Project Structure

```
/backend
├── .venv/                  # Python virtual environment
├── app/                    # Application code
│   ├── __init__.py
│   ├── main.py             # FastAPI app initialization
│   ├── config.py           # Configuration and environment variables
│   ├── database.py         # SQLAlchemy database configuration
│   ├── models.py           # SQLAlchemy ORM models
│   ├── schemas.py          # Pydantic request/response models
│   ├── services.py         # AI services and video processing
│   ├── db_service.py       # Database CRUD operations
│   └── routers/            # API route definitions
│       ├── __init__.py
│       └── project.py      # Main project workflow endpoints
├── static/                 # Static file serving
│   ├── output/             # Rendered video files
│   └── temp/               # Temporary processing files
├── tests/                  # Test suite
├── video_creator.db        # SQLite database file
├── requirements.txt        # Python dependencies
└── README.md               # This documentation
```

## API Workflow

### Step A: Create Project & Get AI Recommendations

```
POST /api/v1/projects
```

Upload audio file and get transcription with AI-recommended footage automatically selected.

Request: `multipart/form-data` with `audio_file` and optional `title`, `description`.

Response:
```json
{
  "project_id": "proj-xyz123",
  "sentences": [
    {
      "id": 1,
      "project_id": "proj-xyz123",
      "text": "Hello world, this is an amazing video.",
      "start_time": 0.5,
      "end_time": 2.0,
      "selected_footage": {
        "id": "pexels-video-123",
        "title": "Amazing Landscape",
        "description": "Beautiful mountain scenery",
        "thumbnail": "https://images.pexels.com/...",
        "duration": 15.0,
        "tags": ["nature", "landscape", "mountains"],
        "category": "nature",
        "mood": "inspiring",
        "relevance_score": 0.89,
        "url": "https://videos.pexels.com/video-files/123/video.mp4"
      }
    }
  ]
}
```

**Note**: The backend automatically selects the best AI-recommended footage for each sentence, eliminating the need for manual selection in most cases.

### Step B: Submit Footage Choices (Optional) & Get Music Recommendations

```
POST /api/v1/projects/{project_id}/footage
```

Submit custom footage choices (optional, since defaults are pre-selected) and receive music recommendations.

Request:
```json
{
  "footage_choices": [
    { 
      "sentence_id": 1, 
      "footage_url": "https://custom-video.com/video.mp4" 
    }
  ]
}
```

Response:
```json
{
  "project_id": "proj-xyz123",
  "recommended_music": [
    { 
      "id": "music-1", 
      "name": "Inspiring Ambient", 
      "url": "https://pixabay.com/music/ambient-123.mp3" 
    },
    { 
      "id": "music-2", 
      "name": "Upbeat Corporate", 
      "url": "https://pixabay.com/music/corporate-456.mp3" 
    }
  ]
}
```

### Step C: Render Final Video

```
POST /api/v1/projects/{project_id}/render
```

Start background video rendering with selected music and subtitle options.

Request:
```json
{
  "music_url": "https://pixabay.com/music/ambient-123.mp3",
  "add_subtitles": true
}
```

Response (202 Accepted):
```json
{
  "render_task_id": "render-789abc",
  "status_url": "/api/v1/render/status/render-789abc"
}
```

### Step D: Check Render Status & Download

```
GET /api/v1/render/status/{render_task_id}
```

Poll for render completion and get download URL.

Response (Processing):
```json
{
  "status": "processing"
}
```

Response (Complete):
```json
{
  "status": "complete",
  "video_url": "/static/output/proj-xyz123_20250608_143022.mp4"
}
```

Response (Failed):
```json
{
  "status": "failed",
  "error": "Detailed error message for debugging"
}
```

## Setup & Installation

### Prerequisites

- Python 3.8 or higher
- API keys for external services:
  - **Groq API**: For AI-powered audio transcription
  - **Pexels API**: For video footage recommendations  
  - **Pixabay API**: For background music recommendations

### Quick Start

1. **Clone and navigate to backend directory:**
```bash
cd backend
```

2. **Create and activate virtual environment:**
```bash
# Create virtual environment
python -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

3. **Install dependencies:**
```bash
# Using pip
pip install -r requirements.txt

# Or using uv (faster)
uv pip install -r requirements.txt
```

4. **Configure environment variables:**

Create a `.env` file in the backend directory:
```env
# Required API Keys
GROQ_API_KEY=your_groq_api_key_here
PEXELS_API_KEY=your_pexels_api_key_here  
PIXABAY_API_KEY=your_pixabay_api_key_here

# Optional Configuration
DATABASE_URL=sqlite:///./video_creator.db
TEMP_DIR=./static/temp
OUTPUT_DIR=./static/output
```

5. **Initialize database:**
```bash
# Database tables are created automatically on first run
python -c "from app.database import create_tables; create_tables()"
```

6. **Start the development server:**
```bash
# Standard FastAPI development server
uvicorn app.main:app --reload --port 8000

# Or using uv for faster startup
uv run fastapi dev app/main.py --port 8000
```

7. **Access the application:**
   - **API Documentation**: http://localhost:8000/docs
   - **Alternative Docs**: http://localhost:8000/redoc
   - **Health Check**: http://localhost:8000/health

### Production Deployment

For production environments:

```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Database Schema

The application uses SQLite with the following main tables:

- **projects**: Store project metadata and audio file paths
- **sentences**: Store transcribed text with timestamps and selected footage
- **footage_choices**: Store user's custom footage selections
- **music_recommendations**: Store AI-generated music suggestions
- **render_tasks**: Track video rendering status and results

## Configuration

Key configuration options (set via environment variables):

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | Required | API key for Groq transcription service |
| `PEXELS_API_KEY` | Required | API key for Pexels video footage |
| `PIXABAY_API_KEY` | Required | API key for Pixabay music |
| `DATABASE_URL` | `sqlite:///./video_creator.db` | Database connection string |
| `TEMP_DIR` | `./static/temp` | Temporary file storage directory |
| `OUTPUT_DIR` | `./static/output` | Rendered video output directory |

## API Features

### Smart Defaults
- **Auto-Selection**: AI recommendations are automatically selected as defaults
- **Streamlined UX**: Users can proceed without manual footage selection
- **Override Option**: Users can still customize footage choices if desired

### Background Processing
- **Async Rendering**: Video processing runs in background tasks
- **Status Polling**: Real-time render progress tracking
- **Error Handling**: Detailed error reporting for failed renders

### File Management
- **Temporary Storage**: Automatic cleanup of processing files
- **Static Serving**: Direct video file serving via `/static/` endpoint
- **Format Support**: MP3 audio input, MP4 video output

## Troubleshooting

### Common Issues

1. **Port already in use**:
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9
# Or use different port
uvicorn app.main:app --reload --port 8001
```

2. **Missing API keys**:
```bash
# Check .env file exists and contains required keys
cat .env
```

3. **Database errors**:
```bash
# Recreate database
rm video_creator.db
python -c "from app.database import create_tables; create_tables()"
```

4. **Dependency issues**:
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Logging

Enable debug logging by setting environment variable:
```bash
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload
``` 