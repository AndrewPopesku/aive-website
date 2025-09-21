# Video Creator Frontend

A modern React/Next.js frontend application for the AI-powered video creation platform. Built with TypeScript, Tailwind CSS, and shadcn/ui components.

## Overview

This frontend provides an intuitive interface for creating videos from voiceover audio files with AI-powered footage recommendations and automated video rendering.

### User Journey

1. **Audio Upload**: Upload voiceover audio files with drag-and-drop support
2. **AI Processing**: Automatic transcription and AI-recommended footage selection
3. **Customization**: Optional footage customization and background music selection
4. **Video Rendering**: Real-time rendering progress with downloadable results

## Key Features

- **Modern React Architecture**: Built with Next.js 15, React 19, and TypeScript
- **Beautiful UI**: shadcn/ui components with Tailwind CSS styling
- **Responsive Design**: Mobile-first approach with adaptive layouts
- **Type-Safe API**: Auto-generated TypeScript client from OpenAPI spec
- **Real-time Updates**: Live progress tracking and status polling
- **Drag & Drop**: Intuitive file upload with visual feedback
- **Dark/Light Mode**: Theme switching with next-themes
- **Form Validation**: React Hook Form with Zod schema validation

## Tech Stack

### Core Framework
- **Next.js 15**: React framework with App Router
- **React 19**: Latest React with concurrent features
- **TypeScript**: Type-safe development

### Styling & UI
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: High-quality React components
- **Radix UI**: Accessible component primitives
- **Lucide React**: Beautiful icon library

### State & Data
- **React Hook Form**: Performant forms with easy validation
- **Zod**: TypeScript-first schema validation
- **Axios**: HTTP client for API communication
- **@hey-api/openapi-ts**: Auto-generated API client

### Development Tools
- **ESLint**: Code linting and formatting
- **PostCSS**: CSS processing and optimization
- **Autoprefixer**: Automatic vendor prefixing

## Project Structure

```
/frontend
├── app/                    # Next.js App Router
│   ├── globals.css         # Global styles
│   ├── layout.tsx          # Root layout component
│   └── page.tsx            # Home page
├── components/             # React components
│   ├── ui/                 # shadcn/ui base components
│   ├── upload-step.tsx     # Audio upload interface
│   ├── segmentation-step.tsx # Footage selection (legacy)
│   ├── preview-step.tsx    # Video preview and rendering
│   └── theme-provider.tsx  # Theme context provider
├── hooks/                  # Custom React hooks
│   ├── useVideoCreator.ts  # Main video creation logic
│   ├── use-mobile.tsx      # Responsive breakpoint hook
│   └── use-toast.ts        # Toast notification hook
├── lib/                    # Utility libraries
│   ├── api-client.ts       # API configuration
│   └── utils.ts            # Common utilities
├── client/                 # Auto-generated API client
│   ├── client.gen.ts       # HTTP client
│   ├── types.gen.ts        # TypeScript types
│   └── sdk.gen.ts          # SDK methods
├── types/                  # Custom TypeScript types
│   └── video-creator.ts    # Application-specific types
├── public/                 # Static assets
├── styles/                 # Additional stylesheets
├── video-creator-app.tsx   # Main application component
├── package.json            # Dependencies and scripts
└── README.md               # This documentation
```

## Setup & Installation

### Prerequisites

- **Node.js 18+**: Latest LTS version recommended
- **Package Manager**: npm, yarn, or pnpm
- **Backend API**: Video Creator Backend running on `http://localhost:8001`

### Quick Start

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
# Using npm
npm install

# Using yarn
yarn install

# Using pnpm (recommended)
pnpm install
```

3. **Configure environment:**

Create `.env.local` file in the frontend directory:
```env
# Backend API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
NEXT_PUBLIC_API_VERSION=v1

# Optional: Development settings
NODE_ENV=development
```

4. **Generate API client (if backend schema changed):**
```bash
# Update OpenAPI specification
npm run generate-client

# Or manually copy from backend
cp ../backend/openapi.json ./openapi.json
npx @hey-api/openapi-ts -i openapi.json -o client -c axios
```

5. **Start development server:**
```bash
# Development mode with hot reload
npm run dev

# Alternative ports if 3000 is taken
npm run dev -- --port 3001
```

6. **Access the application:**
   - **Development Server**: http://localhost:3000
   - **Alternative Port**: http://localhost:3001

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm run start

# Or export static files
npm run build && npm run export
```

## Application Architecture

### Component Hierarchy

```
VideoCreatorApp
├── UploadStep
│   ├── FileUpload (drag & drop)
│   ├── ProgressIndicator
│   └── AudioPreview
├── SegmentationStep (legacy - auto-skipped)
│   ├── SentenceList
│   ├── FootageSelector
│   └── AIRecommendations
└── PreviewStep
    ├── VideoPreview
    ├── MusicSelector
    ├── RenderControls
    └── DownloadInterface
```

### State Management

The application uses a centralized hook pattern with `useVideoCreator`:

