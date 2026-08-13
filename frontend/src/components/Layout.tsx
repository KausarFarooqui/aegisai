import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Network,
  Workflow,
  Users,
  Sparkles,
  Lightbulb,
  Plus,
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

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="flex w-64 shrink-0 flex-col bg-[var(--color-navy-deep)] text-white">
        <div className="flex items-center gap-2.5 px-5 py-6">
          <StarMark />
          <div>
            <p className="font-display text-sm font-semibold tracking-wide">AEGISAI</p>
            <p className="text-[11px] text-white/50">Northstar Bank</p>
          </div>
        </div>

        <nav className="flex-1 space-y-0.5 px-3">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                  isActive
                    ? "bg-white/[0.07] text-white"
                    : "text-white/60 hover:bg-white/[0.04] hover:text-white/90",
                )
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={cn(
                      "h-1.5 w-1.5 shrink-0 rounded-full transition-opacity",
                      isActive ? "bg-[var(--color-star)] opacity-100" : "opacity-0",
                    )}
                  />
                  <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/10 p-3">
          <NavLink
            to="/analyze"
            className={({ isActive }) =>
              cn(
                "flex items-center justify-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-[var(--color-star)] text-[var(--color-navy-deep)]"
                  : "bg-white/[0.08] text-white hover:bg-[var(--color-star)] hover:text-[var(--color-navy-deep)]",
              )
            }
          >
            <Plus className="h-4 w-4" strokeWidth={2} />
            Analyze New Process
          </NavLink>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">{children}</main>
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
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-[var(--color-border)] bg-[var(--color-surface-raised)] px-8 py-6">
      <div>
        <h1 className="font-display text-xl font-semibold text-[var(--color-ink)]">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
