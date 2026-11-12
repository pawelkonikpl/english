/** Two-series stacked bar: mastered (series 1) and learning (series 2), 2px gap between fills. */
export function SegmentedBar({
  mastered,
  learning,
  total,
}: {
  mastered: number;
  learning: number;
  total: number;
}) {
  const pct = (n: number) => (total > 0 ? (n / total) * 100 : 0);
  return (
    <div
      className="flex h-2.5 w-full gap-0.5 overflow-hidden rounded-full bg-surface-sunken"
      role="img"
      aria-label={`Opanowane: ${mastered}, w nauce: ${learning}, wszystkich: ${total}`}
      title={`Opanowane: ${mastered} · W nauce: ${learning} · Wszystkich: ${total}`}
    >
      {mastered > 0 && (
        <div className="rounded-full bg-series-1" style={{ width: `${pct(mastered)}%` }} />
      )}
      {learning > 0 && (
        <div className="rounded-full bg-series-2" style={{ width: `${pct(learning)}%` }} />
      )}
    </div>
  );
}

export function SegmentedBarLegend() {
  return (
    <div className="flex items-center gap-4 text-xs text-ink-soft">
      <span className="inline-flex items-center gap-1.5">
        <span className="size-2.5 rounded-full bg-series-1" aria-hidden /> Opanowane
      </span>
      <span className="inline-flex items-center gap-1.5">
        <span className="size-2.5 rounded-full bg-series-2" aria-hidden /> W nauce
      </span>
    </div>
  );
}
