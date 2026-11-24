from django.test import SimpleTestCase

from .area_suggestions import suggest_areas


class FilenameAreaSuggestionsTests(SimpleTestCase):
    areas = {
        "obstetrics_gynecology": "obstetrics_gynecology",
        "immunology": "immunology",
        "gastroenterology": "gastroenterology",
        "hematology": "hematology",
        "hepatology": "hepatology",
        "dermatology": "dermatology",
        "cardiology": "my-heart",
        "neurology": "neurology",
        "thyroid": "thyroid",
        "endocrinology": "endocrinology",
        "nephrology": "my-kidneys",
        "oncology": "oncology",
        "urology": "urology",
        "otolaryngology": "otolaryngology",
        "ophthalmology": "ophthalmology",
        "pulmonology": "pulmonology",
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

    def test_auto_selects_areas_for_specific_procedure_names(self):
        cases = (
            ("ПАП-тест", "obstetrics_gynecology"),
            ("Панель аллергенов ImmunoCAP", "immunology"),
            ("Анализ на H. pylori", "gastroenterology"),
            ("Пункция костного мозга", "hematology"),
            ("Anti-HCV", "hepatology"),
            ("Видеодерматоскопия", "dermatology"),
            ("СМАД", "my-heart"),
            ("МРТ головного мозга", "neurology"),
            ("Анализ мочи по Нечипоренко", "my-kidneys"),
            ("ПЭТ-КТ всего тела", "oncology"),
            ("КТ околоносовых пазух", "otolaryngology"),
            ("Измерение внутриглазного давления", "ophthalmology"),
            ("Рентген легких", "pulmonology"),
            ("Анти-ЦЦП", "rheumatology"),
            ("Артроскопия", "orthopedics"),
            ("ПСА свободный", "urology"),
            ("Св. Т4", "thyroid"),
            ("Т4 свободный", "thyroid"),
            ("ТТГ", "thyroid"),
            ("НbА1с", "endocrinology"),
        )
        for title, slug in cases:
            with self.subTest(title=title):
                result = suggest_areas(title, self.areas)
                self.assertEqual([(item["slug"], item["auto_select"]) for item in result], [(slug, True)])

    def test_requires_confirmation_for_shared_or_general_terms(self):
        cases = (
            ("Общий анализ мочи", {"my-kidneys", "urology"}),
            ("Флороценоз", {"obstetrics_gynecology", "urology"}),
            ("Мочевая кислота", {"my-kidneys", "rheumatology"}),
            ("С-реактивный белок", {"immunology", "rheumatology"}),
            ("МРТ коленного сустава", {"orthopedics", "rheumatology"}),
            ("Трепанобиопсия", {"hematology", "oncology"}),
            ("ОАК", {"hematology"}),
            ("АЛТ", {"hepatology"}),
            ("Рентген", {"orthopedics"}),
            ("Цитология", {"oncology"}),
        )
        for title, slugs in cases:
            with self.subTest(title=title):
                result = suggest_areas(title, self.areas)
                self.assertEqual({(item["slug"], item["auto_select"]) for item in result}, {(slug, False) for slug in slugs})

    def test_whole_words_keep_short_aliases_out_of_unrelated_names(self):
        self.assertEqual(suggest_areas("xСМАД12; ОКТябрь; ОАК2026; Алексей; АЛТАИР", self.areas), [])

    def test_general_terms_inside_specific_phrases_do_not_add_area_choices(self):
        cases = (
            ("Цитология щитовидной железы", [("thyroid", True)]),
            ("Цитологическое исследование щитовидной железы", [("thyroid", True)]),
            ("Жидкостная цитология", [("obstetrics_gynecology", True)]),
            ("Жидкостная цитология + гистология", [("obstetrics_gynecology", True), ("oncology", False)]),
            ("Рентген легких + рентген кисти", [("pulmonology", True), ("orthopedics", False)]),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                result = suggest_areas(title, self.areas)
                self.assertEqual([(item["slug"], item["auto_select"]) for item in result], expected)
