from django.db.models import OuterRef, Subquery

from .models import DocumentPage


def normalize_text(text: str) -> str:
    return " ".join(text.replace("\x00", "").split())


def search_documents(documents, query: str):
    term = normalize_text(query).casefold()
    if not term:
        return documents

    matching_pages = DocumentPage.objects.filter(
        document_id=OuterRef("pk"), search_text__contains=term,
    ).order_by("number")
    candidates = documents.annotate(
        matched_page=Subquery(matching_pages.values("number")[:1]),
        matched_text=Subquery(matching_pages.values("text")[:1]),
    )

    result = []
    for document in candidates:
        if document.matched_page is not None:
            document.search_match = {
                "page": document.matched_page,
                "excerpt": excerpt(document.matched_text, term),
            }
        elif not any(term in normalize_text(name).casefold() for name in (document.title, document.original_name)):
            continue
        result.append(document)
    return result


def excerpt(text: str, term: str) -> str:
    folded = text.casefold()
    start = folded.index(term)
    end = start + len(term)
    if len(folded) != len(text):
        offsets = [index for index, char in enumerate(text) for _ in char.casefold()]
        start, end = offsets[start], offsets[end - 1] + 1

    left = max(0, start - 54)
    right = min(len(text), end + 76)
    prefix = "…" if left else ""
    suffix = "…" if right < len(text) else ""
    return prefix + text[left:right].strip() + suffix
