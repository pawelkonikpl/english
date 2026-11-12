import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Bot, CheckCircle2, Flag, Lightbulb, ThumbsUp, XCircle } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router";

import { SpeakButton } from "@/modules/phrases/speak-button";
import { useInvalidateLearning } from "@/modules/phrases/use-invalidate-learning";
import { api, queryKeys } from "@/shared/api/endpoints";
import type { Exercise, Lesson } from "@/shared/api/schemas";
import { celebrate } from "@/shared/lib/celebrate";
import { cn } from "@/shared/lib/cn";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { ProgressRing } from "@/shared/ui/progress-ring";
import { ErrorState, Spinner } from "@/shared/ui/states";

import { LESSON_TYPES } from "./lessons-page";

function useLessonUpdate(id: number) {
  const queryClient = useQueryClient();
  const invalidate = useInvalidateLearning();
  return (lesson: Lesson) => {
    queryClient.setQueryData(queryKeys.lesson(id), lesson);
    void queryClient.invalidateQueries({ queryKey: queryKeys.lessons });
    invalidate();
    if (lesson.status === "completed") celebrate();
  };
}

function ExerciseResult({ exercise }: { exercise: Exercise }) {
  const result = exercise.result;
  if (!result) return null;
  return (
    <div className={cn("flex flex-col gap-1 rounded-2xl p-4", result.correct ? "bg-good/12" : "bg-critical/10")}>
      <p className={cn("flex items-center gap-2 font-semibold", result.correct ? "text-good" : "text-critical")}>
        {result.correct ? <CheckCircle2 className="size-5" aria-hidden /> : <XCircle className="size-5" aria-hidden />}
        {result.correct ? "Dobrze! +2 XP" : "Nie tym razem"}
      </p>
      {!result.correct && (
        <p className="text-sm">
          Twoja odpowiedź: <span className="line-through">{result.answer}</span> · Poprawnie:{" "}
          <strong>{result.expected}</strong>
        </p>
      )}
      {result.explanation && <p className="text-sm text-ink-soft">{result.explanation}</p>}
    </div>
  );
}

function Exercises({ lesson }: { lesson: Lesson }) {
  const update = useLessonUpdate(lesson.id);
  const firstOpen = lesson.exercises.findIndex((e) => !e.result);
  const [shown, setShown] = useState(firstOpen === -1 ? lesson.exercises.length : firstOpen);
  const [answer, setAnswer] = useState("");
  const submit = useMutation({
    mutationFn: (index: number) => api.answerExercise(lesson.id, index, answer),
    onSuccess: (data) => {
      update(data);
      setAnswer("");
    },
  });
  const complete = useMutation({ mutationFn: () => api.completeLesson(lesson.id), onSuccess: update });

  const exercise = lesson.exercises[shown];
  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (exercise && answer.trim()) submit.mutate(exercise.index);
  };

  if (!exercise) {
    return (
      <Card className="flex flex-col items-center gap-4 text-center">
        <p className="text-lg font-bold">Wszystkie ćwiczenia zrobione!</p>
        <Button size="lg" onClick={() => complete.mutate()} disabled={complete.isPending}>
          <Flag className="size-5" aria-hidden /> Zakończ lekcję
        </Button>
        {complete.isError && <ErrorState error={complete.error} />}
      </Card>
    );
  }

  return (
    <Card className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <Badge tone="brand">
          Ćwiczenie {shown + 1}/{lesson.exercises.length}
        </Badge>
        <div className="flex gap-1">
          {lesson.exercises.map((e) => (
            <span
              key={e.index}
              className={cn(
                "size-2.5 rounded-full",
                e.result ? (e.result.correct ? "bg-good" : "bg-critical") : e.index === shown ? "bg-brand" : "bg-surface-sunken",
              )}
            />
          ))}
        </div>
      </div>
      <AnimatePresence mode="wait">
        <motion.div
          key={shown}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          className="flex flex-col gap-4"
        >
          <p className="text-sm font-semibold text-ink-soft">{exercise.instruction}</p>
          <p className="text-xl font-bold">{exercise.prompt}</p>
          {exercise.hint && (
            <p className="flex items-center gap-1.5 text-sm text-ink-muted">
              <Lightbulb className="size-4" aria-hidden /> {exercise.hint}
            </p>
          )}
          {exercise.result ? (
            <>
              <ExerciseResult exercise={exercise} />
              <Button className="w-fit" onClick={() => setShown((s) => s + 1)}>
                Dalej <ArrowRight className="size-4" aria-hidden />
              </Button>
            </>
          ) : (
            <form onSubmit={onSubmit} className="flex flex-col gap-3 sm:flex-row">
              <input
                autoFocus
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Twoja odpowiedź…"
                aria-label="Odpowiedź"
                className="h-12 flex-1 rounded-2xl bg-surface-sunken px-4 text-lg outline-none focus:ring-2 focus:ring-brand"
                autoComplete="off"
              />
              <Button type="submit" size="lg" disabled={!answer.trim() || submit.isPending}>
                {submit.isPending ? "Sprawdzam…" : "Sprawdź"}
              </Button>
            </form>
          )}
          {submit.isError && <ErrorState error={submit.error} />}
        </motion.div>
      </AnimatePresence>
    </Card>
  );
}

