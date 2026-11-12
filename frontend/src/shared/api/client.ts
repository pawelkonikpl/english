import { z } from "zod";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

const errorBodySchema = z.object({
  error: z.object({ code: z.string(), message: z.string() }),
});

const API_BASE_URL = "/api";
const NETWORK_ERROR_MESSAGE = "Brak połączenia z aplikacją. Czy serwer jest uruchomiony?";

/** The only place that calls fetch: turns HTTP errors into ApiError and validates responses. */
export async function request<T>(
  path: string,
  schema: z.ZodType<T>,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  } catch (error) {
    throw new ApiError(0, "network_error", NETWORK_ERROR_MESSAGE, { cause: error });
  }

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const parsed = errorBodySchema.safeParse(body);
    if (parsed.success) {
      throw new ApiError(response.status, parsed.data.error.code, parsed.data.error.message);
    }
    throw new ApiError(response.status, "http_error", `Błąd serwera (${response.status}).`);
  }

  if (response.status === 204) {
    return schema.parse(undefined);
  }
  return schema.parse(await response.json());
}

export const json = (body: unknown): RequestInit => ({ body: JSON.stringify(body) });

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Coś poszło nie tak.";
}
