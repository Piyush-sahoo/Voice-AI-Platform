import { useState } from "react";
import { useLocation, Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Home,
  Bot,
  BookOpen,
  Phone,
  History,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Users,
  FileText,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Home },
  { name: "Agents", href: "/agents", icon: Bot },
  { name: "Campaigns", href: "/campaigns", icon: Users },
  { name: "Knowledge Base", href: "/knowledge", icon: BookOpen },
  { name: "Phone Numbers", href: "/phone-numbers", icon: Phone },
  { name: "Call History", href: "/calls", icon: History },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
];

const bottomNavigation = [
  { name: "Documentation", href: "http://localhost:3001/Voice-AI-Platform/", icon: FileText },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function AppSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuth();

  const isActive = (href: string) => location.pathname === href;

  const NavItem = ({ item }: { item: typeof navigation[0] }) => {
    const active = isActive(item.href);
    const Icon = item.icon;
    const isExternal = item.href.startsWith("http");

    const linkClasses = cn(
      "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
      active
        ? "bg-primary text-primary-foreground"
        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
    );

    const innerContent = (
      <>
        <Icon className="h-5 w-5 shrink-0" />
        {!collapsed && (
          <motion.span
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: "auto" }}
            exit={{ opacity: 0, width: 0 }}
            className="truncate"
          >
            {item.name}
          </motion.span>
        )}
      </>
    );

    const content = isExternal ? (
      <a
        href={item.href}
        target="_blank"
        rel="noopener noreferrer"
        className={linkClasses}
      >
        {innerContent}
      </a>
    ) : (
      <Link to={item.href} className={linkClasses}>
        {innerContent}
      </Link>
    );

    if (collapsed) {
      return (
        <Tooltip delayDuration={0}>
          <TooltipTrigger asChild>{content}</TooltipTrigger>
          <TooltipContent side="right" sideOffset={10}>
            {item.name}
          </TooltipContent>
        </Tooltip>
      );
    }

    return content;
  };

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 64 : 240 }}
      transition={{ duration: 0.2, ease: "easeInOut" }}
      className="relative flex h-screen flex-col border-r border-border bg-sidebar"
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between border-b border-border px-4">
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-2"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Bot className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-semibold text-foreground">VoiceAI</span>
          </motion.div>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(!collapsed)}
          className={cn("h-8 w-8 shrink-0", collapsed && "mx-auto")}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 space-y-1 p-3">
        {navigation.map((item) => (
          <NavItem key={item.name} item={item} />
        ))}
      </nav>

      {/* Bottom Navigation */}
      <div className="border-t border-border p-3">
        {bottomNavigation.map((item) => (
          <NavItem key={item.name} item={item} />
        ))}

        {/* User & Logout */}
        <div className="mt-3 border-t border-border pt-3">
          {!collapsed && user && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-2 truncate px-3 text-xs text-muted-foreground"
            >
              {user.email}
            </motion.div>
          )}
          <Tooltip delayDuration={0}>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size={collapsed ? "icon" : "default"}
                onClick={logout}
                className={cn(
                  "w-full justify-start text-muted-foreground hover:text-destructive",
                  collapsed && "justify-center"
                )}
              >
                <LogOut className="h-5 w-5 shrink-0" />
                {!collapsed && <span className="ml-3">Logout</span>}
              </Button>
            </TooltipTrigger>
            {collapsed && (
              <TooltipContent side="right" sideOffset={10}>
                Logout
              </TooltipContent>
            )}
          </Tooltip>
        </div>
      </div>
    </motion.aside>
  );
}
