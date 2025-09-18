"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { Target, Send, User, Bot, Navigation, FileText, Zap, CheckCircle } from "lucide-react";
import { API_BASE_URL } from "@/constants/api";

// Interfaces
interface Intent {
  category: "navigation" | "summarization" | "task_execution" | "unknown";
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent?: Intent;
  mockResponse?: string;
  agentState?: Partial<AgentState>;
}

interface NavigationState {
  reasoning: string;
  id: string | null;
}

interface DocumentContext {
  id: string;
  content: string;
}

interface ApprovalRequest {
  question: string;
  actions: Array<{
    tool: string;
    parameters: any;
    description: string;
  }>;
  query: string;
}

interface AgentState {
  query: string;
  chained: boolean;
  tool_calls: any[];
  tool_response: string;
  summarized_response: string;
  is_moderated: boolean;
  final_response: string;
  context?: DocumentContext[];
  navigation?: NavigationState;
  requires_approval?: boolean;
  actions_to_review?: ApprovalRequest;
}

export default function ChatPlaygroundPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState("");
  const [chained, setChained] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
  const [currentApprovalRequest, setCurrentApprovalRequest] = useState<ApprovalRequest | null>(null);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  const [currentMessageId, setCurrentMessageId] = useState<string | null>(null);
  const { toast } = useToast();
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "navigation":
        return "bg-blue-500";
      case "summarization":
        return "bg-purple-500";
      case "task_execution":
        return "bg-orange-500";
      default:
        return "bg-gray-500";
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "navigation":
        return <Navigation className="h-4 w-4" />;
      case "summarization":
        return <FileText className="h-4 w-4" />;
      case "task_execution":
        return <Zap className="h-4 w-4" />;
      default:
        return null;
    }
  };

  const renderAgentState = (agentState?: Partial<AgentState>, category?: string) => {
    if (!agentState) {
      return <p>Processing...</p>;
    }

    const {
      tool_response = "",
      summarized_response = "",
      is_moderated = false,
      final_response = "",
      context,
      navigation,
      requires_approval,
      actions_to_review,
    } = agentState;

    const hasToolResponse = tool_response && tool_response !== "";
    const hasSummary = summarized_response && summarized_response !== "";
    const hasFinal = final_response && final_response !== "";
    const hasContext = context && context.length > 0;

    if (category === "task_execution" && requires_approval && actions_to_review) {
      return (
        <Card className="border-l-4 border-l-yellow-500">
          <CardContent className="pt-4">
            <h3 className="font-semibold text-yellow-800 mb-3 flex items-center gap-2">
              <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
              Awaiting Approval
            </h3>
            <div className="bg-yellow-50 p-3 rounded">
              <p className="text-sm text-gray-700">
                Please review and approve the actions in the dialog.
              </p>
            </div>
          </CardContent>
        </Card>
      );
    }

    return (
      <div className="space-y-4">
        {hasContext && (
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="pt-4">
              <h3 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                Retrieved Context
              </h3>
              <div className="bg-blue-50 p-3 rounded">
                <p className="text-sm text-gray-700">{context[0].content}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {category === "navigation" && navigation?.reasoning && (
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="pt-4">
              <h3 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                Navigation Reasoning
              </h3>
              <div className="bg-blue-50 p-3 rounded">
                <p className="text-sm text-gray-700">{navigation.reasoning}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {hasToolResponse && (
          <Card className="border-l-4 border-l-green-500">
            <CardContent className="pt-4">
              <h3 className="font-semibold text-green-800 mb-3 flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                Tool Response
              </h3>
              <div className="bg-green-50 p-3 rounded">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                  {tool_response.replace(/\\n/g, "\n")}
                </pre>
              </div>
            </CardContent>
          </Card>
        )}

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
    );
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: query,
    };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setIsLoading(true);

    try {
      const intentResponse = await fetch(`${API_BASE_URL}/api/orchestrator/identify_intent/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMessage.content }),
      });

      if (!intentResponse.ok) {
        throw new Error("Failed to identify intent");
      }

      const intentResult: { category: "navigation" | "summarization" | "task_execution" } = await intentResponse.json();

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: `Intent identified: ${intentResult.category}`,
        intent: intentResult,
        agentState: { query: userMessage.content, chained },
      };
      setMessages((prev) => [...prev, assistantMessage]);

      streamAgentResponse(assistantMessage.id, intentResult.category, userMessage.content);
    } catch (error) {
      console.error("Error in intent identification:", error);
      toast({
        title: "An error occurred",
        description: "Failed to get a response. Please try again.",
        className: "bg-red-50 border-red-200 text-red-800",
      });
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: "Sorry, I couldn't process your request.",
        },
      ]);
      setIsLoading(false);
    }
  };

  const streamAgentResponse = (messageId: string, agent: string, query: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    let accumulatedState: Partial<AgentState> = {};
    let hasFinalResponse = false;

    if (agent === "task_execution") {
      const url = `${API_BASE_URL.replace("http", "ws")}/api/task_execution/ws/task_execution/`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket connected, sending initial data");
        ws.send(JSON.stringify({ query, chained, thread_id: null }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("Received WebSocket message:", data);

          if (data.error) {
            console.error("Task execution error:", data.error);
            toast({
              title: "Task Failed",
              description: data.error,
              className: "bg-red-50 border-red-200 text-red-800",
            });
            setIsLoading(false);
            setApprovalDialogOpen(false);
            if (wsRef.current) {
              wsRef.current.close();
              wsRef.current = null;
            }
            setCurrentThreadId(null);
            return;
          }

          if (data.interrupt) {
            console.log("Interrupt received, showing approval dialog");
            setCurrentApprovalRequest(data.payload || null);
            setApprovalDialogOpen(true);
            setCurrentMessageId(messageId);
            setIsLoading(false);
            if (data.thread_id) {
              setCurrentThreadId(data.thread_id);
            }
            return;
          }

          if (data.thread_id) {
            setCurrentThreadId(data.thread_id);
          }

          accumulatedState = { ...accumulatedState, ...data };

          if (data.response) {
            if (data.is_final) {
              accumulatedState.final_response = data.response;
            } else {
              accumulatedState.tool_response = data.response;
            }
          }

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === messageId ? { ...msg, agentState: accumulatedState } : msg
            )
          );

          if (data.is_final) {
            console.log("Task completed successfully");
            toast({
              title: "Task Completed",
              description: `Task "${query}" has completed successfully`,
              className: "bg-green-50 border-green-200 text-green-800",
            });
            hasFinalResponse = true;
            if (wsRef.current) {
              wsRef.current.close();
              wsRef.current = null;
            }
            setIsLoading(false);
          } else {
            setIsLoading(true);
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
          toast({
            title: "Communication Error",
            description: "Failed to process server response",
            className: "bg-red-50 border-red-200 text-red-800",
          });
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        toast({
          title: "Connection Error",
          description: "Failed to maintain WebSocket connection",
          className: "bg-red-50 border-red-200 text-red-800",
        });
        setIsLoading(false);
        setApprovalDialogOpen(false);
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
        setCurrentThreadId(null);
      };

      ws.onclose = (event) => {
        console.log("WebSocket closed:", event.code, event.reason);
        wsRef.current = null;
        setIsLoading(false);
      };
    } else {
      let url: string;
      url = `${API_BASE_URL}/api/orchestrator/invoke_agent?agent_name=${agent}&query=${encodeURIComponent(query)}&chained=${chained}`;

      eventSourceRef.current = new EventSource(url, { withCredentials: true });

      eventSourceRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.error) {
            toast({ title: "Agent error", description: data.error, className: "bg-red-50 border-red-200 text-red-800" });
            eventSourceRef.current?.close();
            eventSourceRef.current = null;
            setIsLoading(false);
            return;
          }

          accumulatedState = { ...accumulatedState, ...data };

          if (agent === "navigation") {
            if (data.context) {
              accumulatedState.context = data.context;
            }
            if (data.navigation) {
              accumulatedState.navigation = data.navigation;
            }
            if (data.final_response) {
              accumulatedState.final_response = data.final_response;
            }
          }

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === messageId ? { ...msg, agentState: accumulatedState } : msg
            )
          );

          if (data.final_response && !data.requires_approval) {
            hasFinalResponse = true;
            toast({ title: "Task Completed", description: `Task "${query}" completed`, className: "bg-green-50 border-green-200 text-green-800" });
            eventSourceRef.current?.close();
            eventSourceRef.current = null;
            setIsLoading(false);
          }
        } catch (error) {
          console.error("Stream parse error:", error);
          toast({ title: "Stream Error", description: "Failed to parse response", className: "bg-red-50 border-red-200 text-red-800" });
        }
      };

      eventSourceRef.current.onerror = () => {
        toast({ title: "Stream Error", description: "Failed to maintain connection", className: "bg-red-50 border-red-200 text-red-800" });
        eventSourceRef.current?.close();
        eventSourceRef.current = null;
        setIsLoading(false);
      };
    }
  };

  const handleApprove = () => {
    if (!currentThreadId || !wsRef.current) {
      console.error("Cannot approve: missing thread_id or WebSocket");
      toast({
        title: "Approval Error",
        description: "Cannot process approval. Please try again.",
        className: "bg-red-50 border-red-200 text-red-800",
      });
      return;
    }

    console.log("Sending approval: resume=true, thread_id=", currentThreadId);
    setApprovalDialogOpen(false);
    setIsLoading(true);

    wsRef.current.send(
      JSON.stringify({ thread_id: currentThreadId, resume: "true" })
    );
  };

  const handleReject = () => {
    if (!currentThreadId || !wsRef.current) {
      console.error("Cannot reject: missing thread_id or WebSocket");
      toast({
        title: "Rejection Error",
        description: "Cannot process rejection. Please try again.",
        className: "bg-red-50 border-red-200 text-red-800",
      });
      return;
    }

    console.log("Sending rejection: resume=false, thread_id=", currentThreadId);
    setApprovalDialogOpen(false);

    wsRef.current.send(
      JSON.stringify({ thread_id: currentThreadId, resume: "false" })
    );
  };

  return (
    <div className="flex flex-col h-full">
      <header className="p-4 border-b">
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Target className="h-6 w-6 text-green-500" />
          Chat Playground
        </h1>
        <p className="text-muted-foreground">
          Interactive AI chat with intent-based agent routing
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
                    renderAgentState(message.agentState, message.intent?.category)
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
          <Checkbox
            id="chained"
            checked={chained}
            onCheckedChange={(checked) => setChained(Boolean(checked))}
          />
          <label
            htmlFor="chained"
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            Chained
          </label>
        </div>
      </footer>

      {approvalDialogOpen && currentApprovalRequest && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-lg w-full max-w-4xl mx-auto max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-black">
                Action Approval Required
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setApprovalDialogOpen(false)}
                className="h-6 w-6 p-0"
              >
                <span className="sr-only">Close</span>
                ×
              </Button>
            </div>

            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-sm text-blue-800 mb-2">{currentApprovalRequest.question}</p>
              <p className="text-xs text-blue-700">
                <strong>Original Query:</strong> {currentApprovalRequest.query}
              </p>
            </div>

            <div className="mb-6">
              <h4 className="font-medium mb-3 text-black text-sm">
                Proposed Actions ({currentApprovalRequest.actions.length}):
              </h4>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {currentApprovalRequest.actions.map((action, index) => (
                  <div key={index} className="p-4 border rounded-lg bg-gray-50">
                    <div className="flex items-start justify-between mb-2">
                      <p className="font-medium text-green-600 text-sm">{action.tool}</p>
                      <Badge variant="secondary" className="text-xs">
                        Action #{index + 1}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-600 mb-3">{action.description}</p>
                    <details className="mb-2">
                      <summary className="text-xs text-blue-600 cursor-pointer hover:underline">
                        View Parameters
                      </summary>
                      <pre className="text-xs mt-2 bg-muted p-2 rounded overflow-x-auto text-orange-600 border">
                        {JSON.stringify(action.parameters, null, 2)}
                      </pre>
                    </details>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3 justify-end pt-4 border-t">
              <Button
                variant="outline"
                onClick={handleReject}
                className="bg-red-50 border-red-200 text-red-700 hover:bg-red-100"
              >
                Reject & Cancel
              </Button>
              <Button
                onClick={handleApprove}
                className="bg-green-500 text-white hover:bg-green-600"
              >
                Approve & Continue
              </Button>
            </div>

            <div className="text-xs text-gray-500 mt-3 text-center">
              This approval ensures safe execution of automated actions.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}