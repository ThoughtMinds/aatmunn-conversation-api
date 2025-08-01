"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { Zap, Play, CheckCircle, Clock, AlertTriangle, Copy } from "lucide-react"

interface TaskResult {
  taskName: string
  taskId: string
  status: "completed" | "failed" | "running"
  output?: string[]
  errorMessage?: string
}

// Add interface for API response
interface TaskApiResponse {
  response: string
  status: boolean
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || ""

export default function TaskExecutionPage() {
  const [taskName, setTaskName] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TaskResult | null>(null)
  const { toast } = useToast()

  // Update the handleStartTask function:
  const handleStartTask = async () => {
    if (!taskName.trim()) return

    setLoading(true)
    const taskId = `task_${Date.now()}`

    try {
      const response = await fetch(`${API_BASE_URL}/api/task_execution/execute_task/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: taskName,
        }),
      })

      if (response.ok) {
        const data: TaskApiResponse = await response.json()

        const mockResult: TaskResult = {
          taskName: taskName,
          taskId: taskId,
          status: data.status ? "completed" : "failed",
          output: data.status ? data.response.split("\n").filter((line) => line.trim()) : undefined,
          errorMessage: !data.status ? data.response : undefined,
        }

        setResult(mockResult)
        toast({
          title: data.status ? "Task Completed" : "Task Failed",
          description: `Task "${taskName}" has ${data.status ? "completed successfully" : "failed"}`,
          className: data.status
            ? "bg-green-50 border-green-200 text-green-800"
            : "bg-red-50 border-red-200 text-red-800",
        })

        setTaskName("")
      }
    } catch (error) {
      console.error("Failed to execute task:", error)
      toast({
        title: "Task Failed",
        description: "Failed to execute the task",
        className: "bg-red-50 border-red-200 text-red-800",
      })
    } finally {
      setLoading(false)
    }
  }

  const copyOutput = () => {
    if (result?.output) {
      navigator.clipboard.writeText(result.output.join("\n"))
      toast({
        title: "Copied to clipboard",
        description: "Task output has been copied to your clipboard",
      })
    }
  }

  const getStatusIcon = () => {
    if (!result) return null

    switch (result.status) {
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case "failed":
        return <AlertTriangle className="h-5 w-5 text-red-500" />
      case "running":
        return <Clock className="h-5 w-5 text-blue-500" />
      default:
        return null
    }
  }

  const getStatusColor = () => {
    if (!result) return "bg-gray-500"

    switch (result.status) {
      case "completed":
        return "bg-green-500"
      case "failed":
        return "bg-red-500"
      case "running":
        return "bg-blue-500"
      default:
        return "bg-gray-500"
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Zap className="h-8 w-8 text-orange-500" />
          Task Execution
        </h1>
        <p className="text-muted-foreground">Automated task processing and workflow management</p>
      </div>

      {/* Task Creation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            Create New Task
          </CardTitle>
          <CardDescription>Define and execute automated tasks</CardDescription>
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
              />
              <Button onClick={handleStartTask} disabled={loading || !taskName.trim()}>
                {loading ? "Starting..." : "Start Task"}
              </Button>
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
