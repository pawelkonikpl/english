import { Volume2 } from "lucide-react";

import { canSpeak, speak } from "@/shared/lib/speech";
import { cn } from "@/shared/lib/cn";

export function SpeakButton({ text, className }: { text: string; className?: string }) {
  if (!canSpeak()) return null;
  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        speak(text);
      }}
      className={cn(
        "grid size-9 shrink-0 place-items-center rounded-xl text-ink-muted transition hover:bg-surface-sunken hover:text-brand-ink focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none",
        className,
      )}
      aria-label={`Odtwórz wymowę: ${text}`}
      title="Posłuchaj wymowy"
    >
      <Volume2 className="size-5" aria-hidden />
    </button>
  );
}
