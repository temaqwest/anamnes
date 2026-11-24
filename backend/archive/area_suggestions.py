import re
from collections.abc import Mapping
from typing import TypedDict
from unicodedata import normalize


class AreaSuggestion(TypedDict):
    slug: str
    matched_text: str
    auto_select: bool


def whole_words(pattern):
    return re.compile(r"\b(?:" + pattern + r")\b", re.IGNORECASE)


STRONG_RULES = {
    "obstetrics_gynecology": whole_words(r"гинеколог[а-яё]*|акушер[а-яё]*"),
    "immunology": whole_words(r"аллерголог[а-яё]*|иммунолог[а-яё]*|аллергопроб[а-яё]*"),
    "gastroenterology": whole_words(r"гастроэнтеролог[а-яё]*|гастроскопи[а-яё]*|фгдс|эгдс"),
    "hematology": whole_words(r"гематолог[а-яё]*"),
    "hepatology": whole_words(r"гепатолог[а-яё]*|фиброскан[а-яё]*|эластографи[а-яё]* печени"),
    "dermatology": whole_words(r"дерматолог[а-яё]*|дерматоскопи[а-яё]*"),
    "cardiology": whole_words(r"кардиолог[а-яё]*|экг|эхокг|холтер[а-яё]*|электрокардиограмм[а-яё]*"),
    "neurology": whole_words(r"невролог[а-яё]*|невропатолог[а-яё]*|ээг|электроэнцефалограмм[а-яё]*"),
    "nephrology": whole_words(r"нефролог[а-яё]*"),
    "oncology": whole_words(r"онколог[а-яё]*"),
    "otolaryngology": whole_words(r"лор|оториноларинголог[а-яё]*|отоларинголог[а-яё]*"),
    "ophthalmology": whole_words(
        r"офтальмолог[а-яё]*|окулист[а-яё]*|окт (?:сетчатки|макулы|диска зрительного нерва)"
    ),
    "pulmonology": whole_words(r"пульмонолог[а-яё]*|спирометри[а-яё]*|спирографи[а-яё]*"),
    "rheumatology": whole_words(r"ревматолог[а-яё]*"),
    "orthopedics": whole_words(r"травматолог[а-яё]*|ортопед[а-яё]*"),
    "urology": whole_words(r"уролог[а-яё]*"),
    "thyroid": whole_words(r"щитовидн[а-яё]* желез[а-яё]*|ттг"),
    "endocrinology": whole_words(r"эндокринолог[а-яё]*"),
}

AMBIGUOUS_RULES = (
    (whole_words(r"узи (?:почек|почки)"), ("nephrology", "urology")),
    (whole_words(r"(?:мрт|кт|рентген(?:ография)?) (?:колена|коленн[а-яё]* сустав[а-яё]*)"),
     ("orthopedics", "rheumatology")),
)


def suggest_areas(title: str, personal_slugs: Mapping[str, str]) -> list[AreaSuggestion]:
    words = re.sub(r"[\W_]+", " ", normalize("NFKC", title))
    matches: dict[str, AreaSuggestion] = {}
    for preset, pattern in STRONG_RULES.items():
        if (slug := personal_slugs.get(preset)) and (match := pattern.search(words)):
            matches[preset] = {"slug": slug, "matched_text": match.group(), "auto_select": True}

    strong = set(matches)
    for pattern, presets in AMBIGUOUS_RULES:
        if strong.intersection(presets) or not (match := pattern.search(words)):
            continue
        for preset in presets:
            if (slug := personal_slugs.get(preset)) and preset not in matches:
                matches[preset] = {"slug": slug, "matched_text": match.group(), "auto_select": False}
    return list(matches.values())
