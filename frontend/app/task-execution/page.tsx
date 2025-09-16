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
  const eventSourceRef = useRef<EventSource | null>(null);

  const handleStartTask = () => {
    if (!taskName.trim() || eventSourceRef.current || isLoading) return;

    setResult(null);
    setIsLoading(true);
    const eventSource = new EventSource(
      `${API_BASE_URL}/api/task_execution/execute_task/?query=${encodeURIComponent(
        taskName
      )}&chained=${chained}`,
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
        setIsLoading(false);
      } else if (data.requires_approval && data.actions_to_review) {
        setCurrentApprovalRequest(data.actions_to_review);
        setApprovalDialogOpen(true);
        eventSource.close();
        eventSourceRef.current = null;
        setIsLoading(false);
      } else if (data.response && !data.requires_approval) {
        toast({
          title: "Task Completed",
          description: `Task "${taskName}" has completed successfully`,
          className: "bg-green-50 border-green-200 text-green-800",
        });
        setTaskName("");
        eventSource.close();
        eventSourceRef.current = null;
        setIsLoading(false);
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
      setIsLoading(false);
    };
  };

  const handleApprove = async () => {
    if (!result?.thread_id) return;

    const eventSource = new EventSource(
      `${API_BASE_URL}/api/task_execution/handle_approval/?thread_id=${result.thread_id}&approved=true`,
      { withCredentials: true }
    );

    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setResult((prev) => ({
        ...prev,
        ...data,
        requires_approval: false,
        actions_to_review: null,
      }));
      setApprovalDialogOpen(false);

      if (data.response) {
        toast({
          title: "Task Approved",
          description: "Task execution completed successfully",
          className: "bg-green-50 border-green-200 text-green-800",
        });
      } else if (!data.response && data.thread_id) {
        fetchFinalResponse();
      }
    };

    eventSource.onerror = () => {
      toast({
        title: "Approval Failed",
        description: "Failed to process approval",
        className: "bg-red-50 border-red-200 text-red-800",
      });
      eventSource.close();
      eventSourceRef.current = null;
      fetchFinalResponse();
    };
  };

  const handleReject = async () => {
    if (!result?.thread_id) return;

    const eventSource = new EventSource(
      `${API_BASE_URL}/api/task_execution/handle_approval/?thread_id=${result.thread_id}&approved=false`,
      { withCredentials: true }
    );

    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setResult((prev) => ({
        ...prev,
        ...data,
        requires_approval: false,
        actions_to_review: null,
      }));
      setApprovalDialogOpen(false);

      if (data.response) {
        toast({
          title: "Task Rejected",
          description: "Task execution was cancelled",
          className: "bg-yellow-50 border-yellow-200 text-yellow-800",
        });
      }
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

  const fetchFinalResponse = async () => {
    if (!result?.thread_id) return;

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/task_execution/get_final_response/?thread_id=${result.thread_id}`,
        { credentials: "include" }
      );
      const data = await response.json();
      if (data.error) {
        toast({
          title: "Fetch Failed",
          description: data.error,
          className: "bg-red-50 border-red-200 text-red-800",
        });
      } else {
        setResult((prev) => ({
          ...prev,
          ...data,
          requires_approval: false,
          actions_to_review: null,
        }));
        toast({
          title: "Task Completed",
          description: "Final response fetched successfully",
          className: "bg-green-50 border-green-200 text-green-800",
        });
      }
    } catch (error) {
      toast({
        title: "Fetch Error",
        description: "Failed to fetch final response",
        className: "bg-red-50 border-red-200 text-red-800",
      });
    }
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
    if (result.requires_approval)
      return <Clock className="h-5 w-5 text-yellow-500" />;
    if (result.response)
      return <CheckCircle className="h-5 w-5 text-green-500" />;
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
                onKeyDown={(e) => e.key === "Enter" && handleStartTask()}
                disabled={isLoading}
              />
              <Button
                onClick={handleStartTask}
                disabled={
                  !taskName.trim() || !!eventSourceRef.current || isLoading
                }
                className={
                  !taskName.trim() || !!eventSourceRef.current || isLoading
                    ? "opacity-50 cursor-not-allowed"
                    : ""
                }
              >
                {isLoading ? (
                  <svg
                    className="animate-spin h-5 w-5 text-white"
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
                ) : (
                  "Start Task"
                )}
              </Button>
            </div>
            <div className="flex items-center space-x-2 pt-2">
              <Checkbox
                id="chained"
                checked={chained}
                onCheckedChange={(checked) => setChained(Boolean(checked))}
              />
              <label
                htmlFor="chained"
                className="text-sm font-medium leading-none"
              >
                Chained Tool Calls
              </label>
            </div>
          </div>
          {isLoading && (
            <div className="flex items-center justify-center py-4">
              <svg
                className="animate-spin h-8 w-8 text-blue-500"
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
              <span className="ml-2 text-sm text-muted-foreground">
                Processing task...
              </span>
            </div>
          )}
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
              Execution result for task: "{taskName}"
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Task ID</Label>
                <p className="text-sm font-mono">{result.thread_id || "N/A"}</p>
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Status</Label>
                <Badge className={getStatusColor()}>
                  {result.error
                    ? "Failed"
                    : result.requires_approval
                    ? "Awaiting Approval"
                    : result.response
                    ? "Completed"
                    : "Running"}
                </Badge>
              </div>
            </div>

            {result.response && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">Task Output</Label>
                <div className="p-4 bg-muted/50 rounded-lg border font-mono text-sm whitespace-pre-wrap">
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
                  <p className="text-sm text-red-800">{result.error}</p>
                </div>
              </div>
            )}

            {result.requires_approval && result.actions_to_review && (
              <div className="space-y-2">
                <Label className="text-sm font-medium text-yellow-600">
                  Awaiting Approval
                </Label>
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    Please review and approve the actions in the dialog above.
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {approvalDialogOpen && currentApprovalRequest && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-lg w-full max-w-4xl mx-auto max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4 text-black">
              Action Approval Required
            </h3>
            <p className="mb-4 text-black">{currentApprovalRequest.question}</p>
            <div className="mb-4">
              <h4 className="font-medium mb-2 text-black">
                Query: {currentApprovalRequest.query}
              </h4>
              <div className="space-y-2">
                {currentApprovalRequest.actions.map((action, index) => (
                  <div key={index} className="p-3 border rounded-md">
                    <p className="font-medium text-green-600">{action.tool}</p>
                    <pre className="text-xs mt-2 bg-muted p-2 rounded overflow-x-auto text-orange-600">
                      {JSON.stringify(action.parameters, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <Button
                onClick={handleApprove}
                className="bg-green-500 text-white hover:bg-green-600"
              >
                Approve
              </Button>
              <Button
                onClick={handleReject}
                className="bg-red-500 text-white hover:bg-red-600"
              >
                Reject
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
