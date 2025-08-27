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
  agentState?: Partial<AgentState>
}

// Agent state interface (matches backend AgentState)
interface AgentState {
  query: string
  chained: boolean
  tool_calls: any[]
  tool_response: string
  summarized_response: string
  is_moderated: boolean
  final_response: string
}

// Main Component
export default function IntentIdentificationPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [query, setQuery] = useState("")
  const [chained, setChained] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Cleanup EventSource on component unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [])

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
        body: JSON.stringify({ query: userMessage.content }),
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
        agentState: { query: userMessage.content, chained }, // Initialize agent state
      }
      setMessages((prev) => [...prev, assistantMessage])

      // 2. Stream Agent Response
      streamAgentResponse(assistantMessage.id, intentResult.category, userMessage.content)
    } catch (error) {
      console.error("Error in intent identification:", error)
      toast({
        title: "An error occurred",
        description: "Failed to get a response. Please try again.",
        className: "bg-red-50 border-red-200 text-red-800",
      })
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: "Sorry, I couldn't process your request.",
        },
      ])
      setIsLoading(false)
    }
  }

const streamAgentResponse = (messageId: string, agent: string, query: string) => {
  // Close any existing EventSource
  if (eventSourceRef.current) {
    eventSourceRef.current.close();
    eventSourceRef.current = null;
  }

  try {
    // Construct the URL with query parameters
    const url = new URL(`${API_BASE_URL}/api/orchestrator/invoke_agent`);
    url.searchParams.append("agent_name", agent);
    url.searchParams.append("query", encodeURIComponent(query));
    url.searchParams.append("chained", chained.toString());

    // Create new EventSource for streaming
    eventSourceRef.current = new EventSource(url.toString(), {
      withCredentials: true,
    });

    let hasFinalResponse = false;

    eventSourceRef.current.onmessage = (event) => {
      try {
        // Parse the JSON data from the SSE event
        const agentState: Partial<AgentState> = JSON.parse(event.data);
        
        if (agentState.error) {
          toast({
            title: "Agent error",
            description: agentState.error,
            className: "bg-red-50 border-red-200 text-red-800",
          });
          eventSourceRef.current?.close();
          eventSourceRef.current = null;
          setIsLoading(false);
          return;
        }

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === messageId
              ? { 
                  ...msg, 
                  agentState: { ...msg.agentState, ...agentState },
                  content: agentState.final_response || msg.content
                }
              : msg
          )
        );

        // If final_response is received, close the stream
        if (agentState.final_response && !hasFinalResponse) {
          hasFinalResponse = true;
          setTimeout(() => {
            eventSourceRef.current?.close();
            eventSourceRef.current = null;
            setIsLoading(false);
          }, 100);
        }
      } catch (error) {
        console.error("Error parsing stream data:", error);
        toast({
          title: "Streaming error",
          description: "Failed to parse streaming data. Please try again.",
          className: "bg-red-50 border-red-200 text-red-800",
        });
        eventSourceRef.current?.close();
        eventSourceRef.current = null;
        setIsLoading(false);
      }
    };

    eventSourceRef.current.onerror = (error) => {
      console.error("EventSource error:", error);
      if (!hasFinalResponse) {
        toast({
          title: "Streaming error",
          description: "Connection lost. Please try again.",
          className: "bg-red-50 border-red-200 text-red-800",
        });
        eventSourceRef.current?.close();
        eventSourceRef.current = null;
        setIsLoading(false);
      }
    };

    // Set timeout to close connection if it takes too long
    setTimeout(() => {
      if (!hasFinalResponse && eventSourceRef.current) {
        toast({
          title: "Timeout",
          description: "Request took too long to complete.",
          className: "bg-yellow-50 border-yellow-200 text-yellow-800",
        });
        eventSourceRef.current.close();
        eventSourceRef.current = null;
        setIsLoading(false);
      }
    }, 30000); // 30 second timeout

  } catch (error) {
    console.error("Error constructing SSE URL:", error);
    toast({
      title: "Connection error",
      description: "Failed to initiate streaming connection. Please try again.",
      className: "bg-red-50 border-red-200 text-red-800",
    });
    setIsLoading(false);
  }
};

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

