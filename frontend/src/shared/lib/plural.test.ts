import { describe, expect, it } from "vitest";

import { plural } from "./plural";

describe("plural", () => {
  it.each([
    [1, "dzień"],
    [2, "dni (few)"],
    [4, "dni (few)"],
    [5, "dni (many)"],
    [12, "dni (many)"],
    [14, "dni (many)"],
    [22, "dni (few)"],
    [0, "dni (many)"],
  ])("picks the Polish form for %i", (n, expected) => {
    expect(plural(n, "dzień", "dni (few)", "dni (many)")).toBe(expected);
  });
});
