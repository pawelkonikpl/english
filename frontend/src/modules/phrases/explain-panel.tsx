import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Bot, Lightbulb, RefreshCw, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect } from "react";

import { api } from "@/shared/api/endpoints";
import type { Phrase } from "@/shared/api/schemas";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { ErrorState, Spinner } from "@/shared/ui/states";

import { SpeakButton } from "./speak-button";

export function ExplainPanel({ phrase, onClose }: { phrase: Phrase | null; onClose: () => void }) {
  const queryClient = useQueryClient();
  const explain = useMutation({
    mutationFn: ({ id, regenerate }: { id: number; regenerate: boolean }) =>
      api.explainPhrase(id, regenerate),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["phrases", "list"] }),
  });
  const { mutate, reset } = explain;

  useEffect(() => {
    if (phrase) mutate({ id: phrase.id, regenerate: false });
    else reset();
  }, [phrase, mutate, reset]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <AnimatePresence>
      {phrase && (
        <motion.div
          className="fixed inset-0 z-40 flex justify-end bg-black/40 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.aside
            role="dialog"
            aria-modal="true"
            aria-label={`Wyjaśnienie: ${phrase.english}`}
            className="flex h-full w-full max-w-md flex-col gap-5 overflow-y-auto bg-surface-raised p-6 shadow-2xl"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 300, damping: 32 }}
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <Badge tone="brand">
                  <Bot className="size-3.5" aria-hidden /> Wyjaśnienie AI
                </Badge>
                <div className="mt-3 flex items-center gap-1">
                  <h2 className="text-xl font-extrabold">{phrase.english}</h2>
                  <SpeakButton text={phrase.english} />
                </div>
                <p className="text-ink-soft">{phrase.polish}</p>
              </div>
              <Button variant="ghost" size="sm" onClick={onClose} aria-label="Zamknij">
                <X className="size-5" aria-hidden />
              </Button>
            </div>

            {explain.isPending && <Spinner label="AI przygotowuje wyjaśnienie…" />}
            {explain.isError && (
              <ErrorState
                error={explain.error}
                onRetry={() => explain.mutate({ id: phrase.id, regenerate: false })}
              />
            )}
            {explain.data && (
              <div className="flex flex-col gap-5">
                <section>
                  <h3 className="text-xs font-bold tracking-wide text-ink-muted uppercase">Znaczenie</h3>
                  <p className="mt-1">{explain.data.meaning}</p>
                </section>
                <section>
                  <h3 className="text-xs font-bold tracking-wide text-ink-muted uppercase">Kiedy używać</h3>
                  <p className="mt-1">{explain.data.when_to_use}</p>
                </section>
                <section>
                  <h3 className="text-xs font-bold tracking-wide text-ink-muted uppercase">Przykłady</h3>
                  <ul className="mt-2 flex flex-col gap-2">
                    {explain.data.examples.map((ex) => (
                      <li key={ex.english} className="flex items-start gap-2 rounded-2xl bg-surface-sunken p-3">
                        <div className="flex-1">
                          <p className="font-medium">{ex.english}</p>
                          <p className="text-sm text-ink-soft">{ex.translation}</p>
                        </div>
                        <SpeakButton text={ex.english} />
                      </li>
                    ))}
                  </ul>
                </section>
                {explain.data.similar.length > 0 && (
                  <section>
                    <h3 className="text-xs font-bold tracking-wide text-ink-muted uppercase">Podobne</h3>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {explain.data.similar.map((s) => (
                        <Badge key={s}>{s}</Badge>
                      ))}
                    </div>
                  </section>
                )}
                <section className="flex gap-3 rounded-2xl bg-warning/15 p-4">
                  <Lightbulb className="size-5 shrink-0 text-[#b67a00]" aria-hidden />
                  <p className="text-sm">{explain.data.tip}</p>
                </section>
                <div className="flex items-center justify-between text-xs text-ink-muted">
                  <span>Model: {explain.data.model ?? "domyślny"}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => explain.mutate({ id: phrase.id, regenerate: true })}
                  >
                    <RefreshCw className="size-4" aria-hidden /> Wygeneruj ponownie
                  </Button>
                </div>
              </div>
            )}
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
