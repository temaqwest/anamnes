from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from .models import Document


def make_pdf(*pages: str) -> bytes:
    writer = PdfWriter()
    cmap = DecodedStreamObject()
    cmap.set_data(b"""
        /CIDInit /ProcSet findresource begin
        12 dict begin begincmap
        /CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def
        /CMapName /TestCyrillic def /CMapType 2 def
        1 begincodespacerange <00> <FF> endcodespacerange
        2 beginbfrange
            <20> <7E> <0020>
            <C0> <FF> <0410>
        endbfrange
        endcmap CMapName currentdict /CMap defineresource pop end end
    """)
    font = writer._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
        NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
        NameObject("/ToUnicode"): writer._add_object(cmap),
    }))
    for text in pages:
        page = writer.add_blank_page(width=595, height=842)
        if text:
            page[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
            })
            stream = DecodedStreamObject()
            encoded = text.encode("cp1251").hex().encode("ascii")
            stream.set_data(b"BT /F1 16 Tf 72 740 Td <" + encoded + b"> Tj ET")
            page[NameObject("/Contents")] = writer._add_object(stream)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


class DocumentSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="archive-owner")
        cls.other = get_user_model().objects.create_user(username="other-owner")

    def setUp(self):
        self.client.force_login(self.owner)
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(self.settings(MEDIA_ROOT=directory))

    def upload(self, content, title="Анализы", area="thyroid", category=""):
        result = self.client.post("/api/documents/", {
            "file": SimpleUploadedFile("2026-10-01_Бланк.pdf", content),
            "title": title,
            "study_date": "2026-10-01",
            "areas": [area],
            "category": category,
        })
        self.assertEqual(result.status_code, 201)
        return result.json()

    def run_index(self, **options):
        call_command("index_documents", once=True, stdout=StringIO(), **options)

    def search(self, query, area=None):
        response = self.client.get("/api/documents/", {"q": query, **({"area": area} if area else {})})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_finds_a_cyrillic_term_on_the_second_page_and_filters_by_area(self):
        study = self.upload(make_pdf("Общий анализ", "Результаты ТТГ 2.35"))
        self.assertEqual(self.search("ттг"), [])
        self.run_index()

        matches = self.search("ттг", area="thyroid")
        self.assertEqual([item["id"] for item in matches], [study["id"]])
        self.assertEqual(matches[0]["search_match"], {"page": 2, "excerpt": "Результаты ТТГ 2.35"})
        self.assertEqual(matches[0]["index_status"], "ready")
        self.assertEqual(self.search("ттг", area="cardiology"), [])

    def test_finds_only_documents_matching_category_area_and_text(self):
        pdf = make_pdf("Бланк", "Результат ТТГ 2.35")
        expected = self.upload(pdf, category="lab")
        self.upload(pdf, category="doctor_report")
        self.upload(pdf, area="cardiology", category="lab")
        self.upload(make_pdf("Другое исследование"), category="lab")
        self.client.force_login(self.other)
        self.upload(pdf, category="lab")
        self.run_index()
        self.client.force_login(self.owner)

        result = self.client.get("/api/documents/", {"category": "lab", "area": "thyroid", "q": "ттг"})
        self.assertEqual(result.status_code, 200)
        self.assertEqual([item["id"] for item in result.json()], [expected["id"]])
        self.assertEqual(result.json()[0]["search_match"]["page"], 2)

    def test_lists_by_category_and_distinguishes_uncategorized_from_all_categories(self):
        expected = self.upload(make_pdf("Документ"), category="examination")
        uncategorized = self.upload(make_pdf("Документ"))
        url = "/api/documents/"

        for category, item in (("examination", expected), ("uncategorized", uncategorized)):
            with self.subTest(category=category):
                response = self.client.get(url, {"category": category})
                self.assertEqual(response.status_code, 200)
                self.assertEqual([study["id"] for study in response.json()], [item["id"]])
        self.assertEqual(len(self.client.get(url, {"category": ""}).json()), 2)
        self.assertEqual(self.client.get(url, {"category": "unknown"}).status_code, 400)

    def test_filename_search_works_before_indexing(self):
        study = self.upload(make_pdf("ТТГ"))
        match, = self.search("бланк")
        self.assertEqual(match["id"], study["id"])
        self.assertIsNone(match["search_match"])
        self.assertEqual(match["index_status"], "pending")

    def test_text_and_snippets_from_other_owners_are_private(self):
        self.upload(make_pdf("ТТГ 2.35"))
        self.run_index()
        self.client.force_login(self.other)
        self.assertEqual(self.search("ттг"), [])

    def test_blank_pdf_has_a_no_text_status_and_stays_available_by_title(self):
        self.upload(make_pdf(""))
        self.run_index()
        study, = self.search("анализы")
        self.assertEqual(study["index_status"], "no_text")
        self.assertEqual(self.client.get(study["file_url"]).status_code, 200)

    def test_indexing_can_retry_after_a_missing_original(self):
        content = make_pdf("Результаты АСТ 12")
        study = self.upload(content)
        path = Path(Document.objects.get(pk=study["id"]).original.path)
        path.unlink()
        self.run_index()
        self.assertEqual(self.search("анализы")[0]["index_status"], "failed")
        path.write_bytes(content)
        self.run_index(retry_failed=True)
        match, = self.search("аст")
        self.assertEqual(match["search_match"]["page"], 1)
        self.assertEqual(match["index_status"], "ready")
