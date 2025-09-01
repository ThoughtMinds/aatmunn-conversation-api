"use client"

import { useState, useEffect } from "react"
import { useTheme } from "next-themes"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function Footer() {
  const [version, setVersion] = useState("1.0.0")
  const [isOnline, setIsOnline] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchVersionAndHealth()
    // Set up periodic health checks every 30 seconds
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchVersionAndHealth = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setVersion(data.version || "1.0.0")
        setIsOnline(true)
      } else {
        setIsOnline(false)
      }
    } catch (error) {
      console.error("Failed to fetch version:", error)
      setIsOnline(false)
    } finally {
      setLoading(false)
    }
  }

  const fetchHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/`, {
        method: 'HEAD',
        headers: {
          'Accept': 'application/json',
        },
      })
      setIsOnline(response.ok)
    } catch (error) {
      setIsOnline(false)
    }
  }

  return (
    <footer className="sticky bottom-0 z-50 w-full border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-12 items-center justify-between px-6">
        <p className="text-sm text-muted-foreground">© 2025 Aatmunn PoC. All rights reserved.</p>
        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
          <span>{version}</span>
          <span>•</span>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`} />
            <span>Status: {isOnline ? 'Online' : 'Offline'}</span>
          </div>
        </div>
      </div>
    </footer>
  )
}