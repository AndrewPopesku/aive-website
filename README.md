# AIVE - AI Video Editor

AIVE is a modern AI-powered video creation platform that transforms audio narrations into engaging videos with automatically selected stock footage and background music.

## 🎥 Features

- **Audio-to-Video Creation**: Upload audio narration and get a professionally edited video
- **AI-Powered Transcription**: Automatic speech-to-text conversion with sentence segmentation
- **Smart Stock Footage Selection**: AI suggests relevant video clips for each sentence
- **Background Music Integration**: Choose from curated music options that match your content
- **Real-time Preview**: Review your selections before final rendering
- **Professional Output**: Export high-quality videos ready for social media or presentations

## 🏗️ Architecture

AIVE follows a modern microservices architecture with:

### Backend (FastAPI + Python)
- **Framework**: FastAPI for high-performance REST API
- **Database**: SQLModel with PostgreSQL
- **AI Integration**: Groq API for transcription and content analysis
- **Video Processing**: MoviePy for video rendering
- **Containerization**: Docker support for easy deployment

### Frontend (Next.js + React)
- **Framework**: Next.js 15 with React 19
- **UI Components**: Radix UI with Tailwind CSS
- **State Management**: React hooks with custom video creator logic
- **Type Safety**: TypeScript with generated API client
- **Styling**: Tailwind CSS with custom animations

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and pnpm/npm
- Python 3.13+
- PostgreSQL (or Docker)
- Groq API key for AI features

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the development server:
   ```bash
   make dev
   # Or directly: uvicorn src.main:app --reload
   ```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   pnpm install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API endpoint
   ```

4. Run the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3000`

### Docker Setup (Alternative)

For a containerized setup:

```bash
# Backend
cd backend
docker-compose -f docker-compose.dev.yml up

# Frontend (in a new terminal)
cd frontend
npm run dev
```

## 📝 Usage

1. **Upload Audio**: Start by uploading an audio file (MP3, WAV, M4A supported)
2. **Review Transcription**: AI transcribes your audio and segments it into sentences
3. **Select Footage**: Choose from AI-suggested video clips for each sentence
4. **Add Music**: Select background music that complements your content
5. **Preview & Export**: Review your video and download the final result

## 🛠️ Development

### Project Structure

```
aive/
├── backend/
│   ├── src/
│   │   ├── main.py          # FastAPI application
│   │   ├── projects/        # Project management
│   │   ├── render/          # Video rendering
│   │   └── database/        # Database models
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── app/                 # Next.js app directory
│   ├── components/          # React components
│   ├── hooks/              # Custom React hooks
│   └── client/             # Generated API client
└── .github/                # CI/CD workflows
```

### API Documentation

When the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- Built as part of university coursework
- Uses Groq API for AI capabilities
- Stock footage integration powered by external APIs
