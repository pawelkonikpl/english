import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  Award,
  BookOpen,
  Flame,
  Lock,
  Repeat,
  Sparkles,
  Trophy,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { motion } from "motion/react";
import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router";

import { api, queryKeys } from "@/shared/api/endpoints";
import type { Dashboard } from "@/shared/api/schemas";
import { cn } from "@/shared/lib/cn";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { ProgressRing } from "@/shared/ui/progress-ring";
import { ErrorState, Spinner } from "@/shared/ui/states";

import { AchievementCelebration } from "./achievement-celebration";
import { ActivityHeatmap } from "./activity-heatmap";

const HEATMAP_DAYS = 84;

function recommendationPath(target: string, lessonType: string | null): string {
  switch (target) {
    case "review":
      return "/review";
    case "phrases":
      return "/phrases/learn";
    case "lessons":
      return lessonType ? `/lessons?type=${lessonType}` : "/lessons";
    case "conversation":
      return "/conversation";
    default:
      return "/";
  }
}

function greeting(name: string | null): string {
  const hour = new Date().getHours();
  const hello = hour < 12 ? "Dzień dobry" : hour < 18 ? "Cześć" : "Dobry wieczór";
  return name ? `${hello}, ${name}!` : `${hello}!`;
}

function StatTile({
  icon: Icon,
  label,
  value,
  hint,
  to,
  accent,
}: {
  icon: LucideIcon;
  label: string;
  value: ReactNode;
  hint?: string;
  to?: string;
  accent: string;
}) {
  const body = (
    <Card className={cn("flex h-full flex-col gap-3 p-4 sm:p-5", to && "transition hover:-translate-y-0.5 hover:shadow-md")}>
      <span className={cn("grid size-10 place-items-center rounded-2xl", accent)}>
        <Icon className="size-5" aria-hidden />
      </span>
      <div>
        <p className="text-2xl font-extrabold tabular-nums">{value}</p>
        <p className="text-sm font-medium text-ink-soft">{label}</p>
        {hint && <p className="mt-0.5 text-xs text-ink-muted">{hint}</p>}
      </div>
    </Card>
  );
  return to ? <Link to={to}>{body}</Link> : body;
}

function RecommendationCard({ data }: { data: Dashboard }) {
  const navigate = useNavigate();
  const rec = data.recommendation;
  return (
    <div className="relative overflow-hidden rounded-[2rem] bg-brand-gradient p-6 text-white shadow-xl shadow-brand/30 sm:p-8">
      <div className="absolute -top-10 -right-10 size-48 rounded-full bg-white/15 blur-2xl" aria-hidden />
      <div className="absolute -bottom-16 left-10 size-40 rounded-full bg-white/10 blur-2xl" aria-hidden />
      <div className="relative flex h-full flex-col gap-4">
        <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-white/20 px-3 py-1 text-xs font-bold tracking-wide uppercase">
          <Sparkles className="size-3.5" aria-hidden /> Co dziś?
        </span>
        <div>
          <h2 className="text-2xl font-extrabold sm:text-3xl">{rec?.title ?? "Wszystko zrobione!"}</h2>
          <p className="mt-1 text-white/85">
            {rec?.reason ?? "Na dziś nie ma nic do nadrobienia. Wróć jutro albo poćwicz dodatkowo."}
          </p>
        </div>
        {rec && (
          <Button
            variant="secondary"
            size="lg"
            className="mt-auto w-fit bg-white text-[#2b1b7a] ring-0 hover:bg-white/90"
            onClick={() => void navigate(recommendationPath(rec.target, rec.lesson_type))}
          >
            Zaczynamy <ArrowRight className="size-5" aria-hidden />
          </Button>
        )}
      </div>
    </div>
  );
}

function GoalCard({ data }: { data: Dashboard }) {
  const reached = data.xp.today >= data.xp.goal;
  return (
    <Card className="flex flex-col items-center justify-center gap-3 text-center">
      <ProgressRing
        value={data.xp.today}
        max={data.xp.goal}
        label={`Dzisiaj ${data.xp.today} z ${data.xp.goal} XP`}
      >
        <div>
          <p className="text-3xl font-extrabold tabular-nums">{data.xp.today}</p>
          <p className="text-xs font-semibold text-ink-muted">z {data.xp.goal} XP</p>
        </div>
      </ProgressRing>
      <p className="text-sm font-semibold">{reached ? "Cel dnia osiągnięty! 🎉" : "Cel dnia"}</p>
    </Card>
  );
}

