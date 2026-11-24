import re
from datetime import date


YEAR_FIRST = re.compile(r"(?P<year>[0-9]{4})(?P<sep>[-.])(?P<month>[0-9]{2})(?P=sep)(?P<day>[0-9]{2})")
DAY_FIRST = re.compile(r"(?P<day>[0-9]{2})(?P<sep>[-.])(?P<month>[0-9]{2})(?P=sep)(?P<year>[0-9]{4})")


def suggest_metadata(filename: str) -> dict[str, str | None]:
    stem = filename[:-4] if filename.lower().endswith(".pdf") else filename
    parts = [part.strip() for part in stem.split("_") if part.strip()]
    candidates = []
    for index, part in enumerate(parts):
        match = YEAR_FIRST.fullmatch(part) or DAY_FIRST.fullmatch(part)
        if match:
            candidates.append((index, match))

    study_date = None
    if len(candidates) == 1:
        index, match = candidates[0]
        parts.pop(index)
        try:
            study_date = date(*(int(match[group]) for group in ("year", "month", "day"))).isoformat()
        except ValueError:
            pass

    return {"title": " ".join(parts), "study_date": study_date}
