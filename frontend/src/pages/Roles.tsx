import { Link, useParams } from "react-router-dom";
import { useRole, useRoles } from "@/hooks/useApi";
import { PageHeader } from "@/components/Layout";
import { Card } from "@/components/Card";
import { TrendBadge } from "@/components/Badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { Network, ChevronRight, Users } from "lucide-react";

export function RoleListPage() {
  const { data, isLoading, isError, error, refetch } = useRoles();

  return (
    <>
      <PageHeader title="Roles" subtitle="Every role identified across the intelligence graph" />
      <div className="mx-auto max-w-5xl px-8 py-8">
        {isLoading && <LoadingState label="Loading roles" />}
        {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}
        {data && data.length === 0 && (
          <EmptyState title="No roles yet" description="Roles appear once a process is analyzed." />
        )}
        {data && data.length > 0 && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {data.map((role) => (
              <Link key={role.id} to={`/roles/${role.id}`}>
                <Card className="h-full transition-colors hover:border-[var(--color-star)]/50">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-[#6f8fd6]" />
                      <p className="font-display font-medium text-[var(--color-ink)]">{role.title}</p>
                    </div>
                    <ChevronRight className="h-4 w-4 shrink-0 text-slate-300" />
                  </div>
                  {role.skills.length > 0 && (
                    <p className="mt-2 text-xs text-slate-500">
                      {role.skills.map((s) => s.name).join(" · ")}
                    </p>
                  )}
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

export function RoleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: role, isLoading, isError, error, refetch } = useRole(id);

  if (isLoading) return <div className="px-8 py-8"><LoadingState label="Loading role" /></div>;
  if (isError) return <div className="px-8 py-8"><ErrorState message={(error as Error).message} onRetry={() => refetch()} /></div>;
  if (!role) return null;

  return (
    <>
      <PageHeader
        title={role.title}
        action={
          <Link
            to={`/graph?type=role&id=${role.id}`}
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-ink)] hover:border-[var(--color-star)]/60"
          >
            <Network className="h-4 w-4" /> View in graph
          </Link>
        }
      />
      <div className="mx-auto max-w-3xl space-y-6 px-8 py-8">
        <Card>
          {role.current_responsibilities ? (
            <p className="text-sm leading-relaxed text-[var(--color-ink)]">
              {role.current_responsibilities}
            </p>
          ) : (
            <p className="text-sm text-slate-400">No current responsibilities recorded yet.</p>
          )}
        </Card>

        <div>
          <h2 className="mb-3 font-display text-sm font-semibold text-[var(--color-ink)]">
            Required skills ({role.skills.length})
          </h2>
          {role.skills.length === 0 ? (
            <p className="text-sm text-slate-400">No skills linked yet.</p>
          ) : (
            <div className="space-y-2">
              {role.skills.map((skill) => (
                <Link key={skill.id} to={`/skills/${skill.id}`}>
                  <Card className="flex items-center justify-between transition-colors hover:border-[var(--color-star)]/50">
                    <span className="font-medium text-[var(--color-ink)]">{skill.name}</span>
                    <TrendBadge trend={skill.trend_classification} />
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
