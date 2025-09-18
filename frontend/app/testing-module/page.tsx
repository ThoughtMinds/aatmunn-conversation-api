"use client";

import { useState, useRef, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import {
  Upload,
  CheckCircle,
  XCircle,
  Clock,
  FileText,
  Zap,
  Navigation,
  Check,
  X,
} from "lucide-react";
import { API_BASE_URL } from "@/constants/api";

interface TestResult {
  id: string;
  predicted_intent: string;
  predicted_response: string;
  actual_response: string;
  status: "Success" | "Failure";
  summarization_analysis: string;
  summarization_score: number | null;
  tat: string;
}

interface TestCase {
  "Sl No": number;
  Input: string;
  "Actual Intent": string;
  "Actual Response": string;
  Directives: string;
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

export default function TestingModule() {
  const [testResults, setTestResults] = useState<
    (TestResult & { sl_no: number; input: string; directives: string })[]
  >([]);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [totalTests, setTotalTests] = useState(0);
  const [completedTests, setCompletedTests] = useState(0);
  const [previewData, setPreviewData] = useState<TestCase[]>([]);
  const [showPreview, setShowPreview] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
  const [currentApprovalRequest, setCurrentApprovalRequest] = useState<ApprovalRequest | null>(null);
  const [currentTestIndex, setCurrentTestIndex] = useState<number | null>(null);
  const { toast } = useToast();
  const eventSourceRef = useRef<EventSource | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const threadIdRef = useRef<string | null>(null);

  useEffect(() => {
    // Cleanup EventSource and WebSocket on component unmount
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

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setShowPreview(true);
    setTestResults([]);
    setProgress(0);
    setCompletedTests(0);
    setTotalTests(0);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const previewResponse = await fetch(
        `${API_BASE_URL}/api/testing/preview_test_cases/`,
        {
          method: "POST",
          body: formData,
        }
      );
      if (!previewResponse.ok) throw new Error("Failed to fetch preview");
      const jsonData: TestCase[] = await previewResponse.json();
      setPreviewData(jsonData);
    } catch (error) {
      console.error("Error fetching preview:", error);
      toast({
        title: "Error reading file",
        description:
          "Failed to read the test file. Please ensure it's a valid .xlsx or .xls file.",
        variant: "destructive",
      });
      setShowPreview(false);
      setSelectedFile(null);
    }
  };

  const handleRunTests = async () => {
    if (!selectedFile) return;

    setIsLoading(true);
    setShowPreview(false);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      // Get the total number of test cases
      const countResponse = await fetch(
        `${API_BASE_URL}/api/testing/count_test_cases/`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!countResponse.ok) {
        throw new Error("Failed to count test cases");
      }

      const countData = await countResponse.json();
      setTotalTests(countData.total_cases);

      // Start streaming test results
      startTestStreaming(formData);
    } catch (error) {
      console.error("Error processing test file:", error);
      toast({
        title: "Error processing file",
        description: "Failed to process the test file. Please try again.",
        variant: "destructive",
      });
      setIsLoading(false);
    }
  };

  const startTestStreaming = (formData: FormData) => {
    // Close any existing EventSource
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    try {
      // Create new EventSource for streaming test results
      eventSourceRef.current = new EventSource(
        `${API_BASE_URL}/api/testing/run_tests_stream/`,
        {
          withCredentials: true,
        }
      );

      eventSourceRef.current.onmessage = (event) => {
        try {
          const testResult: TestResult & { interrupt?: boolean; payload?: ApprovalRequest } = JSON.parse(event.data);

          if (testResult.error) {
            toast({
              title: "Test error",
              description: testResult.error,
              variant: "destructive",
            });
            eventSourceRef.current?.close();
            eventSourceRef.current = null;
            setIsLoading(false);
            return;
          }

          if (testResult.interrupt && testResult.payload) {
            setCurrentApprovalRequest(testResult.payload);
            setCurrentTestIndex(completedTests);
            setApprovalDialogOpen(true);
            return;
          }

          setTestResults((prev) => [
            ...prev,
            {
              ...testResult,
              sl_no: previewData[prev.length]["Sl No"],
              input: previewData[prev.length].Input,
              directives: previewData[prev.length].Directives,
            },
          ]);
          setCompletedTests((prev) => prev + 1);
          setProgress(Math.round(((completedTests + 1) / totalTests) * 100));
        } catch (error) {
          console.error("Error parsing test result:", error);
        }
      };

      eventSourceRef.current.onerror = (error) => {
        console.error("EventSource error:", error);
        toast({
          title: "Streaming error",
          description: "Connection lost during testing.",
          variant: "destructive",
        });
        eventSourceRef.current?.close();
        eventSourceRef.current = null;
        setIsLoading(false);
      };

      // Send the form data to start the tests
      fetch(`${API_BASE_URL}/api/testing/run_tests/`, {
        method: "POST",
        body: formData,
      }).catch((error) => {
        console.error("Failed to start tests:", error);
        toast({
          title: "Failed to start tests",
          description: "Could not initiate the testing process.",
          variant: "destructive",
        });
        setIsLoading(false);
      });
    } catch (error) {
      console.error("Error setting up test streaming:", error);
      toast({
        title: "Testing error",
        description: "Failed to set up testing stream.",
        variant: "destructive",
      });
      setIsLoading(false);
    }
  };

  const handleApprove = () => {
    if (!threadIdRef.current || !wsRef.current || currentTestIndex === null) {
      console.error("Cannot approve: missing thread_id, WebSocket, or test index");
      return;
    }

    wsRef.current.send(
      JSON.stringify({ thread_id: threadIdRef.current, resume: "true" })
    );
    setApprovalDialogOpen(false);
  };

  const handleReject = () => {
    if (!threadIdRef.current || !wsRef.current || currentTestIndex === null) {
      console.error("Cannot reject: missing thread_id, WebSocket, or test index");
      return;
    }

    wsRef.current.send(
      JSON.stringify({ thread_id: threadIdRef.current, resume: "false" })
    );
    setApprovalDialogOpen(false);
  };

  const getIntentIcon = (intent: string) => {
    switch (intent) {
      case "navigation":
        return <Navigation className="h-4 w-4 text-blue-500" />;
      case "summarization":
        return <FileText className="h-4 w-4 text-purple-500" />;
      case "task_execution":
        return <Zap className="h-4 w-4 text-orange-500" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getStatusBadge = (status: string) => {
    if (status === "Success") {
      return (
        <Badge className="bg-green-100 text-green-800 hover:bg-green-500 hover:text-white dark:bg-green-900 dark:text-green-200">
          <Check className="h-3 w-3 mr-1" />
          Success
        </Badge>
      );
    } else {
      return (
        <Badge className="bg-red-100 text-red-800 hover:bg-red-500 hover:text-white dark:bg-red-900 dark:text-red-200">
          <X className="h-3 w-3 mr-1" />
          Failure
        </Badge>
      );
    }
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return "text-gray-500 dark:text-gray-400";
    if (score >= 80) return "text-green-600 dark:text-green-400";
    if (score >= 50) return "text-yellow-600 dark:text-yellow-400";
    return "text-red-600 dark:text-red-400";
  };

  const getResponseHighlight = (result: TestResult) => {
    if (result.predicted_intent === "navigation") {
      return result.predicted_response === result.actual_response
        ? "bg-green-50 text-green-800 dark:bg-green-900/30 dark:text-green-300"
        : "bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-300";
    } else if (result.predicted_intent === "task_execution") {
      try {
        const predictedJson = JSON.parse(
          result.predicted_response.replace(/'/g, '"')
        );
        const actualJson = JSON.parse(
          result.actual_response.replace(/'/g, '"')
        );
        const predictedStr = JSON.stringify(predictedJson, null, 0);
        const actualStr = JSON.stringify(actualJson, null, 0);
        return predictedStr === actualStr
          ? "bg-green-50 text-green-800 dark:bg-green-900/30 dark:text-green-300"
          : "bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-300";
      } catch (e) {
        return result.predicted_response === result.actual_response
          ? "bg-green-50 text-green-800 dark:bg-green-900/30 dark:text-green-300"
          : "bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-300";
      }
    }
    return result.summarization_score !== null &&
      result.summarization_score >= 80
      ? "bg-green-50 text-green-800 dark:bg-green-900/30 dark:text-green-300"
      : "bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-300";
  };

  const getStatusIcon = (status: string) => {
    return status === "Success" ? (
      <CheckCircle className="h-4 w-4 text-green-500" />
    ) : (
      <XCircle className="h-4 w-4 text-red-500" />
    );
  };

  return (
    <div className="space-y-6">
      {/* Upload Card */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Test File</CardTitle>
          <CardDescription>
            Upload an Excel or CSV file containing test cases
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Input
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileUpload}
              disabled={isLoading}
            />
            <Button variant="outline" disabled={isLoading}>
              <Upload className="h-4 w-4 mr-2" />
              Upload
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Preview Card */}
      {showPreview && previewData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>File Preview</CardTitle>
            <CardDescription>
              Review the test cases before running. For task_execution, include
              'chained=true' in Directives for chained execution.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg overflow-hidden dark:border-gray-700">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 dark:bg-gray-800">
                    <tr>
                      <th className="text-left p-3 font-medium">Sl No</th>
                      <th className="text-left p-3 font-medium">Input</th>
                      <th className="text-left p-3 font-medium">
                        Actual Intent
                      </th>
                      <th className="text-left p-3 font-medium">
                        Actual Response
                      </th>
                      <th className="text-left p-3 font-medium">Directives</th>
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.map((row, index) => (
                      <tr
                        key={index}
                        className="border-b hover:bg-muted/25 dark:border-gray-700 dark:hover:bg-gray-800/50"
                      >
                        <td className="p-3">{row["Sl No"]}</td>
                        <td className="p-3">{row.Input}</td>
                        <td className="p-3">{row["Actual Intent"]}</td>
                        <td className="p-3">{row["Actual Response"]}</td>
                        <td className="p-3">{row.Directives}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowPreview(false)}>
                Cancel
              </Button>
              <Button onClick={handleRunTests} disabled={isLoading}>
                Run Tests
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Progress Card */}
      {isLoading && (
        <Card>
          <CardContent className="space-y-2 pt-6">
            <div className="flex items-center justify-between text-sm">
              <span>Running tests...</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
              <div
                className="bg-blue-600 h-2.5 rounded-full"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <div className="text-sm text-muted-foreground">
              Completed {completedTests} of {totalTests} tests
            </div>
          </CardContent>
        </Card>
      )}

      {/* Approval Dialog */}
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

      {/* Results Table */}
      <Card>
        <CardHeader>
          <CardTitle>Test Results</CardTitle>
          <CardDescription>
            Results of the intent identification and response evaluation
          </CardDescription>
        </CardHeader>
        <CardContent>
          {testResults.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {isLoading ? (
                <div className="flex flex-col items-center gap-2">
                  <Clock className="h-8 w-8 animate-pulse" />
                  <p>
                    Running tests... Results will appear here as they complete.
                  </p>
                </div>
              ) : (
                <p>Upload a test file to see results here</p>
              )}
            </div>
          ) : (
            <div className="border rounded-lg overflow-hidden dark:border-gray-700">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 dark:bg-gray-800">
                    <tr>
                      <th className="text-left p-3 font-medium">Sl No</th>
                      <th className="text-left p-3 font-medium">Input</th>
                      <th className="text-left p-3 font-medium">
                        Predicted Intent
                      </th>
                      <th className="text-left p-3 font-medium">
                        Predicted Response
                      </th>
                      <th className="text-left p-3 font-medium">
                        Actual Response
                      </th>
                      <th className="text-left p-3 font-medium">Status</th>
                      <th className="text-left p-3 font-medium">Analysis</th>
                      <th className="text-left p-3 font-medium">Score</th>
                      <th className="text-left p-3 font-medium">TAT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {testResults.map((result, index) => (
                      <tr
                        key={result.id || index}
                        className="border-b hover:bg-muted/25 dark:border-gray-700 dark:hover:bg-gray-800/50"
                      >
                        <td className="p-3">{result.sl_no}</td>
                        <td className="p-3">{result.input}</td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            {getIntentIcon(result.predicted_intent)}
                            <span className="font-medium">
                              {result.predicted_intent}
                            </span>
                          </div>
                        </td>
                        <td className={`p-3 ${getResponseHighlight(result)}`}>
                          {result.predicted_response}
                        </td>
                        <td className={`p-3 ${getResponseHighlight(result)}`}>
                          {result.predicted_intent === "summarization"
                            ? result.directives
                            : result.actual_response}
                        </td>
                        <td className="p-3">{getStatusIcon(result.status)}</td>
                        <td className="p-3 text-muted-foreground dark:text-gray-400">
                          {result.summarization_analysis}
                        </td>
                        <td
                          className={`p-3 font-medium ${getScoreColor(
                            result.summarization_score
                          )}`}
                        >
                          {result.summarization_score !== null
                            ? `${result.summarization_score}%`
                            : "N/A"}
                        </td>
                        <td className="p-3 text-muted-foreground dark:text-gray-400">
                          {result.tat}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}