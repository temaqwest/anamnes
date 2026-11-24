from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class AllergyApiTests(TestCase):
    url = "/api/allergies/"

    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="allergy-owner")
        cls.other = get_user_model().objects.create_user(username="allergy-other")

    def setUp(self):
        self.client.force_login(self.owner)

    def create(self, **fields):
        return self.client.post(self.url, fields, content_type="application/json")

    def test_adds_an_allergen_to_the_list(self):
        empty = self.client.get(self.url)
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json(), [])
        created = self.create(name="  Пыльца   берёзы  ")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["name"], "Пыльца берёзы")
        self.assertIn("no-store", created.headers["Cache-Control"])

        listed = self.client.get(self.url)
        self.assertEqual(listed.json(), [created.json()])
        self.assertIn("no-store", listed.headers["Cache-Control"])

    def test_rejects_invalid_names(self):
        for name in ("   ", "а" * 161):
            with self.subTest(name=name):
                response = self.create(name=name)
                self.assertEqual(response.status_code, 400)
                self.assertIn("name", response.json())

    def test_rejects_duplicate_names_for_each_owner(self):
        self.assertEqual(self.create(name="Домашняя пыль").status_code, 201)
        duplicate = self.create(name=" дОМАШНЯЯ  пыль ")
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("name", duplicate.json())
        self.assertEqual(len(self.client.get(self.url).json()), 1)

        self.client.force_login(self.other)
        self.assertEqual(self.create(name="Домашняя пыль").status_code, 201)

    def test_only_the_signed_in_owner_can_list_records(self):
        created = self.create(name="Шерсть кошки", owner=self.other.pk)
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.client.get(self.url).json(), [created.json()])

        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).json(), [])

        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.create(name="Шерсть кошки").status_code, 403)

    def test_addition_requires_csrf(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.owner)
        self.assertEqual(self.create(name="Шерсть кошки").status_code, 403)
