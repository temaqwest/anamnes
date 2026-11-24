import hashlib
import os
import shutil
import sqlite3
from contextlib import closing, contextmanager
from io import StringIO
from itertools import islice
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import DatabaseError, connection, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models import F

from accounts.models import AccountEmail
from archive.models import Area, Document


@contextmanager
def migrated_snapshot(database):
    with TemporaryDirectory(prefix="anamnes-transfer-") as workspace:
        snapshot = Path(workspace) / "source.sqlite3"
        with (
            closing(sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)) as source,
            closing(sqlite3.connect(snapshot)) as copy,
        ):
            source.backup(copy)

        alias = f"transfer_{uuid4().hex}"
        connections.databases[alias] = {
            **connection.settings_dict,
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": snapshot,
            "OPTIONS": {},
            "USER": "",
            "PASSWORD": "",
            "HOST": "",
            "PORT": "",
        }
        source_connection = connections[alias]
        try:
            executor = MigrationExecutor(source_connection)
            applied = set(executor.loader.applied_migrations)
            if not any(app == "archive" for app, _ in applied):
                raise CommandError("Source is missing the Anamnes archive migrations.")
            if applied - set(executor.loader.disk_migrations):
                raise CommandError("Source contains migrations unknown to this build of Anamnes.")
            call_command("migrate", database=alias, interactive=False, verbosity=0, stdout=StringIO())
            source_connection.check_constraints()
            yield alias
        finally:
            source_connection.close()
            del connections[alias]
            del connections.databases[alias]


def transfer_models():
    return [
        model
        for config in apps.get_app_configs()
        if config.label in {"auth", "allergies", "archive", "medications"}
        for model in config.get_models(include_auto_created=True)
        if model not in {Permission, Area} and model._meta.managed and not model._meta.proxy
    ] + [AccountEmail]


def records(model, alias=None):
    return model._base_manager.using(alias).order_by()


def check_target(models, source, *, apply):
    executor = MigrationExecutor(connection)
    if (
        set(executor.loader.applied_migrations) - set(executor.loader.disk_migrations)
        or executor.migration_plan(executor.loader.graph.leaf_nodes())
    ):
        raise CommandError("Apply all Anamnes migrations to the target before transferring.")
    if apply and connection.vendor == "postgresql":
        tables = sorted(
            connection.ops.quote_name(model._meta.db_table)
            for model in [*models, Area, Session, ContentType, Permission]
        )
        with connection.cursor() as cursor:
            cursor.execute(f"LOCK TABLE {', '.join(tables)} IN SHARE ROW EXCLUSIVE MODE")
    for model in [*models, Session]:
        if records(model).exists():
            raise CommandError(f"Target is not empty ({model._meta.label_lower}).")
    source_catalogue = dict(records(Area, source).values_list("slug", "name"))
    for slug, name in records(Area).values_list("slug", "name"):
        if source_catalogue.get(slug) != name:
            raise CommandError("Target preset areas differ from the source catalogue.")
    return source_catalogue


def auth_catalogue(source):
    content_types = {}
    for pk, app, model in records(ContentType, source).values_list("pk", "app_label", "model"):
        target, _ = ContentType.objects.get_or_create(app_label=app, model=model)
        content_types[pk] = target.pk
    permissions = {}
    for pk, content_type, codename, name in records(Permission, source).values_list(
        "pk", "content_type_id", "codename", "name",
    ):
        target, _ = Permission.objects.get_or_create(
            content_type_id=content_types[content_type], codename=codename, defaults={"name": name},
        )
        permissions[pk] = target.pk
    return {ContentType: content_types, Permission: permissions}


def copy_records(model, source, foreign_keys):
    quote = connection.ops.quote_name
    fields = model._meta.local_concrete_fields
    columns = ", ".join(quote(field.column) for field in fields)
    placeholders = ", ".join(["%s"] * len(fields))
    statement = f"INSERT INTO {quote(model._meta.db_table)} ({columns}) VALUES ({placeholders})"
    source_rows = records(model, source).values_list(*(field.attname for field in fields)).iterator(chunk_size=500)

    # Raw inserts preserve historical auto_now and auto_now_add timestamps.
    def prepare(field, value):
        if value is not None and field.related_model in foreign_keys:
            value = foreign_keys[field.related_model][value]
        return field.get_db_prep_save(value, connection)

    with connection.cursor() as cursor:
        while batch := list(islice(source_rows, 500)):
            cursor.executemany(statement, [
                tuple(prepare(field, value) for field, value in zip(fields, row, strict=True))
                for row in batch
            ])


def source_originals(source_media, source):
    original_paths = {}
    for owner, name in records(Document, source).values_list("owner_id", "original").iterator():
        parts = name.split("/")
        if (
            len(parts) != 3 or parts[0] != "originals" or parts[1] != str(owner)
            or parts[2] in {"", ".pdf"} or not parts[2].endswith(".pdf")
            or "\\" in name or "\x00" in name
        ):
            raise CommandError("Unsafe original path in source database.")
        owner_dir = source_media / Path(*parts[:2])
        original = owner_dir / parts[2]
        if owner_dir.parent.is_symlink() or owner_dir.is_symlink() or original.is_symlink():
            raise CommandError(f"Symlink in source original path: {name}")
        if not original.is_file():
            raise CommandError(f"Missing original: {name}")
        if name in original_paths:
            raise CommandError(f"Duplicate source original path: {name}")
        original_paths[name] = digest(original)
    return original_paths


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").digest()


