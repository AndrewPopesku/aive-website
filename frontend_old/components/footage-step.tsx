"use client"
import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ChevronLeft, ChevronRight, Check, Loader2, ExternalLink } from "lucide-react"
import type { VideoProject, StockFootage } from "../types/video-creator"

interface FootageStepProps {
  project: VideoProject
  currentSentenceIndex: number
  onSelectFootage: (sentenceId: string, footage: StockFootage) => void
  onNext: () => void
  onPrevious: () => void
  setCurrentSentenceIndex: (index: number) => void
  getStockFootageForSentence: (sentence: any) => Promise<StockFootage[]>
}

export function FootageStep({
  project,
  currentSentenceIndex,
  onSelectFootage,
  onNext,
  onPrevious,
  setCurrentSentenceIndex,
  getStockFootageForSentence,
}: FootageStepProps) {
  const [suggestedFootage, setSuggestedFootage] = useState<StockFootage[]>([])
  const [isLoadingFootage, setIsLoadingFootage] = useState(false)

  const currentSentence = project.sentences[currentSentenceIndex]
  const progress = ((currentSentenceIndex + 1) / project.sentences.length) * 100

  // Load footage suggestions when sentence changes
  useEffect(() => {
    const loadFootage = async () => {
      setIsLoadingFootage(true)
      try {
        const footage = await getStockFootageForSentence(currentSentence)
        setSuggestedFootage(footage)
        
        // Auto-select the AI-recommended footage (first in the list) if no footage is selected
        if (!currentSentence.selectedFootage && footage.length > 0 && footage[0].category === "recommended") {
          if (currentSentence.sentence_id) {
            onSelectFootage(currentSentence.sentence_id, footage[0])
          }
        }
      } catch (error) {
        console.error("Failed to load footage:", error)
        setSuggestedFootage([])
      } finally {
        setIsLoadingFootage(false)
      }
    }

    loadFootage()
  }, [currentSentence, getStockFootageForSentence, onSelectFootage])

  const handleFootageSelect = (footage: StockFootage) => {
    if (currentSentence.sentence_id) {
      onSelectFootage(currentSentence.sentence_id, footage)
    }
  }

  const handleNextSentence = () => {
    if (currentSentenceIndex < project.sentences.length - 1) {
      setCurrentSentenceIndex(currentSentenceIndex + 1)
    } else {
      onNext()
    }
  }

  const handlePreviousSentence = () => {
    if (currentSentenceIndex > 0) {
      setCurrentSentenceIndex(currentSentenceIndex - 1)
    }
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">ШІ підбір відео</h1>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>
              Речення {currentSentenceIndex + 1} з {project.sentences.length}
            </CardTitle>
            <Badge variant={currentSentence.selectedFootage ? "default" : "secondary"}>
              {currentSentence.selectedFootage ? "Вибрано" : "Очікує"}
            </Badge>
          </div>
          <Progress value={progress} className="w-full" />
        </CardHeader>
        <CardContent>
          <Card className="p-4 mb-6 bg-muted/50">
            <p className="text-lg leading-relaxed mb-2">{currentSentence.text}</p>
            {/* Display video tags directly
            {currentSentence.selectedFootage?.tags && currentSentence.selectedFootage.tags.length > 0 ? (
              <div className="flex flex-wrap gap-1 mb-2">
                <span className="text-sm text-muted-foreground mr-2">Теги:</span>
                {currentSentence.selectedFootage.tags.map((tag) => (
                  <Badge key={tag} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
            ) : (
              <div className="flex flex-wrap gap-1 mb-2 text-sm text-muted-foreground">
                Ще немає тегів. Виберіть відео, щоб побачити відповідні теги.
              </div>
            )}
            {currentSentence.selectedFootage?.mood && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Настрій:</span>
                <Badge variant="secondary" className="text-xs">
                  {currentSentence.selectedFootage.mood}
                </Badge>
              </div>
            )} */}
          </Card>

          {isLoadingFootage ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin mr-2" />
              <span>ШІ аналізує контент і знаходить відповідні відео...</span>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {suggestedFootage.map((footage) => (
                <Card
                  key={footage.id}
                  className={`cursor-pointer transition-all hover:shadow-md ${
                    currentSentence.selectedFootage?.id === footage.id ? "ring-2 ring-primary" : ""
                  }`}
                  onClick={() => handleFootageSelect(footage)}
                >
                  <CardContent className="p-3">
                    <div className="relative mb-3">
                      <img
                        src={footage.thumbnail || "/placeholder.svg"}
                        alt={footage.title}
                        className="w-full h-24 object-cover rounded"
                      />
                      {currentSentence.selectedFootage?.id === footage.id && (
                        <div className="absolute top-2 right-2 bg-primary text-primary-foreground rounded-full p-1">
                          <Check className="w-3 h-3" />
                        </div>
                      )}
                    </div>
                    <h4 className="font-medium text-sm mb-2">{footage.title}</h4>
                    {footage.description && (
                      <p className="text-xs text-muted-foreground mb-2 line-clamp-2">{footage.description}</p>
                    )}
                    {footage.url && (
                      <a 
                        href={footage.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-xs text-blue-500 hover:underline flex items-center gap-1"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink className="w-3 h-3" />
                        Переглянути на Pexels
                      </a>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={handlePreviousSentence} disabled={currentSentenceIndex === 0}>
          <ChevronLeft className="w-4 h-4 mr-2" />
          Попередній
        </Button>

        <div className="text-sm text-muted-foreground">
          {project.sentences.filter((s) => s.selectedFootage).length} з {project.sentences.length} завершено
        </div>

        <Button onClick={handleNextSentence}>
          {currentSentenceIndex < project.sentences.length - 1 ? (
            <>
              Далі
              <ChevronRight className="w-4 h-4 ml-2" />
            </>
          ) : (
            "Далі"
          )}
        </Button>
      </div>
    </div>
  )
}
