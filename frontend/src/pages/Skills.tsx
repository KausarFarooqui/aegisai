import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useSkill, useSkills } from "@/hooks/useApi";
import { PageHeader } from "@/components/Layout";
import { Card } from "@/components/Card";
import { TrendBadge } from "@/components/Badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { formatTrend } from "@/lib/format";
import type { SkillTrend } from "@/api/types";
import { Network, ChevronRight, Sparkles } from "lucide-react";
import { cn } from "@/lib/cn";

const TRENDS: SkillTrend[] = [
  "emerging",
  "increasing",
  "ai_augmented",
  "changing",
  "declining",
  "enduring_human_capability",
];

export function SkillListPage() {
  const [trendFilter, setTrendFilter] = useState<SkillTrend | undefined>(undefined);
  const { data, isLoading, isError, error, refetch } = useSkills(trendFilter);

  return (
    <>
      <PageHeader title="Skills" subtitle="Every skill identified across the intelligence graph, and how AI is changing it" />
      <div className="mx-auto max-w-5xl px-8 py-8">
        <div className="mb-5 flex flex-wrap gap-2">
          <FilterChip active={!trendFilter} onClick={() => setTrendFilter(undefined)} label="All" />
          {TRENDS.map((t) => (
            <FilterChip
              key={t}
              active={trendFilter === t}
              onClick={() => setTrendFilter(t)}
              label={formatTrend(t)}
            />
          ))}
        </div>

        {isLoading && <LoadingState label="Loading skills" />}
        {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}
        {data && data.length === 0 && (
          <EmptyState
            title="No skills match this filter"
            description="Try a different trend, or select 'All'."
          />
        )}
        {data && data.length > 0 && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {data.map((skill) => (
              <Link key={skill.id} to={`/skills/${skill.id}`}>
                <Card className="h-full transition-colors hover:border-[var(--color-star)]/50">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-[#4fb3a9]" />
                      <p className="font-display font-medium text-[var(--color-ink)]">{skill.name}</p>
                    </div>
                    <ChevronRight className="h-4 w-4 shrink-0 text-slate-300" />
                  </div>
                  <div className="mt-2">
                    <TrendBadge trend={skill.trend_classification} />
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

function FilterChip({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
        active
          ? "bg-[var(--color-navy)] text-white"
          : "border border-[var(--color-border)] text-slate-600 hover:border-[var(--color-navy)]/40",
      )}
    >
      {label}
    </button>
  );
}

export function SkillDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: skill, isLoading, isError, error, refetch } = useSkill(id);

  if (isLoading) return <div className="px-8 py-8"><LoadingState label="Loading skill" /></div>;
  if (isError) return <div className="px-8 py-8"><ErrorState message={(error as Error).message} onRetry={() => refetch()} /></div>;
  if (!skill) return null;

  return (
    <>
      <PageHeader
        title={skill.name}
        breadcrumbs={[
          { label: "Dashboard", to: "/" },
          { label: "Skills", to: "/skills" },
          { label: skill.name },
        ]}
        backTo="/skills"
        backLabel="Back to Skills"
        action={
          <Link
            to={`/graph?type=skill&id=${skill.id}`}
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-ink)] hover:border-[var(--color-star)]/60"
          >
            <Network className="h-4 w-4" /> View in graph
          </Link>
        }
      />
      <div className="mx-auto max-w-3xl space-y-6 px-8 py-8">
        <Card>
          <div className="flex items-center gap-3">
            <TrendBadge trend={skill.trend_classification} />
            {skill.category && <span className="text-xs text-slate-400">{skill.category}</span>}
          </div>
          {skill.trend_rationale && (
            <div className="mt-4 border-t border-[var(--color-border)] pt-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                Why this classification
              </p>
              <p className="mt-1 text-sm leading-relaxed text-slate-600">{skill.trend_rationale}</p>
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
