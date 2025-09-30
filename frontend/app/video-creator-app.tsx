"use client"

import { useState } from "react"
import { Progress } from "@/components/ui/progress"
import { useVideoCreator } from "@/hooks/useVideoCreator"
import { UploadStep } from "@/components/upload-step"
import { SegmentationStep } from "@/components/segmentation-step"
import { PreviewStep } from "@/components/preview-step"

export default function VideoCreatorApp() {
  const [uploadError, setUploadError] = useState<string | null>(null)
  
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
    try {
      setUploadError(null)
      await processAudioFile(file)
    } catch (error) {
      console.error("Error processing audio:", error)
      setUploadError(error instanceof Error ? error.message : "Failed to process audio file")
    }
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
