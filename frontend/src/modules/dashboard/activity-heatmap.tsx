import { useState } from "react";

import type { DayActivity } from "@/shared/api/schemas";
import { cn } from "@/shared/lib/cn";
import { plural } from "@/shared/lib/plural";

const HEAT_CLASSES = [
  "bg-heat-0",
  "bg-heat-1",
  "bg-heat-2",
  "bg-heat-3",
  "bg-heat-4",
  "bg-heat-5",
] as const;
const WEEKDAYS = ["Pn", "", "Śr", "", "Pt", "", "Nd"];
const LEGEND_LABELS = ["0 XP", "do 25% celu", "do 50% celu", "do 100% celu", "do 150% celu", "ponad 150% celu"];

/** Sequential bins relative to the daily goal, so "full colour" means "goal met". */
export function heatLevel(xp: number, goal: number): number {
  if (xp <= 0) return 0;
  // Upper bounds are inclusive, matching the legend ("do 100% celu" includes 100%).
  const ratio = xp / Math.max(goal, 1);
  if (ratio <= 0.25) return 1;
  if (ratio <= 0.5) return 2;
  if (ratio <= 1) return 3;
  if (ratio <= 1.5) return 4;
  return 5;
}

const dateFormat = new Intl.DateTimeFormat("pl-PL", { weekday: "short", day: "numeric", month: "long" });

/** Calendar heatmap: columns are weeks (Monday first), cells are days. */
export function ActivityHeatmap({ days, goal }: { days: DayActivity[]; goal: number }) {
  const [hovered, setHovered] = useState<DayActivity | null>(null);
  if (days.length === 0) return null;

  const firstWeekday = (new Date(`${days[0]!.date}T12:00:00`).getDay() + 6) % 7; // Monday = 0
  const cells: (DayActivity | null)[] = [...Array<null>(firstWeekday).fill(null), ...days];
  const weeks: (DayActivity | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));

  const activeDays = days.filter((d) => d.count > 0).length;
  const totalXp = days.reduce((sum, d) => sum + d.xp, 0);
  const readout = hovered
    ? `${dateFormat.format(new Date(`${hovered.date}T12:00:00`))}: ${hovered.xp} XP, ${hovered.count} ${plural(hovered.count, "aktywność", "aktywności", "aktywności")}`
    : `Ostatnie ${days.length} dni: ${activeDays} ${plural(activeDays, "aktywny dzień", "aktywne dni", "aktywnych dni")}, ${totalXp} XP`;

  return (
    <div className="flex flex-col gap-3">
      <p className="min-h-5 text-sm text-ink-soft" aria-live="polite">
        {readout}
      </p>
      <div className="flex gap-2 overflow-x-auto pb-1">
        <div className="grid grid-rows-7 gap-1 pt-0.5 text-[10px] text-ink-muted" aria-hidden>
          {WEEKDAYS.map((d, i) => (
            <span key={i} className="flex h-3.5 items-center sm:h-4">
              {d}
            </span>
          ))}
        </div>
        <div className="flex gap-1" role="grid" aria-label="Aktywność w ostatnich tygodniach">
          {weeks.map((week, w) => (
            <div key={w} className="grid grid-rows-7 gap-1" role="row">
              {week.map((day, d) =>
                day ? (
                  <button
                    type="button"
                    key={day.date}
                    role="gridcell"
                    aria-label={`${day.date}: ${day.xp} XP`}
                    onMouseEnter={() => setHovered(day)}
                    onMouseLeave={() => setHovered(null)}
                    onFocus={() => setHovered(day)}
                    onBlur={() => setHovered(null)}
                    className={cn(
                      "size-3.5 rounded-[4px] transition hover:ring-2 hover:ring-ink/40 focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none sm:size-4",
                      HEAT_CLASSES[heatLevel(day.xp, goal)],
                    )}
                  />
                ) : (
                  <span key={`empty-${d}`} className="size-3.5 sm:size-4" />
                ),
              )}
            </div>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-1.5 text-[11px] text-ink-muted">
        <span>Mniej</span>
        {HEAT_CLASSES.map((cls, i) => (
          <span key={cls} className={cn("size-3 rounded-[3px]", cls)} title={LEGEND_LABELS[i]} />
        ))}
        <span>Więcej</span>
      </div>
    </div>
  );
}
