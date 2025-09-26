"use client"

import { useState, useCallback, useEffect } from "react"
import type { VideoProject, Sentence, StockFootage, BackgroundMusic, ProjectCreationResult, FootageSelectionResult, RenderResult, RenderStatusResult } from "../types/video-creator"
import { 
  createProjectApiV1ProjectsPost, 
  submitFootageChoicesApiV1ProjectsProjectIdFootagePost,
  renderProjectApiV1RenderProjectIdRenderPost,
  getRenderStatusApiV1RenderStatusTaskIdGet
} from "@/client"
import { apiClient } from "@/lib/api-client"

// Simplified workflow steps matching the existing components
export type WorkflowStep = "upload" | "footage" | "preview"

export function useVideoCreator() {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>("upload")
  const [project, setProject] = useState<VideoProject | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [footageCache, setFootageCache] = useState<Record<string, StockFootage[]>>({})
  const [musicOptions, setMusicOptions] = useState<BackgroundMusic[]>([])
  const [renderTaskId, setRenderTaskId] = useState<string | null>(null)
  const [renderStatus, setRenderStatus] = useState<string>("idle")
  const [videoUrl, setVideoUrl] = useState<string | null>(null)

  // Step A: Process audio file and create project
  const processAudioFile = useCallback(async (file: File) => {
    setIsProcessing(true)

    try {
      // Check if file is an allowed audio type
      if (!file.type.startsWith('audio/')) {
        throw new Error("Please upload an audio file (MP3 or WAV format)")
      }
      
      // Check specific audio types
      const allowedTypes = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav'];
      if (!allowedTypes.includes(file.type)) {
        throw new Error(`File type ${file.type} not allowed. Supported types: MP3, WAV`)
      }
      
      try {
        console.log("Uploading file:", file.name, "Type:", file.type, "Size:", file.size);
        
        // Create a FormData object and append the file
        const formData = new FormData();
        formData.append('audio_file', file);
        
        // Make direct fetch request to avoid SDK issues
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/v1/projects/`, {
          method: 'POST',
          body: formData,
          // No Content-Type header - browser will set it with boundary
          headers: {
            // No headers needed for FormData
          }
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `Server error: ${response.status}`);
        }
        
        const data = await response.json();

        // Convert API sentences to frontend format
        const sentences: Sentence[] = data.sentences.map((sentence: any) => ({
          ...sentence,
          sentence_id: sentence.sentence_id, // Use backend-provided sentence_id
          // Map API field names to frontend expectations
          startTime: sentence.start,
          endTime: sentence.end,
          keywords: [], // Can be populated from analysis later
          mood: undefined,
          visualCues: [],
          // Use backend-provided selected_footage (backend now provides default selections)
          selectedFootage: sentence.selected_footage ? {
            id: sentence.selected_footage.id,
            title: sentence.selected_footage.title,
            description: sentence.selected_footage.description,
            thumbnail: sentence.selected_footage.thumbnail,
            duration: sentence.selected_footage.duration,
            tags: sentence.selected_footage.tags,
            category: sentence.selected_footage.category,
            mood: sentence.selected_footage.mood,
            relevanceScore: sentence.selected_footage.relevance_score,
            url: sentence.selected_footage.url
          } : undefined
        }))

        console.log(`✅ Created project with ${sentences.length} sentences. Selected footage count:`, 
          sentences.filter(s => s.selectedFootage).length)

        const newProject: VideoProject = {
          id: data.project_id,
          project_id: data.project_id,
          title: file.name.replace(/\.[^/.]+$/, ""),
          sentences,
          totalDuration: sentences.reduce((acc, s) => acc + (s.end - s.start), 0),
          analysis: {
            totalSentences: sentences.length,
            averageDuration: sentences.reduce((acc, s) => acc + (s.end - s.start), 0) / sentences.length,
            overallMood: "neutral"
          }
        }

        setProject(newProject)
        setCurrentStep("footage")
      } catch (apiError: any) {
        console.log("API Error details:", apiError);
        
        // Extract error message from API error response
        let errorMessage = "Failed to process audio file";
        
        if (apiError.message) {
          errorMessage = apiError.message;
        }
        
        throw new Error(errorMessage);
      }
    } catch (error) {
      console.error("Audio processing error:", error)
      console.error(`Failed to process audio: ${error instanceof Error ? error.message : "Unknown error"}`)
      throw error; // Re-throw the error so it can be caught by the component
    } finally {
      setIsProcessing(false)
    }
  }, [])

  // Get stock footage for a sentence - now primarily for alternative options
  // since backend provides default selected footage
  const getStockFootageForSentence = useCallback(
    async (sentence: Sentence): Promise<StockFootage[]> => {
      const sentenceId = sentence.sentence_id || sentence.text.slice(0, 10)
      
      console.log(`Loading footage options for sentence ${sentenceId}:`, {
        hasSelectedFootage: !!sentence.selectedFootage,
        selectedFootageTitle: sentence.selectedFootage?.title,
        sentenceText: sentence.text.slice(0, 50)
      })
      
      // Check cache first
      if (footageCache[sentenceId]) {
        return footageCache[sentenceId]
      }

      // Create footage options list
      const footage: StockFootage[] = []
      
      // If sentence already has selected footage from backend, include it as first option
      if (sentence.selectedFootage) {
        footage.push(sentence.selectedFootage)
        console.log(`Added backend-selected footage as primary option:`, sentence.selectedFootage.title)
      }
      
      // Add alternative mock footage options for user choice
      for (let i = 1; i <= 3; i++) {
        footage.push({
          id: `footage-${sentenceId}-alt-${i}`,
          title: `Alternative footage option ${i}`,
          description: `Alternative stock footage for: ${sentence.text.slice(0, 50)}...`,
          thumbnail: "/placeholder.svg",
          duration: sentence.end - sentence.start,
          tags: ["alternative", "stock"],
          category: "alternative",
          mood: "neutral",
          relevanceScore: Math.floor(Math.random() * 30) + 60, // 60-90%
          url: `/mock-footage-${sentenceId}-${i}.mp4`
        })
      }
      
      // Cache the results
      setFootageCache((prev) => ({
        ...prev,
        [sentenceId]: footage,
      }))

      console.log(`📋 Cached ${footage.length} footage options for sentence ${sentenceId}`)
      return footage
    },
    [footageCache],
  )

  // Step B: Submit footage choices and get music recommendations
  // This will be called automatically during the footage selection step
  const submitFootageChoices = useCallback(async () => {
    if (!project) return

    setIsProcessing(true)

    try {
      const footageChoices = project.sentences
        .filter(s => s.selectedFootage && s.sentence_id) // Only include sentences with both selected footage and sentence ID
        .map(s => ({
          sentence_id: s.sentence_id!, // Use backend-provided sentence ID directly (non-null assertion safe after filter)
          footage_url: s.selectedFootage!.url || s.selectedFootage!.thumbnail // Use actual URL or fallback to thumbnail
        }));

      if (footageChoices.length === 0) {
        setIsProcessing(false)
        return // No footage selected yet
      }

      console.log("Sending footage choices to API:", footageChoices)

      const response = await submitFootageChoicesApiV1ProjectsProjectIdFootagePost({
        client: apiClient,
        path: {
          project_id: project.project_id!
        },
        body: {
          footage_choices: footageChoices
        }
      })

      if (response.error) {
        throw new Error(JSON.stringify(response.error))
      }

      const data = response.data as FootageSelectionResult
      
      console.log("📻 Received music recommendations from API:", data.recommended_music)
      
      // If we didn't get any music recommendations, add local audio file fallback
      if (!data.recommended_music || data.recommended_music.length === 0) {
        console.warn("No music recommendations received from API, using local audio file")
        data.recommended_music = [
          {
            id: "music-local-1",
            name: "Ambient Corporate Music",
            url: "/api/static/audio/Ambient Corporate Music.mp3"
          }
        ] as any
      }

      // Convert API music recommendations to frontend format
      const musicRecommendations: BackgroundMusic[] = data.recommended_music.map(music => ({
        ...music,
        artist: "Unknown Artist",
        duration: 120, // Default duration
        genre: "Background",
        mood: "neutral",
        tempo: "medium",
        description: `Background music: ${music.name}`,
        preview: music.url,
        suitability: 0.8
      }))
      
      console.log("🎵 Setting music options:", musicRecommendations.length, "options available")

      setMusicOptions(musicRecommendations)
      setProject({
        ...project,
        musicOptions: musicRecommendations,
        footageChoices: footageChoices
      })
    } catch (error) {
      console.error("Footage submission error:", error)
      // Add fallback music options if API call fails - use local audio file
      const fallbackMusic = [
        {
          id: "music-error-1",
          name: "Ambient Corporate Music",
          url: "/api/static/audio/Ambient Corporate Music.mp3",
          artist: "Local Artist",
          duration: 120,
          genre: "Background",
          mood: "neutral",
          tempo: "medium",
          description: "Background music: Ambient Corporate Music",
          preview: "/api/static/audio/Ambient Corporate Music.mp3",
          suitability: 0.8
        }
      ]
      
      console.log("🎵 Setting fallback music options after API error")
      setMusicOptions(fallbackMusic)
      setProject(prev => prev ? {
        ...prev,
        musicOptions: fallbackMusic,
      } : null)
      
      console.error(`Failed to submit footage choices: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setIsProcessing(false)
    }
  }, [project])

  // Step C: Render the project (this will be called when moving to preview)
  const renderProject = useCallback(async (musicUrl: string | null = null, addSubtitles: boolean = true) => {
    if (!project) return

    setIsProcessing(true)

    try {
      console.log("Starting render with original audio")
      
      // Create body object with subtitles option and explicitly enable audio
      // Using type assertion to bypass TypeScript check - backend now accepts null for music_url
      const requestBody = {
        add_subtitles: addSubtitles,
        include_audio: true  // Explicitly tell backend to include original audio
      } as any  // Cast to any to bypass TypeScript checking
      
      // If music URL is provided, include it in the request
      if (musicUrl) {
        requestBody.music_url = musicUrl;
        console.log("Including background music:", musicUrl);
      }
      
      const response = await renderProjectApiV1RenderProjectIdRenderPost({
        client: apiClient,
        path: {
          project_id: project.project_id!
        },
        body: requestBody
      })

      if (response.error) {
        throw new Error(response.error as string)
      }

      const data = response.data as RenderResult

      setRenderTaskId(data.render_task_id)
      setRenderStatus("processing")
      setProject({
        ...project,
        renderTaskId: data.render_task_id
      })

      // Start polling for render status
      pollRenderStatus(data.render_task_id)
    } catch (error) {
      console.error("Render error:", error)
      console.error(`Failed to start render: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setIsProcessing(false)
    }
  }, [project])

  // Step D: Poll render status
  const pollRenderStatus = useCallback(async (taskId: string) => {
    try {
      const response = await getRenderStatusApiV1RenderStatusTaskIdGet({
        client: apiClient,
        path: {
          task_id: taskId
        }
      })

      if (response.error) {
        throw new Error(response.error as string)
      }

      const data = response.data as RenderStatusResult

      setRenderStatus(data.status)

      if ((data.status === "completed" || data.status === "complete") && (data.video_url || data.videoUrl)) {
        const videoUrlValue = data.video_url || data.videoUrl || null;
        console.log("✅ Render completed, video URL:", videoUrlValue)
        setVideoUrl(videoUrlValue)
        setCurrentStep("preview")
      } else if (data.status === "failed") {
        console.error(`Render failed: ${data.error || "Unknown error"}`)
      } else if (data.status === "pending" || data.status === "processing") {
        // Continue polling every 5 seconds
        console.log(`🔄 Render still in progress, status: ${data.status}, polling again in 5s`)
        setTimeout(() => pollRenderStatus(taskId), 5000)
      }
    } catch (error) {
      console.error("Render status check error:", error)
      setTimeout(() => pollRenderStatus(taskId), 10000) // Retry after 10 seconds
    }
  }, [])

  const selectFootageForSentence = useCallback(
    (sentenceId: string, footage: StockFootage) => {
      console.log(`🔧 selectFootageForSentence called:`, {
        sentenceId,
        footage: footage.title,
        category: footage.category,
        projectExists: !!project
      })
      
      if (!project) {
        console.error('❌ No project found in selectFootageForSentence')
        return
      }

      const updatedSentences = project.sentences.map((sentence) => {
        const currentSentenceId = sentence.sentence_id || sentence.text.slice(0, 10)
        if (currentSentenceId === sentenceId) {
          console.log(`✅ Updating sentence ${sentenceId} with footage:`, footage.title)
          return { ...sentence, selectedFootage: footage }
        }
        return sentence
      })

      console.log(`🔄 Setting project with updated sentences. Total: ${updatedSentences.length}`)
      setProject({
        ...project,
        sentences: updatedSentences,
      })

      // Auto-submit footage choices when footage is selected
      // This will trigger music recommendations
      setTimeout(() => submitFootageChoices(), 100)
    },
    [project, submitFootageChoices],
  )

  const selectBackgroundMusic = useCallback(
    (music: BackgroundMusic) => {
      if (!project) return

      const updatedProject = {
        ...project,
        backgroundMusic: music,
      }

      setProject(updatedProject)
      
      // Auto-advance to preview step when music is selected
      console.log("🎵 Background music selected, advancing to preview step")
      setCurrentStep("preview")
    },
    [project],
  )

  const nextStep = useCallback(() => {
    const steps: WorkflowStep[] = ["upload", "footage", "preview"]
    const currentIndex = steps.indexOf(currentStep)
    if (currentIndex < steps.length - 1) {
      const nextStepName = steps[currentIndex + 1]
      
      if (nextStepName === "preview" && project?.backgroundMusic) {
        // Start rendering when moving to preview
        renderProject(project.backgroundMusic.url)
      } else {
        setCurrentStep(nextStepName)
      }
    }
  }, [currentStep, project, renderProject])

  const previousStep = useCallback(() => {
    const steps: WorkflowStep[] = ["upload", "footage", "preview"]
    const currentIndex = steps.indexOf(currentStep)
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1])
    }
  },    [currentStep])

  // Auto-submit footage choices when project is created with backend-provided selected footage
  useEffect(() => {
    if (!project || currentStep !== "footage") return

    const sentencesWithFootage = project.sentences.filter(s => s.selectedFootage).length
    console.log(`📊 Project loaded with ${sentencesWithFootage}/${project.sentences.length} sentences having selected footage`)
    
    if (sentencesWithFootage === project.sentences.length && sentencesWithFootage > 0) {
      console.log("🚀 All sentences have backend-selected footage, auto-submitting choices...")
      // Delay to ensure state is fully updated
      setTimeout(() => {
        submitFootageChoices()
      }, 500)
    }
  }, [project, currentStep, submitFootageChoices])

  return {
    currentStep,
    project,
    isProcessing,
    processAudioFile,
    getStockFootageForSentence,
    selectFootageForSentence,
    selectBackgroundMusic,
    submitFootageChoices,
    renderProject,
    nextStep,
    previousStep,
    musicOptions,
    renderTaskId,
    renderStatus,
    videoUrl,
    // Legacy support
    processScript: processAudioFile, // For backward compatibility
    mockBackgroundMusic: musicOptions,
  }
}
