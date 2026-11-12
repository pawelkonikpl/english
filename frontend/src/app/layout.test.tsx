import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { mockApi, renderWithApp } from "@/test/utils";

import { AppLayout, ModuleGate } from "./layout";

function profile(onboardingDone: boolean) {
  return {
    display_name: null,
    level: "A2",
    target_level: null,
    native_language: "pl",
    goals: [],
    daily_goal_xp: 30,
    onboarding_done: onboardingDone,
    created_at: "2026-11-12T10:00:00Z",
  };
}

const MODULES = [
  { key: "progress", title: "Postępy", icon: "x", nav_order: 0 },
  { key: "phrases", title: "Frazy", icon: "x", nav_order: 10 },
];

function render(onboardingDone: boolean, path = "/") {
  mockApi({
    "GET /api/profile": () => profile(onboardingDone),
    "GET /api/modules": () => MODULES,
    "GET /api/llm/status": () => ({ provider: "fake", available: true, detail: null, models: {} }),
  });
  return renderWithApp(
    [
      { path: "/onboarding", element: <p>ONBOARDING</p> },
      {
        element: <AppLayout />,
        children: [
          { index: true, element: <p>HOME</p> },
          {
            path: "lessons",
            element: (
              <ModuleGate moduleKey="lessons">
                <p>LESSONS</p>
              </ModuleGate>
            ),
          },
        ],
      },
    ],
    path,
  );
}

describe("AppLayout", () => {
  it("sends a first-time user to onboarding", async () => {
    render(false);

    expect(await screen.findByText("ONBOARDING")).toBeInTheDocument();
  });

  it("lets an onboarded user in and shows only enabled modules in the menu", async () => {
    render(true);

    expect(await screen.findByText("HOME")).toBeInTheDocument();
    expect((await screen.findAllByRole("link", { name: /Frazy/ })).length).toBeGreaterThan(0);
    expect(screen.queryByRole("link", { name: /Lekcje/ })).not.toBeInTheDocument();
  });

  it("shows a notice instead of a disabled module's page", async () => {
    render(true, "/lessons");

    expect(await screen.findByText("Ten moduł jest wyłączony")).toBeInTheDocument();
    expect(screen.queryByText("LESSONS")).not.toBeInTheDocument();
  });
});
