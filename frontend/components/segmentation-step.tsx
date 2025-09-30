"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from "@/components/ui/dialog"
import { Clock, ImageIcon, Check, Loader2, RefreshCw, ExternalLink } from "lucide-react"
import type { VideoProject, StockFootage, Sentence } from "../types/video-creator"

interface SegmentationStepProps {
  project: VideoProject
  onNext: () => void
  getStockFootageForSentence: (sentence: Sentence) => Promise<StockFootage[]>
  onSelectFootage: (sentenceId: string, footage: StockFootage) => void
}

export function SegmentationStep({
  project,
  onNext,
  getStockFootageForSentence,
  onSelectFootage,
}: SegmentationStepProps) {
  const [loadingFootageForId, setLoadingFootageForId] = useState<string | null>(null)
  const [footageCache, setFootageCache] = useState<Record<string, StockFootage[]>>({})
  const [completedSentences, setCompletedSentences] = useState(0)

  // Helper function to check if URL is a direct video file
  const isDirectVideoUrl = (url: string) => {
    if (!url) return false
    const videoExtensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi']
    return videoExtensions.some(ext => url.toLowerCase().includes(ext)) || 
           url.includes('player.vimeo.com/external/') ||
           url.includes('videos.pexels.com/video-files/')
  }

  // Helper function to render footage preview (video or image)
  const renderFootagePreview = (footage: StockFootage, className = "w-full h-24 object-cover rounded") => {
    if (footage.url && isDirectVideoUrl(footage.url)) {
      return (
        <video
          className={className}
          muted
          loop
          playsInline
          preload="metadata"
          onMouseEnter={(e) => e.currentTarget.play()}
          onMouseLeave={(e) => e.currentTarget.pause()}
        >
          <source src={footage.url} type="video/mp4" />
          <img
            src={footage.thumbnail || "/placeholder.svg"}
            alt={footage.title}
            className={className}
          />
        </video>
      )
    }
    
    return (
      <img
        src={footage.thumbnail || "/placeholder.svg"}
        alt={footage.title}
        className={className}
      />
    )
  }

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

  // Load footage for all sentences on component mount
  useEffect(() => {
    console.log('=== SEGMENTATION STEP DEBUG ===')
    console.log('Project sentences count:', project.sentences.length)
    console.log('Project sentences details:', project.sentences.map(s => ({
      id: s.sentence_id || s.text.slice(0, 10),
      text: s.text.slice(0, 50),
      hasRecommendedUrl: !!s.recommended_footage_url,
      recommendedUrl: s.recommended_footage_url,
      hasSelectedFootage: !!s.selectedFootage,
      selectedFootage: s.selectedFootage
    })))
    console.log('Current footageCache keys:', Object.keys(footageCache))
    console.log('================================')

    const loadAllFootage = async () => {
      for (const sentence of project.sentences) {
        const sentenceId = sentence.id || sentence.sentence_id
        
        if (!footageCache[sentenceId]) {
          setLoadingFootageForId(sentenceId)
          try {
            const footage = await getStockFootageForSentence(sentence)
            
            setFootageCache((prev) => ({
              ...prev,
              [sentenceId]: footage,
            }))

          } catch (error) {
            console.error(`Failed to load footage for sentence ${sentenceId}:`, error)
          }
        }
      }

      setLoadingFootageForId(null)
    }

    loadAllFootage()
  }, [project.id]) // Simplified dependencies to prevent re-triggering

  // Update completed sentences count when project changes
  useEffect(() => {
    const completed = project.sentences.filter(s => s.selectedFootage).length
    setCompletedSentences(completed)
  }, [project.sentences])

  const handleRefreshFootage = async (sentenceId: string) => {
    setLoadingFootageForId(sentenceId)
    try {
      const sentence = project.sentences.find((s) => (s.id || s.sentence_id) === sentenceId)
      if (sentence) {
        const footage = await getStockFootageForSentence(sentence)
        setFootageCache((prev) => ({
          ...prev,
          [sentenceId]: footage,
        }))
      }
    } catch (error) {
      console.error(`Failed to refresh footage for sentence ${sentenceId}:`, error)
    } finally {
      setLoadingFootageForId(null)
    }
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Script Segmentation and Video Selection</h1>
        <p className="text-muted-foreground">Review the segmented script and selected video for each sentence</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              Project: {project.title}
              <Badge variant="secondary">
                <Clock className="w-4 h-4 mr-1" />
                {formatTime(project.total_duration || project.totalDuration || 0)}
              </Badge>
            </CardTitle>
            <div className="text-sm text-muted-foreground">
              {completedSentences} of {project.sentences.length} sentences with video
            </div>
          </div>
          <Progress value={(completedSentences / project.sentences.length) * 100} className="w-full" />
          <CardDescription>{project.sentences.length} sentences detected</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {project.sentences.map((sentence, index) => {
              const sentenceId = sentence.id || sentence.sentence_id || `sentence_${index}`
              return (
                <Card key={sentenceId} className="overflow-hidden">
                  <div className="grid md:grid-cols-3 gap-4">
                    {/* Left side: Selected footage */}
                    <div className="bg-muted relative">
                      {sentence.selectedFootage ? (
                        <div className="relative h-full min-h-[180px] flex flex-col">
                          {renderFootagePreview(sentence.selectedFootage, "w-full h-40 object-cover")}
                          <div className="p-3 bg-muted flex-1">
                            <h4 className="font-medium text-sm mb-1 line-clamp-1">{sentence.selectedFootage.title}</h4>
                            <div className="flex flex-wrap gap-1 mb-2">
                              {sentence.selectedFootage.category === "recommended" && (
                                <Badge variant="secondary" className="text-xs bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                                  AI
                                </Badge>
                              )}
                            </div>
                            {sentence.selectedFootage.url && (
                              <a 
                                href={sentence.selectedFootage.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-xs text-blue-500 hover:underline flex items-center gap-1"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <ExternalLink className="w-3 h-3" />
                                View on Pexels
                              </a>
                            )}
                          </div>
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button variant="secondary" size="sm" className="absolute bottom-3 right-3">
                                <ImageIcon className="w-4 h-4 mr-1" /> Change
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-3xl">
                              <DialogHeader>
                                <DialogTitle>Select video for sentence {index + 1}</DialogTitle>
                                <DialogDescription>
                                  Choose the best video for this sentence from the available options below.
                                </DialogDescription>
                              </DialogHeader>
                              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-h-[60vh] overflow-y-auto p-1">
                                {loadingFootageForId === sentenceId ? (
                                  <div className="col-span-full flex items-center justify-center py-12">
                                    <Loader2 className="w-8 h-8 animate-spin mr-2" />
                                    <span>AI is finding matching video...</span>
                                  </div>
                                ) : (
                                  footageCache[sentenceId]?.map((footage: StockFootage) => (
                                    <Card
                                      key={footage.id}
                                      className={`cursor-pointer transition-all hover:shadow-md ${
                                        sentence.selectedFootage?.id === footage.id ? "ring-2 ring-primary" : ""
                                      }`}
                                      onClick={() => onSelectFootage(sentenceId, footage)}
                                    >
                                      <CardContent className="p-3">
                                        <div className="relative mb-3">
                                          {renderFootagePreview(footage, "w-full h-24 object-cover rounded")}
                                          {sentence.selectedFootage?.id === footage.id && (
                                            <div className="absolute top-2 right-2 bg-primary text-primary-foreground rounded-full p-1">
                                              <Check className="w-3 h-3" />
                                            </div>
                                          )}
                                          {footage.category === "recommended" && (
                                            <div className="absolute top-2 left-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs px-2 py-1 rounded">
                                              AI Selected
                                            </div>
                                          )}
                                        </div>
                                        <h4 className="font-medium text-sm mb-2">{footage.title}</h4>
                                        {footage.url && (
                                          <a 
                                            href={footage.url} 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            className="text-xs text-blue-500 hover:underline flex items-center gap-1 mt-2"
                                            onClick={(e) => e.stopPropagation()}
                                          >
                                            <ExternalLink className="w-3 h-3" />
                                            View on Pexels
                                          </a>
                                        )}
                                      </CardContent>
                                    </Card>
                                  ))
                                )}
                              </div>
                              <div className="flex justify-between mt-4">
                                <Button
                                  variant="outline"
                                  onClick={() => handleRefreshFootage(sentenceId)}
                                  disabled={loadingFootageForId === sentenceId}
                                >
                                  <RefreshCw
                                    className={`w-4 h-4 mr-2 ${loadingFootageForId === sentenceId ? "animate-spin" : ""}`}
                                  />
                                  Refresh Options
                                </Button>
                              </div>
                            </DialogContent>
                          </Dialog>
                        </div>
                      ) : (
                        <div className="h-full min-h-[180px] flex flex-col items-center justify-center p-4">
                          {loadingFootageForId === sentenceId ? (
                            <>
                              <Loader2 className="w-8 h-8 animate-spin mb-2" />
                              <p className="text-sm text-center text-muted-foreground">AI is finding video...</p>
                            </>
                          ) : (
                            <>
                              <ImageIcon className="w-12 h-12 text-muted-foreground mb-2" />
                              <p className="text-sm text-center text-muted-foreground mb-2">No video selected</p>
                              <Dialog>
                                <DialogTrigger asChild>
                                  <Button variant="secondary" size="sm">
                                    Select Video
                                  </Button>
                                </DialogTrigger>
                                <DialogContent className="max-w-3xl">
                                  <DialogHeader>
                                    <DialogTitle>Select video for sentence {index + 1}</DialogTitle>
                                    <DialogDescription>
                                      Choose the best video for this sentence from the available options below.
                                    </DialogDescription>
                                  </DialogHeader>
                                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-h-[60vh] overflow-y-auto p-1">
                                    {footageCache[sentenceId]?.map((footage: StockFootage) => (
                                      <Card
                                        key={footage.id}
                                        className="cursor-pointer transition-all hover:shadow-md"
                                        onClick={() => onSelectFootage(sentenceId, footage)}
                                      >
                                        <CardContent className="p-3">
                                          <div className="relative mb-3">
                                            {renderFootagePreview(footage, "w-full h-24 object-cover rounded")}
                                            {footage.category === "recommended" && (
                                              <div className="absolute top-2 left-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs px-2 py-1 rounded">
                                                AI Selected
                                              </div>
                                            )}
                                          </div>
                                          <h4 className="font-medium text-sm mb-2">{footage.title}</h4>
                                          {footage.url && (
                                            <a 
                                              href={footage.url} 
                                              target="_blank" 
                                              rel="noopener noreferrer"
                                              className="text-xs text-blue-500 hover:underline flex items-center gap-1 mt-2"
                                              onClick={(e) => e.stopPropagation()}
                                            >
                                              <ExternalLink className="w-3 h-3" />
                                              View on Pexels
                                            </a>
                                          )}
                                        </CardContent>
                                      </Card>
                                    ))}
                                  </div>
                                </DialogContent>
                              </Dialog>
                            </>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Right side: Sentence content */}
                    <div className="md:col-span-2 p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline">#{index + 1}</Badge>
                        <span className="text-sm text-muted-foreground">
                          {formatTime(sentence.start_time || sentence.start || 0)} - {formatTime(sentence.end_time || sentence.end || 0)}
                        </span>
                      </div>
                      <p className="text-lg leading-relaxed mb-4">{sentence.text}</p>

                      {/* Display video tags directly instead of tabs */}
                      {/* <div className="space-y-2"> */}
                        {/* Show selected footage tags if available */}
                        {/* {sentence.selectedFootage?.tags && sentence.selectedFootage.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-2">
                            {sentence.selectedFootage.tags.map((tag) => (
                              <Badge key={tag} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )} */}
                        
                        {/* Show mood if available
                        {(sentence.selectedFootage?.mood || sentence.mood) && (
                          <Badge variant="outline" className="mr-1">
                            {sentence.selectedFootage?.mood || sentence.mood}
                          </Badge>
                        )} */}
                      {/* </div> */}
                    </div>
                  </div>
                </Card>
              )
            })}
          </div>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button 
            onClick={onNext} 
            size="lg" 
            disabled={completedSentences < project.sentences.length}
          >
            Continue to Preview
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
