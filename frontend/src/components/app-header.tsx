"use client";

import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Menu, Search } from "lucide-react";
import { AppSidebar } from "./app-sidebar";
import { ThemeToggle } from "./theme-toggle";
import { useState } from "react";
import { Input } from "@/components/ui/input";

interface AppHeaderProps {
  title?: string;
  showSearch?: boolean;
}

export function AppHeader({ title = "Dashboard", showSearch = true }: AppHeaderProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center px-4">
        {/* Mobile sidebar trigger */}
        <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
          <SheetTrigger asChild className="md:hidden">
            <Button variant="ghost" size="icon" className="mr-4">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle sidebar</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="p-0 w-64">
            <AppSidebar onItemClick={() => setSidebarOpen(false)} />
          </SheetContent>
        </Sheet>

        {/* Title */}
        <h1 className="text-lg font-semibold">{title}</h1>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Search */}
        {showSearch && (
          <div className="relative mr-4 hidden sm:block">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search..."
              className="w-64 pl-9"
            />
          </div>
        )}

        {/* User menu */}
        <div className="flex items-center space-x-4">
          <ThemeToggle />
          <Avatar>
            <AvatarImage src="/avatars/user.png" alt="User" />
            <AvatarFallback>U</AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  );
}
