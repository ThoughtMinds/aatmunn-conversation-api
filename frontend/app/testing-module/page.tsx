"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { Upload, CheckCircle, XCircle, Clock, FileText, Zap, Navigation } from "lucide-react"
import { API_BASE_URL } from "@/constants/api"

interface TestResult {
  id: string
  predicted_intent: string
  predicted_response: string
  actual_response: string
  status: "Success" | "Failure"
  summarization_analysis: string
  summarization_score: number | null
  tat: string
}

interface TestCase {
  query: string
  expected_intent: string
  expected_response?: string
  directives?: string
}

export default function TestingModule() {
  const [testResults, setTestResults] = useState<TestResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [totalTests, setTotalTests] = useState(0)
  const [completedTests, setCompletedTests] = useState(0)
  const { toast } = useToast()
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    // Cleanup EventSource on component unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [])

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsLoading(true)
    setTestResults([])
    setProgress(0)
    setCompletedTests(0)

    try {
      const formData = new FormData()
      formData.append("file", file)

      // First, get the total number of test cases
      const countResponse = await fetch(`${API_BASE_URL}/api/testing/count_test_cases/`, {
        method: "POST",
        body: formData,
      })

      if (!countResponse.ok) {
        throw new Error("Failed to count test cases")
      }

      const countData = await countResponse.json()
      setTotalTests(countData.total_cases)

      // Reset form data for the actual test execution
      const executionFormData = new FormData()
      executionFormData.append("file", file)

      // Start streaming test results
      startTestStreaming(executionFormData)
    } catch (error) {
      console.error("Error processing test file:", error)
      toast({
        title: "Error processing file",
        description: "Failed to process the test file. Please try again.",
        variant: "destructive",
      })
      setIsLoading(false)
    }
  }

  const startTestStreaming = (formData: FormData) => {
    // Close any existing EventSource
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    try {
      // Create new EventSource for streaming test results
      eventSourceRef.current = new EventSource(`${API_BASE_URL}/api/testing/run_tests_stream/`, {
        withCredentials: true,
      })

      eventSourceRef.current.onmessage = (event) => {
        try {
          const testResult: TestResult = JSON.parse(event.data)
          
          if (testResult.error) {
            toast({
              title: "Test error",
              description: testResult.error,
              variant: "destructive",
            })
            eventSourceRef.current?.close()
            eventSourceRef.current = null
            setIsLoading(false)
            return
          }

          setTestResults(prev => [...prev, testResult])
          setCompletedTests(prev => prev + 1)
          setProgress(Math.round(((completedTests + 1) / totalTests) * 100))
        } catch (error) {
          console.error("Error parsing test result:", error)
        }
      }

      eventSourceRef.current.onerror = (error) => {
        console.error("EventSource error:", error)
        toast({
          title: "Streaming error",
          description: "Connection lost during testing.",
          variant: "destructive",
        })
        eventSourceRef.current?.close()
        eventSourceRef.current = null
        setIsLoading(false)
      }

      // Send the form data to start the tests
      fetch(`${API_BASE_URL}/api/testing/run_tests/`, {
        method: "POST",
        body: formData,
      }).catch(error => {
        console.error("Failed to start tests:", error)
        toast({
          title: "Failed to start tests",
          description: "Could not initiate the testing process.",
          variant: "destructive",
        })
        setIsLoading(false)
      })

    } catch (error) {
      console.error("Error setting up test streaming:", error)
      toast({
        title: "Testing error",
        description: "Failed to set up testing stream.",
        variant: "destructive",
      })
      setIsLoading(false)
    }
  }

  const getIntentIcon = (intent: string) => {
    switch (intent) {
      case "navigation":
        return <Navigation className="h-4 w-4" />
      case "summarization":
        return <FileText className="h-4 w-4" />
      case "task_execution":
        return <Zap className="h-4 w-4" />
      default:
        return <FileText className="h-4 w-4" />
    }
  }

  const getStatusBadge = (status: string) => {
    if (status === "Success") {
      return (
        <Badge className="bg-green-100 text-green-800 hover:bg-green-100">
          <CheckCircle className="h-3 w-3 mr-1" />
          Success
        </Badge>
      )
    } else {
      return (
        <Badge variant="destructive" className="bg-red-100 text-red-800 hover:bg-red-100">
          <XCircle className="h-3 w-3 mr-1" />
          Failure
        </Badge>
      )
    }
  }

  const getScoreColor = (score: number | null) => {
    if (score === null) return "text-gray-500"
    if (score >= 90) return "text-green-600"
    if (score >= 70) return "text-yellow-600"
    return "text-red-600"
  }

  // Mock data for demonstration
  const mockTestResults: TestResult[] = [
    {
      id: "1",
      predicted_intent: "navigation",
      predicted_response: "Navigating to user profile page",
      actual_response: "Navigating to user profile page",
      status: "Success",
      summarization_analysis: "",
      summarization_score: null,
      tat: "1.5 s"
    },
    {
      id: "2",
      predicted_intent: "task_execution",
      predicted_response: "API called with parameters: {action: 'create', entity: 'user'}",
      actual_response: "API called with parameters: {action: 'create', entity: 'user'}",
      status: "Success",
      summarization_analysis: "",
      summarization_score: null,
      tat: "1.5 s"
    },
    {
      id: "3",
      predicted_intent: "summarization",
      predicted_response: "Not Applicable",
      actual_response: "This is a summary of the provided document content...",
      status: "Success",
      summarization_analysis: "Use LLM to Compare the generated response with Directives in the test case file",
      summarization_score: 95,
      tat: "1.5 s"
    }
  ]

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <FileText className="h-8 w-8 text-blue-500" />
          Testing Module
        </h1>
        <p className="text-muted-foreground">
          Upload test cases to evaluate intent identification and agent responses
        </p>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload Test Cases
          </CardTitle>
          <CardDescription>
            Upload an Excel file containing test cases with queries and expected responses
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
            <Button variant="outline" disabled>
              <Upload className="h-4 w-4 mr-2" />
              Upload
            </Button>
          </div>

          {isLoading && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Running tests...</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className="bg-blue-600 h-2.5 rounded-full" 
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <div className="text-sm text-muted-foreground">
                Completed {completedTests} of {totalTests} tests
              </div>
            </div>
          )}
        </CardContent>
      </Card>

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
                  <p>Running tests... Results will appear here as they complete.</p>
                </div>
              ) : (
                <p>Upload a test file to see results here</p>
              )}
            </div>
          ) : (
            <div className="border rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="text-left p-3 font-medium">Predicted Intent</th>
                      <th className="text-left p-3 font-medium">Predicted Response</th>
                      <th className="text-left p-3 font-medium">Actual Response</th>
                      <th className="text-left p-3 font-medium">Status</th>
                      <th className="text-left p-3 font-medium">Summarization Analysis</th>
                      <th className="text-left p-3 font-medium">Summarization Score</th>
                      <th className="text-left p-3 font-medium">TAT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {testResults.map((result, index) => (
                      <tr key={result.id || index} className="border-b hover:bg-muted/25">
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            {getIntentIcon(result.predicted_intent)}
                            <span className="font-medium">{result.predicted_intent}</span>
                          </div>
                        </td>
                        <td className="p-3 text-muted-foreground">{result.predicted_response}</td>
                        <td className="p-3 text-muted-foreground">{result.actual_response}</td>
                        <td className="p-3">{getStatusBadge(result.status)}</td>
                        <td className="p-3 text-muted-foreground">{result.summarization_analysis}</td>
                        <td className={`p-3 font-medium ${getScoreColor(result.summarization_score)}`}>
                          {result.summarization_score !== null ? `${result.summarization_score}%` : "N/A"}
                        </td>
                        <td className="p-3 text-muted-foreground">{result.tat}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Mock Data for Demonstration */}
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle>Example Test Results (Mock Data)</CardTitle>
          <CardDescription>
            Sample of how test results will appear once you upload a file
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="text-left p-3 font-medium">Predicted Intent</th>
                    <th className="text-left p-3 font-medium">Predicted Response</th>
                    <th className="text-left p-3 font-medium">Actual Response</th>
                    <th className="text-left p-3 font-medium">Status</th>
                    <th className="text-left p-3 font-medium">Summarization Analysis</th>
                    <th className="text-left p-3 font-medium">Summarization Score</th>
                    <th className="text-left p-3 font-medium">TAT</th>
                  </tr>
                </thead>
                <tbody>
                  {mockTestResults.map((result, index) => (
                    <tr key={`mock-${index}`} className="border-b hover:bg-muted/25">
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          {getIntentIcon(result.predicted_intent)}
                          <span className="font-medium">{result.predicted_intent}</span>
                        </div>
                      </td>
                      <td className="p-3 text-muted-foreground">{result.predicted_response}</td>
                      <td className="p-3 text-muted-foreground">{result.actual_response}</td>
                      <td className="p-3">{getStatusBadge(result.status)}</td>
                      <td className="p-3 text-muted-foreground">{result.summarization_analysis}</td>
                      <td className={`p-3 font-medium ${getScoreColor(result.summarization_score)}`}>
                        {result.summarization_score !== null ? `${result.summarization_score}%` : "N/A"}
                      </td>
                      <td className="p-3 text-muted-foreground">{result.tat}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}