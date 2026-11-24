from django.test import SimpleTestCase

from .area_suggestions import suggest_areas


class FilenameAreaSuggestionsTests(SimpleTestCase):
    areas = {
        "cardiology": "my-heart",
        "thyroid": "thyroid",
        "endocrinology": "endocrinology",
        "nephrology": "my-kidneys",
        "urology": "urology",
        "otolaryngology": "otolaryngology",
        "orthopedics": "orthopedics",
        "rheumatology": "rheumatology",
    }

    def test_recognizes_whole_words_and_phrases_across_common_separators(self):
        result = suggest_areas("2025-01-25_ЭКГ+УЗИ щитовидной-железы", self.areas)
        self.assertEqual(result, [
            {"slug": "my-heart", "matched_text": "ЭКГ", "auto_select": True},
            {"slug": "thyroid", "matched_text": "щитовидной железы", "auto_select": True},
        ])
        self.assertEqual(suggest_areas("Протокол ЛОР-врача", self.areas)[0]["slug"], "otolaryngology")

    def test_generic_titles_and_parts_of_unrelated_words_are_not_automatic(self):
        for title in ("МРТ", "Общие анализы", "Заключение", "Флора", "xЭКГ123", "ЭКО"):
            with self.subTest(title=title):
                self.assertEqual(suggest_areas(title, self.areas), [])

    def test_ambiguous_phrase_is_optional_and_explicit_specialty_resolves_it(self):
        result = suggest_areas("УЗИ почек", self.areas)
        self.assertEqual(result, [
            {"slug": "my-kidneys", "matched_text": "УЗИ почек", "auto_select": False},
            {"slug": "urology", "matched_text": "УЗИ почек", "auto_select": False},
        ])
        self.assertEqual(suggest_areas("УЗИ почек – заключение уролога", self.areas), [
            {"slug": "urology", "matched_text": "уролога", "auto_select": True},
        ])

    def test_only_mapped_areas_are_returned_and_duplicate_matches_use_one_reason(self):
        result = suggest_areas("ЭКГ; повторная ЭКГ; заключение эндокринолога", {"cardiology": "my-heart"})
        self.assertEqual(result, [{"slug": "my-heart", "matched_text": "ЭКГ", "auto_select": True}])
