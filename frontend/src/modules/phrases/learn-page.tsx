import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Check, PartyPopper, Repeat, Sparkles } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router";

import { api } from "@/shared/api/endpoints";
import type { Phrase } from "@/shared/api/schemas";
import { celebrate } from "@/shared/lib/celebrate";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Kbd } from "@/shared/ui/kbd";
import { EmptyState, ErrorState, Spinner } from "@/shared/ui/states";

import { SpeakButton } from "./speak-button";
import { useInvalidateLearning } from "./use-invalidate-learning";

// A key outside "phrases" so invalidations during the run do not reshuffle the queue.
const RUN_KEY = ["learn-run"] as const;

function LearnCard({ phrase }: { phrase: Phrase }) {
  return (
    <motion.div
      key={phrase.id}
      initial={{ opacity: 0, x: 60, rotate: 2 }}
      animate={{ opacity: 1, x: 0, rotate: 0 }}
      exit={{ opacity: 0, x: -60, rotate: -2 }}
      transition={{ type: "spring", stiffness: 260, damping: 26 }}
      className="relative overflow-hidden rounded-[2rem] bg-surface-raised p-8 text-center shadow-xl ring-1 ring-line sm:p-12"
    >
      <div className="absolute inset-x-0 top-0 h-1.5 bg-brand-gradient" aria-hidden />
      <Badge tone="brand">{phrase.section_title}</Badge>
      <div className="mt-6 flex items-center justify-center gap-2">
        <h2 className="text-2xl leading-tight font-extrabold sm:text-4xl">{phrase.english}</h2>
        <SpeakButton text={phrase.english} />
      </div>
      <p className="mt-3 text-lg text-ink-soft sm:text-xl">{phrase.polish}</p>
      {phrase.example && <p className="mt-5 text-ink-muted italic">{phrase.example}</p>}
      {phrase.note && (
        <p className="mx-auto mt-4 max-w-md rounded-2xl bg-warning/15 px-4 py-2 text-sm">💡 {phrase.note}</p>
      )}
    </motion.div>
  );
}

export function LearnPage() {
  const run = useQuery({ queryKey: RUN_KEY, queryFn: api.learnSession, gcTime: 0, staleTime: Infinity });
  const invalidate = useInvalidateLearning();
  const [index, setIndex] = useState(0);
  const [learned, setLearned] = useState(0);

  const enroll = useMutation({
    mutationFn: ({ id, known }: { id: number; known: boolean }) => api.enrollPhrase(id, known),
    onSuccess: () => {
      invalidate();
      setLearned((n) => n + 1);
      setIndex((i) => i + 1);
    },
  });

  const queue = run.data?.phrases ?? [];
  const current = queue[index];
  const finished = run.data !== undefined && queue.length > 0 && index >= queue.length;

  const choose = useCallback(
    (known: boolean) => {
      if (current && !enroll.isPending) enroll.mutate({ id: current.id, known });
    },
    [current, enroll],
  );

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "1") choose(true);
      if (event.key === "2" || event.key === "Enter") choose(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [choose]);

  useEffect(() => {
    if (finished) celebrate();
  }, [finished]);

  if (run.isPending) return <Spinner />;
  if (run.isError) return <ErrorState error={run.error} onRetry={() => void run.refetch()} />;

  if (queue.length === 0) {
    return (
      <EmptyState icon={<Check className="size-8" />} title="Na dziś wystarczy nowych fraz">
        <p>
          Dzienny limit to {run.data.daily_limit} nowych fraz. Teraz najlepiej utrwalić to, co już
          znasz.
        </p>
        <Link to="/review" className="mt-4 inline-block">
          <Button>
            <Repeat className="size-4" aria-hidden /> Przejdź do powtórek
          </Button>
        </Link>
      </EmptyState>
    );
  }

  if (finished) {
    return (
      <EmptyState icon={<PartyPopper className="size-8" />} title="Świetna robota!">
        <p>Dodano {learned} fraz do powtórek. Pierwsza powtórka czeka już dziś.</p>
        <div className="mt-5 flex flex-wrap justify-center gap-2">
          <Link to="/review">
            <Button>
              <Repeat className="size-4" aria-hidden /> Powtórz teraz
            </Button>
          </Link>
          <Link to="/">
            <Button variant="secondary">Wróć na start</Button>
          </Link>
        </div>
      </EmptyState>
    );
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div className="flex items-center gap-4">
        <Link to="/phrases" aria-label="Wróć do fraz" className="text-ink-soft hover:text-ink">
          <ArrowLeft className="size-5" aria-hidden />
        </Link>
        <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-surface-sunken">
          <motion.div
            className="h-full rounded-full bg-brand-gradient"
            animate={{ width: `${(index / queue.length) * 100}%` }}
            transition={{ type: "spring", stiffness: 120, damping: 20 }}
          />
        </div>
        <span className="text-sm font-semibold text-ink-muted tabular-nums">
          {index + 1}/{queue.length}
        </span>
      </div>

      <AnimatePresence mode="wait">{current && <LearnCard phrase={current} />}</AnimatePresence>

      {enroll.isError && <ErrorState error={enroll.error} />}

      <div className="grid grid-cols-2 gap-3">
        <Button variant="secondary" size="lg" onClick={() => choose(true)} disabled={enroll.isPending}>
          <Check className="size-5" aria-hidden /> Znam to <Kbd>1</Kbd>
        </Button>
        <Button size="lg" onClick={() => choose(false)} disabled={enroll.isPending}>
          <Sparkles className="size-5" aria-hidden /> Uczę się <Kbd>2</Kbd>
        </Button>
      </div>
      <p className="text-center text-xs text-ink-muted">
        „Znam to” odkłada frazę na 3 dni, „Uczę się” dodaje ją do dzisiejszych powtórek.
      </p>
    </div>
  );
}
