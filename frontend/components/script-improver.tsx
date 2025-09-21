"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Sparkles, Loader2 } from "lucide-react"

interface ScriptImproverProps {
  originalScript: string
  onImprovedScript: (script: string) => void
}

export function ScriptImprover({ originalScript, onImprovedScript }: ScriptImproverProps) {
  const [isImproving, setIsImproving] = useState(false)
  const [improvedScript, setImprovedScript] = useState("")
  const [selectedImprovements, setSelectedImprovements] = useState<string[]>(["clarity", "engagement"])

  const improvementOptions = [
    { id: "clarity", label: "Improve Clarity", description: "Make the message clearer and easier to understand" },
    { id: "engagement", label: "Increase Engagement", description: "Make the content more engaging and compelling" },
    { id: "pacing", label: "Better Pacing", description: "Optimize for video narration timing" },
    { id: "visual", label: "Add Visual Cues", description: "Include suggestions for visual elements" },
    { id: "professional", label: "Professional Tone", description: "Enhance professional language and tone" },
    { id: "concise", label: "Make Concise", description: "Remove unnecessary words and improve flow" },
  ]

  const handleImproveScript = async () => {
    setIsImproving(true)
    try {
      const response = await fetch("/api/improve-script", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          script: originalScript,
          improvements: selectedImprovements,
        }),
      })

      if (!response.ok) throw new Error("Failed to improve script")

      const data = await response.json()
      setImprovedScript(data.improvedScript)
    } catch (error) {
      console.error("Script improvement error:", error)
      console.error("Failed to improve script. Please try again.")
    } finally {
      setIsImproving(false)
    }
  }

  const handleUseImprovedScript = () => {
    onImprovedScript(improvedScript)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5" />
          AI Script Improvement
        </CardTitle>
        <CardDescription>Let AI enhance your script for better video content</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="font-medium mb-3">Select improvements:</h4>
          <div className="grid grid-cols-2 gap-3">
            {improvementOptions.map((option) => (
              <div key={option.id} className="flex items-start space-x-2">
                <Checkbox
                  id={option.id}
                  checked={selectedImprovements.includes(option.id)}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      setSelectedImprovements([...selectedImprovements, option.id])
                    } else {
                      setSelectedImprovements(selectedImprovements.filter((id) => id !== option.id))
                    }
                  }}
                />
                <div className="grid gap-1.5 leading-none">
                  <label
                    htmlFor={option.id}
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    {option.label}
                  </label>
                  <p className="text-xs text-muted-foreground">{option.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <Button
          onClick={handleImproveScript}
          disabled={isImproving || selectedImprovements.length === 0}
          className="w-full"
        >
          {isImproving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              AI is improving your script...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-2" />
              Improve Script with AI
            </>
          )}
        </Button>

        {improvedScript && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <h4 className="font-medium">Improved Script:</h4>
              <Badge className="bg-green-100 text-green-800">AI Enhanced</Badge>
            </div>
            <Textarea
              value={improvedScript}
              onChange={(e) => setImprovedScript(e.target.value)}
              className="min-h-[150px]"
              placeholder="Improved script will appear here..."
            />
            <Button onClick={handleUseImprovedScript} className="w-full">
              Use Improved Script
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
