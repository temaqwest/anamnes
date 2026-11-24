from contextlib import ExitStack
from datetime import timedelta
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from time import monotonic
from uuid import uuid4

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from pypdf import PdfReader

from .models import Document, DocumentPage
from .ocr import OCRFailed, PageOCR
from .search import normalize_text


CLAIM_TTL = timedelta(minutes=15)
CLAIM_REFRESH_SECONDS = 60


class IndexClaimLost(Exception):
    pass


def claim_document() -> Document | None:
    now = timezone.now()
    eligible = Document.objects.filter(
        Q(index_status=Document.IndexStatus.PENDING)
        | Q(index_status=Document.IndexStatus.PROCESSING, index_started_at__lt=now - CLAIM_TTL),
    )
    for pk in eligible.order_by("created_at", "id").values_list("pk", flat=True)[:32]:
        claim = uuid4()
        if eligible.filter(pk=pk).update(
            index_status=Document.IndexStatus.PROCESSING,
            index_started_at=now,
            index_claim=claim,
        ):
            return Document.objects.filter(pk=pk, index_claim=claim).first()
    return None


def active_claim(document: Document):
    return Document.objects.filter(
        pk=document.pk, index_status=Document.IndexStatus.PROCESSING, index_claim=document.index_claim,
    )


def read_pages(document: Document, ocr: PageOCR | None) -> tuple[list[DocumentPage], bool]:
    pages = []
    ocr_failed = False
    pdf_path = None
    renew_at = monotonic() + CLAIM_REFRESH_SECONDS
    with document.original.open("rb") as stream, ExitStack() as stack:
        for number, page in enumerate(PdfReader(stream).pages, start=1):
            if monotonic() >= renew_at:
                if not active_claim(document).update(index_started_at=timezone.now()):
                    raise IndexClaimLost
                renew_at = monotonic() + CLAIM_REFRESH_SECONDS
            text = normalize_text(page.extract_text() or "")
            if not text and ocr is not None:
                if pdf_path is None:
                    directory = stack.enter_context(TemporaryDirectory())
                    pdf_path = Path(directory) / "original.pdf"
                    position = stream.tell()
                    stream.seek(0)
                    with pdf_path.open("wb") as local_pdf:
                        copyfileobj(stream, local_pdf)
                    stream.seek(position)
                try:
                    text = normalize_text(ocr.read_page(pdf_path, number))
                except OCRFailed:
                    ocr_failed = True
            if text:
                pages.append(DocumentPage(document=document, number=number, text=text, search_text=text.casefold()))
    return pages, ocr_failed


@transaction.atomic
def finish_claim(document: Document, pages: list[DocumentPage], status: str) -> bool:
    if not active_claim(document).update(index_status=status, index_started_at=None, index_claim=None):
        return False
    if status == Document.IndexStatus.FAILED:
        DocumentPage.objects.bulk_create(
            pages, batch_size=100, update_conflicts=True,
            update_fields=["text", "search_text"], unique_fields=["document", "number"],
        )
    else:
        DocumentPage.objects.filter(document=document).delete()
        DocumentPage.objects.bulk_create(pages, batch_size=100)
    return True
