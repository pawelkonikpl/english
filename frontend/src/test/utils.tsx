import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { MotionConfig } from "motion/react";
import type { ReactElement } from "react";
import { createMemoryRouter, RouterProvider, type RouteObject } from "react-router";
import { vi } from "vitest";

import { ThemeProvider } from "@/app/theme";

type Handler = (body: unknown) => { status?: number; body?: unknown } | unknown;

/** Replaces fetch with a tiny router: keys are "METHOD /api/path" (query string ignored). */
export function mockApi(routes: Record<string, Handler>) {
  const calls: { key: string; body: unknown }[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), "http://localhost");
    const key = `${init?.method ?? "GET"} ${url.pathname}`;
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ key, body });
    const handler = routes[key];
    if (!handler) {
      return new Response(JSON.stringify({ error: { code: "not_found", message: `No mock for ${key}` } }), {
        status: 404,
      });
    }
    const result = handler(body);
    const isEnvelope = typeof result === "object" && result !== null && "status" in result;
    const status = isEnvelope ? ((result as { status?: number }).status ?? 200) : 200;
    const payload = isEnvelope ? (result as { body?: unknown }).body : result;
    return status === 204
      ? new Response(null, { status })
      : new Response(JSON.stringify(payload), { status, headers: { "Content-Type": "application/json" } });
  });
  vi.stubGlobal("fetch", fetchMock);
  return { calls, fetchMock };
}

export function renderWithApp(routes: RouteObject[], initialPath = "/") {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const router = createMemoryRouter(routes, { initialEntries: [initialPath] });
  const ui: ReactElement = (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <MotionConfig reducedMotion="always">
          <RouterProvider router={router} />
        </MotionConfig>
      </ThemeProvider>
    </QueryClientProvider>
  );
  return { router, ...render(ui) };
}
