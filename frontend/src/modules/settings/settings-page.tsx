import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, CheckCircle2, Monitor, Moon, RotateCcw, Save, Sun, User, XCircle, Zap } from "lucide-react";
import { useState } from "react";

import { useTheme, type ThemePreference } from "@/app/theme";
import { errorMessage } from "@/shared/api/client";
import { api, queryKeys } from "@/shared/api/endpoints";
import { cefrLevels, type CefrLevel, type ModelTestResult, type ModelTier, type Profile } from "@/shared/api/schemas";
import { cn } from "@/shared/lib/cn";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { PageHeader } from "@/shared/ui/page-header";
import { ErrorState, Spinner } from "@/shared/ui/states";

const TIER_INFO: Record<ModelTier, { title: string; description: string }> = {
  main: { title: "Model główny", description: "Rozmowa z AI, generowanie lekcji, podsumowania." },
  fast: { title: "Model szybki", description: "Podpowiedzi, ocena zdań, wyjaśnienia fraz." },
};

const CUSTOM = "__custom__";
const inputClass =
  "h-11 w-full rounded-2xl bg-surface-sunken px-4 text-sm font-medium outline-none focus:ring-2 focus:ring-brand";

function TierEditor({ tier }: { tier: ModelTier }) {
  const queryClient = useQueryClient();
  const settings = useQuery({ queryKey: queryKeys.llmSettings, queryFn: api.llmSettings });
  const models = useQuery({ queryKey: queryKeys.llmModels, queryFn: api.llmModels });
  const current = settings.data?.tiers.find((t) => t.tier === tier);
  const known = new Set(models.data?.map((m) => m.id));
  const [choice, setChoice] = useState<string | null>(null);
  const [custom, setCustom] = useState("");
  const [test, setTest] = useState<ModelTestResult | null>(null);

  const selected = choice ?? (current?.effective && !known.has(current.effective) && models.data ? CUSTOM : (current?.effective ?? ""));
  const customValue = custom || (selected === CUSTOM ? (current?.effective ?? "") : "");
  const target = selected === CUSTOM ? customValue.trim() : selected;

  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ["llm"] });
    setChoice(null);
    setCustom("");
  };
  const save = useMutation({
    mutationFn: (model: string | null) =>
      api.updateLlmSettings({ [tier]: model, allow_custom: selected === CUSTOM }),
    onSuccess: refresh,
  });
  const runTest = useMutation({
    mutationFn: () => api.testModel(target ? { model: target } : { tier }),
    onSuccess: setTest,
  });

  if (!current) return null;
  const info = TIER_INFO[tier];

  return (
    <div className="flex flex-col gap-3 rounded-2xl bg-surface-sunken/60 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-semibold">{info.title}</p>
          <p className="text-xs text-ink-muted">{info.description}</p>
        </div>
        <Badge tone={current.override ? "brand" : "neutral"}>
          {current.override ? "ustawiony w aplikacji" : current.env_model ? "z pliku .env" : "domyślny providera"}
        </Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-[1fr_auto_auto]">
        <select
          value={selected}
          onChange={(e) => {
            setChoice(e.target.value);
            setTest(null);
          }}
          className={inputClass}
          aria-label={`${info.title}: wybór modelu`}
        >
          <option value="">Domyślny providera</option>
          {models.data?.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name}
            </option>
          ))}
          <option value={CUSTOM}>Własny identyfikator…</option>
        </select>
        <Button variant="secondary" onClick={() => runTest.mutate()} disabled={runTest.isPending}>
          <Zap className="size-4" aria-hidden /> {runTest.isPending ? "Testuję…" : "Testuj"}
        </Button>
        <Button onClick={() => save.mutate(target || null)} disabled={save.isPending || (selected === CUSTOM && !target)}>
          <Save className="size-4" aria-hidden /> Zapisz
        </Button>
      </div>
      {selected === CUSTOM && (
        <input
          className={inputClass}
          value={customValue}
          onChange={(e) => setCustom(e.target.value)}
          placeholder="np. claude-opus-5-5 albo alias „sonnet”"
          aria-label="Własny identyfikator modelu"
        />
      )}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-ink-muted">
        <span>
          Aktywny: <strong className="text-ink">{current.effective ?? "domyślny providera"}</strong>
          {current.env_model && ` · w .env: ${current.env_model}`}
        </span>
        {current.override && (
          <Button variant="ghost" size="sm" onClick={() => save.mutate(null)}>
            <RotateCcw className="size-4" aria-hidden /> Przywróć z .env
          </Button>
        )}
      </div>
      {test && (
        <p className={cn("flex items-center gap-2 text-sm font-medium", test.ok ? "text-good" : "text-critical")}>
          {test.ok ? <CheckCircle2 className="size-4" aria-hidden /> : <XCircle className="size-4" aria-hidden />}
          {test.ok
            ? `Działa: ${test.model ?? "model domyślny"} odpowiedział w ${(test.latency_ms / 1000).toFixed(1)} s`
            : test.detail}
        </p>
      )}
      {(save.isError || runTest.isError) && (
        <p className="text-sm text-critical">{errorMessage(save.error ?? runTest.error)}</p>
      )}
    </div>
  );
}

