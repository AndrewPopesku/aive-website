"use client"

import type React from "react"
import { useCallback, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Upload, FileText, Mic, Sparkles, AlertCircle } from "lucide-react"
import { ScriptImprover } from "./script-improver"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

interface UploadStepProps {
  onProcessScript: (content: string) => void
  onProcessAudio: (file: File) => void
  isProcessing: boolean
  error?: string
}

export function UploadStep({ onProcessScript, onProcessAudio, isProcessing, error }: UploadStepProps) {
  const [scriptContent, setScriptContent] = useState("")
  const [dragActive, setDragActive] = useState(false)
  const [showImprover, setShowImprover] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(error || null)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setDragActive(false)
      setUploadError(null)

      const files = Array.from(e.dataTransfer.files)
      const file = files[0]

      if (file) {
        if (file.type.startsWith("audio/")) {
          onProcessAudio(file)
        } else if (file.type === "text/plain") {
          const reader = new FileReader()
          reader.onload = (e) => {
            const content = e.target?.result as string
            setScriptContent(content)
            setShowImprover(true)
          }
          reader.readAsText(file)
        } else {
          setUploadError("Unsupported file type. Please upload an audio file (MP3, WAV) or a text file.")
        }
      }
    },
    [onProcessAudio],
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setUploadError(null)
      const file = e.target.files?.[0]
      if (file) {
        if (file.type.startsWith("audio/")) {
          onProcessAudio(file)
        } else if (file.type === "text/plain") {
          const reader = new FileReader()
          reader.onload = (e) => {
            const content = e.target?.result as string
            setScriptContent(content)
            setShowImprover(true)
          }
          reader.readAsText(file)
        } else {
          setUploadError("Unsupported file type. Please upload an audio file (MP3, WAV) or a text file.")
        }
      }
    },
    [onProcessAudio],
  )

  const handleScriptChange = (value: string) => {
    setScriptContent(value)
    setShowImprover(value.trim().length > 50) // Show improver for substantial content
  }

  const handleImprovedScript = (improvedScript: string) => {
    setScriptContent(improvedScript)
    setShowImprover(false)
  }

  // Update error state when prop changes
  if (error && error !== uploadError) {
    setUploadError(error)
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Create Your AI-Powered Video</h1>
        <p className="text-muted-foreground">
          Upload an audio file with voiceover and let AI enhance your video creation process
        </p>
      </div>

      {uploadError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{uploadError}</AlertDescription>
        </Alert>
      )}

      <div className="grid md:grid-cols-1 gap-6">
        {/* File Upload */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mic className="w-5 h-5" />
              Upload Audio File
            </CardTitle>
            <CardDescription>Upload an audio file with voiceover for transcription and analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-lg font-medium mb-2">Drag and drop files here</p>
              <p className="text-sm text-muted-foreground mb-4">Supports audio files (MP3, WAV)</p>
              <input
                type="file"
                accept="audio/mpeg,audio/mp3,audio/wav,audio/x-wav,.txt"
                onChange={handleFileInput}
                className="hidden"
                id="file-upload"
                disabled={isProcessing}
              />
              <Button asChild disabled={isProcessing}>
                <label htmlFor="file-upload" className="cursor-pointer">
                  Choose Files
                </label>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Script Improver */}
      {showImprover && scriptContent.trim() && (
        <ScriptImprover originalScript={scriptContent} onImprovedScript={handleImprovedScript} />
      )}

      {isProcessing && (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center space-x-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              <span>AI is analyzing your content...</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