```typescript
const {
  // State
  currentStep,
  project,
  isProcessing,
  
  // Actions
  processAudioFile,
  selectBackgroundMusic,
  renderProject,
  
  // Navigation
  nextStep,
  previousStep,
  
  // Render Status
  renderTaskId,
  renderStatus,
  videoUrl
} = useVideoCreator()
```

### API Integration

Type-safe API client automatically generated from backend OpenAPI specification:

```typescript
// Auto-generated from OpenAPI spec
import { createProject, submitFootageChoices, renderProject } from '@/client'

// Type-safe request/response handling
const response = await createProject({
  multipart: { audio_file: file }
})
```

## Key Features & Components

### 1. Audio Upload (`UploadStep`)
- **Drag & Drop**: Visual upload interface
- **File Validation**: Audio format and size checking
- **Progress Tracking**: Upload and processing status
- **Audio Preview**: Playback controls for uploaded files

### 2. Footage Selection (Auto-handled)
- **AI Recommendations**: Backend provides pre-selected footage
- **Automatic Progression**: Skips manual selection step
- **Smart Defaults**: Uses AI-recommended footage automatically

### 3. Video Preview (`PreviewStep`)
- **Real-time Rendering**: Background video processing
- **Music Selection**: Background music options
- **Progress Monitoring**: Live render status updates
- **Download Interface**: Direct video download links

### 4. Responsive Design
- **Mobile-First**: Optimized for all screen sizes
- **Touch-Friendly**: Mobile gesture support
- **Adaptive Layout**: Dynamic component sizing

## API Client Configuration

The frontend uses auto-generated TypeScript client for type-safe API communication:

### Client Generation

```bash
# Install OpenAPI TypeScript generator
npm install @hey-api/openapi-ts --save-dev

# Generate client from OpenAPI spec
npx @hey-api/openapi-ts -i openapi.json -o client -c axios
```

### Usage Examples

```typescript
// Import generated client
import { createProject, getRenderStatus } from '@/client'

// Type-safe API calls
const projectResponse = await createProject({
  multipart: {
    audio_file: audioFile,
    title: "My Video Project"
  }
})

// Automatic type inference
const status = await getRenderStatus({
  path: { render_task_id: taskId }
})
```

## Development Workflow

### Component Development

1. **Create Component**: Use shadcn/ui as base
2. **Add Types**: Define TypeScript interfaces
3. **Implement Logic**: Connect to useVideoCreator hook
4. **Style**: Apply Tailwind CSS classes
5. **Test**: Verify functionality and responsiveness

### API Updates

1. **Backend Changes**: Update backend OpenAPI spec
2. **Copy Spec**: Copy `openapi.json` from backend
3. **Regenerate Client**: Run client generation script
4. **Update Types**: Fix any TypeScript errors
5. **Test Integration**: Verify API functionality

### Styling Guidelines

- **Tailwind First**: Use Tailwind utilities over custom CSS
- **Component Variants**: Use class-variance-authority for component states
- **Responsive Design**: Mobile-first breakpoint approach
- **Theme Support**: Support both light and dark modes

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8001` | Backend API base URL |
| `NEXT_PUBLIC_API_VERSION` | `v1` | API version prefix |
| `NODE_ENV` | `development` | Build environment |

## Browser Support

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+
- **Mobile**: iOS Safari 14+, Chrome Mobile 90+

## Performance Optimizations

- **Code Splitting**: Automatic route-based splitting
- **Image Optimization**: Next.js automatic image optimization
- **Bundle Analysis**: Built-in bundle analyzer
- **Lazy Loading**: Component-level lazy loading
- **API Caching**: Intelligent response caching

## Troubleshooting

### Common Issues

1. **API Connection Errors**:
```bash
# Check backend is running
curl http://localhost:8001/health

# Verify API base URL in .env.local
cat .env.local
```

2. **TypeScript Errors After API Changes**:
```bash
# Regenerate API client
npm run generate-client

# Clear Next.js cache
rm -rf .next && npm run dev
```

3. **Build Failures**:
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run build
```

4. **Styling Issues**:
```bash
# Rebuild Tailwind CSS
npm run dev

# Check for conflicting styles
npx tailwindcss-debug
```

### Development Tips

- **Hot Reload**: Changes auto-refresh in development
- **Component Preview**: Use React DevTools for debugging
- **Network Tab**: Monitor API calls in browser DevTools
- **Console Logging**: Use browser console for debugging

## Contributing

1. **Code Style**: Follow existing patterns and ESLint rules
2. **Type Safety**: Maintain strict TypeScript compliance
3. **Component Structure**: Use consistent component patterns
4. **Documentation**: Update README for significant changes
5. **Testing**: Verify functionality across different screen sizes

## Scripts Reference

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint

# API Client
npm run generate-client  # Regenerate API client from OpenAPI spec

# Analysis
npm run analyze      # Bundle size analysis
```

This frontend provides a polished, modern interface for the Video Creator platform with excellent developer experience and user-friendly design.
