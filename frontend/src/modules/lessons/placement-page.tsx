import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";

import { queryKeys } from "@/shared/api/endpoints";
import { cefrLevels, type CefrLevel } from "@/shared/api/schemas";
import { cn } from "@/shared/lib/cn";
import { Card } from "@/shared/ui/card";
import { PageHeader } from "@/shared/ui/page-header";

import { PlacementTest } from "./placement-test";

export function PlacementPage() {
  const queryClient = useQueryClient();
  const [selfLevel, setSelfLevel] = useState<CefrLevel>("A2");
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-5">
      <Link to="/lessons" className="inline-flex items-center gap-1 text-sm font-semibold text-ink-soft hover:text-ink">
        <ArrowLeft className="size-4" aria-hidden /> Lekcje
      </Link>
      <PageHeader title="Test poziomujący" subtitle="Najpierw oceń się sam, potem rozwiąż dwa zadania." />
      <Card className="flex flex-col gap-5">
        <div>
          <p className="mb-2 text-sm font-semibold">Jak oceniasz swój poziom?</p>
          <div className="grid grid-cols-6 gap-1.5" role="radiogroup" aria-label="Samoocena">
            {cefrLevels.map((level) => (
              <button
                key={level}
                type="button"
                role="radio"
                aria-checked={selfLevel === level}
                onClick={() => setSelfLevel(level)}
                className={cn(
                  "rounded-xl py-2 text-sm font-bold transition",
                  selfLevel === level ? "bg-brand-gradient text-white" : "bg-surface-sunken text-ink-soft hover:text-ink",
                )}
              >
                {level}
              </button>
            ))}
          </div>
        </div>
        <PlacementTest
          key={selfLevel}
          selfLevel={selfLevel}
          onResult={() => {
            void queryClient.invalidateQueries({ queryKey: queryKeys.profile });
            void queryClient.invalidateQueries({ queryKey: ["progress"] });
          }}
        />
      </Card>
    </div>
  );
}
