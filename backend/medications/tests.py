from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class MedicationApiTests(TestCase):
    url = "/api/medications/"

    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="medication-owner")
        cls.other = get_user_model().objects.create_user(username="medication-other")

    def setUp(self):
        self.client.force_login(self.owner)

    def create(self, **fields):
        return self.client.post(self.url, fields, content_type="application/json")

    def archive(self, medication, **fields):
        return self.client.post(
            f"{self.url}{medication['id']}/archive/", fields, content_type="application/json",
        )

    def test_regular_course_is_active_immediately_and_keeps_patient_text(self):
        response = self.create(
            name="  Пример А  ", dose="  1 мерная ложка ",
            course_type="regular", schedule="Утром и вечером", start_date="2026-11-17",
        )
        self.assertEqual(response.status_code, 201)
        saved = response.json()
        self.assertEqual(saved["name"], "Пример А")
        self.assertEqual(saved["dose"], "1 мерная ложка")
        self.assertEqual(saved["schedule"], "Утром и вечером")
        self.assertEqual(saved["start_date"], "2026-11-17")
        self.assertIsNone(saved["archived_at"])
        self.assertIsNone(saved["end_date"])
        listed = self.client.get(self.url)
        self.assertEqual(listed.json(), [saved])
        self.assertIn("no-store", listed.headers["Cache-Control"])

    def test_single_intake_saves_date_with_optional_time_and_dose(self):
        first = self.create(name="Пример Б", course_type="single", intake_date="2026-11-18")
        second = self.create(
            name="Пример Б", course_type="single", intake_date="2026-11-19", intake_time="08:10",
        )
        self.assertEqual((first.status_code, second.status_code), (201, 201))
        self.assertEqual(first.json()["dose"], "")
        self.assertIsNone(first.json()["intake_time"])
        self.assertEqual(second.json()["intake_date"], "2026-11-19")
        self.assertEqual(second.json()["intake_time"], "08:10:00")
        self.assertIsNone(second.json()["archived_at"])

    def test_regular_course_archive_keeps_details_and_supports_another_course(self):
        first = self.create(
            name="Пример В", dose="Записанная доза", course_type="regular", schedule="По будням",
            start_date="2026-11-19",
        ).json()
        response = self.archive(first)
        self.assertEqual(response.status_code, 400)
        self.assertIn("end_date", response.json())
        response = self.archive(first, end_date="2026-11-18")
        self.assertEqual(response.status_code, 400)
        self.assertIn("end_date", response.json())

        response = self.archive(first, end_date="2026-11-20")
        self.assertEqual(response.status_code, 200)
        archived = response.json()
        self.assertIsNotNone(archived["archived_at"])
        self.assertEqual(archived["end_date"], "2026-11-20")
        for field in ("name", "dose", "course_type", "schedule", "start_date", "created_at"):
            self.assertEqual(archived[field], first[field])
        retry = self.archive(first, end_date="2026-11-21")
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.json(), archived)

        second = self.create(
            name="Пример В", course_type="regular", schedule="По выходным", start_date="2026-11-22",
        )
        self.assertEqual(second.status_code, 201)
        self.assertNotEqual(second.json()["id"], first["id"])
        self.assertIsNone(second.json()["archived_at"])
        self.assertEqual(self.client.get(self.url).json(), [second.json(), archived])

    def test_single_intake_moves_to_history_with_its_original_date_and_time(self):
        medication = self.create(
            name="Пример Г", course_type="single", intake_date="2026-11-21", intake_time="19:30",
        ).json()
        self.assertEqual(self.archive(medication, end_date="2026-11-22").status_code, 400)
        response = self.archive(medication)
        self.assertEqual(response.status_code, 200)
        archived = response.json()
        self.assertEqual(archived["intake_date"], medication["intake_date"])
        self.assertEqual(archived["intake_time"], medication["intake_time"])
        self.assertIsNone(archived["end_date"])
        self.assertIsNotNone(archived["archived_at"])

    def test_validates_fields_for_each_intake_type(self):
        cases = [
            ({"name": "  "}, "name"),
            ({"course_type": "regular", "start_date": "2026-11-19"}, "schedule"),
            ({"course_type": "regular", "schedule": "Утром"}, "start_date"),
            ({"course_type": "regular", "schedule": "Утром", "start_date": "2026-11-19",
              "intake_time": "08:00"}, "intake_time"),
            ({"course_type": "regular", "schedule": "Утром", "start_date": "2026-11-19",
              "intake_date": "2026-11-19"}, "intake_date"),
            ({"course_type": "single"}, "intake_date"),
            ({"course_type": "single", "intake_date": "2026-11-31"}, "intake_date"),
            ({"course_type": "single", "intake_date": "2026-11-19", "intake_time": "24:30"}, "intake_time"),
            ({"course_type": "single", "intake_date": "2026-11-19", "schedule": "Утром"}, "schedule"),
            ({"course_type": "single", "intake_date": "2026-11-19", "start_date": "2026-11-19"}, "start_date"),
        ]
        for fields, field in cases:
            with self.subTest(fields=fields):
                response = self.create(**({"name": "Пример Д", "course_type": "single"} | fields))
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json())

    def test_records_are_private_and_archive_state_is_server_managed(self):
        hidden = self.create(
            name="Пример Е", course_type="single", intake_date="2026-11-20", owner=self.other.pk,
            end_date="2026-11-21", archived_at="2026-11-21T08:00:00Z",
        ).json()
        active = self.create(
            name="Пример Ж", course_type="regular", schedule="Утром", start_date="2026-11-19",
        ).json()
        self.assertIsNone(hidden["archived_at"])
        self.assertIsNone(hidden["end_date"])
        self.assertEqual(self.archive(hidden).status_code, 200)
        self.assertEqual(len(self.client.get(self.url).json()), 2)

        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).json(), [])
        self.assertEqual(self.archive(active, end_date="2026-11-21").status_code, 404)
        self.assertEqual(self.archive(hidden).status_code, 404)

        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.create(name="Пример З", course_type="single", intake_date="2026-11-19").status_code, 403)
        self.assertEqual(self.archive(hidden).status_code, 403)

    def test_mutations_require_csrf(self):
        medication = self.create(
            name="Пример И", course_type="regular", schedule="Утром", start_date="2026-11-19",
        ).json()
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.owner)
        self.assertEqual(self.create(name="Пример К", course_type="single", intake_date="2026-11-19").status_code, 403)
        self.assertEqual(self.archive(medication, end_date="2026-11-21").status_code, 403)
