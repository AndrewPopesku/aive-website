"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

export function Navbar() {
  const pathname = usePathname()
  
  return (
    <nav className="border-b bg-background">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="hidden md:flex space-x-4">
              <NavLink href="/" active={pathname === "/"}>
                Create New
              </NavLink>
              <NavLink href="/projects" active={pathname === "/projects"}>
                My Projects
              </NavLink>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

function NavLink({ href, active, children }: { href: string; active: boolean; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className={cn(
        "text-sm font-medium transition-colors hover:text-primary",
        active ? "text-primary" : "text-muted-foreground"
      )}
    >
      {children}
    </Link>
  )
} 