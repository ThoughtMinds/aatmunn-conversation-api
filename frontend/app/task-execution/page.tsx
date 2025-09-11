"use client";

import { useState, useEffect, useRef } from "react";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { Zap, Play, CheckCircle, Clock, AlertTriangle, Copy } from "lucide-react";
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
  processing_time?: number;
  thread_id?: string;
  requires_approval?: boolean;
  actions_to_review?: ApprovalRequest;
  error?: string;
}

export default function TaskExecutionPage() {
  const [taskName, setTaskName] = useState("");
  const [chained, setChained] = useState(false);
  const [result, setResult] = useState<TaskResult | null>(null);
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
  const [currentApprovalRequest, setCurrentApprovalRequest] = useState<ApprovalRequest | null>(null);
  const { toast } = useToast();
  const eventSourceRef = useRef<EventSource | null>(null);

  const handleStartTask = () => {
    if (!taskName.trim() || eventSourceRef.current) return;

    setResult(null);
    const eventSource = new EventSource(
      `${API_BASE_URL}/api/task_execution/execute_task/?query=${encodeURIComponent(taskName)}&chained=${chained}`,
      { withCredentials: true }
    );

    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setResult((prev) => ({ ...prev, ...data }));

      if (data.error) {
        toast({
          title: "Task Failed",
          description: data.error,
          className: "bg-red-50 border-red-200 text-red-800",
        });
        eventSource.close();
        eventSourceRef.current = null;
      } else if (data.requires_approval && data.actions_to_review) {
        setCurrentApprovalRequest(data.actions_to_review);
        setApprovalDialogOpen(true);
        eventSource.close();
        eventSourceRef.current = null;
      } else if (data.response && !data.requires_approval) {
        toast({
          title: "Task Completed",
          description: `Task "${taskName}" has completed successfully`,
          className: "bg-green-50 border-green-200 text-green-800",
        });
        setTaskName("");
        eventSource.close();
        eventSourceRef.current = null;
      }
    };

    eventSource.onerror = () => {
      toast({
        title: "Connection Error",
        description: "Failed to maintain stream connection",
        className: "bg-red-50 border-red-200 text-red-800",
      });
      eventSource.close();
      eventSourceRef.current = null;
    };
  };

  const handleApprove = () => {
    if (!result?.thread_id) return;

    const eventSource = new EventSource(
      `${API_BASE_URL}/api/task_execution/handle_approval/?thread_id=${result.thread_id}&approved=true`,
      { withCredentials: true }
    );

    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setResult((prev) => ({ ...prev, ...data, requires_approval: false, actions_to_review: null }));
      setApprovalDialogOpen(false); // Collapse the view

      if (data.response) {
        toast({
          title: "Task Approved",
          description: "Task execution completed successfully",
          className: "bg-green-50 border-green-200 text-green-800",
        });
      }
      eventSource.close();
      eventSourceRef.current = null;
    };

    eventSource.onerror = () => {
      toast({
        title: "Approval Failed",
        description: "Failed to process approval",
        className: "bg-red-50 border-red-200 text-red-800",
      });
      eventSource.close();
      eventSourceRef.current = null;
    };
  };

  const handleReject = () => {
    if (!result?.thread_id) return;

    const eventSource = new EventSource(
      `${API_BASE_URL}/api/task_execution/handle_approval/?thread_id=${result.thread_id}&approved=false`,
      { withCredentials: true }
    );

    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setResult((prev) => ({ ...prev, ...data, requires_approval: false, actions_to_review: null }));
      setApprovalDialogOpen(false); // Collapse the view

      if (data.response) {
        toast({
          title: "Task Rejected",
          description: "Task execution was cancelled",
          className: "bg-yellow-50 border-yellow-200 text-yellow-800",
        });
      }
      eventSource.close();
      eventSourceRef.current = null;
    };

    eventSource.onerror = () => {
      toast({
        title: "Rejection Failed",
        description: "Failed to process rejection",
        className: "bg-red-50 border-red-200 text-red-800",
      });
      eventSource.close();
      eventSourceRef.current = null;
    };
  };

  const copyOutput = () => {
    if (result?.response) {
      navigator.clipboard.writeText(result.response);
      toast({
        title: "Copied to clipboard",
        description: "Task output has been copied to your clipboard",
      });
    }
  };

  const getStatusIcon = () => {
    if (!result) return null;

    if (result.error) return <AlertTriangle className="h-5 w-5 text-red-500" />;
    if (result.requires_approval) return <Clock className="h-5 w-5 text-yellow-500" />;
    if (result.response) return <CheckCircle className="h-5 w-5 text-green-500" />;
    return <Clock className="h-5 w-5 text-blue-500" />;
  };

  const getStatusColor = () => {
    if (!result) return "bg-gray-500";

    if (result.error) return "bg-red-500";
    if (result.requires_approval) return "bg-yellow-500";
    if (result.response) return "bg-green-500";
    return "bg-blue-500";
  };

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, []);

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Zap className="h-8 w-8 text-orange-500" />
          Task Execution
        </h1>
        <p className="text-muted-foreground">AI powered task execution</p>
      </div>

      {/* Task Creation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            Create New Task
          </CardTitle>
          <CardDescription>Define and execute tasks</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="taskName">Task Name</Label>
            <div className="flex gap-2">
              <Input
                id="taskName"
                placeholder="Enter task name..."
                value={taskName}
                onChange={(e) => setTaskName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !loading) {
                    handleStartTask()
                  }
                }}
              />
              <Button onClick={handleStartTask} disabled={loading || !taskName.trim()}>
                {loading ? "Starting..." : "Start Task"}
              </Button>
            </div>
            <div className="flex items-center space-x-2 pt-2">
              <Checkbox id="chained" checked={chained} onCheckedChange={(checked) => setChained(Boolean(checked))} />
              <label
                htmlFor="chained"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Chained
              </label>
            </div>
            {loading && (
              <div className="flex items-center gap-2">
                <Badge variant="default" className="bg-blue-500">
                  Running
                </Badge>
                <span className="text-sm text-muted-foreground">Task is being processed...</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Task Result */}
      {result && (

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                {getStatusIcon()}
                Task Execution Result
              </span>
              {result.output && (
                <Button variant="outline" size="sm" onClick={copyOutput}>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy Output
                </Button>
              )}
            </CardTitle>
            <CardDescription>Execution result for task: "{result.taskName}"</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Task Details */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Task ID</Label>
                <p className="text-sm font-mono">{result.taskId}</p>
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Status</Label>
                <Badge className={getStatusColor()}>{result.status}</Badge>
              </div>
            </div>

            {/* Metadata */}
            <div className="flex items-center gap-4 pt-2 border-t">
              <Badge variant="outline">Processing Time: {result.processing_time}s</Badge>
            </div>

            {/* Task Output or Error */}
            {result.status === "completed" && result.output && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">Task Output</Label>
                <div className="p-4 bg-muted/50 rounded-lg border font-mono text-sm">
                  {result.output.map((line, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <span className="text-muted-foreground min-w-[20px]">{index + 1}.</span>
                      <span>{line}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.status === "failed" && result.errorMessage && (
              <div className="space-y-2">
                <Label className="text-sm font-medium text-red-600">Error Details</Label>
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-800">{result.errorMessage}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
