import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { mockApi, renderWithApp } from "@/test/utils";

import { SettingsPage } from "./settings-page";

const settings = (main: string | null, override: string | null = null) => ({
  provider: "claude_code",
  tiers: [
    { tier: "main", env_model: "claude-opus-5-5", override, effective: main },
    { tier: "fast", env_model: "claude-haiku-5-5", override: null, effective: "claude-haiku-5-5" },
  ],
});

function renderSettings() {
  let current = settings("claude-opus-5-5");
  const api = mockApi({
    "GET /api/llm/status": () => ({
      provider: "claude_code",
      available: true,
      detail: null,
      models: { main: "claude-opus-5-5", fast: "claude-haiku-5-5" },
    }),
    "GET /api/llm/models": () => [
      { id: "claude-opus-5-5", name: "claude-opus-5-5", source: "config" },
      { id: "claude-haiku-5-5", name: "claude-haiku-5-5", source: "config" },
    ],
    "GET /api/llm/settings": () => current,
    "PUT /api/llm/settings": (body) => {
      const main = (body as { main?: string | null }).main ?? null;
      current = settings(main ?? "claude-opus-5-5", main);
      return current;
    },
    "POST /api/llm/test": () => ({ ok: true, model: "claude-opus-5-5", latency_ms: 1234, detail: null }),
    "GET /api/profile": () => ({
      display_name: "Ola",
      level: "B1",
      target_level: null,
      native_language: "pl",
      goals: [],
      daily_goal_xp: 30,
      onboarding_done: true,
      created_at: "2026-11-12T10:00:00Z",
    }),
  });
  renderWithApp([{ path: "/settings", element: <SettingsPage /> }], "/settings");
  return api;
}

describe("SettingsPage → Model AI", () => {
  it("saves a custom model id with allow_custom", async () => {
    const user = userEvent.setup();
    const { calls } = renderSettings();

    const select = await screen.findByLabelText("Model główny: wybór modelu");
    await waitFor(() => expect(within(select).getAllByRole("option")).toHaveLength(4));
    await user.selectOptions(select, "__custom__");
    await user.clear(screen.getByLabelText("Własny identyfikator modelu"));
    await user.type(screen.getByLabelText("Własny identyfikator modelu"), "sonnet");
    await user.click(screen.getAllByRole("button", { name: /Zapisz$/ })[0]!);

    await waitFor(() =>
      expect(calls.find((c) => c.key === "PUT /api/llm/settings")?.body).toEqual({
        main: "sonnet",
        allow_custom: true,
      }),
    );
  });

  it("tests the selected model and shows the latency", async () => {
    const user = userEvent.setup();
    const { calls } = renderSettings();

    await screen.findByLabelText("Model główny: wybór modelu");
    await user.click(screen.getAllByRole("button", { name: /Testuj/ })[0]!);

    expect(await screen.findByText(/odpowiedział w 1.2 s/)).toBeInTheDocument();
    expect(calls.find((c) => c.key === "POST /api/llm/test")?.body).toEqual({ model: "claude-opus-5-5" });
  });

  it("restores the .env model by sending null", async () => {
    const user = userEvent.setup();
    const { calls } = renderSettings();
    const select = await screen.findByLabelText("Model główny: wybór modelu");
    await waitFor(() => expect(within(select).getAllByRole("option")).toHaveLength(4));
    await user.selectOptions(select, "claude-haiku-5-5");
    await user.click(screen.getAllByRole("button", { name: /Zapisz$/ })[0]!);

    await user.click(await screen.findByRole("button", { name: /Przywróć z .env/ }));

    await waitFor(() => expect(calls.filter((c) => c.key === "PUT /api/llm/settings").at(-1)?.body).toEqual({
      main: null,
      allow_custom: false,
    }));
  });
});
