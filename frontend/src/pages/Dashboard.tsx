import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useDashboard } from "@/hooks/useApi";
import { PageHeader } from "@/components/Layout";
import { Card, CardHeader } from "@/components/Card";
import { KPICard } from "@/components/KPICard";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { TrendingUp, TrendingDown, Plus } from "lucide-react";

export function DashboardPage() {
  const { data, isLoading, isError, error, refetch } = useDashboard();

  return (
    <>
      <PageHeader
        title="Executive Dashboard"
        subtitle="Northstar Bank — AI workforce impact across every analyzed process"
      />
      <div className="mx-auto max-w-7xl px-8 py-8">
        {isLoading && <LoadingState label="Loading dashboard" />}
        {isError && (
          <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
        )}

        {data && data.total_processes === 0 && (
          <EmptyState
            title="No processes analyzed yet"
            description="Run your first analysis to start building the intelligence graph — the same pipeline handles a seeded process or a completely unfamiliar one you type in yourself."
            action={
              <Link
                to="/analyze"
                className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-navy)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-navy-soft)]"
              >
                <Plus className="h-4 w-4" /> Analyze a process
              </Link>
            }
          />
        )}

        {data && data.total_processes > 0 && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
              <KPICard label="Processes" value={data.total_processes} />
              <KPICard label="Activities" value={data.total_activities} />
              <KPICard label="Roles" value={data.total_roles} />
              <KPICard label="Skills" value={data.total_skills} />
              <KPICard label="AI Opportunities" value={data.total_ai_opportunities} />
              <KPICard
                label="High Impact"
                value={data.high_impact_process_count}
                sublabel={`of ${data.total_processes} processes`}
              />
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
              <Card className="lg:col-span-3">
                <CardHeader
                  title="Most affected roles"
                  subtitle="By number of linked AI opportunities"
                />
                {data.most_affected_roles.length === 0 ? (
                  <p className="py-8 text-center text-sm text-slate-400">
                    No roles linked to AI opportunities yet.
                  </p>
                ) : (
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={data.most_affected_roles}
                        layout="vertical"
                        margin={{ left: 8, right: 16 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e5eb" />
                        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} />
                        <YAxis
                          type="category"
                          dataKey="title"
                          width={150}
                          tick={{ fontSize: 12, fill: "#0b1220" }}
                        />
                        <Tooltip
                          cursor={{ fill: "#f7f8fa" }}
                          contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e5eb" }}
                        />
                        <Bar dataKey="ai_opportunity_count" name="AI Opportunities" fill="#d4a73c" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </Card>

              <div className="space-y-6 lg:col-span-2">
                <Card>
                  <CardHeader title="Emerging skills" action={<TrendingUp className="h-4 w-4 text-[#3d8c5a]" />} />
                  <SkillList skills={data.emerging_skills} emptyText="None classified as emerging yet." />
                </Card>
                <Card>
                  <CardHeader title="Declining skills" action={<TrendingDown className="h-4 w-4 text-[#b4472a]" />} />
                  <SkillList skills={data.declining_skills} emptyText="None classified as declining yet." />
                </Card>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

function SkillList({ skills, emptyText }: { skills: string[]; emptyText: string }) {
  if (skills.length === 0) {
    return <p className="text-sm text-slate-400">{emptyText}</p>;
  }
  return (
    <ul className="space-y-1.5">
      {skills.map((s) => (
        <li key={s} className="text-sm text-[var(--color-ink)]">
          {s}
        </li>
      ))}
    </ul>
  );
}
