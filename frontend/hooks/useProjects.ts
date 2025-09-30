"use client"

import { useState, useEffect, useCallback } from "react"
import { VideoProject } from "@/types/video-creator"
import { 
  getAllProjectsApiV1ProjectsGet, 
  getProjectDetailsApiV1ProjectsProjectIdGet,
  deleteProjectApiV1ProjectsProjectIdDelete
} from "@/client"
import { apiClient } from "@/lib/api-client"

// Base API URL for formatting video URLs
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useProjects() {
  const [projects, setProjects] = useState<VideoProject[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch all projects from API
  const fetchProjects = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Use the client method instead of direct fetch
      const response = await getAllProjectsApiV1ProjectsGet({
        client: apiClient
      });
      
      if (response.error) {
        throw new Error(`Failed to fetch projects: ${JSON.stringify(response.error)}`);
      }
      
      const data = response.data || [];
      
      // Transform API response to VideoProject format
      const projectsData = data.map((item: any) => {
        // Format videoUrl to include the base URL if it's a relative path
        let videoUrl = item.videoUrl || item.video_url || null;
        if (videoUrl && typeof videoUrl === 'string' && !videoUrl.startsWith('http')) {
          videoUrl = `${API_BASE_URL}${videoUrl}`;
        }
        
        return {
          id: item.project_id,
          project_id: item.project_id,
          title: item.title,
          sentences: item.sentences && Array.isArray(item.sentences) ? (item.sentences as any[]).map((s: any, index: number) => ({
            ...s,
            start: s.start_time || s.start || 0,
            end: s.end_time || s.end || 0,
            sentence_id: s.sentence_id || s.id || index.toString()
          })) : [],
          totalDuration: item.sentences && Array.isArray(item.sentences) 
            ? item.sentences.reduce((total: number, s: any) => total + ((s.end_time || s.end || 0) - (s.start_time || s.start || 0)), 0) 
            : 0,
          videoUrl: videoUrl,
          renderStatus: item.render_status || 'pending',
          renderTaskId: item.render_task_id
        } as VideoProject
      });
      
      setProjects(projectsData);
    } catch (err) {
      console.error('Error fetching projects:', err)
      setError('Failed to load projects')
    } finally {
      setLoading(false)
    }
  }, [])

  // Get a single project by ID
  const getProject = useCallback(async (projectId: string): Promise<VideoProject | undefined> => {
    try {
      // Use the client method instead of direct fetch
      const response = await getProjectDetailsApiV1ProjectsProjectIdGet({
        client: apiClient,
        path: {
          project_id: projectId
        }
      });
      
      if (response.error) {
        throw new Error(`Failed to fetch project: ${JSON.stringify(response.error)}`);
      }
      
      const project = response.data;
      
      if (!project) return undefined;
      
      // Format videoUrl to include the base URL if it's a relative path
      let videoUrl = project.videoUrl || project.video_url || null;
      if (videoUrl && typeof videoUrl === 'string' && !videoUrl.startsWith('http')) {
        videoUrl = `${API_BASE_URL}${videoUrl}`;
      }
      
      return {
        id: project.project_id,
        project_id: project.project_id,
        title: project.title,
        sentences: project.sentences && Array.isArray(project.sentences) ? (project.sentences as any[]).map((s: any, index: number) => ({
          ...s,
          start: s.start_time || s.start || 0,
          end: s.end_time || s.end || 0,
          sentence_id: s.sentence_id || s.id || index.toString()
        })) : [],
        totalDuration: project.sentences && Array.isArray(project.sentences)
          ? project.sentences.reduce((total: number, s: any) => total + ((s.end_time || s.end || 0) - (s.start_time || s.start || 0)), 0)
          : 0,
        videoUrl: videoUrl,
        renderStatus: project.render_status || 'pending',
        renderTaskId: project.render_task_id
      } as VideoProject;
    } catch (err) {
      console.error(`Error fetching project ${projectId}:`, err)
      return undefined
    }
  }, [])

  // Delete a project using the client method
  const deleteProject = useCallback(async (projectId: string) => {
    try {
      // Use the client method instead of direct fetch
      const response = await deleteProjectApiV1ProjectsProjectIdDelete({
        client: apiClient,
        path: {
          project_id: projectId
        }
      });
      
      if (response.error) {
        throw new Error(`Failed to delete project: ${JSON.stringify(response.error)}`);
      }
      
      // Update local state after successful deletion
      setProjects(prev => prev.filter(p => 
        p.id !== projectId && p.project_id !== projectId
      ))
      
      return true;
    } catch (err) {
      console.error(`Error deleting project ${projectId}:`, err)
      throw err;
    }
  }, [])

  // Load projects on initial mount
  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  return {
    projects,
    loading,
    error,
    fetchProjects,
    getProject,
    deleteProject
  }
} 