// Import types from the generated API client
import type { 
  Sentence as APISentence, 
  MusicRecommendation, 
  FootageChoice,
  ProjectResponse,
  MusicResponse,
  RenderRequest,
  RenderResponse,
  RenderStatusResponse 
} from '../client'

export interface Sentence extends APISentence {
  keywords?: string[]
  mood?: string
  visualCues?: string[]
  selectedFootage?: StockFootage
}

export interface StockFootage {
  id: string
  title: string
  description?: string
  thumbnail: string
  duration: number
  tags: string[]
  category?: string
  mood?: string
  relevanceScore?: number
  url?: string  // Add URL field for the actual footage link
}

export interface BackgroundMusic extends MusicRecommendation {
  artist?: string
  duration?: number
  genre?: string
  mood?: string
  tempo?: string
  description?: string
  preview?: string
  suitability?: number
}

export interface VideoProject {
  id: string
  title: string
  sentences: Sentence[]
  backgroundMusic?: BackgroundMusic
  totalDuration: number
  overallMood?: string
  analysis?: {
    totalSentences: number
    averageDuration: number
    overallMood: string
  }
  // New backend API fields
  project_id?: string
  musicOptions?: BackgroundMusic[]
  footageChoices?: FootageChoice[]
  renderTaskId?: string
  renderStatus?: 'pending' | 'processing' | 'completed' | 'failed'
  videoUrl?: string
}

// New types for the backend workflow
export interface ProjectCreationResult extends ProjectResponse {
  sentences: Sentence[]
}

export interface FootageSelectionResult extends MusicResponse {
  musicOptions: BackgroundMusic[]
}

export interface RenderResult extends RenderResponse {
  renderTaskId: string
  statusUrl: string
}

export interface RenderStatusResult extends RenderStatusResponse {
  status: string
  videoUrl?: string | null
  video_url?: string | null  // Add this field to match backend response
  error?: string | null
}

export type WorkflowStep = "upload" | "segmentation" | "preview"
