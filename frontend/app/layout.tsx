import type { Metadata } from 'next'
import './globals.css'
import { AppProvider } from './providers'
import { VirtualKeyboardProvider } from '@/components/VirtualKeyboard'

export const metadata: Metadata = {
  title: 'Diabeetech',
  description: 'Glucose Monitoring System',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preload" href="/fonts/ProximaNovaBlack.ttf" as="font" type="font/ttf" crossOrigin="anonymous" />
        <link rel="preload" href="/fonts/pointersregular.ttf" as="font" type="font/ttf" crossOrigin="anonymous" />
      </head>
      <body className="bg-db-bg text-white font-body">
        <AppProvider>
          <VirtualKeyboardProvider>
            {children}
          </VirtualKeyboardProvider>
        </AppProvider>
      </body>
    </html>
  )
}
