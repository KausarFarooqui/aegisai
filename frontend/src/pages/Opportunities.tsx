import { useOpportunities } from "@/hooks/useApi";
import { PageHeader } from "@/components/Layout";
import { Card } from "@/components/Card";
import { ResponsibilityBadge, ImpactBandBadge, AutomationPotentialBadge } from "@/components/Badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { Lightbulb } from "lucide-react";

export function OpportunitiesPage() {
  const { data, isLoading, isError, error, refetch } = useOpportunities();

  return (
    <>
      <PageHeader
        title="AI Opportunities"
        subtitle="Every AI opportunity identified across the intelligence graph, with its deterministic impact score"
      />
      <div className="mx-auto max-w-5xl px-8 py-8">
        {isLoading && <LoadingState label="Loading AI opportunities" />}
        {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}
        {data && data.length === 0 && (
          <EmptyState
            title="No AI opportunities yet"
            description="They appear automatically once a process is analyzed."
          />
        )}
        {data && data.length > 0 && (
          <div className="space-y-3">
            {data.map((opp) => (
              <Card key={opp.id}>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-[var(--color-star)]" />
                    <div>
                      <p className="font-display font-medium text-[var(--color-ink)]">{opp.name}</p>
                      {opp.description && (
                        <p className="mt-1 text-sm text-slate-500">{opp.description}</p>
                      )}
                      <div className="mt-3 flex flex-wrap gap-2">
                        <ResponsibilityBadge value={opp.human_ai_responsibility} />
                        <AutomationPotentialBadge value={opp.automation_potential} />
                      </div>
                    </div>
                  </div>
                  {opp.assessment && (
                    <div className="flex shrink-0 flex-col items-end gap-1">
                      <span className="font-mono text-xl font-medium tabular-nums text-[var(--color-ink)]">
                        {opp.assessment.total_score.toFixed(1)}
                      </span>
                      <ImpactBandBadge band={opp.assessment.impact_band} />
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
