/** Read English text aloud with the browser's built-in speech synthesis (no backend). */
export function speak(text: string): void {
  if (!("speechSynthesis" in window)) return;
  const utterance = new SpeechSynthesisUtterance(text.replaceAll(" / ", ". "));
  utterance.lang = "en-US";
  utterance.rate = 0.92;
  const voice = window.speechSynthesis
    .getVoices()
    .find((v) => v.lang.startsWith("en") && v.localService);
  if (voice) utterance.voice = voice;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

export const canSpeak = (): boolean => "speechSynthesis" in window;
