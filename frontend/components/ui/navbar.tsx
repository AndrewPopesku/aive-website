"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { useAuth } from "@/hooks/useAuth"
import { Button } from "@/components/ui/button"
import { LogOut, User } from "lucide-react"

export function Navbar() {
  const pathname = usePathname()
  const { isAuthenticated, user, logout, loading } = useAuth()
  
  return (
    <nav className="border-b bg-background">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-2 sm:space-x-4">
            <Link href="/" className="font-bold text-lg text-primary">
              AIVE
            </Link>
            <div className="flex space-x-2 sm:space-x-4">
              <NavLink href="/" active={pathname === "/"}>
                Create New
              </NavLink>
              {isAuthenticated && (
                <NavLink href="/projects" active={pathname === "/projects"}>
                  My Projects
                </NavLink>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {loading ? (
              <div className="text-xs sm:text-sm text-muted-foreground">Loading...</div>
            ) : isAuthenticated && user ? (
              <>
                <div className="hidden sm:flex items-center space-x-2 text-sm text-muted-foreground">
                  <User size={16} />
                  <span className="max-w-[100px] truncate">{user.username}</span>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={logout}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <LogOut size={16} className="sm:mr-2" />
                  <span className="hidden sm:inline">Logout</span>
                </Button>
              </>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost" size="sm">
                    Login
                  </Button>
                </Link>
                <Link href="/register">
                  <Button size="sm">
                    Register
                  </Button>
                </Link>
              </>
            )}
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