from time import sleep

from django.core.management.base import BaseCommand, CommandError

from archive.indexing import IndexClaimLost, claim_document, finish_claim, read_pages
from archive.models import Document
from archive.ocr import PageOCR


class Command(BaseCommand):
    help = "Index PDF text and recognize scanned pages in the private archive."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Exit when the pending queue is empty.")
        parser.add_argument("--retry-failed", action="store_true", help="Queue documents whose last indexing attempt failed.")
        parser.add_argument("--retry-no-text", action="store_true", help="Queue documents previously marked as having no text.")
        parser.add_argument("--retry-ready", action="store_true", help="Reindex ready PDFs to recognize scanned pages in mixed documents.")

    def handle(self, *args, **options):
        ocr = PageOCR.available()
        if ocr is None:
            message = "OCR requires pdftoppm and Tesseract with Russian and English language data."
            if options["retry_no_text"] or options["retry_ready"]:
                raise CommandError(message)
            self.stderr.write(message)
        if options["retry_failed"]:
            failed = Document.objects.filter(index_status=Document.IndexStatus.FAILED)
            if ocr is None:
                if failed.filter(indexed_pages__isnull=False).exists():
                    self.stderr.write("Partial OCR results retained. Enable OCR before retrying these PDFs.")
                failed = failed.filter(indexed_pages__isnull=True)
            failed.update(index_status=Document.IndexStatus.PENDING)
        to_reindex = [
            status
            for flag, status in (
                ("retry_no_text", Document.IndexStatus.NO_TEXT),
                ("retry_ready", Document.IndexStatus.READY),
            )
            if options[flag]
        ]
        if to_reindex:
            Document.objects.filter(index_status__in=to_reindex).update(index_status=Document.IndexStatus.PENDING)
        while True:
            document = claim_document()
            if document is None:
                if options["once"]:
                    return
                sleep(2)
                continue

            try:
                pages, ocr_failed = read_pages(document, ocr)
            except IndexClaimLost:
                continue
            except Exception:
                if finish_claim(document, [], Document.IndexStatus.FAILED):
                    self.stderr.write(f"Could not index document {document.pk}.")
                continue

            if ocr_failed:
                if finish_claim(document, pages, Document.IndexStatus.FAILED):
                    self.stderr.write(f"Could not recognize all pages of document {document.pk}.")
                continue

            status = Document.IndexStatus.READY if pages else Document.IndexStatus.NO_TEXT
            finish_claim(document, pages, status)
