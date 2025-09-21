"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useProjects } from "@/hooks/useProjects"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Trash } from "lucide-react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

export default function ProjectsPage() {
  const { projects, loading, error, fetchProjects, deleteProject } = useProjects()
  const [isDeleting, setIsDeleting] = useState(false)
  const [projectToDelete, setProjectToDelete] = useState<string | null>(null)
  
  // Video preview functions
  const handleMouseEnter = (e: React.MouseEvent<HTMLVideoElement>) => {
    const video = e.target as HTMLVideoElement;
    video.muted = true;
    video.play();
  }
  
  const handleMouseLeave = (e: React.MouseEvent<HTMLVideoElement>) => {
    const video = e.target as HTMLVideoElement;
    video.pause();
    video.currentTime = 0;
  }

  // Open confirmation dialog
  const handleDeleteClick = (projectId: string) => {
    setProjectToDelete(projectId);
  }

  // Confirm deletion
  const handleConfirmDelete = async () => {
    if (!projectToDelete || isDeleting) return;
    
    setIsDeleting(true);
    try {
      await deleteProject(projectToDelete);
    } catch (error) {
      console.error("Failed to delete project:", error);
      console.error("Failed to delete project. Please try again.");
    } finally {
      setIsDeleting(false);
      setProjectToDelete(null);
    }
  }

  // Cancel deletion
  const handleCancelDelete = () => {
    setProjectToDelete(null);
  }

  if (loading) {
    return (
      <div className="container mx-auto max-w-6xl py-8">
        <h1 className="text-2xl font-bold mb-6">Мої проекти</h1>
        <div className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">Завантаження проектів...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto max-w-6xl py-8">
        <h1 className="text-2xl font-bold mb-6">Мої проекти</h1>
        <div className="flex items-center justify-center h-64">
          <p className="text-red-500">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto max-w-6xl py-8">
      <h1 className="text-2xl font-bold mb-6">Мої проекти</h1>
      
      {projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 bg-muted/20 rounded-lg border border-dashed">
          <p className="text-muted-foreground mb-4">У вас ще немає проектів</p>
          <Link href="/">
            <Button>Створити новий проект</Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Card key={project.id || project.project_id} className="overflow-hidden">
              <CardHeader className="p-4 pb-2">
                <CardTitle className="text-lg truncate">{project.title}</CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-2">
                <div className="aspect-video bg-muted/30 rounded-md flex items-center justify-center mb-2 overflow-hidden">
                  {project.videoUrl ? (
                    <video 
                      className="w-full h-full object-cover"
                      src={project.videoUrl}
                      poster={project.videoUrl + "?time=1"} // Use the first frame as poster
                      preload="metadata"
                      onMouseEnter={handleMouseEnter}
                      onMouseLeave={handleMouseLeave}
                    />
                  ) : (
                    <p className="text-sm text-muted-foreground">Немає попереднього перегляду</p>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">
                  {project.sentences?.length || 0} sentences · 
                  {project.totalDuration ? ` ${Math.round(project.totalDuration)}s` : ' Unknown duration'}
                </p>
              </CardContent>
              <CardFooter className="px-4 py-3 border-t flex justify-between">
                <Link href={`/projects/${project.id || project.project_id}`}>
                  <Button variant="outline">Переглянути проект</Button>
                </Link>
                <Button 
                  variant="ghost" 
                  size="icon"
                  onClick={() => handleDeleteClick(project.id || project.project_id!)}
                  className="text-destructive"
                  disabled={isDeleting}
                >
                  <Trash size={16} />
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!projectToDelete} onOpenChange={(open) => !open && handleCancelDelete()}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Ви впевнені?</AlertDialogTitle>
            <AlertDialogDescription>
              Ця дія не може бути скасована. Це видалить проект і всі пов'язані з ним дані.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelDelete} disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleConfirmDelete} 
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
} 