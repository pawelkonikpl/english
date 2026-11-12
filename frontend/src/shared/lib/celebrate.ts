import confetti from "canvas-confetti";

const prefersReducedMotion = (): boolean =>
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export function celebrate(): void {
  if (prefersReducedMotion()) return;
  const colors = ["#6d4aff", "#c04dff", "#ff7a59", "#2a78d6", "#1baf7a"];
  void confetti({ particleCount: 90, spread: 75, origin: { y: 0.65 }, colors });
  window.setTimeout(() => {
    void confetti({ particleCount: 60, spread: 110, origin: { y: 0.55 }, colors });
  }, 220);
}
