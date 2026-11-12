import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check, Rocket, Sparkles, Target } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useState, type ReactNode } from "react";
import { useNavigate } from "react-router";

import { errorMessage } from "@/shared/api/client";
import { api, queryKeys } from "@/shared/api/endpoints";
import type { CefrLevel } from "@/shared/api/schemas";
import { celebrate } from "@/shared/lib/celebrate";
import { cn } from "@/shared/lib/cn";
import { Button } from "@/shared/ui/button";

import { PlacementTest } from "../lessons/placement-test";

const GOALS = [
  "Rozmowy na co dzień",
  "Praca i spotkania",
  "Podróże",
  "Pewność siebie w mówieniu",
  "Więcej słówek",
  "Gramatyka",
];

const LEVELS: { level: CefrLevel; title: string; description: string }[] = [
  { level: "A1", title: "Początkujący", description: "Znam podstawowe słowa: hello, thank you." },
  { level: "A2", title: "Podstawowy", description: "Przedstawię się i dogadam w prostych sprawach." },
  { level: "B1", title: "Średni", description: "Rozmawiam o znanych tematach i wyrażam opinię." },
  { level: "B2", title: "Średnio zaawansowany", description: "Swobodnie rozmawiam na wiele tematów." },
  { level: "C1", title: "Zaawansowany", description: "Mówię płynnie, także o złożonych sprawach." },
  { level: "C2", title: "Biegły", description: "Prawie jak native speaker." },
];

const DAILY_GOALS = [
  { xp: 10, title: "Na luzie", description: "ok. 5 minut dziennie" },
  { xp: 20, title: "Regularnie", description: "ok. 10 minut dziennie" },
  { xp: 30, title: "Ambitnie", description: "ok. 15 minut dziennie" },
  { xp: 50, title: "Intensywnie", description: "ok. 25 minut dziennie" },
];

function Choice({
  selected,
  onClick,
  children,
}: {
  selected: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        "flex items-center gap-3 rounded-2xl p-4 text-left ring-1 transition focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none",
        selected ? "bg-brand-soft ring-brand" : "bg-surface-raised ring-line hover:ring-brand/50",
      )}
    >
      <span
        className={cn(
          "grid size-6 shrink-0 place-items-center rounded-full ring-1",
          selected ? "bg-brand-gradient text-white ring-transparent" : "ring-line",
        )}
      >
        {selected && <Check className="size-4" aria-hidden />}
      </span>
      <span className="flex-1">{children}</span>
    </button>
  );
}

