import { afterEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";

import { ApiError, errorMessage, request } from "./client";

const schema = z.object({ status: z.string() });

function respond(status: number, body: unknown, raw = false) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(raw ? String(body) : JSON.stringify(body), { status })),
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("request", () => {
  it("validates and returns the body", async () => {
    respond(200, { status: "ok" });

    await expect(request("/health", schema)).resolves.toEqual({ status: "ok" });
  });

  it("sends JSON with a content type and the /api prefix", async () => {
    respond(200, { status: "ok" });

    await request("/x", schema, { method: "POST", body: JSON.stringify({ a: 1 }) });

    const [url, init] = vi.mocked(fetch).mock.calls[0]!;
    expect(url).toBe("/api/x");
    expect(new Headers(init?.headers).get("Content-Type")).toBe("application/json");
  });

  it("turns the unified error body into ApiError with the Polish message", async () => {
    respond(503, { error: { code: "llm_unavailable", message: "Model AI jest niedostępny." } });

    const error = await request("/llm/test", schema).catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 503, code: "llm_unavailable", message: "Model AI jest niedostępny." });
    expect(errorMessage(error)).toBe("Model AI jest niedostępny.");
  });

  it("handles errors that are not JSON", async () => {
    respond(500, "boom", true);

    await expect(request("/x", schema)).rejects.toMatchObject({ code: "http_error", status: 500 });
  });

  it("reports a missing server as a network error", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => Promise.reject(new TypeError("Failed to fetch"))));

    await expect(request("/x", schema)).rejects.toMatchObject({ code: "network_error", status: 0 });
  });

  it("rejects responses that do not match the schema", async () => {
    respond(200, { status: 42 });

    await expect(request("/x", schema)).rejects.toThrow();
  });

  it("accepts an empty 204 response", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(null, { status: 204 })));

    await expect(request("/x", z.undefined())).resolves.toBeUndefined();
  });
});
