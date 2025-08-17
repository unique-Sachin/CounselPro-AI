"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { 
  LayoutDashboard, 
  Users, 
  MessageSquare,
  Settings,
  PlayCircle,
  FolderOpen
} from "lucide-react";

const sidebarItems = [
  {
    title: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    title: "Counselors",
    href: "/counselors",
    icon: Users,
  },
  {
    title: "Sessions",
    href: "/sessions",
    icon: MessageSquare,
  },
  {
    title: "Catalogs",
    href: "/catalogs",
    icon: FolderOpen,
  },
  {
    title: "Demo",
    href: "/counselors-demo",
    icon: PlayCircle,
  },
];

interface AppSidebarProps {
  className?: string;
  onItemClick?: () => void;
}

export function AppSidebar({ className, onItemClick }: AppSidebarProps) {
  const pathname = usePathname();

  return (
    <div className={cn("flex h-full w-64 flex-col bg-muted/20 border-r", className)}>
      {/* Logo/Brand */}
      <div className="flex h-16 items-center px-6 border-b">
        <h1 className="text-xl font-bold text-primary">CounselPro AI</h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {sidebarItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || 
            (item.href !== "/" && pathname.startsWith(item.href));
          
          return (
            <Button
              key={item.href}
              asChild
              variant={isActive ? "secondary" : "ghost"}
              className={cn(
                "w-full justify-start h-12",
                isActive && "bg-secondary font-medium"
              )}
              onClick={onItemClick}
            >
              <Link href={item.href}>
                <Icon className="mr-3 h-5 w-5" />
                {item.title}
              </Link>
            </Button>
          );
        })}
      </nav>

      <Separator />
      
      {/* Footer */}
      <div className="p-4">
        <Button
          variant="ghost"
          className="w-full justify-start h-12"
          onClick={onItemClick}
        >
          <Settings className="mr-3 h-5 w-5" />
          Settings
        </Button>
      </div>
    </div>
  );
}
