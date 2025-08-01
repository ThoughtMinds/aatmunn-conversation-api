"use client"
import { useState, useEffect } from "react"
import { Navigation, FileText, Zap, Activity, CheckCircle, Target } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { useTheme } from "next-themes"
import { useToast } from "@/hooks/use-toast"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Intent {
  intent_id: number
  intent: string
  description: string
  parameters: Record<string, string>
  required: string[]
  responses: Record<string, string>
}

interface NavigationTestResult {
  query: string
  actual_intent: string
  predicted_intent: string
  response_time: number
}

interface NavigationResult {
  id: string
  reasoning: string
  intent_name: string
}

interface DashboardStats {
  total_intents: number
  total_summaries: number
  total_tasks: number
  total_queries: number
}

interface OrchestrationResponse {
  category: "navigation" | "summarization" | "task_execution"
}

export default function IntentManagementApp() {
  const { theme, setTheme } = useTheme()
  const { toast } = useToast()

  // Intent Classification state
  const [intentQuery, setIntentQuery] = useState("")
  const [intentLoading, setIntentLoading] = useState(false)
  const [intentResult, setIntentResult] = useState<OrchestrationResponse | null>(null)

  // Dashboard stats state
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null)
  const [loadingStats, setLoadingStats] = useState(true)

  // Add this useEffect to fetch dashboard stats
  useEffect(() => {
    fetchDashboardStats()
  }, [])

  const fetchDashboardStats = async () => {
    setLoadingStats(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/metadata/get_dashboard_stats/`)
      if (response.ok) {
        const data = await response.json()
        setDashboardStats(data)
      }
    } catch (error) {
      console.error("Failed to fetch dashboard stats:", error)
    } finally {
      setLoadingStats(false)
    }
  }

  const handleIntentClassification = async () => {
    if (!intentQuery.trim()) return

    setIntentLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/orchestrator/identify_intent/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: intentQuery,
        }),
      })

      if (response.ok) {
        const result: OrchestrationResponse = await response.json()
        setIntentResult(result)
        toast({
          title: "Intent Classified",
          description: `Query classified as: ${result.category}`,
          className: "bg-green-50 border-green-200 text-green-800",
        })
      }
    } catch (error) {
      console.error("Failed to classify intent:", error)
      toast({
        title: "Classification Failed",
        description: "Failed to classify the intent",
        className: "bg-red-50 border-red-200 text-red-800",
      })
    } finally {
      setIntentLoading(false)
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
    <div className="space-y-8">
      {/* Dashboard Section */}
      <div className="space-y-6">
        {/* Welcome Section */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome to Aatmunn PoC - Your intelligent navigation, summarization, and task execution platform.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{loadingStats ? "..." : dashboardStats?.total_queries || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Intents</CardTitle>
              <Navigation className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{loadingStats ? "..." : dashboardStats?.total_intents || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Summaries</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{loadingStats ? "..." : dashboardStats?.total_summaries || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{loadingStats ? "..." : dashboardStats?.total_tasks || 0}</div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Intent Classification Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-green-500" />
            Intent Classification
          </CardTitle>
          <CardDescription>
            Enter your query to automatically identify its category and get routed to the appropriate service
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="intent-query">Query</Label>
            <div className="flex gap-2">
              <Input
                id="intent-query"
                placeholder="Enter your query to classify its intent..."
                value={intentQuery}
                onChange={(e) => setIntentQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleIntentClassification()}
              />
              <Button onClick={handleIntentClassification} disabled={intentLoading || !intentQuery.trim()}>
                {intentLoading ? "Classifying..." : "Classify"}
              </Button>
            </div>
          </div>

          {intentResult && (
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-500" />
                      <span className="font-medium">Intent Identified</span>
                    </div>
                    <p className="text-sm text-muted-foreground">Query: "{intentQuery}"</p>
                  </div>
                  <Badge className={`${getCategoryColor(intentResult.category)} text-white`}>
                    <span className="flex items-center gap-1">
                      {getCategoryIcon(intentResult.category)}
                      {intentResult.category.replace("_", " ")}
                    </span>
                  </Badge>
                </div>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>

      {/* Main Components Overview */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Navigation className="h-5 w-5 text-blue-500" />
              <CardTitle>Navigation</CardTitle>
            </div>
            <CardDescription>Intelligent query routing and intent recognition system</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Total Intents</span>
              <Badge variant="secondary">{loadingStats ? "..." : dashboardStats?.total_intents || 0}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-purple-500" />
              <CardTitle>Summarization</CardTitle>
            </div>
            <CardDescription>Document analysis and intelligent content summarization</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Total Summaries</span>
              <Badge variant="secondary">{loadingStats ? "..." : dashboardStats?.total_summaries || 0}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Zap className="h-5 w-5 text-orange-500" />
              <CardTitle>Task Execution</CardTitle>
            </div>
            <CardDescription>Automated task processing and workflow management</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Total Tasks</span>
              <Badge variant="secondary">{loadingStats ? "..." : dashboardStats?.total_tasks || 0}</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
