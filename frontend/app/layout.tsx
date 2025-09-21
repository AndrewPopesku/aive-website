import type { Metadata } from 'next'
import './globals.css'
import { Navbar } from '@/components/ui/navbar'

export const metadata: Metadata = {
  title: 'Video Creator App',
  description: 'Create videos with AI-powered voiceover and footage',
  generator: 'v0.dev',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        {children}
      </body>
    </html>
  )
}
