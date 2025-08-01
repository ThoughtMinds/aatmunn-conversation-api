"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { FileText, Zap, CheckCircle, Copy } from "lucide-react"
import { API_BASE_URL } from "@/constants/api"

interface SummarizationResult {
  query: string
  summary: string
}

interface SummaryResponse {
  summary: string
  content_moderated: boolean
}

export default function SummarizationPage() {
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SummarizationResult | null>(null)
  const { toast } = useToast()

  const handleSummarize = async () => {
    if (!query.trim()) return

    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/summarization/get_summary/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
        }),
      })

      if (response.ok) {
        const data: SummaryResponse = await response.json()
        const mockResult: SummarizationResult = {
          query: query,
          summary: data.summary,
        }

        setResult(mockResult)
        toast({
          title: "Summarization Complete",
          description: data.content_moderated
            ? "Query has been summarized (content was moderated)"
            : "Query has been successfully summarized",
          className: data.content_moderated
            ? "bg-yellow-50 border-yellow-200 text-yellow-800"
            : "bg-purple-50 border-purple-200 text-purple-800",
        })
      }
    } catch (error) {
      console.error("Failed to get summary:", error)
      toast({
        title: "Summarization Failed",
        description: "Failed to process the summarization request",
        className: "bg-red-50 border-red-200 text-red-800",
      })
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast({
      title: "Copied to clipboard",
      description: "Summary has been copied to your clipboard",
    })
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <FileText className="h-8 w-8 text-purple-500" />
          Summarization
        </h1>
        <p className="text-muted-foreground">Document analysis and intelligent content summarization</p>
      </div>

      {/* Query Summarization */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Query Summarization
          </CardTitle>
          <CardDescription>Enter your query for intelligent summarization</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="query">Query</Label>
            <Input
              id="query"
              placeholder="Enter your query for summarization..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <Button onClick={handleSummarize} disabled={loading || !query.trim()}>
            {loading ? "Summarizing..." : "Summarize"}
          </Button>
        </CardContent>
      </Card>

      {/* Summarization Result */}
      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                Summarization Result
              </span>
              <Button variant="outline" size="sm" onClick={() => copyToClipboard(result.summary)}>
                <Copy className="h-4 w-4 mr-2" />
                Copy
              </Button>
            </CardTitle>
            <CardDescription>Generated summary for: "{result.query}"</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Summary Text */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Summary</Label>
              <div className="p-4 bg-muted/50 rounded-lg border">
                <p className="text-sm leading-relaxed">{result.summary}</p>
              </div>
            </div>

            {/* Metadata */}
            <div className="flex items-center gap-4 pt-2 border-t">
              <Badge variant="outline">Processing Time: 2.3s</Badge>
              <Badge variant="outline">Generated: {new Date().toLocaleString()}</Badge>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
