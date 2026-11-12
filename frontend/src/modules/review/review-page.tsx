import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Bot,
  Brain,
  CheckCircle2,
  Eye,
  Keyboard,
  PartyPopper,
  PenLine,
  Sparkles,
  XCircle,
} from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router";

import { SpeakButton } from "@/modules/phrases/speak-button";
import { useInvalidateLearning } from "@/modules/phrases/use-invalidate-learning";
import { api } from "@/shared/api/endpoints";
import type { DueItem, Grade, ReviewMode, SentenceCheck } from "@/shared/api/schemas";
import { celebrate } from "@/shared/lib/celebrate";
import { cn } from "@/shared/lib/cn";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Kbd } from "@/shared/ui/kbd";
import { PageHeader } from "@/shared/ui/page-header";
import { EmptyState, ErrorState, Spinner } from "@/shared/ui/states";

const RUN_KEY = ["review-run"] as const;

const MODES: { mode: ReviewMode; label: string; icon: typeof Eye; hint: string }[] = [
  { mode: "recognition", label: "Rozpoznawanie", icon: Eye, hint: "Widzisz angielski, przypominasz sobie znaczenie." },
  { mode: "recall", label: "Przypominanie", icon: Keyboard, hint: "Widzisz polski, wpisujesz angielski." },
  { mode: "sentence", label: "Zdanie z AI", icon: PenLine, hint: "Układasz własne zdanie, AI je sprawdza." },
];

const GRADES: { grade: Grade; label: string; key: string; className: string; xp: number }[] = [
  { grade: "again", label: "Nie pamiętam", key: "1", className: "bg-critical/12 text-critical ring-critical/30", xp: 0 },
  { grade: "hard", label: "Trudne", key: "2", className: "bg-warning/18 text-[#9a6700] ring-warning/40 dark:text-warning", xp: 0.5 },
  { grade: "good", label: "Dobrze", key: "3", className: "bg-good/12 text-good ring-good/30", xp: 1 },
  { grade: "easy", label: "Łatwe", key: "4", className: "bg-series-1/12 text-series-1 ring-series-1/30", xp: 1 },
];

type Answer =
  | { kind: "none" }
  | { kind: "recall"; correct: boolean; expected: string }
  | { kind: "sentence"; result: SentenceCheck };

function XpPop({ amount, id }: { amount: number; id: number }) {
  return (
    <AnimatePresence>
      {amount > 0 && (
        <motion.span
          key={id}
          className="pointer-events-none absolute -top-4 right-6 rounded-full bg-warning px-3 py-1 text-sm font-extrabold text-black shadow-lg"
          initial={{ opacity: 0, y: 10, scale: 0.8 }}
          animate={{ opacity: 1, y: -14, scale: 1 }}
          exit={{ opacity: 0, y: -30 }}
          transition={{ duration: 0.5 }}
        >
          +{amount} XP
        </motion.span>
      )}
    </AnimatePresence>
  );
}

