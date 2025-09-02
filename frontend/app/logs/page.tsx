"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  FileText,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Loader2,
  Map,
  Terminal,
  ChevronDown,
} from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface RequestData {
  input: string
  output: string
}

interface AuditLogEntry {
  id: number
  timestamp: string
  intent_type: "navigation" | "summarization" | "task-execution"
  data: RequestData
  status: "success" | "error"
}

export default function LogsPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([])
  const [latestLog, setLatestLog] = useState<AuditLogEntry | null>(null)
  const [loading, setLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(10)
  const [filterType, setFilterType] = useState<string>("all")
  const [totalLogs, setTotalLogs] = useState(0)
  const [expandedLogs, setExpandedLogs] = useState<number[]>([])

  const totalPages = Math.ceil(totalLogs / itemsPerPage)

  useEffect(() => {
    fetchAuditLogs()
  }, [currentPage, itemsPerPage, filterType])

  const fetchAuditLogs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        offset: ((currentPage - 1) * itemsPerPage).toString(),
        limit: itemsPerPage.toString(),
        intentType: filterType,
      })
      const response = await fetch(`${API_BASE_URL}/api/logging/get_audit_log/?${params}`)
      const countResponse = await fetch(
        `${API_BASE_URL}/api/logging/get_audit_log_count/?intentType=${filterType}`
      )

      if (response.ok && countResponse.ok) {
        const data: AuditLogEntry[] = await response.json()
        const countData = await countResponse.json()
        setLogs(data)
        setTotalLogs(countData.total)
        if (currentPage === 1 && data.length > 0 && !latestLog) {
          setLatestLog(data[0])
        }
      }
    } catch (error) {
      console.error("Failed to fetch audit log:", error)
    } finally {
      setLoading(false)
    }
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handleItemsPerPageChange = (value: string) => {
    setItemsPerPage(Number(value))
    setCurrentPage(1)
  }

  const handleFilterChange = (value: string) => {
    setFilterType(value)
    setCurrentPage(1)
  }

  const toggleLogExpansion = (id: number) => {
    setExpandedLogs((prev) => (prev.includes(id) ? prev.filter((logId) => logId !== id) : [...prev, id]))
  }

  const getIntentIcon = (type: string) => {
    switch (type) {
      case "navigation":
        return <Map className="h-5 w-5 text-blue-500" />
      case "summarization":
        return <FileText className="h-5 w-5 text-purple-500" />
      case "task_execution":
        return <Terminal className="h-5 w-5 text-orange-500" />
      default:
        return <FileText className="h-5 w-5 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "success":
        return "bg-green-500"
      case "error":
        return "bg-red-500"
      default:
        return "bg-gray-500"
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case "navigation":
        return "text-blue-500 border-blue-500"
      case "summarization":
        return "text-purple-500 border-purple-500"
      case "task_execution":
        return "text-orange-500 border-orange-500"
      default:
        return "text-gray-500 border-gray-500"
    }
  }

  const formatJsonOutput = (output: string) => {
    try {
      const parsed = JSON.parse(output)
      return JSON.stringify(parsed, null, 2)
    } catch (error) {
      return output
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <FileText className="h-8 w-8 text-gray-500" />
          Logs
        </h1>
        <p className="text-muted-foreground">System activity logs and history</p>
      </div>

      {latestLog && currentPage === 1 && (
        <Card className="mb-6 bg-muted/25">
          <CardHeader>
            <CardTitle>Latest Audit Entry</CardTitle>
            <CardDescription>Most recent system activity</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant={latestLog.status === "success" ? "default" : "destructive"}>
                  {latestLog.intent_type.replace("_", " ")}
                </Badge>
                <Badge variant="outline">{latestLog.status}</Badge>
              </div>
              <div className="text-sm font-mono bg-white p-2 rounded">
                <strong>Input:</strong> {latestLog.data.input}
              </div>
              <div className="text-sm font-mono bg-white p-2 rounded">
                <strong>Output:</strong>
                <pre className="whitespace-pre-wrap break-all">{formatJsonOutput(latestLog.data.output)}</pre>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              Activity History
              <Badge variant="outline" className="ml-2">
                {totalLogs} total
              </Badge>
            </span>
          </CardTitle>
          <CardDescription>Complete history of system activities and events</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Controls */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Label htmlFor="filter-type" className="text-sm">
                  Filter:
                </Label>
                <Select value={filterType} onValueChange={handleFilterChange}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="navigation">Navigation</SelectItem>
                    <SelectItem value="summarization">Summarization</SelectItem>
                    <SelectItem value="task_execution">Task Execution</SelectItem>
                  </SelectContent>
                </Select>
              </div>

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
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(1)}
                disabled={currentPage === 1 || loading}
              >
                <ChevronsLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1 || loading}
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
                disabled={currentPage === totalPages || loading}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(totalPages)}
                disabled={currentPage === totalPages || loading}
              >
                <ChevronsRight className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Logs List */}
          <div className="space-y-2">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                Loading logs...
              </div>
            ) : logs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">No logs found for the selected filter.</div>
            ) : (
              logs.map((log) => (
                <Card key={log.id} className="overflow-hidden">
                  <div
                    className="flex items-center space-x-4 p-4 cursor-pointer hover:bg-muted/50"
                    onClick={() => toggleLogExpansion(log.id)}
                  >
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(log.status)} flex-shrink-0`}></div>
                    {getIntentIcon(log.intent_type)}
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium capitalize">
                          {log.intent_type.replace("_", " ")} processed
                        </p>
                        <Badge variant="outline" className={`text-xs ${getTypeColor(log.intent_type)}`}>
                          {log.intent_type}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Input: {log.data.input.substring(0, 80)}... • {new Date(log.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <Badge
                      variant={log.status === "success" ? "default" : "secondary"}
                      className={log.status === "success" ? "bg-green-500" : "bg-red-500"}
                    >
                      {log.status}
                    </Badge>
                    <ChevronDown
                      className={`h-5 w-5 text-muted-foreground transform transition-transform ${
                        expandedLogs.includes(log.id) ? "rotate-180" : ""
                      }`}
                    />
                  </div>
                  {expandedLogs.includes(log.id) && (
                    <div className="p-4 border-t bg-muted/25">
                      <div className="space-y-2">
                        <div className="text-sm font-mono bg-white p-2 rounded">
                          <strong>Input:</strong>
                          <p className="whitespace-pre-wrap break-all">{log.data.input}</p>
                        </div>
                        <div className="text-sm font-mono bg-white p-2 rounded">
                          <strong>Output:</strong>
                          <pre className="whitespace-pre-wrap break-all">{formatJsonOutput(log.data.output)}</pre>
                        </div>
                      </div>
                    </div>
                  )}
                </Card>
              ))
            )}
          </div>

          {/* Pagination Controls - Bottom */}
          {totalLogs > 0 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <div className="text-sm text-muted-foreground">
                Showing {Math.min((currentPage - 1) * itemsPerPage + 1, totalLogs)} to{" "}
                {Math.min(currentPage * itemsPerPage, totalLogs)} of {totalLogs} logs
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(1)}
                  disabled={currentPage === 1 || loading}
                >
                  <ChevronsLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1 || loading}
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
                  disabled={currentPage === totalPages || loading}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(totalPages)}
                  disabled={currentPage === totalPages || loading}
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
