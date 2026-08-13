import { Link } from "react-router-dom";
import { useProcesses } from "@/hooks/useApi";
import { PageHeader } from "@/components/Layout";
import { Card } from "@/components/Card";
import { SourceBadge } from "@/components/Badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { truncate } from "@/lib/format";
import { Plus, ChevronRight } from "lucide-react";

export function ProcessListPage() {
  const { data, isLoading, isError, error, refetch } = useProcesses();

  return (
    <>
      <PageHeader
        title="Processes"
        subtitle="Every process in the intelligence graph, seeded or dynamically analyzed"
        action={
          <Link
            to="/analyze"
            className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-navy)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-navy-soft)]"
          >
            <Plus className="h-4 w-4" /> Analyze new
          </Link>
        }
      />
      <div className="mx-auto max-w-5xl px-8 py-8">
        {isLoading && <LoadingState label="Loading processes" />}
        {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}
        {data && data.length === 0 && (
          <EmptyState
            title="No processes yet"
            description="Analyze your first process to start building the graph."
          />
        )}
        {data && data.length > 0 && (
          <div className="space-y-2">
            {data.map((p) => (
              <Link key={p.id} to={`/processes/${p.id}`}>
                <Card className="flex items-center justify-between transition-colors hover:border-[var(--color-star)]/50">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-display font-medium text-[var(--color-ink)]">{p.name}</p>
                      <SourceBadge source={p.source} />
                    </div>
                    {p.business_purpose && (
                      <p className="mt-1 text-sm text-slate-500">{truncate(p.business_purpose, 140)}</p>
                    )}
                  </div>
                  <ChevronRight className="h-5 w-5 shrink-0 text-slate-300" />
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
