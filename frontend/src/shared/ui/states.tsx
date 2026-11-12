import { AlertTriangle, Loader2, RotateCcw } from "lucide-react";
import type { ReactNode } from "react";

import { errorMessage } from "@/shared/api/client";

import { Button } from "./button";

export function Spinner({ label = "Ładowanie…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-ink-muted" role="status">
      <Loader2 className="size-5 animate-spin" aria-hidden />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-3xl bg-critical/10 p-8 text-center">
      <AlertTriangle className="size-8 text-critical" aria-hidden />
      <p className="max-w-md text-sm text-ink">{errorMessage(error)}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          <RotateCcw className="size-4" aria-hidden /> Spróbuj ponownie
        </Button>
      )}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  children,
}: {
  icon: ReactNode;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 px-6 py-14 text-center">
      <div className="grid size-16 place-items-center rounded-3xl bg-brand-soft text-brand-ink">
        {icon}
      </div>
      <h2 className="text-lg font-bold">{title}</h2>
      {children && <div className="max-w-md text-sm text-ink-soft">{children}</div>}
    </div>
  );
}
