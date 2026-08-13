import { useEffect, useState, type ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Network,
  Workflow,
  Users,
  Sparkles,
  Lightbulb,
  Plus,
  PanelLeftClose,
  PanelLeftOpen,
  ArrowLeft,
} from "lucide-react";
import { cn } from "@/lib/cn";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/graph", label: "Intelligence Graph", icon: Network },
  { to: "/processes", label: "Processes", icon: Workflow },
  { to: "/roles", label: "Roles", icon: Users },
  { to: "/skills", label: "Skills", icon: Sparkles },
  { to: "/opportunities", label: "AI Opportunities", icon: Lightbulb },
];

const COLLAPSE_STORAGE_KEY = "aegisai:sidebar-collapsed";

export function Layout({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem(COLLAPSE_STORAGE_KEY) === "1";
    } catch {
      return false; // localStorage can throw in some privacy modes — default open, never crash the app over this
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(COLLAPSE_STORAGE_KEY, collapsed ? "1" : "0");
    } catch {
      // ignore — persistence is a nicety, not a requirement
    }
  }, [collapsed]);

  return (
    <div className="flex min-h-screen">
      <aside
        className={cn(
          "flex shrink-0 flex-col bg-[var(--color-navy-deep)] text-white transition-[width] duration-200",
          collapsed ? "w-[68px]" : "w-64",
        )}
      >
        <div className={cn("flex items-center gap-2.5 px-5 py-6", collapsed && "justify-center px-0")}>
          <StarMark className="shrink-0" />
          {!collapsed && (
            <div className="min-w-0">
              <p className="font-display text-sm font-semibold tracking-wide">AEGISAI</p>
              <p className="text-[11px] text-white/50">Northstar Bank</p>
            </div>
          )}
        </div>

        <nav className="flex-1 space-y-0.5 px-3">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              title={collapsed ? label : undefined}
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                  collapsed && "justify-center px-0",
                  isActive
                    ? "bg-white/[0.07] text-white"
                    : "text-white/60 hover:bg-white/[0.04] hover:text-white/90",
                )
              }
            >
              {({ isActive }) => (
                <>
                  {!collapsed && (
                    <span
                      className={cn(
                        "h-1.5 w-1.5 shrink-0 rounded-full transition-opacity",
                        isActive ? "bg-[var(--color-star)] opacity-100" : "opacity-0",
                      )}
                    />
                  )}
                  <Icon
                    className={cn("h-4 w-4 shrink-0", collapsed && isActive && "text-[var(--color-star)]")}
                    strokeWidth={1.75}
                  />
                  {!collapsed && label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="space-y-2 border-t border-white/10 p-3">
          <NavLink
            to="/analyze"
            title={collapsed ? "Analyze New Process" : undefined}
            className={({ isActive }) =>
              cn(
                "flex items-center justify-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-[var(--color-star)] text-[var(--color-navy-deep)]"
                  : "bg-white/[0.08] text-white hover:bg-[var(--color-star)] hover:text-[var(--color-navy-deep)]",
              )
            }
          >
            <Plus className="h-4 w-4 shrink-0" strokeWidth={2} />
            {!collapsed && "Analyze New Process"}
          </NavLink>

          <button
            onClick={() => setCollapsed((c) => !c)}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="flex w-full items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs text-white/40 transition-colors hover:bg-white/[0.04] hover:text-white/70"
          >
            {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
            {!collapsed && "Collapse"}
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}

/** The signature glyph — a four-point star, used sparingly: here, and on
 * the constellation graph's high-impact nodes. Everything else stays quiet. */
export function StarMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={cn("h-5 w-5", className)}>
      <path
        d="M12 2 L14 10 L22 12 L14 14 L12 22 L10 14 L2 12 L10 10 Z"
        fill="var(--color-star)"
      />
    </svg>
  );
}

export function PageHeader({
  title,
  subtitle,
  action,
  backTo,
  backLabel,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  /** When set, renders a "← backLabel" link above the title — used on
   * every detail page so there's always a way back that isn't the browser
   * button or re-clicking the sidebar. */
  backTo?: string;
  backLabel?: string;
}) {
  return (
    <div className="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)] px-8 py-6">
      {backTo && (
        <Link
          to={backTo}
          className="mb-2 inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-[var(--color-navy)]"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> {backLabel ?? "Back"}
        </Link>
      )}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-xl font-semibold text-[var(--color-ink)]">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
        </div>
        {action}
      </div>
    </div>
  );
}
