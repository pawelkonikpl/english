import type { HTMLAttributes } from "react";

import { cn } from "@/shared/lib/cn";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-3xl bg-surface-raised p-5 shadow-sm ring-1 ring-line sm:p-6",
        className,
      )}
      {...props}
    />
  );
}
