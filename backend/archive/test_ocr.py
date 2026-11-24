from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import Mock, call, patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import CommandError, call_command
from django.test import TestCase

from .models import Document
from .ocr import OCRFailed
from .test_search import make_pdf


class OCRIndexTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="ocr-owner")

    def setUp(self):
        media = self.enterContext(TemporaryDirectory())
        self.enterContext(self.settings(MEDIA_ROOT=media))
        self.client.force_login(self.owner)

    def create_document(self, content):
        return Document.objects.create(
            owner=self.owner,
            original=ContentFile(content, name="original.pdf"),
            original_name="original.pdf",
            title="Лабораторный бланк",
            study_date="2026-10-01",
        )

    def run_index(self, ocr, **options):
        errors = StringIO()
        with patch("archive.management.commands.index_documents.PageOCR.available", return_value=ocr):
            call_command("index_documents", once=True, stdout=StringIO(), stderr=errors, **options)
        return errors.getvalue()

    def test_mixed_pdf_prefers_native_text_and_indexes_ocr_on_the_original_page(self):
        original = make_pdf("Нативный текст", "", "")
        document = self.create_document(original)
        ocr = Mock()

        def recognize(pdf, number):
            self.assertEqual(pdf.read_bytes(), original)
            self.assertEqual(pdf.parent.stat().st_mode & 0o777, 0o700)
            return "\n Результат    ТТГ 2.35 \n" if number == 2 else "\n\f"

        ocr.read_page.side_effect = recognize
        self.run_index(ocr)

        source = ocr.read_page.call_args.args[0]
        self.assertEqual(ocr.read_page.call_args_list, [call(source, 2), call(source, 3)])
        self.assertFalse(source.parent.exists())
        document.refresh_from_db()
        self.assertEqual(document.index_status, Document.IndexStatus.READY)
        self.assertEqual(list(document.indexed_pages.order_by("number").values_list("number", "text")), [
            (1, "Нативный текст"), (2, "Результат ТТГ 2.35"),
        ])
        match, = self.client.get("/api/documents/", {"q": "ттг"}).json()
        self.assertEqual(match["search_match"], {"page": 2, "excerpt": "Результат ТТГ 2.35"})

    def test_retry_no_text_reindexes_a_scan_once_with_ocr(self):
        document = self.create_document(make_pdf(""))
        self.run_index(None)
        document.refresh_from_db()
        self.assertEqual(document.index_status, Document.IndexStatus.NO_TEXT)
        with self.assertRaises(CommandError):
            self.run_index(None, retry_no_text=True)
        document.refresh_from_db()
        self.assertEqual(document.index_status, Document.IndexStatus.NO_TEXT)

        ocr = Mock()
        ocr.read_page.return_value = "Результат"
        self.run_index(ocr)
        ocr.read_page.assert_not_called()
        self.run_index(ocr, retry_no_text=True)
        ocr.read_page.assert_called_once()
        document.refresh_from_db()
        self.assertEqual(document.index_status, Document.IndexStatus.READY)

    def test_retry_ready_reindexes_scans_in_a_previously_indexed_mixed_pdf(self):
        document = self.create_document(make_pdf("Нативный текст", ""))
        self.run_index(None)
        document.refresh_from_db()
        self.assertEqual(document.index_status, Document.IndexStatus.READY)
        self.assertEqual(document.indexed_pages.count(), 1)

        with self.assertRaises(CommandError):
            self.run_index(None, retry_ready=True)
        ocr = Mock()
        ocr.read_page.return_value = "Результат OCR"
        self.run_index(ocr, retry_ready=True)
        self.assertEqual(list(document.indexed_pages.order_by("number").values_list("number", "text")), [
            (1, "Нативный текст"), (2, "Результат OCR"),
        ])

    def test_failed_ocr_keeps_other_pages_searchable_and_can_be_retried(self):
        document = self.create_document(make_pdf("Антитела", "", ""))
        ocr = Mock()
        ocr.read_page.side_effect = [OCRFailed(), "Глюкоза"]
        self.assertIn(str(document.pk), self.run_index(ocr))
        document.refresh_from_db()
        self.assertEqual(document.index_status, Document.IndexStatus.FAILED)
        self.assertEqual(list(document.indexed_pages.order_by("number").values_list("number", "text")), [
            (1, "Антитела"), (3, "Глюкоза"),
        ])

        self.run_index(None, retry_failed=True)
        document.refresh_from_db()
        self.assertEqual(document.index_status, Document.IndexStatus.FAILED)
        self.assertEqual(document.indexed_pages.count(), 2)

        ocr.read_page.side_effect = [OCRFailed(), OCRFailed()]
        self.run_index(ocr, retry_failed=True)
        self.assertEqual(document.indexed_pages.get(number=3).text, "Глюкоза")

        ocr.read_page.side_effect = ["Результат", "Глюкоза"]
        self.run_index(ocr, retry_failed=True)
        document.refresh_from_db()
        self.assertEqual(document.index_status, Document.IndexStatus.READY)
        self.assertEqual(document.indexed_pages.count(), 3)
