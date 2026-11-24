from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import StudyArea
from .test_search import make_pdf


class StudyAreaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="area-owner")
        cls.other = get_user_model().objects.create_user(username="area-other")

    def setUp(self):
        self.client.force_login(self.owner)
        media = self.enterContext(TemporaryDirectory())
        self.enterContext(self.settings(MEDIA_ROOT=media))

    def create_area(self, name):
        return self.client.post("/api/areas/", {"name": name}, content_type="application/json")

    def rename_area(self, slug, name):
        return self.client.patch(f"/api/areas/{slug}/", {"name": name}, content_type="application/json")

    def list_areas(self):
        return {area["slug"]: area["name"] for area in self.client.get("/api/areas/").json()}

    def upload(self, area):
        return self.client.post("/api/documents/", {
            "file": SimpleUploadedFile("fixture.pdf", make_pdf("PDF")),
            "title": "Контроль", "study_date": "2026-10-01", "areas": [area],
        })

    def test_create_normalizes_whitespace_and_prevents_duplicate_names(self):
        response = self.create_area("  Нефрология  и\tанализы  ")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.list_areas()[response.json()["slug"]], "Нефрология и анализы")
        self.assertEqual(self.create_area("НЕФРОЛОГИЯ и анализы").status_code, 400)
        self.assertEqual(self.create_area("Кардиология").status_code, 400)

    def test_new_archives_include_default_specialties_with_descriptions_and_keep_existing_areas(self):
        areas = {item["slug"]: item for item in self.client.get("/api/areas/").json()}
        expected = {
            "gastroenterology": "Гастроэнтерология",
            "pulmonology": "Пульмонология",
            "neurology": "Неврология",
            "endocrinology": "Эндокринология",
            "hematology": "Гематология",
            "rheumatology": "Ревматология",
            "dermatology": "Дерматология",
            "oncology": "Онкология",
            "immunology": "Аллергология и иммунология",
            "hepatology": "Гепатология",
            "obstetrics_gynecology": "Акушерство и гинекология",
            "nephrology": "Нефрология",
            "urology": "Урология",
            "otolaryngology": "Оториноларингология (ЛОР)",
            "ophthalmology": "Офтальмология",
            "orthopedics": "Травматология и ортопедия",
        }
        for slug, name in expected.items():
            with self.subTest(slug=slug):
                self.assertIn(slug, areas)
                self.assertEqual(areas[slug]["name"], name)
                self.assertTrue(areas[slug]["description"])
        self.assertEqual(set(areas) - set(expected), {"thyroid", "cardiology", "general"})
        self.assertEqual(
            dict(StudyArea.objects.filter(owner=self.owner).values_list("slug", "preset_id")),
            {slug: slug for slug in areas},
        )

    def test_can_create_edit_and_clear_a_private_description_without_renaming_the_area(self):
        created = self.client.post("/api/areas/", {
            "name": "Моя область", "description": "  Первая строка\nВторая строка  ",
        }, content_type="application/json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["description"], "Первая строка\nВторая строка")
        slug = created.json()["slug"]
        url = f"/api/areas/{slug}/"
        self.assertEqual(self.client.patch(url, {"description": "x" * 301}, content_type="application/json").status_code, 400)
        updated = self.client.patch(url, {"description": "Обновлено"}, content_type="application/json")
        self.assertEqual(updated.json(), {"slug": slug, "name": "Моя область", "description": "Обновлено"})
        self.assertEqual(self.rename_area(slug, "Личный раздел").json()["description"], "Обновлено")
        self.assertEqual(self.client.patch(url, {"description": ""}, content_type="application/json").json()["description"], "")

        self.client.force_login(self.other)
        self.assertEqual(self.client.patch(url, {"description": "Чужая подсказка"}, content_type="application/json").status_code, 404)

    def test_changing_a_default_description_is_private_and_survives_reloading_the_catalog(self):
        url = "/api/areas/gastroenterology/"
        self.assertEqual(self.client.patch(url, {"description": "Моя подсказка"}, content_type="application/json").status_code, 200)
        areas = {item["slug"]: item for item in self.client.get("/api/areas/").json()}
        self.assertEqual(areas["gastroenterology"]["description"], "Моя подсказка")
        self.client.force_login(self.other)
        areas = {item["slug"]: item for item in self.client.get("/api/areas/").json()}
        self.assertEqual(areas["gastroenterology"]["description"], "лечение желудочно-кишечного тракта")

    def test_renaming_initial_area_is_private_and_preserves_document_links(self):
        study = self.upload("thyroid")
        self.assertEqual(study.status_code, 201)
        self.assertEqual(self.rename_area("thyroid", "Щитовидка").status_code, 200)
        self.assertEqual(self.list_areas()["thyroid"], "Щитовидка")
        self.assertEqual(StudyArea.objects.get(owner=self.owner, slug="thyroid").preset_id, "thyroid")
        filtered = self.client.get("/api/documents/?area=thyroid").json()
        self.assertEqual([item["id"] for item in filtered], [study.json()["id"]])
        self.client.force_login(self.other)
        self.assertEqual(self.list_areas()["thyroid"], "Щитовидная железа")

    def test_other_user_cannot_list_rename_or_assign_a_private_area(self):
        response = self.create_area("Моя область")
        self.assertEqual(response.status_code, 201)
        slug = response.json()["slug"]
        self.client.force_login(self.other)
        self.assertNotIn(slug, self.list_areas())
        self.assertEqual(self.rename_area(slug, "Чужая область").status_code, 404)
        response = self.upload(slug)
        self.assertEqual(response.status_code, 400)
        self.assertIn("areas", response.json())
from tempfile import TemporaryDirectory

