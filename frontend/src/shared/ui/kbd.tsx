import type { ReactNode } from "react";

export function Kbd({ children }: { children: ReactNode }) {
  return (
    <kbd className="hidden rounded-md bg-black/10 px-1.5 py-0.5 font-mono text-[10px] font-semibold sm:inline dark:bg-white/10">
      {children}
    </kbd>
  );
}
