"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FileText, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Loader2 } from "lucide-react"

interface LogEntry {
  id: number
  type: "navigation" | "summarization" | "task"
  action: string
  details: string
  timestamp: string
  status: "success" | "error" | "warning" | "info"
}

// Add interfaces for API response
interface RequestData {
  input: string
  output: string
}

interface AuditLogEntry {
  intent_type: "navigation" | "summarization" | "task-execution"
  data: RequestData
  status: "success" | "error"
}

// Mock data for logs
const mockLogs: LogEntry[] = [
  {
    id: 1,
    type: "navigation",
    action: "Navigation query processed",
    details: "Intent: navigate_to_dashboard",
    timestamp: "2 minutes ago",
    status: "success",
  },
  {
    id: 2,
    type: "summarization",
    action: "Document summarization completed",
    details: "File: quarterly_report.pdf",
    timestamp: "5 minutes ago",
    status: "success",
  },
  {
    id: 3,
    type: "task",
    action: "Task execution started",
    details: "Task: data_processing_batch_001",
    timestamp: "8 minutes ago",
    status: "info",
  },
  {
    id: 4,
    type: "navigation",
    action: "New intent created",
    details: "Intent: navigate_to_reports",
    timestamp: "12 minutes ago",
    status: "success",
  },
  {
    id: 5,
    type: "task",
    action: "Task execution completed",
    details: "Task: email_notification_batch",
    timestamp: "15 minutes ago",
    status: "success",
  },
  {
    id: 6,
    type: "summarization",
    action: "Summarization failed",
    details: "Error: File format not supported",
    timestamp: "18 minutes ago",
    status: "error",
  },
  {
    id: 7,
    type: "navigation",
    action: "Intent updated",
    details: "Intent: navigate_to_settings",
    timestamp: "22 minutes ago",
    status: "info",
  },
  {
    id: 8,
    type: "task",
    action: "Task execution queued",
    details: "Task: report_generation_weekly",
    timestamp: "25 minutes ago",
    status: "warning",
  },
  {
    id: 9,
    type: "summarization",
    action: "Query summarization completed",
    details: 'Query: "Analyze market trends"',
    timestamp: "28 minutes ago",
    status: "success",
  },
  {
    id: 10,
    type: "navigation",
    action: "Navigation test completed",
    details: "Batch test: 95% accuracy",
    timestamp: "30 minutes ago",
    status: "success",
  },
  {
    id: 11,
    type: "task",
    action: "Task execution failed",
    details: "Task: backup_database - Connection timeout",
    timestamp: "35 minutes ago",
    status: "error",
  },
  {
    id: 12,
    type: "summarization",
    action: "Document processed",
    details: "File: user_manual.docx",
    timestamp: "40 minutes ago",
    status: "success",
  },
  {
    id: 13,
    type: "navigation",
    action: "Intent deleted",
    details: "Intent: deprecated_function",
    timestamp: "45 minutes ago",
    status: "warning",
  },
  {
    id: 14,
    type: "task",
    action: "Scheduled task created",
    details: "Task: daily_cleanup",
    timestamp: "50 minutes ago",
    status: "info",
  },
  {
    id: 15,
    type: "summarization",
    action: "Batch summarization started",
    details: "Processing 5 documents",
    timestamp: "55 minutes ago",
    status: "info",
  },
]

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(10)
  const [filterType, setFilterType] = useState<string>("all")
  const [auditLog, setAuditLog] = useState<AuditLogEntry | null>(null)

  // Calculate pagination values
  const filteredLogs = filterType === "all" ? mockLogs : mockLogs.filter((log) => log.type === filterType)

  const totalLogs = filteredLogs.length
  const totalPages = Math.ceil(totalLogs / itemsPerPage)
  const offset = (currentPage - 1) * itemsPerPage
  const paginatedLogs = filteredLogs.slice(offset, offset + itemsPerPage)

  // Add useEffect to fetch audit log
  useEffect(() => {
    fetchAuditLog()
  }, [])

  const fetchAuditLog = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/logging/get_audit_log/`)
      if (response.ok) {
        const data: AuditLogEntry = await response.json()
        setAuditLog(data)

        // Convert audit log to display format (you can expand this logic)
        const mockLogs: LogEntry[] = [
          {
            id: 1,
            type: data.intent_type === "task-execution" ? "task" : data.intent_type,
            action: `${data.intent_type} processed`,
            details: `Input: ${data.data.input.substring(0, 50)}...`,
            timestamp: "Just now",
            status: data.status === "success" ? "success" : "error",
          },
        ]
        setLogs(mockLogs)
      }
    } catch (error) {
      console.error("Failed to fetch audit log:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setLoading(true)
    // Simulate API call
    setTimeout(() => {
      setLogs(paginatedLogs)
      setLoading(false)
    }, 500)
  }, [currentPage, itemsPerPage, filterType])

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "success":
        return "bg-green-500"
      case "error":
        return "bg-red-500"
      case "warning":
        return "bg-yellow-500"
      case "info":
        return "bg-blue-500"
      default:
        return "bg-gray-500"
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case "navigation":
        return "text-blue-500"
      case "summarization":
        return "text-purple-500"
      case "task":
        return "text-orange-500"
      default:
        return "text-gray-500"
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

      {auditLog && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Latest Audit Entry</CardTitle>
            <CardDescription>Most recent system activity</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant={auditLog.status === "success" ? "default" : "destructive"}>
                  {auditLog.intent_type}
                </Badge>
                <Badge variant="outline">{auditLog.status}</Badge>
              </div>
              <div className="text-sm">
                <strong>Input:</strong> {auditLog.data.input}
              </div>
              <div className="text-sm">
                <strong>Output:</strong> {auditLog.data.output.substring(0, 200)}...
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
                    <SelectItem value="task">Task Execution</SelectItem>
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
          <div className="space-y-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                Loading logs...
              </div>
            ) : logs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">No logs found for the selected filter.</div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="flex items-center space-x-4 p-4 border rounded-lg hover:bg-muted/25">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(log.status)}`}></div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium">{log.action}</p>
                      <Badge variant="outline" className={`text-xs ${getTypeColor(log.type)}`}>
                        {log.type}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {log.details} • {log.timestamp}
                    </p>
                  </div>
                  <Badge
                    variant={log.status === "success" ? "default" : "secondary"}
                    className={
                      log.status === "success"
                        ? "bg-green-500"
                        : log.status === "error"
                          ? "bg-red-500"
                          : log.status === "warning"
                            ? "bg-yellow-500"
                            : "bg-blue-500"
                    }
                  >
                    {log.status}
                  </Badge>
                </div>
              ))
            )}
          </div>

          {/* Pagination Controls - Bottom */}
          {totalLogs > 0 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <div className="text-sm text-muted-foreground">
                Showing {offset + 1} to {Math.min(offset + itemsPerPage, totalLogs)} of {totalLogs} logs
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
