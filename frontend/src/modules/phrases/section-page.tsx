import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Bot, Check, MessagesSquare, Plus } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { api, queryKeys } from "@/shared/api/endpoints";
import { useModuleEnabled } from "@/shared/api/use-modules";
import type { Phrase, PhraseStatus } from "@/shared/api/schemas";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { PageHeader } from "@/shared/ui/page-header";
import { ErrorState, Spinner } from "@/shared/ui/states";

import { ExplainPanel } from "./explain-panel";
import { SpeakButton } from "./speak-button";
import { useInvalidateLearning } from "./use-invalidate-learning";

const STATUS: Record<PhraseStatus, { label: string; tone: "neutral" | "warning" | "good" }> = {
  new: { label: "Nowa", tone: "neutral" },
  learning: { label: "W nauce", tone: "warning" },
  mastered: { label: "Opanowana", tone: "good" },
};

function PhraseRow({ phrase, onExplain }: { phrase: Phrase; onExplain: () => void }) {
  const invalidate = useInvalidateLearning();
  const enroll = useMutation({
    mutationFn: () => api.enrollPhrase(phrase.id, false),
    onSuccess: invalidate,
  });
  const status = STATUS[phrase.status];
  return (
    <li>
      <Card className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:p-5">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1">
            <p className="font-semibold">{phrase.english}</p>
            <SpeakButton text={phrase.english} />
          </div>
          <p className="text-ink-soft">{phrase.polish}</p>
          {phrase.example && <p className="mt-1 text-sm text-ink-muted italic">{phrase.example}</p>}
          {phrase.note && <p className="mt-1 text-sm text-ink-muted">💡 {phrase.note}</p>}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Badge tone={status.tone}>{status.label}</Badge>
          <Button variant="ghost" size="sm" onClick={onExplain}>
            <Bot className="size-4" aria-hidden /> Wyjaśnij
          </Button>
          {phrase.status === "new" ? (
            <Button variant="secondary" size="sm" onClick={() => enroll.mutate()} disabled={enroll.isPending}>
              <Plus className="size-4" aria-hidden /> Do nauki
            </Button>
          ) : (
            <Check className="size-5 text-good" aria-label="Już w nauce" />
          )}
        </div>
      </Card>
    </li>
  );
}

export function SectionPage() {
  const { code = "" } = useParams();
  const [explained, setExplained] = useState<Phrase | null>(null);
  const phrases = useQuery({
    queryKey: queryKeys.phrases(code),
    queryFn: () => api.phrases(code),
  });
  const title = phrases.data?.[0]?.section_title;
  const canPractise = useModuleEnabled("conversation");

  return (
    <div>
      <Link to="/phrases" className="mb-4 inline-flex items-center gap-1 text-sm font-semibold text-ink-soft hover:text-ink">
        <ArrowLeft className="size-4" aria-hidden /> Wszystkie sekcje
      </Link>
      <PageHeader
        title={title ?? code}
        subtitle={`Sekcja ${code}`}
        actions={
          canPractise && (
            <Link to={`/conversation?section=${encodeURIComponent(code)}`}>
              <Button variant="secondary">
                <MessagesSquare className="size-4" aria-hidden /> Przećwicz w rozmowie
              </Button>
            </Link>
          )
        }
      />
      {phrases.isPending && <Spinner />}
      {phrases.isError && <ErrorState error={phrases.error} onRetry={() => void phrases.refetch()} />}
      {phrases.data && (
        <ul className="flex flex-col gap-3">
          {phrases.data.map((phrase) => (
            <PhraseRow key={phrase.id} phrase={phrase} onExplain={() => setExplained(phrase)} />
          ))}
        </ul>
      )}
      <ExplainPanel phrase={explained} onClose={() => setExplained(null)} />
    </div>
  );
}
