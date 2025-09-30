import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Vinyl Music Player',
  description: 'Modern vinyl music player with academic patterns',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}