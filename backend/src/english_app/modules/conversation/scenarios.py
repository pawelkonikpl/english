import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

SCENARIOS_FILE = Path(__file__).parent / "seed" / "scenarios.json"


@dataclass(frozen=True)
class Scenario:
    key: str
    title: str
    emoji: str
    description: str
    ai_role: str
    learner_role: str
    goal: str


@cache
def all_scenarios() -> tuple[Scenario, ...]:
    raw = json.loads(SCENARIOS_FILE.read_text(encoding="utf-8"))
    return tuple(Scenario(**item) for item in raw)


def find_scenario(key: str) -> Scenario | None:
    return next((s for s in all_scenarios() if s.key == key), None)
