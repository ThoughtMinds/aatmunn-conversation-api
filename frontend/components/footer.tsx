export function Footer() {
  return (
    <footer className="sticky bottom-0 z-50 w-full border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-12 items-center justify-between px-6">
        <p className="text-sm text-muted-foreground">© 2025 Aatmunn PoC. All rights reserved.</p>
        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
          <span>v1.0.0</span>
          <span>•</span>
          <span>Status: Online</span>
        </div>
      </div>
    </footer>
  )
}
