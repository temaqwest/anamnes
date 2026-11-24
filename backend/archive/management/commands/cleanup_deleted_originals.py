from django.core.management.base import BaseCommand, CommandError

from archive.deletion import remove_originals
from archive.models import PendingOriginalDeletion


class Command(BaseCommand):
    help = "Retry physical removal of PDFs whose archive entries have already been deleted."

    def handle(self, *args, **options):
        names = list(PendingOriginalDeletion.objects.values_list("name", flat=True))
        remove_originals(names)
        if remaining := PendingOriginalDeletion.objects.count():
            raise CommandError(f"{remaining} PDF(s) still pending deletion. Check media storage.")
        self.stdout.write(self.style.SUCCESS("No PDFs pending deletion."))