function CompletedSummary({ lesson }: { lesson: Lesson }) {
  return (
    <Card className="flex flex-wrap items-center gap-5">
      <ProgressRing
        value={lesson.score ?? 0}
        max={lesson.max_score ?? 1}
        size={110}
        stroke={10}
        label={`Wynik ${lesson.score} na ${lesson.max_score}`}
      >
        <p className="text-xl font-extrabold">
          {lesson.score}/{lesson.max_score}
        </p>
      </ProgressRing>
      <div className="flex-1">
        <h2 className="text-xl font-extrabold">Lekcja ukończona!</h2>
        <p className="text-sm text-ink-soft">
          {lesson.type === "vocabulary"
            ? "Słówka z tej lekcji czekają już w powtórkach."
            : "Świetnie, utrwal to w kolejnej lekcji albo rozmowie."}
        </p>
        <Link to="/lessons" className="mt-3 inline-block">
          <Button>Kolejna lekcja</Button>
        </Link>
      </div>
    </Card>
  );
}

function VocabularyLesson({ lesson }: { lesson: Lesson }) {
  const [practising, setPractising] = useState(lesson.exercises.some((e) => e.result));
  if (!practising && lesson.status !== "completed") {
    return (
      <div className="flex flex-col gap-4">
        <div className="grid gap-3 sm:grid-cols-2">
          {lesson.words.map((w, i) => (
            <motion.div key={w.word} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}>
              <Card className="flex h-full flex-col gap-2">
                <div className="flex items-center gap-1">
                  <h3 className="text-xl font-extrabold">{w.word}</h3>
                  <SpeakButton text={w.word} />
                  <span className="ml-auto font-mono text-sm text-ink-muted">{w.phonetic}</span>
                </div>
                <p className="font-medium text-ink-soft">{w.translation}</p>
                <p className="rounded-xl bg-warning/15 px-3 py-2 text-sm">🧠 {w.mnemonic}</p>
                <ul className="flex flex-col gap-1 text-sm text-ink-soft italic">
                  {w.examples.map((ex) => (
                    <li key={ex}>{ex}</li>
                  ))}
                </ul>
              </Card>
            </motion.div>
          ))}
        </div>
        <Button size="lg" className="w-fit" onClick={() => setPractising(true)}>
          Do ćwiczeń <ArrowRight className="size-5" aria-hidden />
        </Button>
      </div>
    );
  }
  return lesson.status === "completed" ? <CompletedSummary lesson={lesson} /> : <Exercises lesson={lesson} />;
}

function GrammarLesson({ lesson }: { lesson: Lesson }) {
  return (
    <div className="flex flex-col gap-4">
      <Card className="flex flex-col gap-4">
        <p className="leading-relaxed whitespace-pre-line">{lesson.explanation}</p>
        <ul className="flex flex-col gap-2">
          {lesson.examples.map((ex) => (
            <li key={ex.english} className="rounded-2xl bg-surface-sunken p-3">
              <div className="flex items-center gap-1">
                <p className="font-semibold">{ex.english}</p>
                <SpeakButton text={ex.english} />
              </div>
              <p className="text-sm text-ink-soft">{ex.note}</p>
            </li>
          ))}
        </ul>
      </Card>
      {lesson.status === "completed" ? <CompletedSummary lesson={lesson} /> : <Exercises lesson={lesson} />}
    </div>
  );
}