function ReviewCard({
  item,
  mode,
  revealed,
  answer,
  onReveal,
  onAnswer,
}: {
  item: DueItem;
  mode: ReviewMode;
  revealed: boolean;
  answer: Answer;
  onReveal: () => void;
  onAnswer: (answer: Answer) => void;
}) {
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLInputElement & HTMLTextAreaElement>(null);
  const recall = useMutation({
    mutationFn: (value: string) => api.checkRecall(item.id, value),
    onSuccess: (r) => onAnswer({ kind: "recall", correct: r.correct, expected: r.expected }),
  });
  const sentence = useMutation({
    mutationFn: (value: string) => api.checkSentence(item.id, value),
    onSuccess: (r) => onAnswer({ kind: "sentence", result: r }),
  });

  useEffect(() => {
    inputRef.current?.focus();
  }, [item.id, mode]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!text.trim()) return;
    if (mode === "recall") recall.mutate(text);
    else sentence.mutate(text);
  };

  const showEnglish = mode !== "recall" || revealed;
  const showPolish = mode !== "recognition" || revealed;

  return (
    <div className="relative overflow-hidden rounded-[2rem] bg-surface-raised p-6 text-center shadow-xl ring-1 ring-line sm:p-10">
      <div className="absolute inset-x-0 top-0 h-1.5 bg-brand-gradient" aria-hidden />
      {item.card.label && <Badge tone="brand">{item.card.label}</Badge>}

      <div className="mt-5 min-h-28">
        {showEnglish && (
          <div className="flex items-center justify-center gap-2">
            <h2 className="text-2xl leading-tight font-extrabold sm:text-3xl">{item.card.front}</h2>
            <SpeakButton text={item.card.front} />
          </div>
        )}
        {showPolish && (
          <p className={cn("mt-3", mode === "recall" && !revealed ? "text-2xl font-bold" : "text-lg text-ink-soft")}>
            {item.card.back}
          </p>
        )}
        {revealed && item.card.example && <p className="mt-4 text-ink-muted italic">{item.card.example}</p>}
        {revealed && item.card.note && <p className="mt-2 text-sm text-ink-muted">💡 {item.card.note}</p>}
      </div>

      {mode === "recognition" && !revealed && (
        <Button size="lg" className="mt-6" onClick={onReveal}>
          <Eye className="size-5" aria-hidden /> Pokaż znaczenie <Kbd>Spacja</Kbd>
        </Button>
      )}

      {mode !== "recognition" && answer.kind === "none" && (
        <form onSubmit={submit} className="mx-auto mt-6 flex max-w-lg flex-col gap-3">
          {mode === "recall" ? (
            <input
              ref={inputRef}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Wpisz po angielsku…"
              aria-label="Twoja odpowiedź po angielsku"
              className="h-14 rounded-2xl bg-surface-sunken px-5 text-center text-lg font-semibold outline-none focus:ring-2 focus:ring-brand"
              autoComplete="off"
              spellCheck={false}
            />
          ) : (
            <textarea
              ref={inputRef}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Napisz własne zdanie z tą frazą…"
              aria-label="Twoje zdanie po angielsku"
              rows={3}
              className="resize-none rounded-2xl bg-surface-sunken p-4 text-base outline-none focus:ring-2 focus:ring-brand"
            />
          )}
          <Button type="submit" size="lg" disabled={recall.isPending || sentence.isPending || !text.trim()}>
            {mode === "sentence" ? <Bot className="size-5" aria-hidden /> : <CheckCircle2 className="size-5" aria-hidden />}
            {sentence.isPending ? "AI sprawdza…" : "Sprawdź"}
          </Button>
          {(recall.isError || sentence.isError) && <ErrorState error={recall.error ?? sentence.error} />}
        </form>
      )}

      {answer.kind === "recall" && (
        <div className={cn("mx-auto mt-6 flex max-w-lg items-center justify-center gap-2 rounded-2xl p-4 font-semibold", answer.correct ? "bg-good/12 text-good" : "bg-critical/12 text-critical")}>
          {answer.correct ? <CheckCircle2 className="size-5" aria-hidden /> : <XCircle className="size-5" aria-hidden />}
          {answer.correct ? "Dobrze!" : `Poprawnie: ${answer.expected}`}
        </div>
      )}

      {answer.kind === "sentence" && (
        <div className="mx-auto mt-6 flex max-w-lg flex-col gap-2 rounded-2xl bg-surface-sunken p-4 text-left">
          <p className={cn("flex items-center gap-2 font-semibold", answer.result.correct && answer.result.uses_phrase ? "text-good" : "text-critical")}>
            {answer.result.correct && answer.result.uses_phrase ? <CheckCircle2 className="size-5" aria-hidden /> : <XCircle className="size-5" aria-hidden />}
            {answer.result.correct && answer.result.uses_phrase ? "Świetne zdanie!" : "Prawie! Zobacz poprawkę:"}
          </p>
          {!(answer.result.correct && answer.result.uses_phrase) && <p className="font-medium">{answer.result.corrected_sentence}</p>}
          <p className="text-sm text-ink-soft">{answer.result.explanation}</p>
        </div>
      )}
    </div>
  );
}

export function ReviewPage() {
  const run = useQuery({ queryKey: RUN_KEY, queryFn: () => api.reviewDue(50), gcTime: 0, staleTime: Infinity });
  if (run.isPending) return <Spinner />;
  if (run.isError) return <ErrorState error={run.error} onRetry={() => void run.refetch()} />;
  return <ReviewSession initialQueue={run.data} />;
}

