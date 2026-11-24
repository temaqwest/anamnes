import logging
from itertools import batched

from django.db import transaction

from .models import Document, PendingOriginalDeletion


logger = logging.getLogger(__name__)
batch_size = 500


def remove_originals(names):
    storage = Document._meta.get_field("original").storage
    removed = []
    for name in names:
        try:
            storage.delete(name)
        except OSError:
            logger.warning("Could not remove an archived PDF. Deletion is queued for retry.", exc_info=True)
        else:
            removed.append(name)
    for batch in batched(removed, batch_size):
        PendingOriginalDeletion.objects.filter(name__in=batch).delete()


@transaction.atomic
def delete_documents(owner, ids):
    owned = Document.objects.filter(owner=owner)
    locked = owned.select_for_update().order_by("pk").values_list("pk", "original")
    if ids is None:
        documents = list(locked)
    else:
        documents = [
            document
            for batch in batched(sorted(set(ids)), batch_size)
            for document in locked.filter(pk__in=batch)
        ]

    names = [name for _, name in documents if name]
    PendingOriginalDeletion.objects.bulk_create([PendingOriginalDeletion(name=name) for name in names])
    for batch in batched((pk for pk, _ in documents), batch_size):
        owned.filter(pk__in=batch).delete()
    if names:
        transaction.on_commit(lambda: remove_originals(names), robust=True)
    return len(documents)
