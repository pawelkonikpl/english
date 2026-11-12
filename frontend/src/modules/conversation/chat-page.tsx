import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Check,
  CheckCircle2,
  Flag,
  Lightbulb,
  Plus,
  SendHorizonal,
  Sparkles,
  ThumbsUp,
} from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { Link, useParams } from "react-router";

import { SpeakButton } from "@/modules/phrases/speak-button";
import { useInvalidateLearning } from "@/modules/phrases/use-invalidate-learning";
import { api, queryKeys } from "@/shared/api/endpoints";
import type { ChatMessage, Conversation, HintList } from "@/shared/api/schemas";
import { celebrate } from "@/shared/lib/celebrate";
import { cn } from "@/shared/lib/cn";
import { plural } from "@/shared/lib/plural";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { ProgressRing } from "@/shared/ui/progress-ring";
import { ErrorState, Spinner } from "@/shared/ui/states";

const HINT_LABELS = { easy: "Prosto", medium: "Średnio", advanced: "Ambitnie" } as const;

function Feedback({ message }: { message: ChatMessage }) {
  const [open, setOpen] = useState(false);
  const feedback = message.feedback;
  if (!feedback) return null;
  const count = feedback.corrections.length;
  if (count === 0 && feedback.better_alternatives.length === 0) {
    return (
      <p className="mt-1 flex items-center justify-end gap-1 text-xs font-semibold text-good">
        <CheckCircle2 className="size-3.5" aria-hidden /> Bez błędów
      </p>
    );
  }
  return (
    <div className="mt-1 flex flex-col items-end">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex items-center gap-1 rounded-full bg-warning/20 px-2.5 py-1 text-xs font-semibold text-ink"
      >
        <Lightbulb className="size-3.5 text-[#b67a00]" aria-hidden />
        {count > 0
          ? `${count} ${plural(count, "poprawka", "poprawki", "poprawek")}`
          : "Jak powiedzieć naturalniej"}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-2 w-full max-w-md overflow-hidden rounded-2xl bg-surface-sunken p-3 text-left text-sm"
          >
            {feedback.corrections.map((c, i) => (
              <div key={i} className="mb-2 last:mb-0">
                <p>
                  <span className="text-critical line-through">{c.original}</span>{" "}
                  <span className="font-semibold text-good">{c.corrected}</span>
                </p>
                <p className="text-xs text-ink-soft">{c.explanation}</p>
              </div>
            ))}
            {feedback.better_alternatives.length > 0 && (
              <div className="mt-2 border-t border-line pt-2">
                <p className="text-xs font-bold text-ink-muted">Naturalniej:</p>
                {feedback.better_alternatives.map((a) => (
                  <p key={a} className="italic">
                    {a}
                  </p>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Bubble({ message, pending }: { message: ChatMessage; pending?: boolean }) {
  const mine = message.role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className={cn("flex flex-col", mine ? "items-end" : "items-start")}
    >
      <div
        className={cn(
          "flex max-w-[85%] items-start gap-1 rounded-3xl px-4 py-3 text-[15px] leading-relaxed sm:max-w-[75%]",
          mine
            ? "rounded-br-lg bg-brand-gradient text-white shadow-md shadow-brand/20"
            : "rounded-bl-lg bg-surface-raised ring-1 ring-line",
          pending && "opacity-70",
        )}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {!mine && <SpeakButton text={message.content} className="-my-1 -mr-2 size-8" />}
      </div>
      {mine && <Feedback message={message} />}
    </motion.div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex w-fit gap-1 rounded-3xl rounded-bl-lg bg-surface-raised px-4 py-4 ring-1 ring-line" aria-label="AI pisze">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="size-2 rounded-full bg-ink-muted"
          animate={{ y: [0, -4, 0] }}
          transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
        />
      ))}
    </div>
  );
}

function Summary({ conversation }: { conversation: Conversation }) {
  const invalidate = useInvalidateLearning();
  const [added, setAdded] = useState<Set<string>>(new Set());
  const add = useMutation({
    mutationFn: ({ english, polish }: { english: string; polish: string }) =>
      api.addConversationPhrase(conversation.id, english, polish),
    onSuccess: (_, { english }) => {
      setAdded((s) => new Set(s).add(english));
      invalidate();
    },
  });
  const summary = conversation.summary;
  if (!summary) return null;

  return (
    <Card className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-5">
        <ProgressRing value={summary.score} max={10} size={110} stroke={10} label={`Wynik ${summary.score} na 10`}>
          <p className="text-2xl font-extrabold">{summary.score}/10</p>
        </ProgressRing>
        <div className="flex-1">
          <h2 className="text-xl font-extrabold">Podsumowanie rozmowy</h2>
          <ul className="mt-2 flex flex-col gap-1">
            {summary.strengths.map((s) => (
              <li key={s} className="flex items-start gap-2 text-sm">
                <ThumbsUp className="mt-0.5 size-4 shrink-0 text-good" aria-hidden /> {s}
              </li>
            ))}
          </ul>
        </div>
      </div>
      {summary.mistakes.length > 0 && (
        <section>
          <h3 className="mb-2 text-sm font-bold text-ink-muted">Do poprawy</h3>
          <ul className="flex flex-col gap-2">
            {summary.mistakes.map((m, i) => (
              <li key={i} className="rounded-2xl bg-surface-sunken p-3 text-sm">
                <p>
                  <span className="text-critical line-through">{m.original}</span>{" "}
                  <span className="font-semibold text-good">{m.corrected}</span>
                </p>
                <p className="text-xs text-ink-soft">{m.explanation}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
      {summary.new_phrases.length > 0 && (
        <section>
          <h3 className="mb-2 text-sm font-bold text-ink-muted">Warto się nauczyć</h3>
          <ul className="flex flex-col gap-2">
            {summary.new_phrases.map((p) => (
              <li key={p.english} className="flex items-center gap-3 rounded-2xl bg-brand-soft p-3">
                <div className="flex-1">
                  <p className="font-semibold">{p.english}</p>
                  <p className="text-sm text-ink-soft">{p.polish}</p>
                </div>
                <SpeakButton text={p.english} />
                {added.has(p.english) ? (
                  <Badge tone="good">
                    <Check className="size-3.5" aria-hidden /> W powtórkach
                  </Badge>
                ) : (
                  <Button size="sm" variant="secondary" onClick={() => add.mutate(p)} disabled={add.isPending}>
                    <Plus className="size-4" aria-hidden /> Do powtórek
                  </Button>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
      <Link to="/conversation">
        <Button>
          <Sparkles className="size-4" aria-hidden /> Nowa rozmowa
        </Button>
      </Link>
    </Card>
  );
}

export function ChatPage() {
  const id = Number(useParams().id);
  const queryClient = useQueryClient();
  const invalidate = useInvalidateLearning();
  const conversation = useQuery({ queryKey: queryKeys.conversation(id), queryFn: () => api.conversation(id) });
  const [draft, setDraft] = useState("");
  const [pendingText, setPendingText] = useState<string | null>(null);
  const [hints, setHints] = useState<HintList | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const send = useMutation({
    mutationFn: (content: string) => api.sendMessage(id, content),
    onMutate: (content) => {
      setPendingText(content);
      setDraft("");
      setHints(null);
    },
    onSuccess: ({ user_message, assistant_message }) => {
      queryClient.setQueryData<Conversation>(queryKeys.conversation(id), (old) =>
        old ? { ...old, messages: [...old.messages, user_message, assistant_message] } : old,
      );
    },
    onError: (_, content) => setDraft(content),
    onSettled: () => setPendingText(null),
  });
  const hint = useMutation({ mutationFn: () => api.hint(id), onSuccess: setHints });
  const finish = useMutation({
    mutationFn: () => api.finishConversation(id),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.conversation(id), data);
      void queryClient.invalidateQueries({ queryKey: queryKeys.conversations });
      invalidate();
      celebrate();
    },
  });

  const messageCount = conversation.data?.messages.length ?? 0;
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messageCount, pendingText, hints]);

  if (conversation.isPending) return <Spinner />;
  if (conversation.isError) return <ErrorState error={conversation.error} onRetry={() => void conversation.refetch()} />;
  const data = conversation.data;
  const active = data.status === "active";
  const used = new Set(data.messages.flatMap((m) => m.feedback?.used_target_phrases ?? []).map((p) => p.toLowerCase()));
  const lastModel = [...data.messages].reverse().find((m) => m.role === "assistant")?.model;

  const submit = (event?: FormEvent) => {
    event?.preventDefault();
    const content = draft.trim();
    if (content && !send.isPending) send.mutate(content);
  };
  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <Link to="/conversation" aria-label="Wróć do scenek" className="text-ink-soft hover:text-ink">
          <ArrowLeft className="size-5" aria-hidden />
        </Link>
        <span className="text-3xl" aria-hidden>
          {data.emoji}
        </span>
        <div className="flex-1">
          <h1 className="text-xl font-extrabold">{data.title}</h1>
          <p className="text-xs text-ink-muted">
            Poziom {data.level}
            {lastModel && ` · model: ${lastModel}`}
            {data.topic && ` · temat: ${data.topic}`}
          </p>
        </div>
        {active && (
          <Button variant="secondary" size="sm" onClick={() => finish.mutate()} disabled={finish.isPending || send.isPending}>
            <Flag className="size-4" aria-hidden /> {finish.isPending ? "Oceniam…" : "Zakończ"}
          </Button>
        )}
      </div>

      {data.target_phrases.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {data.target_phrases.map((p) => (
            <Badge key={p.id} tone={used.has(p.english.toLowerCase()) ? "good" : "neutral"} title={p.polish}>
              {used.has(p.english.toLowerCase()) && <Check className="size-3" aria-hidden />}
              {p.english}
            </Badge>
          ))}
        </div>
      )}

      <div className="flex flex-col gap-3 rounded-[2rem] bg-surface-sunken/60 p-3 sm:p-5" aria-live="polite">
        {data.messages.map((m) => (
          <Bubble key={m.id} message={m} />
        ))}
        {pendingText && (
          <>
            <Bubble
              pending
              message={{ id: -1, role: "user", content: pendingText, feedback: null, model: null, created_at: "" }}
            />
            <TypingIndicator />
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {send.isError && <ErrorState error={send.error} />}
      {finish.isError && <ErrorState error={finish.error} />}

      {active ? (
        <div className="sticky bottom-20 flex flex-col gap-2 lg:bottom-4">
          <AnimatePresence>
            {hints && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="grid gap-2 sm:grid-cols-3"
              >
                {hints.suggestions.map((h) => (
                  <button
                    key={h.text}
                    type="button"
                    onClick={() => setDraft(h.text)}
                    className="rounded-2xl bg-surface-raised p-3 text-left text-sm ring-1 ring-line transition hover:ring-brand"
                  >
                    <span className="text-[11px] font-bold text-brand-ink uppercase">{HINT_LABELS[h.level]}</span>
                    <p className="font-medium">{h.text}</p>
                    <p className="text-xs text-ink-muted">{h.translation}</p>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
          <form
            onSubmit={submit}
            className="flex items-end gap-2 rounded-3xl bg-surface-raised p-2 shadow-lg ring-1 ring-line"
          >
            <Button
              variant="ghost"
              size="sm"
              className="h-11"
              onClick={() => hint.mutate()}
              disabled={hint.isPending || send.isPending}
              aria-label="Podpowiedz mi, co odpowiedzieć"
              title="Podpowiedź"
            >
              <Lightbulb className={cn("size-5", hint.isPending && "animate-pulse")} aria-hidden />
            </Button>
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              placeholder="Napisz po angielsku… (Enter wysyła)"
              aria-label="Twoja wiadomość"
              className="max-h-40 min-h-11 flex-1 resize-none bg-transparent px-2 py-2.5 outline-none"
              disabled={send.isPending}
            />
            <Button type="submit" className="h-11 w-11 px-0" disabled={!draft.trim() || send.isPending} aria-label="Wyślij">
              <SendHorizonal className="size-5" aria-hidden />
            </Button>
          </form>
          {hint.isError && <ErrorState error={hint.error} />}
        </div>
      ) : (
        <Summary conversation={data} />
      )}
    </div>
  );
}
