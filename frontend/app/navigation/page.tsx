"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { Separator } from "@/components/ui/separator"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Navigation,
  Search,
  Upload,
  Plus,
  Edit,
  Trash2,
  X,
  Loader2,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Check,
} from "lucide-react"

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

export default function NavigationPage() {
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [navigationResult, setNavigationResult] = useState<NavigationResult | null>(null)
  const [testResults, setTestResults] = useState<NavigationTestResult[]>([])
  const { toast } = useToast()

  // Intent management state
  const [intents, setIntents] = useState<Intent[]>([])
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
      const response = await fetch(`${API_BASE_URL}/api/navigation_intents/get_intent_count`)
      if (response.ok) {
        const data = await response.json()
        setTotalIntents(data.total_intents || 0)
      }
    } catch (error) {
      console.error("Failed to fetch intent count:", error)
    }
  }

  const fetchIntents = async () => {
    setLoadingIntents(true)
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/navigation_intents/intents/?offset=${offset}&limit=${itemsPerPage}`,
      )
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

  const handleQuerySubmit = async () => {
    if (!query.trim()) return

    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/navigation/get_navigation/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
          source: null,
        }),
      })

      if (response.ok) {
        const result = await response.json()
        setNavigationResult(result)
        toast({
          title: "Navigation Query Processed",
          description: `Successfully processed: "${query}"`,
          className: "bg-green-50 border-green-200 text-green-800",
        })
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
      const response = await fetch(`${API_BASE_URL}/api/navigation_intents/intents/${intentId}`, {
        method: "DELETE",
      })

      if (response.ok) {
        setIntents(intents.filter((intent) => intent.intent_id !== intentId))
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
      const response = await fetch(`${API_BASE_URL}/api/navigation_intents/intents/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          intent: newIntent.intent,
          description: newIntent.description,
          parameters: newIntent.parameters,
          required: newIntent.required,
          responses: newIntent.responses,
          chroma_id: newIntent.chroma_id,
        }),
      })

      if (response.ok) {
        const createdIntent = await response.json()
        setShowAddModal(false)
        resetForm()
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
      const response = await fetch(`${API_BASE_URL}/api/navigation_intents/intents/${editingIntent.intent_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          intent: editIntent.intent,
          description: editIntent.description,
          parameters: editIntent.parameters,
          required: editIntent.required,
          responses: editIntent.responses,
          chroma_id: editIntent.chroma_id,
        }),
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
    setCurrentPage(1)
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Navigation className="h-8 w-8 text-blue-500" />
          Navigation
        </h1>
        <p className="text-muted-foreground">Intelligent query routing and intent recognition system</p>
      </div>

      {/* Query Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Query Navigation
          </CardTitle>
          <CardDescription>Enter your query to get intelligent navigation suggestions</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="query">Navigation Query</Label>
            <div className="flex gap-2">
              <Input
                id="query"
                placeholder="Enter your navigation query..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleQuerySubmit()}
              />
              <Button onClick={handleQuerySubmit} disabled={loading}>
                {loading ? "Processing..." : "Submit"}
              </Button>
            </div>
          </div>

          {navigationResult && (
            <Card>
              <CardContent className="pt-4">
                <div className="space-y-2">
                  <div>
                    <strong>ID:</strong> {navigationResult.id}
                  </div>
                  <div>
                    <strong>Intent Name:</strong> {navigationResult.intent_name}
                  </div>
                  <div>
                    <strong>Reasoning:</strong> {navigationResult.reasoning}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>

      <Separator />

      {/* Test Navigation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Test Navigation
          </CardTitle>
          <CardDescription>Upload Excel files for batch navigation testing</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Input type="file" accept=".xlsx,.xls" onChange={handleTestNavigation} disabled={loading} />
              <Upload className="h-4 w-4 text-muted-foreground" />
            </div>

            {testResults.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-medium">Test Results</h4>
                <div className="border rounded-lg overflow-hidden">
                  <div className="overflow-x-auto max-h-96">
                    <table className="w-full text-sm">
                      <thead className="bg-muted/50 border-b">
                        <tr>
                          <th className="text-left p-3 font-medium">User Query</th>
                          <th className="text-left p-3 font-medium">Actual Intent</th>
                          <th className="text-left p-3 font-medium">Predicted Intent</th>
                          <th className="text-left p-3 font-medium">Response Time (ms)</th>
                          <th className="text-center p-3 font-medium">Match</th>
                        </tr>
                      </thead>
                      <tbody>
                        {testResults.map((result, index) => (
                          <tr key={index} className="border-b hover:bg-muted/25">
                            <td className="p-3 font-medium">{result.query}</td>
                            <td className="p-3 text-muted-foreground">{result.actual_intent}</td>
                            <td className="p-3 text-muted-foreground">{result.predicted_intent}</td>
                            <td className="p-3 text-muted-foreground">{result.response_time}</td>
                            <td className="p-3 text-center">
                              {result.actual_intent === result.predicted_intent ? (
                                <Check className="h-4 w-4 text-green-500 mx-auto" />
                              ) : (
                                <X className="h-4 w-4 text-red-500 mx-auto" />
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Manage Intents */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              Manage Intents
              <Badge variant="outline" className="ml-2">
                {totalIntents} total
              </Badge>
            </span>
            <Dialog open={showAddModal} onOpenChange={setShowAddModal}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Intent
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Add New Intent</DialogTitle>
                  <DialogDescription>
                    Create a new intent with parameters, required fields, and responses.
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-6">
                  {/* Basic Info */}
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="intent-name">Intent Name *</Label>
                      <Input
                        id="intent-name"
                        value={newIntent.intent}
                        onChange={(e) => setNewIntent((prev) => ({ ...prev, intent: e.target.value }))}
                        placeholder="e.g., navigate_to_dashboard"
                      />
                    </div>

                    <div>
                      <Label htmlFor="intent-description">Description *</Label>
                      <Textarea
                        id="intent-description"
                        value={newIntent.description}
                        onChange={(e) => setNewIntent((prev) => ({ ...prev, description: e.target.value }))}
                        placeholder="Describe what this intent does..."
                      />
                    </div>
                  </div>

                  {/* Parameters */}
                  <div className="space-y-3">
                    <Label>Parameters</Label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Parameter name"
                        value={parameterInput.key}
                        onChange={(e) => setParameterInput((prev) => ({ ...prev, key: e.target.value }))}
                      />
                      <Input
                        placeholder="Parameter value"
                        value={parameterInput.value}
                        onChange={(e) => setParameterInput((prev) => ({ ...prev, value: e.target.value }))}
                      />
                      <Button type="button" onClick={addParameter} size="sm">
                        Add
                      </Button>
                    </div>
                    {Object.entries(newIntent.parameters).length > 0 && (
                      <div className="space-y-1">
                        {Object.entries(newIntent.parameters).map(([key, value]) => (
                          <div key={key} className="flex items-center justify-between bg-muted p-2 rounded">
                            <span className="text-sm">
                              {key}: {value}
                            </span>
                            <Button variant="ghost" size="sm" onClick={() => removeParameter(key)}>
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Required Fields */}
                  <div className="space-y-3">
                    <Label>Required Fields</Label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Required field name"
                        value={requiredInput}
                        onChange={(e) => setRequiredInput(e.target.value)}
                      />
                      <Button type="button" onClick={addRequired} size="sm">
                        Add
                      </Button>
                    </div>
                    {newIntent.required.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {newIntent.required.map((item) => (
                          <Badge key={item} variant="secondary" className="flex items-center gap-1">
                            {item}
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-auto p-0 ml-1"
                              onClick={() => removeRequired(item)}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Responses */}
                  <div className="space-y-3">
                    <Label>Responses</Label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Response key"
                        value={responseInput.key}
                        onChange={(e) => setResponseInput((prev) => ({ ...prev, key: e.target.value }))}
                      />
                      <Input
                        placeholder="Response value"
                        value={responseInput.value}
                        onChange={(e) => setResponseInput((prev) => ({ ...prev, value: e.target.value }))}
                      />
                      <Button type="button" onClick={addResponse} size="sm">
                        Add
                      </Button>
                    </div>
                    {Object.entries(newIntent.responses).length > 0 && (
                      <div className="space-y-1">
                        {Object.entries(newIntent.responses).map(([key, value]) => (
                          <div key={key} className="flex items-center justify-between bg-muted p-2 rounded">
                            <span className="text-sm">
                              {key}: {value}
                            </span>
                            <Button variant="ghost" size="sm" onClick={() => removeResponse(key)}>
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowAddModal(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateIntent} disabled={!newIntent.intent || !newIntent.description}>
                    Create Intent
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
            {/* Edit Intent Modal */}
            <Dialog
              open={showEditModal}
              onOpenChange={(open) => {
                setShowEditModal(open)
                if (!open) resetEditForm()
              }}
            >
              <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Edit Intent</DialogTitle>
                  <DialogDescription>
                    Update the intent with new parameters, required fields, and responses.
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-6">
                  {/* Basic Info */}
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="edit-intent-name">Intent Name *</Label>
                      <Input
                        id="edit-intent-name"
                        value={editIntent.intent}
                        onChange={(e) => setEditIntent((prev) => ({ ...prev, intent: e.target.value }))}
                        placeholder="e.g., navigate_to_dashboard"
                      />
                    </div>

                    <div>
                      <Label htmlFor="edit-intent-description">Description *</Label>
                      <Textarea
                        id="edit-intent-description"
                        value={editIntent.description}
                        onChange={(e) => setEditIntent((prev) => ({ ...prev, description: e.target.value }))}
                        placeholder="Describe what this intent does..."
                      />
                    </div>

                    <div>
                      <Label htmlFor="edit-chroma-id">Chroma ID (Optional)</Label>
                      <Input
                        id="edit-chroma-id"
                        value={editIntent.chroma_id || ""}
                        onChange={(e) => setEditIntent((prev) => ({ ...prev, chroma_id: e.target.value || null }))}
                        placeholder="Optional chroma identifier"
                      />
                    </div>
                  </div>

                  {/* Parameters */}
                  <div className="space-y-3">
                    <Label>Parameters</Label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Parameter name"
                        value={editParameterInput.key}
                        onChange={(e) => setEditParameterInput((prev) => ({ ...prev, key: e.target.value }))}
                      />
                      <Input
                        placeholder="Parameter value"
                        value={editParameterInput.value}
                        onChange={(e) => setEditParameterInput((prev) => ({ ...prev, value: e.target.value }))}
                      />
                      <Button type="button" onClick={addEditParameter} size="sm">
                        Add
                      </Button>
                    </div>
                    {Object.entries(editIntent.parameters).length > 0 && (
                      <div className="space-y-1">
                        {Object.entries(editIntent.parameters).map(([key, value]) => (
                          <div key={key} className="flex items-center justify-between bg-muted p-2 rounded">
                            <span className="text-sm">
                              {key}: {value}
                            </span>
                            <Button variant="ghost" size="sm" onClick={() => removeEditParameter(key)}>
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Required Fields */}
                  <div className="space-y-3">
                    <Label>Required Fields</Label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Required field name"
                        value={editRequiredInput}
                        onChange={(e) => setEditRequiredInput(e.target.value)}
                      />
                      <Button type="button" onClick={addEditRequired} size="sm">
                        Add
                      </Button>
                    </div>
                    {editIntent.required.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {editIntent.required.map((item) => (
                          <Badge key={item} variant="secondary" className="flex items-center gap-1">
                            {item}
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-auto p-0 ml-1"
                              onClick={() => removeEditRequired(item)}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Responses */}
                  <div className="space-y-3">
                    <Label>Responses</Label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Response key"
                        value={editResponseInput.key}
                        onChange={(e) => setEditResponseInput((prev) => ({ ...prev, key: e.target.value }))}
                      />
                      <Input
                        placeholder="Response value"
                        value={editResponseInput.value}
                        onChange={(e) => setEditResponseInput((prev) => ({ ...prev, value: e.target.value }))}
                      />
                      <Button type="button" onClick={addEditResponse} size="sm">
                        Add
                      </Button>
                    </div>
                    {Object.entries(editIntent.responses).length > 0 && (
                      <div className="space-y-1">
                        {Object.entries(editIntent.responses).map(([key, value]) => (
                          <div key={key} className="flex items-center justify-between bg-muted p-2 rounded">
                            <span className="text-sm">
                              {key}: {value}
                            </span>
                            <Button variant="ghost" size="sm" onClick={() => removeEditResponse(key)}>
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowEditModal(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleUpdateIntent} disabled={!editIntent.intent || !editIntent.description}>
                    Update Intent
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </CardTitle>
          <CardDescription>Manage intents with their parameters and responses</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Pagination Controls - Top */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Label htmlFor="items-per-page" className="text-sm">
                Items per page:
              </Label>
              <Select value={itemsPerPage.toString()} onValueChange={handleItemsPerPageChange}>
                <SelectTrigger className="w-20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">5</SelectItem>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(1)}
                disabled={currentPage === 1 || loadingIntents}
              >
                <ChevronsLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1 || loadingIntents}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-muted-foreground px-2">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages || loadingIntents}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(totalPages)}
                disabled={currentPage === totalPages || loadingIntents}
              >
                <ChevronsRight className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Intents List */}
          <div className="space-y-4">
            {loadingIntents ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                Loading intents...
              </div>
            ) : intents.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No intents found. Add your first intent to get started.
              </div>
            ) : (
              intents.map((intent) => (
                <Card key={intent.intent_id}>
                  <CardContent className="pt-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium">{intent.intent}</h4>
                          <Badge variant="secondary">ID: {intent.intent_id}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{intent.description}</p>

                        {intent.required.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            <span className="text-xs font-medium">Required:</span>
                            {intent.required.map((param) => (
                              <Badge key={param} variant="outline" className="text-xs">
                                {param}
                              </Badge>
                            ))}
                          </div>
                        )}

                        {Object.keys(intent.parameters).length > 0 && (
                          <div className="text-xs text-muted-foreground">
                            Parameters: {Object.keys(intent.parameters).join(", ")}
                          </div>
                        )}
                      </div>

                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => openEditModal(intent)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleDeleteIntent(intent.intent_id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>

          {/* Pagination Controls - Bottom */}
          {totalIntents > 0 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <div className="text-sm text-muted-foreground">
                Showing {offset + 1} to {Math.min(offset + itemsPerPage, totalIntents)} of {totalIntents} intents
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(1)}
                  disabled={currentPage === 1 || loadingIntents}
                >
                  <ChevronsLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1 || loadingIntents}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-muted-foreground px-2">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages || loadingIntents}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(totalPages)}
                  disabled={currentPage === totalPages || loadingIntents}
                >
                  <ChevronsRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
