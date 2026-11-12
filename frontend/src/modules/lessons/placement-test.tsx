import { useMutation, useQuery } from "@tanstack/react-query";
import { Bot, Target } from "lucide-react";
import { useState } from "react";

import { api, queryKeys } from "@/shared/api/endpoints";
import type { CefrLevel, PlacementResult } from "@/shared/api/schemas";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { ErrorState, Spinner } from "@/shared/ui/states";

const textareaClass =
  "w-full resize-none rounded-2xl bg-surface-sunken p-4 outline-none focus:ring-2 focus:ring-brand";

/** Two short tasks from the original assessment; AI places the learner on A1-C2. */
export function PlacementTest({
  selfLevel,
  onResult,
}: {
  selfLevel: CefrLevel;
  onResult?: (result: PlacementResult) => void;
}) {
  const questions = useQuery({
    queryKey: queryKeys.placement(selfLevel),
    queryFn: () => api.placementQuestions(selfLevel),
  });
  const [translation, setTranslation] = useState("");
  const [correction, setCorrection] = useState("");
  const run = useMutation({
    mutationFn: () => api.runPlacement(selfLevel, translation, correction),
    onSuccess: (result) => onResult?.(result),
  });

  if (questions.isPending) return <Spinner />;
  if (questions.isError) return <ErrorState error={questions.error} />;

  if (run.data) {
    return (
      <div className="flex flex-col gap-3 rounded-3xl bg-brand-soft p-5">
        <p className="flex items-center gap-2 font-bold">
          <Target className="size-5 text-brand-ink" aria-hidden /> Twój poziom:
          <Badge tone="brand" className="text-sm">
            {run.data.level}
          </Badge>
        </p>
        <p className="text-sm">{run.data.explanation}</p>
        <ul className="list-disc pl-5 text-sm text-ink-soft">
          {run.data.next_steps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ul>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <label className="flex flex-col gap-2">
        <span className="text-sm font-semibold">1. Przetłumacz na angielski:</span>
        <span className="rounded-2xl bg-surface-raised p-3 font-medium ring-1 ring-line">
          {questions.data.translation_source}
        </span>
        <textarea rows={2} className={textareaClass} value={translation} onChange={(e) => setTranslation(e.target.value)} />
      </label>
      <label className="flex flex-col gap-2">
        <span className="text-sm font-semibold">2. Popraw błąd w zdaniu:</span>
        <span className="rounded-2xl bg-surface-raised p-3 font-medium ring-1 ring-line">
          {questions.data.correction_source}
        </span>
        <textarea rows={2} className={textareaClass} value={correction} onChange={(e) => setCorrection(e.target.value)} />
      </label>
      {run.isError && <ErrorState error={run.error} />}
      <Button onClick={() => run.mutate()} disabled={run.isPending || !translation.trim() || !correction.trim()}>
        <Bot className="size-4" aria-hidden /> {run.isPending ? "AI ocenia…" : "Sprawdź mój poziom"}
      </Button>
    </div>
  );
}
