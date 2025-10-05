"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Progress } from "@/components/ui/progress"
import { useVideoCreator } from "@/hooks/useVideoCreator"
import { UploadStep } from "@/components/upload-step"
import { SegmentationStep } from "@/components/segmentation-step"
import { PreviewStep } from "@/components/preview-step"
import { useAuth } from "@/hooks/useAuth"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export default function VideoCreatorApp() {
  const [uploadError, setUploadError] = useState<string | null>(null)
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()
  
  const {
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
  } = useVideoCreator()

  // For the current workflow, we'll use the existing 3-step process but enhance it
  const getStepProgress = () => {
    const steps = ["upload", "footage", "preview"]
    return ((steps.indexOf(currentStep) + 1) / steps.length) * 100
  }

  const getStepTitle = () => {
    switch (currentStep) {
      case "upload":
        return "Upload Audio"
      case "footage":
        return "Select Video and Music"
      case "preview":
        return "Preview and Download"
      default:
        return ""
    }
  }
  
  // Wrapper for processAudioFile to handle errors
  const handleProcessAudio = async (file: File) => {
    // Check authentication before processing
    if (!isAuthenticated) {
      setUploadError("You must be logged in to create a project")
      return
    }
    
    try {
      setUploadError(null)
      await processAudioFile(file)
    } catch (error) {
      console.error("Error processing audio:", error)
      setUploadError(error instanceof Error ? error.message : "Failed to process audio file")
    }
  }

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  // Show auth prompt if not authenticated and on upload step
  if (!isAuthenticated && currentStep === "upload") {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto max-w-2xl py-16">
          <Alert>
            <AlertDescription className="flex flex-col items-center space-y-4 py-4">
              <p className="text-center">
                You need to be logged in to create video projects.
              </p>
              <div className="flex space-x-4">
                <Link href="/login">
                  <Button>Login</Button>
                </Link>
                <Link href="/register">
                  <Button variant="outline">Register</Button>
                </Link>
              </div>
            </AlertDescription>
          </Alert>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Progress Header */}
      {currentStep !== "upload" && (
        <div className="border-b bg-card">
          <div className="max-w-6xl mx-auto p-4">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-semibold">{getStepTitle()}</h2>
              <span className="text-sm text-muted-foreground">
                Step {["upload", "footage", "preview"].indexOf(currentStep) + 1} of 3
              </span>
            </div>
            <Progress value={getStepProgress()} className="w-full" />
          </div>
        </div>
      )}

      {/* Step Content */}
      <main className="py-6">
        {currentStep === "upload" && (
          <UploadStep 
            onProcessScript={(content: string) => {
              // For now, just alert that script processing isn't supported
              console.error("Script processing is not yet supported. Please upload an audio file instead.")
            }} 
            onProcessAudio={handleProcessAudio} 
            isProcessing={isProcessing}
            error={uploadError || undefined}
          />
        )}

        {currentStep === "footage" && project && (
          <SegmentationStep
            project={project}
            onNext={nextStep}
            getStockFootageForSentence={getStockFootageForSentence}
            onSelectFootage={selectFootageForSentence}
          />
        )}

        {currentStep === "preview" && project && (
          <PreviewStep 
            project={project} 
            onPrevious={previousStep}
            renderProject={renderProject}
            renderStatus={renderStatus}
            videoUrl={videoUrl}
            isProcessing={isProcessing}
          />
        )}
      </main>
    </div>
  )
}
