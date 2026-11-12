import { useMutation, useQuery } from "@tanstack/react-query";
import { ChevronRight, MessagesSquare, Target } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";

import { api, queryKeys } from "@/shared/api/endpoints";
import type { Scenario } from "@/shared/api/schemas";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { PageHeader } from "@/shared/ui/page-header";
import { ErrorState, Spinner } from "@/shared/ui/states";

const dateFormat = new Intl.DateTimeFormat("pl-PL", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

export function ConversationPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const sectionCode = params.get("section") ?? undefined;
  const [topic, setTopic] = useState("");
  const scenarios = useQuery({ queryKey: queryKeys.scenarios, queryFn: api.scenarios, staleTime: Infinity });
  const recent = useQuery({ queryKey: queryKeys.conversations, queryFn: api.conversations });
  const targets = useQuery({
    queryKey: queryKeys.phrases(sectionCode),
    queryFn: () => api.phrases(sectionCode),
    enabled: sectionCode !== undefined,
  });

  const start = useMutation({
    mutationFn: (scenario: Scenario) =>
      api.startConversation(
        scenario.key,
        targets.data?.map((p) => p.id) ?? [],
        scenario.key === "free_topic" ? topic : undefined,
      ),
    onSuccess: (conversation) => void navigate(`/conversation/${conversation.id}`),
  });

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Rozmowa z AI"
        subtitle="Wybierz scenkę. AI zagra drugą osobę i po każdej Twojej wiadomości pokaże poprawki."
      />

      {sectionCode && targets.data && (
        <div className="flex items-start gap-3 rounded-2xl bg-brand-soft p-4 text-sm">
          <Target className="mt-0.5 size-5 shrink-0 text-brand-ink" aria-hidden />
          <p>
            Przećwiczysz frazy z sekcji <strong>{targets.data[0]?.section_title}</strong> (
            {targets.data.length}). AI stworzy okazje, żeby ich użyć.
          </p>
        </div>
      )}

      {start.isPending && <Spinner label="AI przygotowuje scenkę…" />}
      {start.isError && <ErrorState error={start.error} />}
      {scenarios.isError && <ErrorState error={scenarios.error} onRetry={() => void scenarios.refetch()} />}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {scenarios.data?.map((scenario, i) => (
          <motion.div
            key={scenario.key}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
          >
            <Card className="flex h-full flex-col gap-3 p-5">
              <span className="text-4xl" aria-hidden>
                {scenario.emoji}
              </span>
              <div className="flex-1">
                <h2 className="font-bold">{scenario.title}</h2>
                <p className="mt-1 text-sm text-ink-soft">{scenario.description}</p>
              </div>
              {scenario.key === "free_topic" && (
                <input
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="O czym chcesz porozmawiać?"
                  aria-label="Temat rozmowy"
                  className="h-10 rounded-xl bg-surface-sunken px-3 text-sm outline-none focus:ring-2 focus:ring-brand"
                />
              )}
              <Button onClick={() => start.mutate(scenario)} disabled={start.isPending}>
                <MessagesSquare className="size-4" aria-hidden /> Zacznij
              </Button>
            </Card>
          </motion.div>
        ))}
      </div>

      {recent.data && recent.data.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-bold">Ostatnie rozmowy</h2>
          <ul className="flex flex-col gap-2">
            {recent.data.map((c) => (
              <li key={c.id}>
                <Link
                  to={`/conversation/${c.id}`}
                  className="flex items-center gap-3 rounded-2xl bg-surface-raised p-4 ring-1 ring-line transition hover:ring-brand/40"
                >
                  <span className="text-2xl" aria-hidden>
                    {c.emoji}
                  </span>
                  <div className="flex-1">
                    <p className="font-semibold">{c.title}</p>
                    <p className="text-xs text-ink-muted">
                      {dateFormat.format(new Date(c.started_at))} · {c.messages} wiadomości
                    </p>
                  </div>
                  {c.status === "finished" ? (
                    <Badge tone="good">{c.score}/10</Badge>
                  ) : (
                    <Badge tone="brand">w trakcie</Badge>
                  )}
                  <ChevronRight className="size-5 text-ink-muted" aria-hidden />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
