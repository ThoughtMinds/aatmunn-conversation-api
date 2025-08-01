"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Moon, Sun, Navigation, FileText, Zap, Activity } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useTheme } from "next-themes"
import { Badge } from "@/components/ui/badge"

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

// Add this interface near the top with other interfaces
interface DashboardStats {
  total_intents: number
  total_summaries: number
  total_tasks: number
  total_queries: number
}

export default function IntentManagementApp() {
  const { theme, setTheme } = useTheme()
  const [intents, setIntents] = useState<Intent[]>([])
  const [navigationQuery, setNavigationQuery] = useState("")
  const [navigationResult, setNavigationResult] = useState<NavigationResult | null>(null)
  const [testResults, setTestResults] = useState<NavigationTestResult[]>([])
  const [loading, setLoading] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [newIntent, setNewIntent] = useState({
    intent: "",
    description: "",
    parameters: {} as Record<string, string>,
    required: [] as string[],
    responses: {} as Record<string, string>,
    chroma_id: null as string | null,
  })
  const [parameterInput, setParameterInput] = useState({ key: "", value: "" })
  const [requiredInput, setRequiredInput] = useState("")
  const [responseInput, setResponseInput] = useState({ key: "", value: "" })

  const [showEditModal, setShowEditModal] = useState(false)
  const [editingIntent, setEditingIntent] = useState<Intent | null>(null)
  const [editIntent, setEditIntent] = useState({
    intent: "",
    description: "",
    parameters: {} as Record<string, string>,
    required: [] as string[],
    responses: {} as Record<string, string>,
    chroma_id: null as string | null,
  })
  const [editParameterInput, setEditParameterInput] = useState({ key: "", value: "" })
  const [editRequiredInput, setEditRequiredInput] = useState("")
  const [editResponseInput, setEditResponseInput] = useState({ key: "", value: "" })

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(10)
  const [totalIntents, setTotalIntents] = useState(0)
  const [loadingIntents, setLoadingIntents] = useState(false)

  // Replace the existing stats cards section with:
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

  // Calculate pagination values
  const totalPages = Math.ceil(totalIntents / itemsPerPage)
  const offset = (currentPage - 1) * itemsPerPage

  // Load intents and count on component mount and when pagination changes
  useEffect(() => {
    fetchIntents()
    fetchIntentCount()
  }, [currentPage, itemsPerPage])

  const fetchIntentCount = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/database/get_intent_count`)
      if (response.ok) {
        const data = await response.json()
        // Assuming the response is { "count": number }
        setTotalIntents(data.count || Object.values(data)[0] || 0)
      }
    } catch (error) {
      console.error("Failed to fetch intent count:", error)
    }
  }

  const fetchIntents = async () => {
    setLoadingIntents(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/database/intents/?offset=${offset}&limit=${itemsPerPage}`)
      if (response.ok) {
        const data = await response.json()
        setIntents(data)
      }
    } catch (error) {
      console.error("Failed to fetch intents:", error)
    } finally {
      setLoadingIntents(false)
    }
  }

  const handleGetNavigation = async () => {
    if (!navigationQuery.trim()) return

    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/navigation/get_navigation/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: navigationQuery,
          source: null,
        }),
      })

      if (response.ok) {
        const result = await response.json()
        setNavigationResult(result)
      }
    } catch (error) {
      console.error("Failed to get navigation:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleTestNavigation = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append("file", file)

      const response = await fetch(`${API_BASE_URL}/api/navigation/test_navigation/`, {
        method: "POST",
        body: formData,
      })

      if (response.ok) {
        const results = await response.json()
        setTestResults(results)
      }
    } catch (error) {
      console.error("Failed to test navigation:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteIntent = async (intentId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/database/intents/${intentId}`, {
        method: "DELETE",
      })

      if (response.ok) {
        setIntents(intents.filter((intent) => intent.intent_id !== intentId))
        // Refresh count and potentially adjust current page
        await fetchIntentCount()
        if (intents.length === 1 && currentPage > 1) {
          setCurrentPage(currentPage - 1)
        } else {
          fetchIntents()
        }
      }
    } catch (error) {
      console.error("Failed to delete intent:", error)
    }
  }

  const resetForm = () => {
    setNewIntent({
      intent: "",
      description: "",
      parameters: {},
      required: [],
      responses: {},
      chroma_id: null,
    })
    setParameterInput({ key: "", value: "" })
    setRequiredInput("")
    setResponseInput({ key: "", value: "" })
  }

  const addParameter = () => {
    if (parameterInput.key && parameterInput.value) {
      setNewIntent((prev) => ({
        ...prev,
        parameters: { ...prev.parameters, [parameterInput.key]: parameterInput.value },
      }))
      setParameterInput({ key: "", value: "" })
    }
  }

  const removeParameter = (key: string) => {
    setNewIntent((prev) => {
      const { [key]: removed, ...rest } = prev.parameters
      return { ...prev, parameters: rest }
    })
  }

  const addRequired = () => {
    if (requiredInput && !newIntent.required.includes(requiredInput)) {
      setNewIntent((prev) => ({
        ...prev,
        required: [...prev.required, requiredInput],
      }))
      setRequiredInput("")
    }
  }

  const removeRequired = (item: string) => {
    setNewIntent((prev) => ({
      ...prev,
      required: prev.required.filter((r) => r !== item),
    }))
  }

  const addResponse = () => {
    if (responseInput.key && responseInput.value) {
      setNewIntent((prev) => ({
        ...prev,
        responses: { ...prev.responses, [responseInput.key]: responseInput.value },
      }))
      setResponseInput({ key: "", value: "" })
    }
  }

  const removeResponse = (key: string) => {
    setNewIntent((prev) => {
      const { [key]: removed, ...rest } = prev.responses
      return { ...prev, responses: rest }
    })
  }

  const handleCreateIntent = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/database/intents/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...newIntent,
          chroma_id: null,
        }),
      })

      if (response.ok) {
        const createdIntent = await response.json()
        setShowAddModal(false)
        resetForm()
        // Refresh the data
        await fetchIntentCount()
        fetchIntents()
      }
    } catch (error) {
      console.error("Failed to create intent:", error)
    }
  }

  const openEditModal = (intent: Intent) => {
    setEditingIntent(intent)
    setEditIntent({
      intent: intent.intent,
      description: intent.description,
      parameters: { ...intent.parameters },
      required: [...intent.required],
      responses: { ...intent.responses },
      chroma_id: intent.chroma_id || null,
    })
    setShowEditModal(true)
  }

  const resetEditForm = () => {
    setEditingIntent(null)
    setEditIntent({
      intent: "",
      description: "",
      parameters: {},
      required: [],
      responses: {},
      chroma_id: null,
    })
    setEditParameterInput({ key: "", value: "" })
    setEditRequiredInput("")
    setEditResponseInput({ key: "", value: "" })
  }

  const addEditParameter = () => {
    if (editParameterInput.key && editParameterInput.value) {
      setEditIntent((prev) => ({
        ...prev,
        parameters: { ...prev.parameters, [editParameterInput.key]: editParameterInput.value },
      }))
      setEditParameterInput({ key: "", value: "" })
    }
  }

  const removeEditParameter = (key: string) => {
    setEditIntent((prev) => {
      const { [key]: removed, ...rest } = prev.parameters
      return { ...prev, parameters: rest }
    })
  }

  const addEditRequired = () => {
    if (editRequiredInput && !editIntent.required.includes(editRequiredInput)) {
      setEditIntent((prev) => ({
        ...prev,
        required: [...prev.required, editRequiredInput],
      }))
      setEditRequiredInput("")
    }
  }

  const removeEditRequired = (item: string) => {
    setEditIntent((prev) => ({
      ...prev,
      required: prev.required.filter((r) => r !== item),
    }))
  }

  const addEditResponse = () => {
    if (editResponseInput.key && editResponseInput.value) {
      setEditIntent((prev) => ({
        ...prev,
        responses: { ...prev.responses, [editResponseInput.key]: editResponseInput.value },
      }))
      setEditResponseInput({ key: "", value: "" })
    }
  }

  const removeEditResponse = (key: string) => {
    setEditIntent((prev) => {
      const { [key]: removed, ...rest } = prev.responses
      return { ...prev, responses: rest }
    })
  }

  const handleUpdateIntent = async () => {
    if (!editingIntent) return

    try {
      const response = await fetch(`${API_BASE_URL}/api/database/intents/${editingIntent.intent_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(editIntent),
      })

      if (response.ok) {
        const updatedIntent = await response.json()
        setIntents((prev) =>
          prev.map((intent) => (intent.intent_id === editingIntent.intent_id ? updatedIntent : intent)),
        )
        setShowEditModal(false)
        resetEditForm()
      }
    } catch (error) {
      console.error("Failed to update intent:", error)
    }
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handleItemsPerPageChange = (value: string) => {
    setItemsPerPage(Number(value))
    setCurrentPage(1) // Reset to first page when changing items per page
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Intent Management</h1>
          <Button variant="outline" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
            <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Toggle theme</span>
          </Button>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 space-y-8">
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
      </div>
    </div>
  )
}