def matching_target_originals(target_media, original_paths):
    originals = target_media / "originals"
    if originals.is_symlink() or (originals.exists() and not originals.is_dir()):
        raise CommandError("Target originals must be a directory without symlinks.")
    if not originals.exists():
        return False

    installed = set()
    owner_dirs = list(originals.iterdir())
    for owner_dir in owner_dirs:
        if owner_dir.is_symlink() or not owner_dir.is_dir():
            raise CommandError("Target originals differ from the source.")
        for path in owner_dir.iterdir():
            name = path.relative_to(target_media).as_posix()
            if (
                path.is_symlink() or not path.is_file()
                or name not in original_paths or digest(path) != original_paths[name]
            ):
                raise CommandError("Target originals differ from the source.")
            installed.add(name)
    if owner_dirs and installed != original_paths.keys():
        raise CommandError("Target originals differ from the source.")
    return bool(installed)


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def install_originals(source_media, target_media, original_paths):
    if not original_paths or matching_target_originals(target_media, original_paths):
        return
    with TemporaryDirectory(prefix=".archive-transfer-", dir=target_media) as workspace:
        stage = Path(workspace)
        for name, expected in original_paths.items():
            staged = stage / name
            staged.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with (source_media / name).open("rb") as source, staged.open("xb") as target:
                shutil.copyfileobj(source, target)
                target.flush()
                os.fsync(target.fileno())
            if digest(staged) != expected:
                raise CommandError(f"Source original changed during transfer: {name}")
        for owner_dir in (stage / "originals").iterdir():
            sync_directory(owner_dir)
        sync_directory(stage / "originals")
        (stage / "originals").rename(target_media / "originals")
        sync_directory(target_media)


class Command(BaseCommand):
    help = "Check or copy an offline SQLite archive into an empty migrated Anamnes database."

    def add_arguments(self, parser):
        parser.add_argument("--source-db", required=True, type=Path, help="Path to the source SQLite database.")
        parser.add_argument("--source-media", required=True, type=Path, help="Source media root containing originals/.")
        parser.add_argument("--apply", action="store_true", help="Apply after checking. The default is a dry run.")

    def handle(self, *args, **options):
        try:
            source_db = Path(options["source_db"]).resolve(strict=True)
            source_media = Path(options["source_media"]).resolve(strict=True)
            target_media = Path(settings.MEDIA_ROOT).resolve(strict=True)
            if not source_db.is_file() or not source_media.is_dir() or not target_media.is_dir():
                raise CommandError("Specify an existing source database file and two media directories.")
            if source_media.is_relative_to(target_media) or target_media.is_relative_to(source_media):
                raise CommandError("Source and target media directories must be separate.")
            if connection.vendor == "sqlite" and Path(connection.settings_dict["NAME"]).exists():
                if source_db.samefile(connection.settings_dict["NAME"]):
                    raise CommandError("Source and target database must be separate.")
            self.transfer(source_db, source_media, target_media, options["apply"])
        except (DatabaseError, OSError, sqlite3.Error, ValueError) as exc:
            raise CommandError(f"Transfer failed ({type(exc).__name__}). Check paths, permissions and database health.") from exc

    def transfer(self, source_db, source_media, target_media, apply):
        models = transfer_models()
        with migrated_snapshot(source_db) as source, transaction.atomic(durable=True):
            catalogue = check_target(models, source, apply=apply)
            if records(Document.areas.through, source).exclude(studyarea__owner=F("document__owner")).exists():
                raise CommandError("A source document links to another owner's study area.")
            originals = source_originals(source_media, source)
            matching_target_originals(target_media, originals)
            counts = {model: records(model, source).count() for model in models}

            if apply:
                for slug, name in catalogue.items():
                    Area.objects.get_or_create(slug=slug, defaults={"name": name})
                foreign_keys = auth_catalogue(source)
                for model, count in counts.items():
                    copy_records(model, source, foreign_keys)
                    if records(model).count() != count:
                        raise CommandError(f"Record count differs for {model._meta.label_lower}.")
                Document.objects.filter(index_status=Document.IndexStatus.PROCESSING).update(
                    index_status=Document.IndexStatus.PENDING, index_started_at=None, index_claim=None,
                )
                connection.check_constraints()
                with connection.cursor() as cursor:
                    for statement in connection.ops.sequence_reset_sql(no_style(), models):
                        cursor.execute(statement)
                install_originals(source_media, target_media, originals)

        self.stdout.write("Transfer complete." if apply else "Dry run passed. No target changes made.")
        for model, count in counts.items():
            self.stdout.write(f"{model._meta.label_lower}: {count}")
        self.stdout.write(f"PDF originals: {len(originals)}")
