import ProjectDetailsClient from './project-details-client'

// Generate static params for static export
export async function generateStaticParams() {
  // Return a placeholder param to make the static export work
  // This will create a fallback route that handles all project IDs client-side
  return [
    { id: 'placeholder' }
  ]
}

export default function ProjectDetailsPage() {
  return <ProjectDetailsClient />
}
