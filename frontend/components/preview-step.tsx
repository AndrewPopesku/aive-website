"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Download, Play, Music, Film, ExternalLink } from "lucide-react"
import type { VideoProject } from "../types/video-creator"
import { useState, useEffect } from "react"

interface PreviewStepProps {
  project: VideoProject
  onPrevious: () => void
  renderProject: (musicUrl: string | null, addSubtitles?: boolean) => Promise<void>
  renderStatus: string
  videoUrl: string | null
  isProcessing: boolean
}

export function PreviewStep({ project, onPrevious, renderProject, renderStatus, videoUrl, isProcessing }: PreviewStepProps) {
  const [isRendering, setIsRendering] = useState(false)
  
  // Reset rendering state when render status changes to completed or failed
  useEffect(() => {
    if ((renderStatus === "completed" || renderStatus === "complete" || renderStatus === "failed") && isRendering) {
      setIsRendering(false)
    }
  }, [renderStatus, isRendering])
  
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    
    // Format seconds: remove trailing zeros and unnecessary decimals
    let formattedSecs
    if (secs % 1 === 0) {
      // Whole number - no decimals needed
      formattedSecs = secs.toString()
    } else {
      // Has decimals - format and remove trailing zeros
      formattedSecs = secs.toFixed(2).replace(/\.?0+$/, '')
    }
    
    return `${mins}:${formattedSecs}`
  }

  const handleStartRender = async () => {
    try {
      // Set rendering state immediately to show loading animation
      setIsRendering(true)
      
      // Call renderProject without music URL
      await renderProject(null, true)
    } catch (error) {
      console.error("Render failed:", error)
      console.error("Failed to start video rendering")
      setIsRendering(false)
    }
  }

  const handleDownload = () => {
    if (videoUrl) {
      // Create a temporary anchor element to trigger download
      const link = document.createElement('a')
      link.href = videoUrl
      link.download = `${project.title}.mp4`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } else {
      console.error("Video is not ready yet. Please wait for rendering to complete.")
    }
  }

  const getVideoPreviewContent = () => {
    if (isRendering || renderStatus === "processing") {
      return (
        <div className="text-center text-white">
          <div className="animate-spin w-16 h-16 mx-auto mb-4 border-4 border-white border-t-transparent rounded-full"></div>
          <p className="text-lg">Відео обробляється...</p>
          <p className="text-sm opacity-75">Це може зайняти кілька хвилин</p>
        </div>
      )
    } else if ((renderStatus === "completed" || renderStatus === "complete") && videoUrl) {
      console.log("Video URL in preview component:", videoUrl);
      const formattedUrl = videoUrl.startsWith('http') ? videoUrl : `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${videoUrl}`;
      console.log("Formatted video URL:", formattedUrl);
      
      return (
        <>
          <video 
            src={formattedUrl} 
            controls 
            className="w-full h-full rounded-lg"
            poster="/placeholder.svg"
            preload="auto"
            crossOrigin="anonymous"
            onLoadedMetadata={(e) => {
              // Ensure video is not muted when loaded
              const videoElement = e.currentTarget;
              videoElement.muted = false;
              videoElement.volume = 1.0;
              
              // Debug log to check audio tracks
              console.log("Video loaded metadata:", {
                hasMuted: videoElement.muted,
                duration: videoElement.duration,
                volume: videoElement.volume,
                defaultMuted: videoElement.defaultMuted
              });
            }}
          >
            Ваш браузер не підтримує відео.
          </video>
          {/* <div className="mt-2 text-xs text-gray-500 bg-gray-100 p-1 rounded text-center">
            Debug URL: {formattedUrl.split('/').pop()}
          </div> */}
        </>
      )
    } else if (renderStatus === "failed") {
      return (
        <div className="text-center text-white">
          <div className="w-16 h-16 mx-auto mb-4 bg-red-500 rounded-full flex items-center justify-center">
            ❌
          </div>
          <p className="text-lg">Відтворення не вдалося</p>
          <p className="text-sm opacity-75">Спробуйте ще раз</p>
        </div>
      )
    } else {
      return (
        <div className="text-center text-white">
          <Play className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p className="text-lg">Готово до відтворення</p>
          <p className="text-sm opacity-75">{formatTime(project.totalDuration)} тривалість</p>
        </div>
      )
    }
  }

  const getActionButtons = () => {
    if (isRendering || renderStatus === "processing") {
      return (
        <div className="flex gap-2">
          <Button disabled className="flex-1">
            <div className="animate-spin w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full"></div>
            Обробляється...
          </Button>
        </div>
      )
    } else if ((renderStatus === "completed" || renderStatus === "complete") && videoUrl) {
      return (
        <div className="flex gap-2">
          <Button 
            onClick={() => {
              const videoElement = document.querySelector('video');
              if (videoElement) {
                videoElement.play();
              }
            }} 
            variant="outline" 
            className="flex-1"
          >
            <Play className="w-4 h-4 mr-2" />
            Відтворити відео
          </Button>
          <Button onClick={handleDownload} variant="default">
            <Download className="w-4 h-4 mr-2" />
            Завантажити відео
          </Button>
        </div>
      )
    } else {
      return (
        <div className="flex gap-2">
          <Button 
            onClick={handleStartRender} 
            className="flex-1"
            disabled={isProcessing}
          >
            <Play className="w-4 h-4 mr-2" />
            Почати обробку
          </Button>
        </div>
      )
    }
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Перегляд відео</h1>
        <p className="text-muted-foreground">Перевірте ваше відео перед завантаженням</p>
      </div>

      <div className="grid lg:grid-cols-1 gap-6">
        {/* Video Preview */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Film className="w-5 h-5" />
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="aspect-video bg-black rounded-lg flex items-center justify-center mb-4">
                {getVideoPreviewContent()}
              </div>
              {getActionButtons()}
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  )
}
