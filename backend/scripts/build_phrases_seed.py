"""Convert the phrase tables in resources/communication-phrases-pl.md into the seed JSON.

Run from the repository root after editing the markdown:
    uv --directory backend run python scripts/build_phrases_seed.py

Only tables inside the tier sections ("POZIOM 1-3") and "Pułapki" are converted;
section 3.4 and level 4 have no tables and are skipped on purpose.
"""

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "resources" / "communication-phrases-pl.md"
TARGET = (
    REPO_ROOT
    / "backend/src/english_app/modules/phrases/seed/communication_phrases.json"
)

TIER_HEADING = re.compile(r"^## .*POZIOM (\d)\s+—\s+(.+)$")
PITFALLS_HEADING = re.compile(r"^## .*Pułapki dla Polaków")
SECTION_HEADING = re.compile(r"^### \[ \] (?:(\d\.\d+) )?(.+)$")
OTHER_H2 = re.compile(r"^## ")
TABLE_SEPARATOR = re.compile(r"^\|\s*-+")
MARKDOWN_EMPHASIS = re.compile(r"\*\*|(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)|`")


@dataclass
class SeedPhrase:
    tier: str
    tier_title: str
    section_code: str
    section_title: str
    position: int
    english: str
    polish: str
    example: str | None
    note: str | None
    kind: str


def clean(cell: str) -> str:
    return MARKDOWN_EMPHASIS.sub("", cell).strip()


def split_row(line: str) -> list[str]:
    # Escaped pipes (\|) belong to the cell text.
    cells = re.split(r"(?<!\\)\|", line.strip().strip("|"))
    return [clean(cell.replace("\\|", "|")) for cell in cells]


def to_phrase(header: list[str], cells: list[str], base: dict[str, object]) -> SeedPhrase:
    first = header[0].lower()
    example: str | None = None
    note: str | None = None
    kind = "phrase"
    if first.startswith("❌"):
        # | ❌ Źle | ✅ Dobrze | Dlaczego |
        wrong, right, why = cells[:3]
        english, polish, note, kind = right, why, f"Nie mów: {wrong}", "common_error"
    elif first.startswith("angielskie"):
        # | Angielskie słowo | Znaczy | NIE znaczy... | ...bo to po angielsku |
        word, meaning, not_meaning, instead = cells[:4]
        english, polish = word, meaning
        note = f"Nie myl z „{not_meaning}” (to po angielsku: {instead})"
        kind = "false_friend"
    else:
        english, polish = cells[0], cells[1]
        example = cells[2] if len(cells) > 2 and cells[2] else None
        if first == "phrasal verb":
            kind = "phrasal_verb"
        elif first in ("czasownik", "english") and len(cells) > 2:
            kind = "word"
    return SeedPhrase(
        english=english, polish=polish, example=example, note=note, kind=kind, **base  # type: ignore[arg-type]
    )


def parse(markdown: str) -> list[SeedPhrase]:
    phrases: list[SeedPhrase] = []
    tier: str | None = None
    tier_title = ""
    section_code = ""
    section_title = ""
    pitfall_index = 0
    header: list[str] | None = None

    for line in markdown.splitlines():
        if match := TIER_HEADING.match(line):
            tier, tier_title = match.group(1), clean(match.group(2))
            header = None
            continue
        if PITFALLS_HEADING.match(line):
            tier, tier_title = "pitfalls", "Pułapki dla Polaków"
            header = None
            continue
        if OTHER_H2.match(line):
            tier = None
            header = None
            continue
        if tier is None:
            continue
        if match := SECTION_HEADING.match(line):
            if match.group(1):
                section_code = match.group(1)
            else:
                pitfall_index += 1
                section_code = f"P.{pitfall_index}"
            section_title = clean(match.group(2))
            header = None
            continue
        if not line.startswith("|"):
            header = None
            continue
        if TABLE_SEPARATOR.match(line):
            continue
        cells = split_row(line)
        if header is None:
            header = cells
            continue
        base = {
            "tier": tier,
            "tier_title": tier_title,
            "section_code": section_code,
            "section_title": section_title,
            "position": len(phrases) + 1,
        }
        phrases.append(to_phrase(header, cells, base))
    return phrases


def main() -> int:
    phrases = parse(SOURCE.read_text(encoding="utf-8"))
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(
        json.dumps([asdict(p) for p in phrases], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    sections = sorted({p.section_code for p in phrases})
    print(f"Wrote {len(phrases)} phrases in {len(sections)} sections to {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
