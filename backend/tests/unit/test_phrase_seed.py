import importlib.util
import json
from collections import Counter
from pathlib import Path

from english_app.modules.phrases.seed import SEED_FILE

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "build_phrases_seed.py"


def load_script():
    spec = importlib.util.spec_from_file_location("build_phrases_seed", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def table_rows_in_tier_sections(markdown: str) -> int:
    """Data rows of every table in the markdown, minus the 4-week plan table."""
    plan_rows = 4
    total = rows_in_current_table = 0
    for line in [*markdown.splitlines(), ""]:
        is_separator = line.replace("|", "").replace("-", "").strip() == ""
        if line.startswith("|"):
            rows_in_current_table += 0 if is_separator else 1
        elif rows_in_current_table:
            total += rows_in_current_table - 1  # minus the header row
            rows_in_current_table = 0
    return total - plan_rows


def test_seed_has_one_phrase_per_table_row_in_the_markdown() -> None:
    script = load_script()
    markdown = script.SOURCE.read_text(encoding="utf-8")

    phrases = script.parse(markdown)

    assert len(phrases) == table_rows_in_tier_sections(markdown) == 239


def test_committed_seed_file_matches_the_markdown() -> None:
    script = load_script()
    parsed = [vars(p) for p in script.parse(script.SOURCE.read_text(encoding="utf-8"))]

    assert json.loads(SEED_FILE.read_text(encoding="utf-8")) == parsed


def test_seed_sections_and_kinds() -> None:
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    sections = Counter(item["section_code"] for item in data)

    assert len(sections) == 19
    assert sections["1.1"] == 10
    assert {item["kind"] for item in data if item["section_code"] == "P.1"} == {"false_friend"}
    assert {item["kind"] for item in data if item["section_code"] == "3.2"} == {"phrasal_verb"}
    assert [item["position"] for item in data] == list(range(1, len(data) + 1))
    assert all("**" not in item["english"] for item in data)
