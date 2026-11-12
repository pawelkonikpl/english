import type { HTMLAttributes } from "react";

import { cn } from "@/shared/lib/cn";

type Tone = "neutral" | "brand" | "good" | "warning" | "critical";

const TONES: Record<Tone, string> = {
  neutral: "bg-surface-sunken text-ink-soft",
  brand: "bg-brand-soft text-brand-ink",
  good: "bg-good/15 text-good",
  warning: "bg-warning/20 text-ink",
  critical: "bg-critical/15 text-critical",
};

export function Badge({
  tone = "neutral",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold",
        TONES[tone],
        className,
      )}
      {...props}
    />
  );
}
