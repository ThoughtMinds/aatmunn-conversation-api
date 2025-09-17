"use client";

import { useState, useEffect, useRef } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import {
  Zap,
  Play,
  CheckCircle,
  Clock,
  AlertTriangle,
  Copy,
} from "lucide-react";
import { API_BASE_URL } from "@/constants/api";

interface ApprovalRequest {
  question: string;
  actions: Array<{
    tool: string;
    parameters: any;
    description: string;
  }>;
  query: string;
}

interface TaskResult {
  response?: string;
  status?: boolean;
  thread_id?: string;
  requires_approval?: boolean;
  actions_to_review?: ApprovalRequest;
  error?: string;
  is_final?: boolean;
  interrupt?: boolean;
  payload?: ApprovalRequest;
}

export default function TaskExecutionPage() {
  const [taskName, setTaskName] = useState("");
  const [chained, setChained] = useState(false);
  const [result, setResult] = useState<TaskResult | null>(null);
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
  const [currentApprovalRequest, setCurrentApprovalRequest] =
    useState<ApprovalRequest | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const wsRef = useRef<WebSocket | null>(null);
  const threadIdRef = useRef<string | null>(null);

  const connectWebSocket = (initialData: {
    query?: string;
    chained?: boolean;
    thread_id?: string | null;
    resume?: string;
  }) => {
    if (!taskName.trim() && !threadIdRef.current && !initialData.resume) return;

    setIsLoading(true);
    setApprovalDialogOpen(false);
    setResult(null);

    const url = `${API_BASE_URL.replace("http", "ws")}/api/task_execution/ws/task_execution/`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected, sending initial data:", initialData);
      ws.send(JSON.stringify(initialData));
    };

    ws.onmessage = (event) => {
      try {
        const data: TaskResult = JSON.parse(event.data);
        console.log("Received WebSocket message:", data);

        if (data.interrupt) {
          console.log("Interrupt received, showing approval dialog");
          setCurrentApprovalRequest(data.payload || null);
          setApprovalDialogOpen(true);
          setIsLoading(false);
          if (data.thread_id) {
            threadIdRef.current = data.thread_id;
          }
          return;
        }

        setResult((prev) => ({ ...prev, ...data }));

        if (data.thread_id) {
          threadIdRef.current = data.thread_id;
        }

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
          threadIdRef.current = null;
          return;
        }

        if (data.requires_approval && data.actions_to_review) {
          console.log("Approval required, showing dialog");
          setCurrentApprovalRequest(data.actions_to_review);
          setApprovalDialogOpen(true);
          setIsLoading(false);
        } else if (data.is_final) {
          console.log("Task completed successfully");
          toast({
            title: "Task Completed",
            description: `Task "${taskName}" has completed successfully`,
            className: "bg-green-50 border-green-200 text-green-800",
          });
          setTaskName("");
          setIsLoading(false);
          setApprovalDialogOpen(false);
          if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
          }
          threadIdRef.current = null;
        } else {
          setIsLoading(true);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error, event.data);
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
      threadIdRef.current = null;
    };

    ws.onclose = (event) => {
      console.log("WebSocket closed:", event.code, event.reason);
      wsRef.current = null;
      setIsLoading(false);
    };
  };

  const handleStartTask = () => {
    console.log("Starting new task:", taskName, "chained:", chained);
    threadIdRef.current = null;
    setResult(null);
    connectWebSocket({ query: taskName, chained, thread_id: null });
  };

  const handleApprove = () => {
    if (!threadIdRef.current || !wsRef.current) {
      console.error("Cannot approve: missing thread_id or WebSocket");
      return;
    }

    console.log("Sending approval: resume=true, thread_id=", threadIdRef.current);
    setApprovalDialogOpen(false);
    setIsLoading(true);

    wsRef.current.send(
      JSON.stringify({ thread_id: threadIdRef.current, resume: "true" })
    );
  };

  const handleReject = () => {
    if (!threadIdRef.current || !wsRef.current) {
      console.error("Cannot reject: missing thread_id or WebSocket");
      return;
    }

    console.log("Sending rejection: resume=false, thread_id=", threadIdRef.current);
    setApprovalDialogOpen(false);

    wsRef.current.send(
      JSON.stringify({ thread_id: threadIdRef.current, resume: "false" })
    );
  };

  const copyOutput = () => {
    if (result?.response) {
      navigator.clipboard.writeText(result.response).then(() => {
        toast({
          title: "Copied to clipboard",
          description: "Task output has been copied to your clipboard",
        });
      }).catch((err) => {
        console.error("Failed to copy to clipboard:", err);
        toast({
          title: "Copy Failed",
          description: "Unable to copy to clipboard",
          className: "bg-red-50 border-red-200 text-red-800",
        });
      });
    }
  };

  const getStatusIcon = () => {
    if (!result) return null;

    if (result.error) return <AlertTriangle className="h-5 w-5 text-red-500" />;
    if (result.requires_approval || result.interrupt)
      return <Clock className="h-5 w-5 text-yellow-500" />;
    if (result.is_final)
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    return <Clock className="h-5 w-5 text-blue-500" />;
  };

  const getStatusColor = () => {
    if (!result) return "bg-gray-500";

    if (result.error) return "bg-red-500";
    if (result.requires_approval || result.interrupt) return "bg-yellow-500";
    if (result.is_final) return "bg-green-500";
    return "bg-blue-500";
  };

  const getStatusText = () => {
    if (!result) return "Not Started";

    if (result.error) return "Failed";
    if (result.requires_approval || result.interrupt) return "Awaiting Approval";
    if (result.is_final) return "Completed";
    return "Running";
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        console.log("Cleaning up WebSocket on unmount");
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Zap className="h-8 w-8 text-orange-500" />
          Task Execution
        </h1>
        <p className="text-muted-foreground">AI powered task execution with approval workflow</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            Create New Task
          </CardTitle>
          <CardDescription>Define and execute tasks with optional chained tool execution</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="taskName">Task Description</Label>
            <div className="flex gap-2">
              <Input
                id="taskName"
                placeholder="e.g., List available tools or Search users by name John"
                value={taskName}
                onChange={(e) => setTaskName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleStartTask()}
                disabled={isLoading}
              />
              <Button
                onClick={handleStartTask}
                disabled={!taskName.trim() || isLoading}
                className={
                  !taskName.trim() || isLoading
                    ? "opacity-50 cursor-not-allowed"
                    : ""
                }
              >
                {isLoading ? (
                  <svg
                    className="animate-spin h-5 w-5 text-white mr-2"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                ) : null}
                {isLoading ? "Executing..." : "Start Task"}
              </Button>
            </div>
            <div className="flex items-center space-x-2 pt-2">
              <Checkbox
                id="chained"
                checked={chained}
                onCheckedChange={(checked) => setChained(Boolean(checked))}
                disabled={isLoading}
              />
              <label
                htmlFor="chained"
                className="text-sm font-medium leading-none"
              >
                Enable Chained Tool Calls (Multi-step execution)
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                {getStatusIcon()}
                Task Execution Result
              </span>
              {result.response && (
                <Button variant="outline" size="sm" onClick={copyOutput}>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy Output
                </Button>
              )}
            </CardTitle>
            <CardDescription>
              Execution result for task: "{taskName}" {threadIdRef.current ? `(ID: ${threadIdRef.current})` : ''}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Task ID</Label>
                <p className="text-sm font-mono break-all">{result.thread_id || "N/A"}</p>
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Status</Label>
                <Badge className={`${getStatusColor()} text-white`}>
                  {getStatusText()}
                </Badge>
              </div>
            </div>

            {result.response && !result.is_final && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">Partial Output</Label>
                <div className="p-4 bg-muted/50 rounded-lg border font-mono text-sm whitespace-pre-wrap max-h-48 overflow-y-auto">
                  {result.response}
                </div>
              </div>
            )}

            {result.response && result.is_final && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">Final Output</Label>
                <div className="p-4 bg-green-50 text-gray-800 border border-green-200 rounded-lg font-mono text-sm whitespace-pre-wrap">
                  {result.response}
                </div>
              </div>
            )}

            {result.error && (
              <div className="space-y-2">
                <Label className="text-sm font-medium text-red-600">
                  Error Details
                </Label>
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-800 whitespace-pre-wrap">{result.error}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

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