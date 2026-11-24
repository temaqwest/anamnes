from io import BytesIO, StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase
from pypdf import PdfWriter

from .models import Document, DocumentPage
from .study_areas import areas_for


class ArchiveTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="owner", password="example-password")
        cls.other = get_user_model().objects.create_user(username="other")
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        buffer = BytesIO()
        writer.write(buffer)
        cls.pdf = buffer.getvalue()

    def setUp(self):
        self.client.force_login(self.owner)
        media = self.enterContext(TemporaryDirectory())
        self.enterContext(self.settings(MEDIA_ROOT=media))

    def upload(self, title="УЗИ", date="2025-03-14", content=None, areas=None, upload_key=None, category=None):
        return self.client.post("/api/documents/", {
            "file": SimpleUploadedFile("2025-03-14_УЗИ.pdf", self.pdf if content is None else content),
            "title": title,
            "study_date": date,
            "areas": areas or [],
            **({"upload_key": upload_key} if upload_key else {}),
            **({"category": category} if category is not None else {}),
        })

    def test_suggestions_handle_valid_missing_and_ambiguous_dates(self):
        response = self.client.post(
            "/api/documents/suggestions/",
            {"names": ["2025-03-14_УЗИ_щитовидной_железы.pdf", "Анализы_17.02.2025.pdf",
                       "Анализы.pdf", "31.02.2025_Анализы.pdf", "2025-03-14_Анализы_2025-04-14.pdf"]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [
            {"title": "УЗИ щитовидной железы", "study_date": "2025-03-14", "area_suggestions": [
                {"slug": "thyroid", "matched_text": "щитовидной железы", "auto_select": True},
            ]},
            {"title": "Анализы", "study_date": "2025-02-17", "area_suggestions": []},
            {"title": "Анализы", "study_date": None, "area_suggestions": []},
            {"title": "Анализы", "study_date": None, "area_suggestions": []},
            {"title": "2025-03-14 Анализы 2025-04-14", "study_date": None, "area_suggestions": []},
        ])

    def test_area_suggestions_use_current_owners_personal_area_and_do_not_save_documents(self):
        area = areas_for(self.owner).get(slug="cardiology")
        area.slug = "personal-heart"
        area.name = "Сердце"
        area.save(update_fields=["slug", "name"])
        url = "/api/documents/suggestions/"
        batch = {"names": ["2025-03-14_ЭКГ.pdf", "2025-03-14_УЗИ_почек.pdf"]}

        response = self.client.post(url, batch, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        cardiac, kidneys = [item["area_suggestions"] for item in response.json()]
        self.assertEqual(cardiac, [{"slug": "personal-heart", "matched_text": "ЭКГ", "auto_select": True}])
        self.assertEqual({item["slug"] for item in kidneys}, {"nephrology", "urology"})
        self.assertTrue(all(not item["auto_select"] for item in kidneys))
        self.assertFalse(Document.objects.exists())

        self.client.force_login(self.other)
        other = self.client.post(url, batch, content_type="application/json")
        self.assertEqual(other.json()[0]["area_suggestions"][0]["slug"], "cardiology")
        self.assertEqual(Client().post(url, batch, content_type="application/json").status_code, 403)

    def test_upload_preserves_original_and_uses_confirmed_metadata(self):
        response = self.upload(title="Дуплекс", date="2025-03-12")
        self.assertEqual(response.status_code, 201)
        document = response.json()
        self.assertEqual(document["original_name"], "2025-03-14_УЗИ.pdf")
        self.assertEqual((document["title"], document["study_date"]), ("Дуплекс", "2025-03-12"))
        original = self.client.get(document["file_url"])
        self.assertEqual(original.status_code, 200)
        self.assertEqual(original["Content-Type"], "application/pdf")
        self.assertIn("no-store", original["Cache-Control"])
        self.assertEqual(b"".join(original.streaming_content), self.pdf)

    def test_pdf_validation_does_not_add_a_broken_document(self):
        self.assertEqual(self.upload(content=b"%PDF-1.7\nno body").status_code, 400)
        self.assertEqual(self.client.get("/api/documents/").json(), [])

    def test_category_is_optional_for_older_clients_and_can_be_changed(self):
        document = self.upload().json()
        self.assertEqual(document["category"], "")
        url = f"/api/documents/{document['id']}/"
        update = self.client.patch(url, {"category": "examination"}, content_type="application/json")
        self.assertEqual(update.status_code, 200)
        self.assertEqual(self.client.get(url).json()["category"], "examination")

    def test_upload_accepts_supported_categories_and_rejects_other_values(self):
        self.assertEqual(self.upload(category="lab").json()["category"], "lab")
        self.assertEqual(self.upload(category="unsupported").status_code, 400)

    def test_retrying_the_same_upload_does_not_duplicate_the_document(self):
        key = "f093b8ad-c988-43f1-a719-812cde1f33e1"
        first = self.upload(upload_key=key).json()
        repeated = self.upload(upload_key=key).json()
        self.assertEqual(repeated["id"], first["id"])
        self.assertEqual(len(self.client.get("/api/documents/").json()), 1)

    def test_other_user_cannot_see_or_retrieve_pdf(self):
        document = self.upload().json()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get("/api/documents/").json(), [])
        self.assertEqual(self.client.get(document["file_url"]).status_code, 404)
        self.assertEqual(Client().get(document["file_url"]).status_code, 403)

    def delete_documents(self, payload, client=None):
        with self.captureOnCommitCallbacks(execute=True):
            return (client or self.client).post("/api/documents/bulk-delete/", payload, content_type="application/json")

    def test_deleting_selected_documents_removes_originals_and_index_and_respects_ownership(self):
        first = self.upload(areas=["thyroid"]).json()
        second = self.upload(title="Другое исследование").json()
        self.client.force_login(self.other)
        foreign = self.upload().json()
        self.client.force_login(self.owner)
        entry = Document.objects.get(pk=first["id"])
        original = entry.original
        DocumentPage.objects.create(document=entry, number=1, text="ТТГ", search_text="ттг")

        response = self.delete_documents({"ids": [first["id"], first["id"], foreign["id"]]})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"deleted": 1})
        self.assertFalse(original.storage.exists(original.name))
        self.assertEqual(self.client.get(first["file_url"]).status_code, 404)
        self.assertFalse(DocumentPage.objects.filter(document_id=first["id"]).exists())
        self.assertEqual(Document.objects.count(), 2)
        self.assertTrue(Document.objects.filter(pk=second["id"]).exists())
        self.assertTrue(Document.objects.filter(pk=foreign["id"]).exists())
        self.assertEqual(self.delete_documents({"ids": [first["id"]]}).json(), {"deleted": 0})

    def test_delete_all_covers_the_whole_archive_and_keeps_areas(self):
        thyroid = self.upload(areas=["thyroid"]).json()
        heart = self.upload(areas=["cardiology"]).json()
        self.client.force_login(self.other)
        foreign = self.upload().json()
        self.client.force_login(self.owner)
        files = [Document.objects.get(pk=item["id"]).original for item in (thyroid, heart)]
        areas = self.client.get("/api/areas/").json()

        response = self.delete_documents({"all": True})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"deleted": 2})
        self.assertEqual(self.client.get("/api/documents/").json(), [])
        self.assertEqual(self.client.get("/api/areas/").json(), areas)
        self.assertTrue(Document.objects.filter(pk=foreign["id"]).exists())
        for original in files:
            self.assertFalse(original.storage.exists(original.name))

    def test_delete_rejects_ambiguous_payloads_and_requires_authentication_and_csrf(self):
        entry = self.upload().json()
        for payload in ({}, {"all": False}, {"ids": []}, {"ids": ["invalid"]}, {"all": True, "ids": [entry["id"]]}):
            self.assertEqual(self.delete_documents(payload).status_code, 400)
        self.assertEqual(self.delete_documents({"all": True}, Client()).status_code, 403)
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.owner)
        self.assertEqual(self.delete_documents({"all": True}, browser).status_code, 403)
        self.assertTrue(Document.objects.filter(pk=entry["id"]).exists())

    def test_failed_file_removal_can_be_retried_without_restoring_the_document(self):
        item = self.upload().json()
        original = Document.objects.get(pk=item["id"]).original
        with patch.object(original.storage, "delete", side_effect=PermissionError):
            with self.assertLogs("archive.deletion", level="WARNING"):
                response = self.delete_documents({"ids": [item["id"]]})
        self.assertEqual(response.json(), {"deleted": 1})
        self.assertFalse(Document.objects.filter(pk=item["id"]).exists())
        self.assertTrue(original.storage.exists(original.name))
        call_command("cleanup_deleted_originals", stdout=StringIO())
        self.assertFalse(original.storage.exists(original.name))

    def test_lists_newest_first_and_filters_by_study_area(self):
        self.assertEqual(self.upload(title="Ранний", date="2025-01-05", areas=["thyroid"]).status_code, 201)
        self.assertEqual(self.upload(title="Поздний", date="2025-05-16", areas=["cardiology"]).status_code, 201)
        self.assertEqual([d["title"] for d in self.client.get("/api/documents/").json()], ["Поздний", "Ранний"])
        self.assertEqual([d["title"] for d in self.client.get("/api/documents/?area=thyroid").json()], ["Ранний"])

    def test_edit_updates_metadata_and_keeps_original(self):
        document = self.upload().json()
        response = self.client.patch(
            f"/api/documents/{document['id']}/", {"title": "Новое имя", "areas": ["thyroid"]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Новое имя")
        self.assertEqual(response.json()["areas"], ["thyroid"])
        self.assertEqual(response.json()["original_name"], document["original_name"])

    def test_login_requires_csrf_and_establishes_a_private_session(self):
        browser = Client(enforce_csrf_checks=True)
        self.assertEqual(browser.get("/api/auth/session/").json(), {"username": None})
        payload = {"username": "owner", "password": "example-password"}
        self.assertEqual(browser.post("/api/auth/login/", payload, content_type="application/json").status_code, 403)
        token = browser.cookies["csrftoken"].value
        response = browser.post("/api/auth/login/", payload, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.json(), {"username": "owner"})
        self.assertEqual(browser.get("/api/documents/").status_code, 200)
