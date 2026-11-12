import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ActivityHeatmap, heatLevel } from "./activity-heatmap";

const days = [
  { date: "2026-11-09", xp: 0, count: 0 }, // Monday
  { date: "2026-11-10", xp: 30, count: 12 },
  { date: "2026-11-11", xp: 5, count: 1 },
];

describe("heatLevel", () => {
  it.each([
    [0, 0],
    [5, 1],
    [7.5, 1],
    [10, 2],
    [20, 3],
    [30, 3],
    [31, 4],
    [45, 4],
    [46, 5],
  ])("%i XP with a 30 XP goal is level %i", (xp, level) => {
    expect(heatLevel(xp, 30)).toBe(level);
  });
});

describe("ActivityHeatmap", () => {
  it("summarises the period with Polish plurals", () => {
    render(<ActivityHeatmap days={days} goal={30} />);

    expect(screen.getByText("Ostatnie 3 dni: 2 aktywne dni, 35 XP")).toBeInTheDocument();
  });

  it("shows one cell per day and the details of a hovered day", () => {
    render(<ActivityHeatmap days={days} goal={30} />);

    const cells = screen.getAllByRole("gridcell");
    fireEvent.mouseEnter(cells[2]!);

    expect(cells).toHaveLength(3);
    expect(screen.getByText(/11 listopada: 5 XP, 1 aktywność/)).toBeInTheDocument();
  });

  it("uses the singular for one active day", () => {
    render(<ActivityHeatmap days={days.slice(2)} goal={30} />);

    expect(screen.getByText(/1 aktywny dzień/)).toBeInTheDocument();
  });
});
