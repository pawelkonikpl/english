import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Trophy } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect } from "react";

import { api, queryKeys } from "@/shared/api/endpoints";
import type { Achievement } from "@/shared/api/schemas";
import { celebrate } from "@/shared/lib/celebrate";
import { Button } from "@/shared/ui/button";

export function AchievementCelebration({ achievements }: { achievements: Achievement[] }) {
  const queryClient = useQueryClient();
  const dismiss = useMutation({
    mutationFn: api.markAchievementsSeen,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
      void queryClient.invalidateQueries({ queryKey: queryKeys.achievements });
    },
  });
  const open = achievements.length > 0;

  useEffect(() => {
    if (open) celebrate();
  }, [open]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 grid place-items-center bg-black/50 p-4 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="achievement-title"
        >
          <motion.div
            className="w-full max-w-sm rounded-[2rem] bg-surface-raised p-8 text-center shadow-2xl"
            initial={{ scale: 0.8, y: 30 }}
            animate={{ scale: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
          >
            <div className="mx-auto mb-4 grid size-20 animate-float place-items-center rounded-3xl bg-brand-gradient text-white shadow-xl shadow-brand/40">
              <Trophy className="size-10" aria-hidden />
            </div>
            <h2 id="achievement-title" className="text-xl font-extrabold">
              {achievements.length === 1 ? "Nowe osiągnięcie!" : "Nowe osiągnięcia!"}
            </h2>
            <ul className="mt-4 flex flex-col gap-3">
              {achievements.map((a) => (
                <li key={a.key} className="rounded-2xl bg-brand-soft px-4 py-3">
                  <p className="font-bold text-brand-ink">{a.title}</p>
                  <p className="text-sm text-ink-soft">{a.description}</p>
                </li>
              ))}
            </ul>
            <Button className="mt-6 w-full" onClick={() => dismiss.mutate()} disabled={dismiss.isPending}>
              Super, lecimy dalej!
            </Button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