function ModelSettingsCard() {
  const status = useQuery({ queryKey: queryKeys.llmStatus, queryFn: api.llmStatus });
  return (
    <Card className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-lg font-bold">
          <Bot className="size-5 text-brand-ink" aria-hidden /> Model AI
        </h2>
        {status.data && (
          <Badge tone={status.data.available ? "good" : "critical"}>
            {status.data.provider} · {status.data.available ? "dostępny" : "niedostępny"}
          </Badge>
        )}
      </div>
      {status.data?.detail && <p className="text-sm text-ink-soft">{status.data.detail}</p>}
      <p className="text-xs text-ink-muted">
        Providera zmieniasz w pliku <code>.env</code> (<code>LLM_PROVIDER</code>), modele możesz
        zmieniać tutaj bez restartu.
      </p>
      <TierEditor tier="main" />
      <TierEditor tier="fast" />
    </Card>
  );
}

function ProfileCard() {
  const queryClient = useQueryClient();
  const profile = useQuery({ queryKey: queryKeys.profile, queryFn: api.profile });
  const [draft, setDraft] = useState<Partial<Profile>>({});
  const save = useMutation({
    mutationFn: () => api.updateProfile(draft),
    onSuccess: () => {
      setDraft({});
      void queryClient.invalidateQueries({ queryKey: queryKeys.profile });
      void queryClient.invalidateQueries({ queryKey: ["progress"] });
    },
  });
  if (profile.isPending) return <Spinner />;
  if (profile.isError) return <ErrorState error={profile.error} />;
  const value = { ...profile.data, ...draft };

  return (
    <Card className="flex flex-col gap-4">
      <h2 className="flex items-center gap-2 text-lg font-bold">
        <User className="size-5 text-brand-ink" aria-hidden /> Profil
      </h2>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5 text-sm font-semibold">
          Imię
          <input
            className={inputClass}
            value={value.display_name ?? ""}
            onChange={(e) => setDraft((d) => ({ ...d, display_name: e.target.value || null }))}
          />
        </label>
        <label className="flex flex-col gap-1.5 text-sm font-semibold">
          Poziom
          <select
            className={inputClass}
            value={value.level}
            onChange={(e) => setDraft((d) => ({ ...d, level: e.target.value as CefrLevel }))}
          >
            {cefrLevels.map((l) => (
              <option key={l}>{l}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-sm font-semibold sm:col-span-2">
          Dzienny cel: {value.daily_goal_xp} XP
          <input
            type="range"
            min={10}
            max={100}
            step={5}
            value={value.daily_goal_xp}
            onChange={(e) => setDraft((d) => ({ ...d, daily_goal_xp: Number(e.target.value) }))}
            className="accent-[#6d4aff]"
          />
        </label>
      </div>
      <Button className="w-fit" onClick={() => save.mutate()} disabled={save.isPending || Object.keys(draft).length === 0}>
        <Save className="size-4" aria-hidden /> Zapisz profil
      </Button>
      {save.isError && <p className="text-sm text-critical">{errorMessage(save.error)}</p>}
    </Card>
  );
}

function ThemeCard() {
  const { preference, setPreference } = useTheme();
  const options: { value: ThemePreference; label: string; icon: typeof Sun }[] = [
    { value: "system", label: "Systemowy", icon: Monitor },
    { value: "light", label: "Jasny", icon: Sun },
    { value: "dark", label: "Ciemny", icon: Moon },
  ];
  return (
    <Card className="flex flex-col gap-4">
      <h2 className="text-lg font-bold">Wygląd</h2>
      <div className="grid grid-cols-3 gap-2 rounded-2xl bg-surface-sunken p-1.5" role="radiogroup" aria-label="Motyw">
        {options.map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={preference === value}
            onClick={() => setPreference(value)}
            className={cn(
              "flex items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-semibold transition",
              preference === value ? "bg-surface-raised shadow-sm" : "text-ink-muted hover:text-ink",
            )}
          >
            <Icon className="size-4" aria-hidden /> {label}
          </button>
        ))}
      </div>
    </Card>
  );
}

export function SettingsPage() {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Ustawienia" />
      <ModelSettingsCard />
      <ProfileCard />
      <ThemeCard />
    </div>
  );
}
