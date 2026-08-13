import type { ReactNode } from "react";

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-12 text-sm text-slate-500" role="status">
      <span className="relative flex h-3 w-3">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--color-star)] opacity-60" />
        <span className="relative inline-flex h-3 w-3 rounded-full bg-[var(--color-star)]" />
      </span>
      {label}…
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-xl border border-[#f0c4b5] bg-[#fbe9e3] p-5 text-sm text-[#8a3319]">
      <p className="font-medium">Something went wrong.</p>
      <p className="mt-1 text-[#8a3319]/80">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 rounded-md border border-[#e6a68f] bg-white px-3 py-1.5 text-xs font-medium text-[#8a3319] hover:bg-[#fdf2ee]"
        >
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--color-border)] px-6 py-16 text-center">
      <div className="mb-3 h-8 w-8 rounded-full border-2 border-dashed border-[var(--color-star-soft)]" />
      <p className="font-display text-sm font-semibold text-[var(--color-ink)]">{title}</p>
      {description && <p className="mt-1.5 max-w-sm text-sm text-slate-500">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
