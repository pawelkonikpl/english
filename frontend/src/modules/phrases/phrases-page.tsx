import { useQuery } from "@tanstack/react-query";
import { ChevronRight, Sparkles } from "lucide-react";
import { Link } from "react-router";

import { api, queryKeys } from "@/shared/api/endpoints";
import type { Section } from "@/shared/api/schemas";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { PageHeader } from "@/shared/ui/page-header";
import { SegmentedBar, SegmentedBarLegend } from "@/shared/ui/segmented-bar";
import { ErrorState, Spinner } from "@/shared/ui/states";

const TIER_LABELS: Record<string, string> = {
  "1": "Poziom 1",
  "2": "Poziom 2",
  "3": "Poziom 3",
  pitfalls: "Pułapki",
};

function groupByTier(sections: Section[]): [string, Section[]][] {
  const groups = new Map<string, Section[]>();
  for (const section of sections) {
    groups.set(section.tier, [...(groups.get(section.tier) ?? []), section]);
  }
  return [...groups.entries()];
}

export function PhrasesPage() {
  const sections = useQuery({ queryKey: queryKeys.sections, queryFn: api.sections });
  const session = useQuery({ queryKey: queryKeys.learnSession, queryFn: api.learnSession });

  return (
    <div>
      <PageHeader
        title="Frazy do komunikacji"
        subtitle="Zwroty ułożone od najważniejszych. Zacznij od Poziomu 1: frazy ratunkowe."
        actions={
          <Link to="/phrases/learn">
            <Button size="lg" disabled={session.data?.remaining_today === 0}>
              <Sparkles className="size-5" aria-hidden />
              Ucz się nowych
              {session.data ? ` (${session.data.remaining_today})` : ""}
            </Button>
          </Link>
        }
      />
      {sections.isPending && <Spinner />}
      {sections.isError && <ErrorState error={sections.error} onRetry={() => void sections.refetch()} />}
      {sections.data && (
        <div className="flex flex-col gap-8">
          <SegmentedBarLegend />
          {groupByTier(sections.data).map(([tier, items]) => (
            <section key={tier}>
              <h2 className="mb-3 flex items-baseline gap-2 text-lg font-bold">
                <span className="text-brand-gradient">{TIER_LABELS[tier] ?? tier}</span>
                <span className="text-sm font-medium text-ink-muted">{items[0]?.tier_title}</span>
              </h2>
              <div className="grid gap-3 sm:grid-cols-2">
                {items.map((section) => (
                  <Link key={section.code} to={`/phrases/${encodeURIComponent(section.code)}`}>
                    <Card className="group flex flex-col gap-3 p-4 transition hover:-translate-y-0.5 hover:shadow-md sm:p-5">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-xs font-bold text-ink-muted">{section.code}</p>
                          <p className="font-semibold">{section.title}</p>
                        </div>
                        <ChevronRight
                          className="size-5 shrink-0 text-ink-muted transition group-hover:translate-x-0.5 group-hover:text-brand-ink"
                          aria-hidden
                        />
                      </div>
                      <SegmentedBar
                        mastered={section.mastered}
                        learning={section.learning}
                        total={section.total}
                      />
                      <p className="text-xs text-ink-muted">
                        {section.mastered} opanowane · {section.learning} w nauce · {section.total} fraz
                      </p>
                    </Card>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
