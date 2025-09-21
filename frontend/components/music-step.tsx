"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Play, Pause, Clock, Sparkles } from "lucide-react"
import type { VideoProject, BackgroundMusic } from "../types/video-creator"

interface MusicStepProps {
  project: VideoProject
  musicOptions: BackgroundMusic[]
  onSelectMusic: (music: BackgroundMusic) => void
  onNext: () => void
  onPrevious: () => void
}

export function MusicStep({ project, musicOptions, onSelectMusic, onNext, onPrevious }: MusicStepProps) {
  const [playingId, setPlayingId] = useState<string | null>(null)

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  const handlePlayPause = (musicId: string) => {
    if (playingId === musicId) {
      setPlayingId(null)
    } else {
      setPlayingId(musicId)
      // Auto-stop after 3 seconds for demo
      setTimeout(() => setPlayingId(null), 3000)
    }
  }

  // Sort music by suitability score
  const sortedMusic = [...musicOptions].sort((a, b) => (b.suitability || 0) - (a.suitability || 0))

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">ШІ-підбір фонової музики</h1>
        <p className="text-muted-foreground">Музичні пропозиції, підібрані під ваш настрій і контент</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            ШІ-рекомендовані музичні треки
          </CardTitle>
          <CardDescription>
            На основі вашого настрою: <Badge variant="outline">{project.analysis?.overallMood || "нейтральний"}</Badge>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sortedMusic.map((music, index) => (
              <Card
                key={music.id}
                className={`cursor-pointer transition-all hover:shadow-md ${
                  project.backgroundMusic?.id === music.id ? "ring-2 ring-primary" : ""
                }`}
                onClick={() => onSelectMusic(music)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-medium">{music.name}</h4>
                        {index === 0 && (
                          <Badge className="bg-gradient-to-r from-purple-500 to-pink-500">
                            <Sparkles className="w-3 h-3 mr-1" />
                            ШІ-кращий вибір
                          </Badge>
                        )}
                        {project.backgroundMusic?.id === music.id && <Badge>Вибрано</Badge>}
                        {music.suitability && <Badge variant="outline">{music.suitability}% відповідності</Badge>}
                      </div>
                      {music.artist && <p className="text-sm text-muted-foreground mb-2">автор: {music.artist}</p>}
                      {music.description && <p className="text-sm text-muted-foreground mb-2">{music.description}</p>}
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        {music.genre && <Badge variant="outline">{music.genre}</Badge>}
                        {music.mood && <Badge variant="outline">{music.mood}</Badge>}
                        {music.tempo && <Badge variant="outline">{music.tempo} tempo</Badge>}
                        {music.duration && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatDuration(music.duration)}
                          </span>
                        )}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation()
                        handlePlayPause(music.id)
                      }}
                    >
                      {playingId === music.id ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={onPrevious}>
          Попередній крок
        </Button>
        <Button onClick={onNext} disabled={!project.backgroundMusic}>
          Далі
        </Button>
      </div>
    </div>
  )
}
