import type {
  AutomationPotential,
  EntitySource,
  HumanAIResponsibility,
  ImpactBand,
  SkillTrend,
} from "@/api/types";
import {
  formatAutomationPotential,
  formatImpactBand,
  formatResponsibility,
  formatSource,
  formatTrend,
} from "@/lib/format";
import { cn } from "@/lib/cn";

function BadgeBase({ className, children }: { className: string; children: React.ReactNode }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium font-mono",
        className,
      )}
    >
      {children}
    </span>
  );
}

const IMPACT_CLASSES: Record<ImpactBand, string> = {
  low: "bg-slate-100 text-slate-600 border border-slate-200",
  medium: "bg-teal-50 text-[#2f7d8c] border border-teal-200",
  high: "bg-amber-50 text-[#c68a2e] border border-amber-200",
  very_high: "bg-[#fbe9e3] text-[#b4472a] border border-[#f0c4b5]",
};

export function ImpactBandBadge({ band }: { band: ImpactBand }) {
  return (
    <BadgeBase className={IMPACT_CLASSES[band]}>
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: `var(--color-impact-${band.replace("_", "-")})` }}
      />
      {formatImpactBand(band)}
    </BadgeBase>
  );
}

const TREND_CLASSES: Record<SkillTrend, string> = {
  emerging: "bg-teal-50 text-[#2f7d8c] border border-teal-200",
  increasing: "bg-emerald-50 text-[#3d8c5a] border border-emerald-200",
  ai_augmented: "bg-blue-50 text-[#4a6a9e] border border-blue-200",
  changing: "bg-violet-50 text-[#8b7fb0] border border-violet-200",
  declining: "bg-[#fbe9e3] text-[#b4472a] border border-[#f0c4b5]",
  enduring_human_capability: "bg-slate-100 text-[#1b2a4a] border border-slate-300",
  unclassified: "bg-slate-50 text-slate-400 border border-slate-200",
};

export function TrendBadge({ trend }: { trend: SkillTrend }) {
  return <BadgeBase className={TREND_CLASSES[trend]}>{formatTrend(trend)}</BadgeBase>;
}

const RESPONSIBILITY_CLASSES: Record<HumanAIResponsibility, string> = {
  ai_automates: "bg-[#fbe9e3] text-[#b4472a] border border-[#f0c4b5]",
  ai_augments: "bg-blue-50 text-[#4a6a9e] border border-blue-200",
  human_led: "bg-slate-100 text-[#1b2a4a] border border-slate-300",
  human_approval_required: "bg-amber-50 text-[#c68a2e] border border-amber-200",
};

export function ResponsibilityBadge({ value }: { value: HumanAIResponsibility }) {
  return <BadgeBase className={RESPONSIBILITY_CLASSES[value]}>{formatResponsibility(value)}</BadgeBase>;
}

const AUTOMATION_CLASSES: Record<AutomationPotential, string> = {
  low: "bg-slate-100 text-slate-600 border border-slate-200",
  medium: "bg-teal-50 text-[#2f7d8c] border border-teal-200",
  high: "bg-amber-50 text-[#c68a2e] border border-amber-200",
};

export function AutomationPotentialBadge({ value }: { value: AutomationPotential }) {
  return (
    <BadgeBase className={AUTOMATION_CLASSES[value]}>
      Automation: {formatAutomationPotential(value)}
    </BadgeBase>
  );
}

export function SourceBadge({ source }: { source: EntitySource }) {
  return (
    <BadgeBase
      className={
        source === "seed"
          ? "bg-slate-100 text-slate-500 border border-slate-200"
          : "bg-[#f0dca3]/40 text-[#8a6a1f] border border-[#e6cd85]"
      }
    >
      {formatSource(source)}
    </BadgeBase>
  );
}
