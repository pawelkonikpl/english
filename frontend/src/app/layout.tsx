import { useQuery } from "@tanstack/react-query";
import { Flame, Settings, Sparkles, TriangleAlert, Zap } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { Suspense, type ReactNode } from "react";
import { Link, Navigate, NavLink, Outlet, useLocation } from "react-router";

import { MODULE_NAV, type ModuleNavEntry } from "@/modules/registry";
import { api, queryKeys } from "@/shared/api/endpoints";
import { cn } from "@/shared/lib/cn";
import { EmptyState, Spinner } from "@/shared/ui/states";

function useEnabledModules() {
  return useQuery({ queryKey: queryKeys.modules, queryFn: api.modules, staleTime: Infinity });
}

function useNavEntries(): ModuleNavEntry[] {
  const { data: modules } = useEnabledModules();
  const enabled = new Set(modules?.map((m) => m.key));
  return MODULE_NAV.filter((entry) => enabled.has(entry.key));
}

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2.5 font-extrabold tracking-tight">
      <span className="grid size-9 place-items-center rounded-2xl bg-brand-gradient text-white shadow-lg shadow-brand/30">
        <Sparkles className="size-5" aria-hidden />
      </span>
      <span className="text-lg">
        Speak <span className="text-brand-gradient">Up</span>
      </span>
    </Link>
  );
}

function StatsPills() {
  const { data } = useQuery({ queryKey: queryKeys.dashboard, queryFn: api.dashboard });
  if (!data) return null;
  return (
    <div className="flex items-center gap-2">
      <span
        className="inline-flex items-center gap-1.5 rounded-full bg-surface-raised px-3 py-1.5 text-sm font-bold ring-1 ring-line"
        title="Seria dni nauki"
      >
        <Flame
          className={cn("size-4", data.streak.active_today ? "text-[#ff7a59]" : "text-ink-muted")}
          aria-hidden
        />
        {data.streak.current}
      </span>
      <span
        className="inline-flex items-center gap-1.5 rounded-full bg-surface-raised px-3 py-1.5 text-sm font-bold ring-1 ring-line"
        title="XP dzisiaj / cel dzienny"
      >
        <Zap className="size-4 text-warning" aria-hidden />
        {data.xp.today}/{data.xp.goal}
      </span>
    </div>
  );
}

function LlmBanner() {
  const { data } = useQuery({
    queryKey: queryKeys.llmStatus,
    queryFn: api.llmStatus,
    staleTime: 60_000,
  });
  if (!data || data.available) return null;
  return (
    <div className="mb-6 flex items-start gap-3 rounded-2xl bg-warning/15 p-4 text-sm ring-1 ring-warning/40">
      <TriangleAlert className="mt-0.5 size-5 shrink-0 text-warning" aria-hidden />
      <div className="flex-1">
        <p className="font-semibold">Model AI jest niedostępny ({data.provider})</p>
        <p className="text-ink-soft">
          {data.detail ?? "Sprawdź konfigurację providera."} Frazy, powtórki i postępy działają
          normalnie.
        </p>
      </div>
      <Link to="/settings" className="font-semibold text-brand-ink underline-offset-2 hover:underline">
        Ustawienia
      </Link>
    </div>
  );
}

function SideNav({ entries }: { entries: ModuleNavEntry[] }) {
  const item = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition",
      isActive
        ? "bg-brand-soft text-brand-ink"
        : "text-ink-soft hover:bg-surface-sunken hover:text-ink",
    );
  return (
    <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 flex-col gap-8 border-r border-line bg-surface-raised/60 p-5 backdrop-blur lg:flex">
      <Logo />
      <nav className="flex flex-1 flex-col gap-1" aria-label="Główna nawigacja">
        {entries.map(({ key, path, label, icon: Icon }) => (
          <NavLink key={key} to={path} end={path === "/"} className={item}>
            <Icon className="size-5" aria-hidden /> {label}
          </NavLink>
        ))}
      </nav>
      <NavLink to="/settings" className={item}>
        <Settings className="size-5" aria-hidden /> Ustawienia
      </NavLink>
    </aside>
  );
}

function BottomNav({ entries }: { entries: ModuleNavEntry[] }) {
  const all = [...entries, { key: "settings", path: "/settings", label: "Więcej", icon: Settings }];
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-30 flex justify-around border-t border-line bg-surface-raised/90 px-2 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] backdrop-blur lg:hidden"
      aria-label="Główna nawigacja"
    >
      {all.map(({ key, path, label, icon: Icon }) => (
        <NavLink
          key={key}
          to={path}
          end={path === "/"}
          className={({ isActive }) =>
            cn(
              "flex min-w-14 flex-col items-center gap-1 rounded-xl px-2 py-1 text-[11px] font-semibold",
              isActive ? "text-brand-ink" : "text-ink-muted",
            )
          }
        >
          <Icon className="size-5" aria-hidden />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

export function AppLayout() {
  const location = useLocation();
  const entries = useNavEntries();
  const profile = useQuery({ queryKey: queryKeys.profile, queryFn: api.profile });

  if (profile.data && !profile.data.onboarding_done && location.pathname !== "/onboarding") {
    return <Navigate to="/onboarding" replace />;
  }

  return (
    <div className="flex min-h-dvh">
      <SideNav entries={entries} />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex items-center justify-between gap-4 border-b border-line/60 bg-surface/80 px-4 py-3 backdrop-blur sm:px-8 lg:justify-end">
          <div className="lg:hidden">
            <Logo />
          </div>
          <StatsPills />
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-4 pt-6 pb-28 sm:px-8 lg:pb-12">
          <LlmBanner />
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.22, ease: "easeOut" }}
            >
              <Suspense fallback={<Spinner />}>
                <Outlet />
              </Suspense>
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
      <BottomNav entries={entries} />
    </div>
  );
}

/** Shows a page only when its backend module is enabled. */
export function ModuleGate({ moduleKey, children }: { moduleKey: string; children: ReactNode }) {
  const { data, isPending } = useEnabledModules();
  if (isPending) return <Spinner />;
  if (!data?.some((m) => m.key === moduleKey)) {
    return (
      <EmptyState icon={<Settings className="size-7" />} title="Ten moduł jest wyłączony">
        Włącz go w pliku <code>.env</code> (zmienna <code>ENABLED_MODULES</code>) i uruchom
        aplikację ponownie.
      </EmptyState>
    );
  }
  return children;
}
