import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { mockApi, renderWithApp } from "@/test/utils";

import { ReviewPage } from "./review-page";

function dueItem(id: number, front: string, back: string) {
  return {
    id,
    item_type: "phrase",
    item_id: id,
    step: 0,
    mastery: 0,
    due_on: "2026-11-12",
    lapses: 0,
    card: { front, back, example: null, note: null, label: "Gdy czegoś nie rozumiesz" },
  };
}

const DUE = [
  dueItem(1, "Sorry, I didn't catch that.", "Przepraszam, nie dosłyszałem."),
  dueItem(2, "Could you say that again?", "Możesz powtórzyć?"),
];

function gradeResult(id: number, dueAgainToday: boolean) {
  return { id, step: 1, mastery: 1, interval_days: 1, due_on: "2026-11-13", due_again_today: dueAgainToday };
}

function renderReview(gradeHandler = () => gradeResult(1, false)) {
  const api = mockApi({
    "GET /api/review/due": () => DUE,
    "POST /api/review/items/1/grade": gradeHandler,
    "POST /api/review/items/2/grade": () => gradeResult(2, false),
    "POST /api/review/items/2/check-recall": (body) => ({
      correct: (body as { answer: string }).answer === "Could you say that again?",
      expected: "Could you say that again?",
    }),
  });
  renderWithApp([{ path: "/review", element: <ReviewPage /> }], "/review");
  return api;
}

describe("ReviewPage", () => {
  it("reveals the meaning with Space and grades with number keys", async () => {
    const { calls } = renderReview();

    await screen.findByText("Sorry, I didn't catch that.");
    expect(screen.queryByText("Przepraszam, nie dosłyszałem.")).not.toBeInTheDocument();

    fireEvent.keyDown(window, { key: " " });
    expect(await screen.findByText("Przepraszam, nie dosłyszałem.")).toBeInTheDocument();

    fireEvent.keyDown(window, { key: "3" });
    await screen.findByText("Could you say that again?");

    expect(calls.find((c) => c.key === "POST /api/review/items/1/grade")?.body).toEqual({
      grade: "good",
      mode: "recognition",
    });
  });

  it("does not grade before the answer is revealed", async () => {
    const { calls } = renderReview();
    await screen.findByText("Sorry, I didn't catch that.");

    fireEvent.keyDown(window, { key: "3" });

    expect(calls.some((c) => c.key.endsWith("/grade"))).toBe(false);
  });

  it("puts a forgotten card back at the end of the queue", async () => {
    renderReview(() => gradeResult(1, true));
    await screen.findByText("Sorry, I didn't catch that.");

    fireEvent.keyDown(window, { key: " " });
    fireEvent.keyDown(window, { key: "1" });
    await screen.findByText("Could you say that again?");
    fireEvent.keyDown(window, { key: " " });
    fireEvent.keyDown(window, { key: "3" });

    expect(await screen.findByText("Sorry, I didn't catch that.")).toBeInTheDocument();
    expect(screen.getByText("Zostało: 1")).toBeInTheDocument();
  });

  it("checks a typed answer in recall mode and then finishes the session", async () => {
    const user = userEvent.setup();
    renderReview();
    await screen.findByText("Sorry, I didn't catch that.");
    fireEvent.keyDown(window, { key: " " });
    fireEvent.keyDown(window, { key: "3" });
    await screen.findByText("Could you say that again?");

    await user.click(screen.getByRole("tab", { name: /Przypominanie/ }));
    await user.type(screen.getByLabelText("Twoja odpowiedź po angielsku"), "Could you say that again?");
    await user.click(screen.getByRole("button", { name: /Sprawdź/ }));
    expect(await screen.findByText("Dobrze!")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Łatwe/ }));

    await waitFor(() => expect(screen.getByText("Powtórki zrobione!")).toBeInTheDocument());
    expect(screen.getByText(/2 odpowiedzi · 100% dobrze · \+2 XP/)).toBeInTheDocument();
  });

  it("shows an empty state when nothing is due", async () => {
    mockApi({ "GET /api/review/due": () => [] });
    renderWithApp([{ path: "/review", element: <ReviewPage /> }], "/review");

    expect(await screen.findByText("Brak powtórek na dziś")).toBeInTheDocument();
  });
});