export function OnboardingPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [step, setStep] = useState(0);
  const [name, setName] = useState("");
  const [goals, setGoals] = useState<string[]>([]);
  const [level, setLevel] = useState<CefrLevel>("A2");
  const [dailyGoal, setDailyGoal] = useState(20);
  const [testing, setTesting] = useState(false);
  const modules = useQuery({ queryKey: queryKeys.modules, queryFn: api.modules, staleTime: Infinity });
  const canTest = modules.data?.some((m) => m.key === "lessons") ?? false;

  const finish = useMutation({
    mutationFn: () =>
      api.updateProfile({
        display_name: name.trim() || null,
        goals,
        level,
        daily_goal_xp: dailyGoal,
        onboarding_done: true,
      }),
    onSuccess: (profile) => {
      // Write the saved profile into the cache: the layout's onboarding guard reads it right away.
      queryClient.setQueryData(queryKeys.profile, profile);
      void queryClient.invalidateQueries({ queryKey: ["progress"] });
      celebrate();
      void navigate("/", { replace: true });
    },
  });

  const steps: { title: string; subtitle: string; body: ReactNode }[] = [
    {
      title: "Cześć! Jak masz na imię?",
      subtitle: "Będziemy się do Ciebie tak zwracać. Możesz to pominąć.",
      body: (
        <input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Twoje imię"
          className="h-14 w-full rounded-2xl bg-surface-raised px-5 text-lg font-semibold ring-1 ring-line outline-none focus:ring-2 focus:ring-brand"
        />
      ),
    },
    {
      title: "Na czym Ci zależy?",
      subtitle: "Wybierz dowolnie wiele. Dopasujemy do tego rozmowy i lekcje.",
      body: (
        <div className="grid gap-2 sm:grid-cols-2">
          {GOALS.map((goal) => (
            <Choice
              key={goal}
              selected={goals.includes(goal)}
              onClick={() => setGoals((g) => (g.includes(goal) ? g.filter((x) => x !== goal) : [...g, goal]))}
            >
              <span className="font-semibold">{goal}</span>
            </Choice>
          ))}
        </div>
      ),
    },
    {
      title: "Jak oceniasz swój angielski?",
      subtitle: "Bez stresu: poziom zmienisz później w ustawieniach.",
      body: (
        <div className="flex flex-col gap-4">
          <div className="grid gap-2 sm:grid-cols-2">
            {LEVELS.map((l) => (
              <Choice key={l.level} selected={level === l.level} onClick={() => setLevel(l.level)}>
                <span className="block font-semibold">
                  {l.level} · {l.title}
                </span>
                <span className="block text-sm text-ink-soft">{l.description}</span>
              </Choice>
            ))}
          </div>
          {canTest &&
            (testing ? (
              <div className="rounded-3xl bg-surface-raised p-5 ring-1 ring-line">
                <PlacementTest selfLevel={level} onResult={(result) => setLevel(result.level)} />
              </div>
            ) : (
              <Button variant="secondary" className="w-fit" onClick={() => setTesting(true)}>
                <Target className="size-4" aria-hidden /> Nie wiem, zrób krótki test z AI
              </Button>
            ))}
        </div>
      ),
    },
    {
      title: "Ile chcesz się uczyć?",
      subtitle: "Regularność wygrywa z długością. Codzienny cel pomoże budować serię.",
      body: (
        <div className="grid gap-2 sm:grid-cols-2">
          {DAILY_GOALS.map((g) => (
            <Choice key={g.xp} selected={dailyGoal === g.xp} onClick={() => setDailyGoal(g.xp)}>
              <span className="block font-semibold">
                {g.title} · {g.xp} XP
              </span>
              <span className="block text-sm text-ink-soft">{g.description}</span>
            </Choice>
          ))}
        </div>
      ),
    },
  ];
  const current = steps[step]!;
  const last = step === steps.length - 1;

  return (
    <div className="grid min-h-dvh place-items-center px-4 py-10">
      <div className="w-full max-w-2xl">
        <div className="mb-8 flex items-center gap-3">
          <span className="grid size-11 place-items-center rounded-2xl bg-brand-gradient text-white shadow-lg shadow-brand/30">
            <Sparkles className="size-6" aria-hidden />
          </span>
          <div className="flex flex-1 gap-1.5" aria-label={`Krok ${step + 1} z ${steps.length}`}>
            {steps.map((_, i) => (
              <span
                key={i}
                className={cn("h-2 flex-1 rounded-full transition", i <= step ? "bg-brand-gradient" : "bg-surface-sunken")}
              />
            ))}
          </div>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            transition={{ duration: 0.22 }}
          >
            <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">{current.title}</h1>
            <p className="mt-2 mb-6 text-ink-soft">{current.subtitle}</p>
            {current.body}
          </motion.div>
        </AnimatePresence>

        {finish.isError && <p className="mt-4 text-sm text-critical">{errorMessage(finish.error)}</p>}

        <div className="mt-8 flex justify-between gap-3">
          <Button variant="ghost" onClick={() => setStep((s) => s - 1)} disabled={step === 0}>
            <ArrowLeft className="size-4" aria-hidden /> Wstecz
          </Button>
          {last ? (
            <Button size="lg" onClick={() => finish.mutate()} disabled={finish.isPending}>
              <Rocket className="size-5" aria-hidden /> Zaczynamy!
            </Button>
          ) : (
            <Button size="lg" onClick={() => setStep((s) => s + 1)}>
              Dalej <ArrowRight className="size-5" aria-hidden />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