function ReviewSession({ initialQueue }: { initialQueue: DueItem[] }) {
  const invalidate = useInvalidateLearning();
  const [mode, setMode] = useState<ReviewMode>("recognition");
  const [queue, setQueue] = useState<DueItem[]>(initialQueue);
  const [revealed, setRevealed] = useState(false);
  const [answer, setAnswer] = useState<Answer>({ kind: "none" });
  const [stats, setStats] = useState({ done: 0, good: 0, xp: 0 });
  const [pop, setPop] = useState({ amount: 0, id: 0 });

  const current = queue?.[0];
  const canGrade = mode === "recognition" ? revealed : answer.kind !== "none";
  const finished = queue.length === 0 && stats.done > 0;

  const grade = useMutation({
    mutationFn: ({ item, value }: { item: DueItem; value: Grade }) => api.grade(item.id, value, mode),
    onSuccess: (result, { item, value }) => {
      const xp = GRADES.find((g) => g.grade === value)?.xp ?? 0;
      setPop((p) => ({ amount: xp, id: p.id + 1 }));
      setStats((s) => ({ done: s.done + 1, good: s.good + (value === "good" || value === "easy" ? 1 : 0), xp: s.xp + xp }));
      setQueue((q) => {
        const rest = q.slice(1);
        return result.due_again_today ? [...rest, item] : rest;
      });
      setRevealed(false);
      setAnswer({ kind: "none" });
      invalidate();
    },
  });

  const submitGrade = useCallback(
    (value: Grade) => {
      if (current && canGrade && !grade.isPending) grade.mutate({ item: current, value });
    },
    [current, canGrade, grade],
  );

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") return;
      if (event.key === " " && mode === "recognition" && !revealed) {
        event.preventDefault();
        setRevealed(true);
      }
      const match = GRADES.find((g) => g.key === event.key);
      if (match) submitGrade(match.grade);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mode, revealed, submitGrade]);

  useEffect(() => {
    if (finished) celebrate();
  }, [finished]);

  if (finished) {
    const accuracy = Math.round((stats.good / Math.max(stats.done, 1)) * 100);
    return (
      <EmptyState icon={<PartyPopper className="size-8" />} title="Powtórki zrobione!">
        <p>
          {stats.done} odpowiedzi · {accuracy}% dobrze · +{Math.floor(stats.xp)} XP
        </p>
        <Link to="/" className="mt-5 inline-block">
          <Button>Wróć na start</Button>
        </Link>
      </EmptyState>
    );
  }

  if (!current) {
    return (
      <EmptyState icon={<Brain className="size-8" />} title="Brak powtórek na dziś">
        <p>Wszystko powtórzone. Możesz poznać nowe frazy.</p>
        <Link to="/phrases/learn" className="mt-5 inline-block">
          <Button>
            <Sparkles className="size-4" aria-hidden /> Ucz się nowych fraz
          </Button>
        </Link>
      </EmptyState>
    );
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-5">
      <PageHeader title="Powtórki" subtitle={`Zostało: ${queue.length}`} />

      <div className="grid grid-cols-3 gap-2 rounded-2xl bg-surface-sunken p-1.5" role="tablist" aria-label="Tryb powtórek">
        {MODES.map(({ mode: m, label, icon: Icon }) => (
          <button
            key={m}
            type="button"
            role="tab"
            aria-selected={mode === m}
            onClick={() => {
              setMode(m);
              setRevealed(false);
              setAnswer({ kind: "none" });
            }}
            className={cn(
              "flex items-center justify-center gap-1.5 rounded-xl px-2 py-2.5 text-xs font-semibold transition sm:text-sm",
              mode === m ? "bg-surface-raised text-ink shadow-sm" : "text-ink-muted hover:text-ink",
            )}
          >
            <Icon className="size-4" aria-hidden />
            <span className="truncate">{label}</span>
          </button>
        ))}
      </div>
      <p className="-mt-2 text-center text-xs text-ink-muted">{MODES.find((m) => m.mode === mode)?.hint}</p>

      <div className="relative">
        <XpPop amount={pop.amount} id={pop.id} />
        <AnimatePresence mode="wait">
          <motion.div
            key={`${current.id}-${stats.done}`}
            initial={{ opacity: 0, rotateY: -12, y: 10 }}
            animate={{ opacity: 1, rotateY: 0, y: 0 }}
            exit={{ opacity: 0, rotateY: 12, y: -10 }}
            transition={{ duration: 0.25 }}
          >
            <ReviewCard
              item={current}
              mode={mode}
              revealed={revealed}
              answer={answer}
              onReveal={() => setRevealed(true)}
              onAnswer={(a) => {
                setAnswer(a);
                setRevealed(true);
              }}
            />
          </motion.div>
        </AnimatePresence>
      </div>

      <div className={cn("grid grid-cols-2 gap-2 transition sm:grid-cols-4", !canGrade && "pointer-events-none opacity-40")}>
        {GRADES.map((g) => (
          <button
            key={g.grade}
            type="button"
            disabled={!canGrade || grade.isPending}
            onClick={() => submitGrade(g.grade)}
            className={cn(
              "flex h-14 items-center justify-center gap-2 rounded-2xl text-sm font-bold ring-1 transition hover:-translate-y-0.5 focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none",
              g.className,
            )}
          >
            {g.label} <Kbd>{g.key}</Kbd>
          </button>
        ))}
      </div>
      {grade.isError && <ErrorState error={grade.error} />}
    </div>
  );
}