function AchievementsCard() {
  const { data } = useQuery({ queryKey: queryKeys.achievements, queryFn: api.achievements });
  if (!data) return null;
  const unlocked = data.filter((a) => a.unlocked_at).length;
  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-bold">
          <Award className="size-5 text-brand-ink" aria-hidden /> Osiągnięcia
        </h2>
        <Badge tone="brand">
          {unlocked}/{data.length}
        </Badge>
      </div>
      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {data.map((a) => (
          <li
            key={a.key}
            className={cn(
              "flex items-start gap-3 rounded-2xl p-3 ring-1",
              a.unlocked_at ? "bg-brand-soft ring-brand/20" : "bg-surface-sunken ring-transparent opacity-70",
            )}
            title={a.description}
          >
            <span
              className={cn(
                "grid size-9 shrink-0 place-items-center rounded-xl",
                a.unlocked_at ? "bg-brand-gradient text-white" : "bg-surface-raised text-ink-muted",
              )}
            >
              {a.unlocked_at ? <Trophy className="size-4" aria-hidden /> : <Lock className="size-4" aria-hidden />}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-bold">{a.title}</p>
              <p className="line-clamp-2 text-xs text-ink-muted">{a.description}</p>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function DashboardPage() {
  const dashboard = useQuery({ queryKey: queryKeys.dashboard, queryFn: api.dashboard });
  const activity = useQuery({
    queryKey: queryKeys.activity(HEATMAP_DAYS),
    queryFn: () => api.activity(HEATMAP_DAYS),
  });

  if (dashboard.isPending) return <Spinner />;
  if (dashboard.isError) return <ErrorState error={dashboard.error} onRetry={() => void dashboard.refetch()} />;
  const data = dashboard.data;
  const phrases = data.items.find((i) => i.item_type === "phrase");

  return (
    <div className="flex flex-col gap-6">
      <AchievementCelebration achievements={data.new_achievements} />
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl">{greeting(data.display_name)}</h1>
        <Badge tone="brand">Poziom {data.level}</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-[1fr_auto]">
        <RecommendationCard data={data} />
        <GoalCard data={data} />
      </div>

      <motion.div
        className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4"
        initial="hidden"
        animate="show"
        variants={{ hidden: {}, show: { transition: { staggerChildren: 0.06 } } }}
      >
        {[
          {
            icon: Flame,
            label: "Seria dni",
            value: data.streak.current,
            hint: `Rekord: ${data.streak.longest}`,
            accent: "bg-[#ff7a59]/15 text-[#e2562f]",
          },
          {
            icon: Zap,
            label: "XP łącznie",
            value: data.xp.total,
            accent: "bg-warning/20 text-[#b67a00]",
          },
          {
            icon: Repeat,
            label: "Powtórki na dziś",
            value: data.reviews_due,
            to: "/review",
            accent: "bg-series-1/15 text-series-1",
          },
          {
            icon: BookOpen,
            label: "Frazy opanowane",
            value: phrases?.mastered ?? 0,
            hint: `W nauce: ${(phrases?.learning ?? 0) + (phrases?.familiar ?? 0)}`,
            to: "/phrases",
            accent: "bg-brand-soft text-brand-ink",
          },
        ].map((tile) => (
          <motion.div key={tile.label} variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }}>
            <StatTile {...tile} />
          </motion.div>
        ))}
      </motion.div>

      <Card>
        <h2 className="mb-3 text-lg font-bold">Twoja aktywność</h2>
        {activity.data ? (
          <ActivityHeatmap days={activity.data} goal={data.xp.goal} />
        ) : activity.isError ? (
          <ErrorState error={activity.error} />
        ) : (
          <Spinner />
        )}
      </Card>

      <AchievementsCard />
    </div>
  );
}
