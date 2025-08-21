"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { Target, Send, User, Bot, Navigation, FileText, Zap, CheckCircle } from "lucide-react"
import { API_BASE_URL } from "@/constants/api"

// Interfaces
interface Intent {
  category: "navigation" | "summarization" | "task_execution" | "unknown"
}

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  intent?: Intent
  mockResponse?: string
}

// Main Component
export default function IntentIdentificationPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [query, setQuery] = useState("")
  const [chained, setChained] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || isLoading) return

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: query,
    }
    setMessages((prev) => [...prev, userMessage])
    setQuery("")
    setIsLoading(true)

    try {
      // 1. Intent Identification
      const intentResponse = await fetch(`${API_BASE_URL}/api/orchestrator/identify_intent/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMessage.content}),
      })

      if (!intentResponse.ok) {
        throw new Error("Failed to identify intent")
      }

      const intentResult: { category: "navigation" | "summarization" | "task_execution" } = await intentResponse.json()

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: `Intent identified: ${intentResult.category}`,
        intent: intentResult,
      }
      setMessages((prev) => [...prev, assistantMessage])

      // 2. Mock Agent Invocation
      // Simulate a delay for agent response
      await new Promise((resolve) => setTimeout(resolve, 1500))

      const mockResponse = getMockResponse(intentResult.category)

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id ? { ...msg, mockResponse } : msg
        )
      )
    } catch (error) {
      console.error("Error in intent identification:", error)
      toast({
        title: "An error occurred",
        description: "Failed to get a response. Please try again.",
        className: "bg-red-50 border-red-200 text-red-800",
      })
      const errorMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: "Sorry, I couldn't process your request.",
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const getMockResponse = (category: string) => {
    switch (category) {
      case "navigation":
        return "This is a mock navigation response. Navigating you to the requested page."
      case "summarization":
        return "This is a mock summarization response. Here is a summary of the document you provided."
      case "task_execution":
        return "This is a mock task execution response. The task has been completed successfully."
      default:
        return "This is a mock response for an unknown intent."
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "navigation":
        return <Navigation className="h-4 w-4" />
      case "summarization":
        return <FileText className="h-4 w-4" />
      case "task_execution":
        return <Zap className="h-4 w-4" />
      default:
        return <Target className="h-4 w-4" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "navigation":
        return "bg-blue-500"
      case "summarization":
        return "bg-purple-500"
      case "task_execution":
        return "bg-orange-500"
      default:
        return "bg-gray-500"
    }
  }

  return (
    <div className="flex flex-col h-full">
      <header className="p-4 border-b">
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Target className="h-6 w-6 text-green-500" />
          Intent Identification
        </h1>
        <p className="text-muted-foreground">
          A chat-like interface to identify intent and invoke corresponding agents.
        </p>
      </header>

      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex items-start gap-3 ${message.role === "user" ? "justify-end" : ""}`}
          >
            {message.role === "assistant" && (
              <div className="bg-primary text-primary-foreground rounded-full p-2">
                <Bot className="h-5 w-5" />
              </div>
            )}
            <div
              className={`max-w-lg rounded-lg p-3 ${
                message.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              }`}
            >
              {message.role === "user" ? (
                <p>{message.content}</p>
              ) : (
                <div className="space-y-3">
                  {message.intent && (
                    <Card>
                      <CardContent className="pt-4">
                        <div className="flex items-center justify-between gap-4">
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <CheckCircle className="h-5 w-5 text-green-500" />
                              <span className="font-medium">Intent Identified</span>
                            </div>
                          </div>
                          <Badge className={`${getCategoryColor(message.intent.category)} text-white`}>
                            <span className="flex items-center gap-1">
                              {getCategoryIcon(message.intent.category)}
                              {message.intent.category.replace("_", " ")}
                            </span>
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                  {message.mockResponse ? (
                    <p>{message.mockResponse}</p>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 bg-gray-500 rounded-full animate-pulse"></span>
                      <span className="w-2 h-2 bg-gray-500 rounded-full animate-pulse delay-75"></span>
                      <span className="w-2 h-2 bg-gray-500 rounded-full animate-pulse delay-150"></span>
                    </div>
                  )}
                </div>
              )}
            </div>
            {message.role === "user" && (
              <div className="bg-muted rounded-full p-2">
                <User className="h-5 w-5" />
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </main>

      <footer className="p-4 border-t">
        <form onSubmit={handleSendMessage} className="flex items-center gap-2">
          <Input
            id="intent-query"
            placeholder="Enter your query..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading}
            autoComplete="off"
          />
          <Button type="submit" disabled={isLoading || !query.trim()}>
            {isLoading ? "..." : <Send className="h-5 w-5" />}
          </Button>
        </form>
        <div className="flex items-center space-x-2 pt-2">
          <Checkbox id="chained" checked={chained} onCheckedChange={(checked) => setChained(Boolean(checked))} />
          <label
            htmlFor="chained"
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            Chained
          </label>
        </div>
      </footer>
    </div>
  )
}
