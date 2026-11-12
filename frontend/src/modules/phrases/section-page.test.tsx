import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { mockApi, renderWithApp } from "@/test/utils";

import { SectionPage } from "./section-page";

const PHRASE = {
  id: 1,
  tier: "1",
  section_code: "1.1",
  section_title: "Gdy czegoś nie rozumiesz",
  english: "Sorry, could you say that again?",
  polish: "Przepraszam, możesz powtórzyć?",
  example: null,
  note: null,
  kind: "phrase",
  source: "seed",
  status: "new",
  mastery: 0,
  due_on: null,
  has_explanation: false,
};

function render(moduleKeys: string[]) {
  mockApi({
    "GET /api/phrases": () => [PHRASE],
    "GET /api/modules": () => moduleKeys.map((key, i) => ({ key, title: key, icon: "x", nav_order: i })),
  });
  renderWithApp([{ path: "/phrases/:code", element: <SectionPage /> }], "/phrases/1.1");
}

describe("SectionPage", () => {
  it("offers conversation practice when the conversation module is enabled", async () => {
    render(["phrases", "conversation"]);

    const link = await screen.findByRole("link", { name: /Przećwicz w rozmowie/ });

    expect(link).toHaveAttribute("href", "/conversation?section=1.1");
  });

  it("hides conversation practice when the conversation module is disabled", async () => {
    render(["phrases", "review"]);

    await screen.findByText("Sorry, could you say that again?");

    expect(screen.queryByRole("link", { name: /Przećwicz w rozmowie/ })).not.toBeInTheDocument();
  });
});
