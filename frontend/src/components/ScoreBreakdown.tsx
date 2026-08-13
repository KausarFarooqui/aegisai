import type { AIAssessmentOut } from "@/api/types";
import { ImpactBandBadge } from "./Badge";

type FactorKey =
  | "factor_repetitiveness"
  | "factor_data_availability"
  | "factor_predictability"
  | "factor_digitalization"
  | "factor_ai_capability_fit";

const FACTORS: { key: FactorKey; label: string; weight: string }[] = [
  { key: "factor_repetitiveness", label: "Repetitiveness", weight: "30%" },
  { key: "factor_data_availability", label: "Data availability", weight: "20%" },
  { key: "factor_predictability", label: "Predictability", weight: "20%" },
  { key: "factor_digitalization", label: "Digitalization", weight: "15%" },
  { key: "factor_ai_capability_fit", label: "AI capability fit", weight: "15%" },
];

export function ScoreBreakdown({ assessment }: { assessment: AIAssessmentOut }) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-2xl font-medium text-[var(--color-ink)] tabular-nums">
            {assessment.total_score.toFixed(1)}
          </span>
          <span className="text-xs text-slate-400">/ 100</span>
        </div>
        <ImpactBandBadge band={assessment.impact_band} />
      </div>

      <div className="mt-4 space-y-2.5">
        {FACTORS.map(({ key, label, weight }) => {
          const value = assessment[key];
          const reason = assessment.factor_rationale[key.replace("factor_", "")];
          return (
            <div key={key}>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-600">
                  {label} <span className="text-slate-400">({weight})</span>
                </span>
                <span className="font-mono tabular-nums text-slate-600">{value}</span>
              </div>
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-[var(--color-star)]"
                  style={{ width: `${value}%` }}
                />
              </div>
              {reason && <p className="mt-1 text-xs leading-snug text-slate-500">{reason}</p>}
            </div>
          );
        })}
      </div>

      <p className="mt-3 text-[11px] text-slate-400">
        Scoring model {assessment.scoring_model_version} — total is a fixed weighted
        formula, computed deterministically, never set by the AI directly.
      </p>
    </div>
  );
}