const renderAgentState = (agentState?: Partial<AgentState>) => {
  if (!agentState) return null

  const { tool_calls, tool_response, summarized_response, is_moderated, final_response } = agentState
  const hasToolCalls = tool_calls && tool_calls.length > 0
  const hasToolResponse = !!tool_response
  const hasSummary = !!summarized_response
  const hasFinal = !!final_response

  return (
    <div className="space-y-4">
      {/* Progress Steps */}
      <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
        <div className={`flex items-center gap-1 ${hasToolCalls ? 'text-blue-600' : ''}`}>
          <div className={`w-2 h-2 rounded-full ${hasToolCalls ? 'bg-blue-500' : 'bg-gray-300'}`}></div>
          <span>Tool Calls</span>
        </div>
        <div className="flex-1 h-px bg-gray-300 mx-2"></div>
        <div className={`flex items-center gap-1 ${hasToolResponse ? 'text-green-600' : ''}`}>
          <div className={`w-2 h-2 rounded-full ${hasToolResponse ? 'bg-green-500' : 'bg-gray-300'}`}></div>
          <span>Response</span>
        </div>
        <div className="flex-1 h-px bg-gray-300 mx-2"></div>
        <div className={`flex items-center gap-1 ${hasSummary ? 'text-purple-600' : ''}`}>
          <div className={`w-2 h-2 rounded-full ${hasSummary ? 'bg-purple-500' : 'bg-gray-300'}`}></div>
          <span>Summary</span>
        </div>
        <div className="flex-1 h-px bg-gray-300 mx-2"></div>
        <div className={`flex items-center gap-1 ${hasFinal ? 'text-emerald-600' : ''}`}>
          <div className={`w-2 h-2 rounded-full ${hasFinal ? 'bg-emerald-500' : 'bg-gray-300'}`}></div>
          <span>Final</span>
        </div>
      </div>

      {/* Tool Calls */}
      {hasToolCalls && (
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="pt-4">
            <h3 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              Tool Execution
            </h3>
            {tool_calls.map((call, index) => (
              <div key={index} className="mb-3 last:mb-0">
                <p className="font-medium text-sm text-blue-700 mb-1">{call.name}</p>
                <div className="bg-blue-50 p-2 rounded text-xs text-gray-700 font-mono">
                  {JSON.stringify(call.args, null, 2)}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Tool Response */}
      {hasToolResponse && (
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="pt-4">
            <h3 className="font-semibold text-green-800 mb-3 flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              Raw Data
            </h3>
            <div className="bg-green-50 p-3 rounded">
              <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                {tool_response}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summarized Response */}
      {hasSummary && (
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="pt-4">
            <h3 className="font-semibold text-purple-800 mb-3 flex items-center gap-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              AI Summary
            </h3>
            <div className="bg-purple-50 p-3 rounded">
              <p className="text-sm text-gray-700">{summarized_response}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Moderation Status - Only show if moderated */}
      {is_moderated && (
        <Card className="border-l-4 border-l-red-500">
          <CardContent className="pt-4">
            <h3 className="font-semibold text-red-800 mb-3 flex items-center gap-2">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              Content Moderation
            </h3>
            <div className="bg-red-50 p-3 rounded">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <p className="text-sm font-medium text-red-700">Content flagged by moderation policy</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Final Response */}
      {hasFinal ? (
        <Card className="border-l-4 border-l-emerald-500">
          <CardContent className="pt-4">
            <h3 className="font-semibold text-emerald-800 mb-3 flex items-center gap-2">
              <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
              Final Answer
            </h3>
            <div className="bg-emerald-50 p-3 rounded">
              <p className="text-sm text-gray-700">{final_response}</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        // Loading state
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-center gap-2 py-6">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></span>
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-75"></span>
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-150"></span>
              <span className="text-sm text-gray-500 ml-2">Generating response...</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
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
              className={`max-w-lg rounded-lg p-3 ${message.role === "user"
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
                    renderAgentState(message.agentState)
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