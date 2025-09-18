"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Bug, LayoutDashboard, Navigation, FileText, Zap, History, Target } from "lucide-react"

const navigation = [
  {
    name: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    name: "Chat Playground",
    href: "/intent-identification",
    icon: Target,
  },
  {
    name: "Navigation",
    href: "/navigation",
    icon: Navigation,
  },
  {
    name: "Summarization",
    href: "/summarization",
    icon: FileText,
  },
  {
    name: "Task Execution",
    href: "/task-execution",
    icon: Zap,
  },
  {
    name: "Testing",
    href: "/testing-module",
    icon: Bug,
  },
  {
    name: "Logs",
    href: "/logs",
    icon: History,
  },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="hidden md:flex md:w-64 md:flex-col">
      <div className="flex flex-col flex-grow pt-5 bg-background border-r overflow-y-auto">
        <div className="flex flex-col flex-grow">
          <ScrollArea className="flex-1 px-4">
            <nav className="space-y-2">
              {navigation.map((item) => {
                const isActive = pathname === item.href
                return (
                  <Link key={item.name} href={item.href}>
                    <Button
                      variant={isActive ? "secondary" : "ghost"}
                      className={cn("w-full justify-start", isActive && "bg-secondary")}
                    >
                      <item.icon className="mr-3 h-4 w-4" />
                      {item.name}
                    </Button>
                  </Link>
                )
              })}
            </nav>
          </ScrollArea>
        </div>
      </div>
    </div>
  )
}
