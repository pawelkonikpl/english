import { useMutation, useQuery } from "@tanstack/react-query";
import { BookOpen, ChevronRight, PenLine, Sparkles, SpellCheck2, Target } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";

import { api, queryKeys } from "@/shared/api/endpoints";
import type { LessonType } from "@/shared/api/schemas";
import { cn } from "@/shared/lib/cn";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { PageHeader } from "@/shared/ui/page-header";
import { ErrorState, Spinner } from "@/shared/ui/states";

type CreatableType = Exclude<LessonType, "placement">;

export const LESSON_TYPES: Record<CreatableType, { title: string; description: string; icon: typeof BookOpen; accent: string }> = {
  vocabulary: {
    title: "Słówka",
    description: "5 nowych słów z wymową, skojarzeniem i przykładami, potem ćwiczenia.",
    icon: BookOpen,
    accent: "from-[#2a78d6] to-[#6d4aff]",
  },
  grammar: {
    title: "Gramatyka",
    description: "Krótkie wyjaśnienie po polsku, przykłady i 5 ćwiczeń.",
    icon: SpellCheck2,
    accent: "from-[#6d4aff] to-[#c04dff]",
  },
  writing: {
    title: "Swobodne pisanie",
    description: "Napisz krótki tekst, a AI oceni go i poprawi błędy.",
    icon: PenLine,
    accent: "from-[#c04dff] to-[#ff7a59]",
  },
};

const dateFormat = new Intl.DateTimeFormat("pl-PL", { day: "numeric", month: "short" });

export function LessonsPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const suggested = params.get("type");
  const [topic, setTopic] = useState("");
  const history = useQuery({ queryKey: queryKeys.lessons, queryFn: api.lessons });
  const create = useMutation({
    mutationFn: (type: CreatableType) => api.createLesson(type, topic.trim()),
    onSuccess: (lesson) => void navigate(`/lessons/${lesson.id}`),
  });

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Lekcje z AI" subtitle="AI przygotuje lekcję dopasowaną do Twojego poziomu i celów." />

      <label className="flex flex-col gap-1.5 text-sm font-semibold">
        Temat (opcjonalnie)
        <input
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="np. spotkania w pracy, podróże, Present Perfect… Puste = AI wybierze sam"
          className="h-11 rounded-2xl bg-surface-raised px-4 font-normal ring-1 ring-line outline-none focus:ring-2 focus:ring-brand"
        />
      </label>

      {create.isPending && <Spinner label="AI przygotowuje lekcję… to może potrwać kilkanaście sekund." />}
      {create.isError && <ErrorState error={create.error} />}

      <div className="grid gap-4 md:grid-cols-3">
        {(Object.keys(LESSON_TYPES) as CreatableType[]).map((type, i) => {
          const info = LESSON_TYPES[type];
          const Icon = info.icon;
          return (
            <motion.div key={type} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
              <Card className={cn("flex h-full flex-col gap-4", suggested === type && "ring-2 ring-brand")}>
                <span className={cn("grid size-12 place-items-center rounded-2xl bg-gradient-to-br text-white shadow-lg", info.accent)}>
                  <Icon className="size-6" aria-hidden />
                </span>
                <div className="flex-1">
                  <h2 className="flex items-center gap-2 text-lg font-bold">
                    {info.title} {suggested === type && <Badge tone="brand">polecane</Badge>}
                  </h2>
                  <p className="mt-1 text-sm text-ink-soft">{info.description}</p>
                </div>
                <Button onClick={() => create.mutate(type)} disabled={create.isPending}>
                  <Sparkles className="size-4" aria-hidden /> Nowa lekcja
                </Button>
              </Card>
            </motion.div>
          );
        })}
      </div>

      <Link to="/lessons/placement">
        <Card className="flex items-center gap-4 p-4 transition hover:ring-brand/40">
          <Target className="size-6 text-brand-ink" aria-hidden />
          <div className="flex-1">
            <p className="font-semibold">Test poziomujący</p>
            <p className="text-sm text-ink-soft">Dwa krótkie zadania, AI ustali Twój poziom (A1–C2).</p>
          </div>
          <ChevronRight className="size-5 text-ink-muted" aria-hidden />
        </Card>
      </Link>

      {history.data && history.data.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-bold">Twoje lekcje</h2>
          <ul className="flex flex-col gap-2">
            {history.data.map((lesson) => {
              const info = lesson.type === "placement" ? null : LESSON_TYPES[lesson.type];
              return (
                <li key={lesson.id}>
                  <Link
                    to={`/lessons/${lesson.id}`}
                    className="flex items-center gap-3 rounded-2xl bg-surface-raised p-4 ring-1 ring-line transition hover:ring-brand/40"
                  >
                    <div className="flex-1">
                      <p className="font-semibold">{lesson.topic}</p>
                      <p className="text-xs text-ink-muted">
                        {info?.title} · {dateFormat.format(new Date(lesson.created_at))}
                      </p>
                    </div>
                    {lesson.status === "completed" ? (
                      <Badge tone="good">
                        {lesson.score}/{lesson.max_score}
                      </Badge>
                    ) : (
                      <Badge tone="brand">w trakcie</Badge>
                    )}
                    <ChevronRight className="size-5 text-ink-muted" aria-hidden />
                  </Link>
                </li>
              );
            })}
          </ul>
        </section>
      )}
    </div>
  );
}
