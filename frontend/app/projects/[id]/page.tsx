"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { useProjects } from "@/hooks/useProjects"
import { Button } from "@/components/ui/button"
import { PreviewStep } from "@/components/preview-step"
import { VideoProject, StockFootage } from "@/types/video-creator"
import { ChevronLeft, Download } from "lucide-react"
import { Badge } from "@/components/ui/badge"

export default function ProjectDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const { getProject } = useProjects()
  const [project, setProject] = useState<VideoProject | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedFootage, setSelectedFootage] = useState<StockFootage | null>(null)
  
  // Get the project ID from the URL
  const projectId = params.id as string
  
  useEffect(() => {
    async function loadProject() {
      if (projectId) {
        try {
          setLoading(true)
          const foundProject = await getProject(projectId)
          if (foundProject) {
            setProject(foundProject)
            
            // Find the first sentence with selectedFootage for the project preview
            const firstFootage = foundProject.sentences?.find(s => s.selectedFootage)?.selectedFootage || null
            setSelectedFootage(firstFootage)
          } else {
            setError("Project not found")
          }
        } catch (err) {
          console.error(`Error loading project ${projectId}:`, err)
          setError("Failed to load project")
        } finally {
          setLoading(false)
        }
      }
    }
    
    loadProject()
  }, [projectId, getProject])
  
  const handleBack = () => {
    router.back()
  }

  const handleDownloadVideo = () => {
    if (project?.videoUrl) {
      const link = document.createElement('a');
      link.href = project.videoUrl;
      link.download = `${project.title}.mp4`;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }
  
  if (loading) {
    return (
      <div className="container mx-auto max-w-6xl py-8">
        <div className="flex items-center mb-6">
          <Button variant="ghost" size="icon" onClick={handleBack} className="mr-2">
            <ChevronLeft size={16} />
          </Button>
          <h1 className="text-2xl font-bold">Loading Project...</h1>
        </div>
        <div className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">Loading projects...</p>
        </div>
      </div>
    )
  }
  
  if (error || !project) {
    return (
      <div className="container mx-auto max-w-6xl py-8">
        <div className="flex items-center mb-6">
          <Button variant="ghost" size="icon" onClick={handleBack} className="mr-2">
            <ChevronLeft size={16} />
          </Button>
          <h1 className="text-2xl font-bold">Project Not Found</h1>
        </div>
        <div className="flex items-center justify-center h-64 bg-muted/20 rounded-lg border border-dashed">
          <p className="text-muted-foreground">
            {error || "This project does not exist or has been deleted."}
          </p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="container mx-auto max-w-6xl py-8">
      <div className="flex items-center mb-6">
        <Button variant="ghost" size="icon" onClick={handleBack} className="mr-2">
          <ChevronLeft size={16} />
        </Button>
        <h1 className="text-2xl font-bold">{project.title}</h1>
      </div>
      
      {/* Project preview */}
      <div className="mb-8">
        {project.videoUrl ? (
          <div className="aspect-video bg-black rounded-lg overflow-hidden">
            <video 
              src={project.videoUrl} 
              controls
              className="w-full h-full"
              preload="metadata"
              poster={project.videoUrl + "?time=1"}
            />
          </div>
        ) : (
          <div className="aspect-video bg-muted/30 rounded-lg flex items-center justify-center">
            <p className="text-muted-foreground">No video available for this project</p>
          </div>
        )}
      </div>
      
      {/* Project details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-card rounded-lg border p-4">
            <h2 className="text-lg font-semibold mb-3">Project Information</h2>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Sentences</span>
                <span>{project.sentences?.length || 0}</span>
              </div>
              {project.backgroundMusic && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Background Music</span>
                  <span>{project.backgroundMusic.name}</span>
                </div>
              )}
            </div>
          </div>
          
          {project.sentences && project.sentences.length > 0 && (
            <div className="bg-card rounded-lg border p-4">
              <h2 className="text-lg font-semibold mb-3">Sentences</h2>
              <div className="space-y-3">
                {project.sentences.map((sentence, index) => (
                  <div key={sentence.sentence_id || index} className="p-3 bg-muted/30 rounded-md">
                    <p className="text-sm">{sentence.text}</p>
                    <div className="flex justify-between mt-2 text-xs text-muted-foreground">
                      <span>{Math.round(sentence.start)}s - {Math.round(sentence.end)}s</span>
                      <span>{Math.round(sentence.end - sentence.start)}s</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="space-y-6">
          {selectedFootage && (
            <div className="bg-card rounded-lg border p-4">
              <h2 className="text-lg font-semibold mb-3">Selected Footage</h2>
              <div className="space-y-3">
                <div className="aspect-video bg-muted/30 rounded-md overflow-hidden">
                  {selectedFootage.url ? (
                    <video 
                      src={selectedFootage.url}
                      className="w-full h-full object-cover"
                      preload="metadata"
                      muted
                      loop
                      onClick={(e) => {
                        const video = e.target as HTMLVideoElement;
                        video.paused ? video.play() : video.pause();
                      }}
                    />
                  ) : (
                    <img 
                      src={selectedFootage.thumbnail} 
                      alt="Footage thumbnail"
                      className="w-full h-full object-cover"
                    />
                  )}
                </div>
                <p className="text-sm font-medium">{selectedFootage.title}</p>
                <p className="text-xs text-muted-foreground">{selectedFootage.description}</p>
                
                {/* Display footage tags
                {selectedFootage.tags && selectedFootage.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {selectedFootage.tags.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )} */}
                
                {/* Display mood if available */}
                {selectedFootage.mood && (
                  <div className="mt-2">
                    <Badge variant="outline">{selectedFootage.mood}</Badge>
                  </div>
                )}
              </div>
            </div>
          )}
          
          <div className="bg-card rounded-lg border p-4">
            <h2 className="text-lg font-semibold mb-3">Actions</h2>
            <div className="space-y-3">
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => router.push('/')}
              >
                Create New Project
              </Button>
              {project.videoUrl && (
                <Button 
                  className="w-full"
                  onClick={handleDownloadVideo}
                >
                  <Download size={16} className="mr-2" />
                  Download Video
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 