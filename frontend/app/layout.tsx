import type { Metadata } from 'next'
import './globals.css'
import { Navbar } from '@/components/ui/navbar'
import { AuthProvider } from '@/context/auth-context'

export const metadata: Metadata = {
  title: 'AIVE - AI Video Editor',
  description: 'Create videos with AI-powered voiceover and footage',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <Navbar />
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}
