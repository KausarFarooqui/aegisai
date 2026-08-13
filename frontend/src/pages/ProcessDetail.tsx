import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useProcess } from "@/hooks/useApi";
import { PageHeader } from "@/components/Layout";
import { Card } from "@/components/Card";
import { SourceBadge, ResponsibilityBadge, TrendBadge } from "@/components/Badge";
import { ScoreBreakdown } from "@/components/ScoreBreakdown";
import { ErrorState, LoadingState } from "@/components/States";
import { Network, ChevronDown, ChevronRight, Lightbulb } from "lucide-react";
import type { ActivityOut } from "@/api/types";

export function ProcessDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: process, isLoading, isError, error, refetch } = useProcess(id);

  if (isLoading) {
    return (
      <div className="px-8 py-8">
        <LoadingState label="Loading process" />
      </div>
    );
  }
  if (isError) {
    return (
      <div className="px-8 py-8">
        <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
      </div>
    );
  }
  if (!process) return null;

  return (
    <>
      <PageHeader
        title={process.name}
        action={
          <Link
            to={`/graph?type=process&id=${process.id}`}
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-ink)] hover:border-[var(--color-star)]/60"
          >
            <Network className="h-4 w-4" /> View in graph
          </Link>
        }
      />
      <div className="mx-auto max-w-5xl space-y-6 px-8 py-8">
        <Card>
          <SourceBadge source={process.source} />
          {process.business_purpose && (
            <div className="mt-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                Business purpose
              </p>
              <p className="mt-1 text-sm leading-relaxed text-[var(--color-ink)]">
                {process.business_purpose}
              </p>
            </div>
          )}
          {process.current_challenges && (
            <div className="mt-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                Current challenges
              </p>
              <p className="mt-1 text-sm leading-relaxed text-slate-600">
                {process.current_challenges}
              </p>
            </div>
          )}
        </Card>

        <div>
          <h2 className="mb-3 font-display text-sm font-semibold text-[var(--color-ink)]">
            Activities ({process.activities.length})
          </h2>
          <div className="space-y-3">
            {process.activities.map((activity) => (
              <ActivityCard key={activity.id} activity={activity} />
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

function ActivityCard({ activity }: { activity: ActivityOut }) {
  const [open, setOpen] = useState(true);
  const opportunityCount = activity.ai_opportunities.length;

  return (
    <Card padded={false}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-5 py-4 text-left"
      >
        <div className="flex items-center gap-2">
          {open ? (
            <ChevronDown className="h-4 w-4 shrink-0 text-slate-400" />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0 text-slate-400" />
          )}
          <span className="font-display font-medium text-[var(--color-ink)]">{activity.name}</span>
        </div>
        {opportunityCount > 0 && (
          <span className="flex items-center gap-1 text-xs text-[#c68a2e]">
            <Lightbulb className="h-3.5 w-3.5" /> {opportunityCount} opportunit
            {opportunityCount === 1 ? "y" : "ies"}
          </span>
        )}
      </button>

      {open && (
        <div className="space-y-4 border-t border-[var(--color-border)] px-5 py-4">
          {activity.description && <p className="text-sm text-slate-500">{activity.description}</p>}

          {activity.roles.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">
                Performed by
              </p>
              <div className="flex flex-wrap gap-2">
                {activity.roles.map((role) => (
                  <Link
                    key={role.id}
                    to={`/roles/${role.id}`}
                    className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm text-[var(--color-ink)] hover:border-[var(--color-star)]/60"
                  >
                    {role.title}
                    {role.skills.length > 0 && (
                      <span className="ml-1.5 text-xs text-slate-400">
                        · {role.skills.map((s) => s.name).join(", ")}
                      </span>
                    )}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {activity.ai_opportunities.map((opp) => (
            <div key={opp.id} className="rounded-lg border border-[var(--color-border)] p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-[var(--color-ink)]">{opp.name}</p>
                  {opp.description && (
                    <p className="mt-1 text-sm text-slate-500">{opp.description}</p>
                  )}
                </div>
                <ResponsibilityBadge value={opp.human_ai_responsibility} />
              </div>

              {opp.assessment && (
                <div className="mt-4 border-t border-[var(--color-border)] pt-4">
                  <ScoreBreakdown assessment={opp.assessment} />
                </div>
              )}

              {(opp.business_benefit || opp.risks) && (
                <div className="mt-4 grid grid-cols-1 gap-3 border-t border-[var(--color-border)] pt-4 sm:grid-cols-2">
                  {opp.business_benefit && (
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                        Business benefit
                      </p>
                      <p className="mt-1 text-sm text-slate-600">{opp.business_benefit}</p>
                    </div>
                  )}
                  {opp.risks && (
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Risks</p>
                      <p className="mt-1 text-sm text-slate-600">{opp.risks}</p>
                    </div>
                  )}
                </div>
              )}

              {opp.affected_skills.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-1.5 border-t border-[var(--color-border)] pt-4">
                  {opp.affected_skills.map((s) => (
                    <div key={s.id} className="flex items-center gap-1.5">
                      <span className="text-xs text-slate-500">{s.name}</span>
                      <TrendBadge trend={s.trend_classification} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