function WritingLesson({ lesson }: { lesson: Lesson }) {
  const update = useLessonUpdate(lesson.id);
  const [text, setText] = useState(lesson.writing_text ?? "");
  const submit = useMutation({ mutationFn: () => api.submitWriting(lesson.id, text), onSuccess: update });
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  const task = lesson.writing;
  const feedback = lesson.writing_feedback;
  if (!task) return null;

  return (
    <div className="flex flex-col gap-4">
      <Card className="flex flex-col gap-3">
        <p className="text-lg font-bold">{task.prompt}</p>
        <p className="text-sm text-ink-soft">{task.instructions}</p>
        <div className="flex flex-wrap gap-2">
          {task.useful_phrases.map((p) => (
            <Badge key={p}>{p}</Badge>
          ))}
        </div>
      </Card>
      {feedback ? (
        <Card className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-5">
            <ProgressRing value={feedback.score} max={10} size={100} stroke={9} label={`Ocena ${feedback.score} na 10`}>
              <p className="text-xl font-extrabold">{feedback.score}/10</p>
            </ProgressRing>
            <ul className="flex flex-1 flex-col gap-1">
              {feedback.strengths.map((s) => (
                <li key={s} className="flex items-start gap-2 text-sm">
                  <ThumbsUp className="mt-0.5 size-4 shrink-0 text-good" aria-hidden /> {s}
                </li>
              ))}
            </ul>
          </div>
          {feedback.errors.length > 0 && (
            <ul className="flex flex-col gap-2">
              {feedback.errors.map((e, i) => (
                <li key={i} className="rounded-2xl bg-surface-sunken p-3 text-sm">
                  <span className="text-critical line-through">{e.fragment}</span>{" "}
                  <span className="font-semibold text-good">{e.correction}</span>
                  <p className="text-xs text-ink-soft">{e.explanation}</p>
                </li>
              ))}
            </ul>
          )}
          <div>
            <p className="mb-1 text-xs font-bold text-ink-muted uppercase">Poprawiona wersja</p>
            <p className="rounded-2xl bg-good/10 p-4 leading-relaxed whitespace-pre-line">{feedback.corrected_text}</p>
          </div>
          <Link to="/lessons">
            <Button>Kolejna lekcja</Button>
          </Link>
        </Card>
      ) : (
        <Card className="flex flex-col gap-3">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={10}
            placeholder="Napisz tutaj swój tekst po angielsku…"
            aria-label="Twój tekst"
            className="resize-y rounded-2xl bg-surface-sunken p-4 leading-relaxed outline-none focus:ring-2 focus:ring-brand"
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className={cn("text-sm font-semibold", words >= task.min_words ? "text-good" : "text-ink-muted")}>
              {words}/{task.min_words} słów
            </span>
            <Button onClick={() => submit.mutate()} disabled={submit.isPending || words === 0}>
              <Bot className="size-4" aria-hidden /> {submit.isPending ? "AI czyta Twój tekst…" : "Wyślij do oceny"}
            </Button>
          </div>
          {submit.isError && <ErrorState error={submit.error} />}
        </Card>
      )}
    </div>
  );
}

export function LessonPage() {
  const id = Number(useParams().id);
  const lesson = useQuery({ queryKey: queryKeys.lesson(id), queryFn: () => api.lesson(id) });
  if (lesson.isPending) return <Spinner />;
  if (lesson.isError) return <ErrorState error={lesson.error} onRetry={() => void lesson.refetch()} />;
  const data = lesson.data;
  const info = data.type === "placement" ? null : LESSON_TYPES[data.type];

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-5">
      <Link to="/lessons" className="inline-flex items-center gap-1 text-sm font-semibold text-ink-soft hover:text-ink">
        <ArrowLeft className="size-4" aria-hidden /> Lekcje
      </Link>
      <div>
        <div className="flex flex-wrap items-center gap-2">
          {info && <Badge tone="brand">{info.title}</Badge>}
          <Badge>Poziom {data.level}</Badge>
          {data.model && <span className="text-xs text-ink-muted">model: {data.model}</span>}
        </div>
        <h1 className="mt-2 text-2xl font-extrabold tracking-tight sm:text-3xl">{data.topic}</h1>
      </div>
      {data.type === "vocabulary" && <VocabularyLesson lesson={data} />}
      {data.type === "grammar" && <GrammarLesson lesson={data} />}
      {data.type === "writing" && <WritingLesson lesson={data} />}
    </div>
  );
}
