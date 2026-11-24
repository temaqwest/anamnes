import os
import sqlite3
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from pypdf import PdfWriter


class ArchiveTransferTests(SimpleTestCase):
    def setUp(self):
        workspace = TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        for name in ("source", "target"):
            (self.root / name / "media").mkdir(parents=True)
        self.key = "11111111-1111-1111-1111-111111111111"
        self.original_path = Path(f"originals/17/{self.key}.pdf")
        self.original = self.root / "source" / "media" / self.original_path
        self.target_original = self.root / "target" / "media" / self.original_path
        self.source_db = self.root / "source" / "db.sqlite3"
        self.target_db = self.root / "target" / "db.sqlite3"
        self.command("source", "migrate", "--noinput", "--verbosity", "0")
        self.command("target", "migrate", "--noinput", "--verbosity", "0")
        self.command("source", "shell", "-c", "\n".join([
            "from django.contrib.auth.models import Group, Permission, User",
            "from accounts.models import AccountEmail",
            "from allergies.models import Allergy",
            "from archive.models import Document, DocumentPage, StudyArea",
            "user = User.objects.create_user(pk=17, username='transfer-user', password='synthetic-only')",
            "AccountEmail.objects.create(user=user, address='transfer@example.test', verified_at='2025-01-01T12:00:00Z')",
            "Allergy.objects.create(id='22222222-2222-2222-2222-222222222222', owner=user, "
            "name='Пыльца берёзы', name_key='пыльца берёзы')",
            "group = Group.objects.create(name='Readers')",
            "group.permissions.add(Permission.objects.get(codename='view_document'))",
            "user.groups.add(group)",
            "user.user_permissions.add(Permission.objects.get(codename='change_document'))",
            "area = StudyArea.objects.create(owner=user, slug='personal', name='Персональная', "
            "name_key='персональная', description='Моя подсказка')",
            f"doc = Document.objects.create(id='{self.key}', owner=user, "
            f"original='{self.original_path.as_posix()}', original_name='01.pdf', "
            "title='Анализ', study_date='2025-01-02', index_status='ready')",
            "doc.areas.add(area)",
            "Document.objects.filter(pk=doc.pk).update(created_at='2025-01-02T03:04:05Z')",
            "DocumentPage.objects.create(document=doc, number=2, text='Гемоглобин', search_text='гемоглобин')",
        ]))
        pdf = PdfWriter()
        pdf.add_blank_page(72, 72)
        buffer = BytesIO()
        pdf.write(buffer)
        self.original.parent.mkdir(parents=True)
        self.original.write_bytes(buffer.getvalue())

    def command(self, archive, *args, error=None):
        process = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[1] / "manage.py"), *map(str, args)],
            env={
                **os.environ,
                "POSTGRES_DB": "",
                "ANAMNES_SQLITE_PATH": str(self.root / archive / "db.sqlite3"),
                "ANAMNES_MEDIA_ROOT": str(self.root / archive / "media"),
            },
            capture_output=True,
            text=True,
        )
        if error:
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(error, process.stderr)
        else:
            self.assertEqual(process.returncode, 0, process.stderr)
        return process.stdout

    def transfer(self, *flags, error=None):
        return self.command(
            "target", "transfer_archive", "--source-db", self.source_db,
            "--source-media", self.root / "source" / "media", *flags, error=error,
        )

    def assert_empty_target(self):
        self.command("target", "shell", "-c", "from archive.models import Document; assert not Document.objects.exists()")
        self.assertEqual(list((self.root / "target" / "media").iterdir()), [])

    def test_check_leaves_source_and_target_intact_then_apply_preserves_archive(self):
        source_before = self.source_db.read_bytes()
        output = self.transfer()
        self.assertIn("archive.document: 1", output)
        self.assertIn("allergies.allergy: 1", output)
        self.assert_empty_target()
        self.assertEqual(self.source_db.read_bytes(), source_before)

        self.transfer("--apply")
        self.command("target", "shell", "-c", "\n".join([
            "from django.contrib.auth.models import User",
            "from accounts.models import AccountEmail",
            "from allergies.models import Allergy",
            "from archive.models import Document, DocumentPage",
            "user = User.objects.get(pk=17)",
            "assert user.check_password('synthetic-only')",
            "assert user.get_all_permissions() == {'archive.view_document', 'archive.change_document'}",
            "assert AccountEmail.objects.get(user=user).address == 'transfer@example.test'",
            "assert AccountEmail.objects.get(user=user).verified_at.isoformat() == '2025-01-01T12:00:00+00:00'",
            "allergy = Allergy.objects.get(pk='22222222-2222-2222-2222-222222222222', owner=user)",
            "assert (allergy.name, allergy.name_key) == ('Пыльца берёзы', 'пыльца берёзы')",
            f"document = Document.objects.get(pk='{self.key}')",
            "assert document.owner == user",
            "assert document.created_at.isoformat() == '2025-01-02T03:04:05+00:00'",
            "assert document.areas.get().name == 'Персональная'",
            "assert document.areas.get().description == 'Моя подсказка'",
            "assert DocumentPage.objects.get(document=document, number=2).search_text == 'гемоглобин'",
        ]))
        self.assertEqual(self.target_original.read_bytes(), self.original.read_bytes())
        self.assertEqual(self.source_db.read_bytes(), source_before)

    def test_rejects_nonempty_target_before_creating_files(self):
        self.command("target", "shell", "-c",
                     "from django.contrib.auth.models import User; User.objects.create_user(username='existing-user')")
        self.transfer("--apply", error="Target is not empty")
        self.assert_empty_target()
        self.command("target", "shell", "-c", "from django.contrib.auth.models import User; "
                     "assert list(User.objects.values_list('username', flat=True)) == ['existing-user']")

    def test_upgrades_a_snapshot_and_migrates_legacy_area_links(self):
        (self.root / "legacy").mkdir()
        self.source_db = self.root / "legacy" / "db.sqlite3"
        self.command("legacy", "migrate", "auth", "--noinput", "--verbosity", "0")
        self.command("legacy", "migrate", "archive", "0004", "--noinput", "--verbosity", "0")
        self.command("legacy", "shell", "-c", "\n".join([
            "from django.contrib.auth.models import User",
            "from django.db import connection",
            "from django.db.migrations.executor import MigrationExecutor",
            "key = ('archive', '0004_document_index_claim_document_index_started_at_and_more')",
            "old = MigrationExecutor(connection).loader.project_state([key]).apps",
            "Document = old.get_model('archive', 'Document')",
            "User.objects.create_user(pk=17, username='legacy')",
            f"doc = Document.objects.create(pk='{self.key}', owner_id=17, title='До обновления', "
            f"original='{self.original_path.as_posix()}', original_name='01.pdf', study_date='2025-01-02', "
            "index_status='processing', index_started_at='2025-01-02T00:00:00Z', "
            "index_claim='22222222-2222-2222-2222-222222222222')",
            "doc.areas.add('thyroid')",
        ]))
        old_database = self.source_db.read_bytes()

        self.transfer("--apply")
        self.command("target", "shell", "-c", "\n".join([
            "from archive.models import Document",
            f"document = Document.objects.get(pk='{self.key}')",
            "area = document.areas.get(owner_id=17)",
            "assert (area.slug, area.preset_id) == ('thyroid', 'thyroid')",
            "assert (document.index_status, document.index_claim, document.index_started_at) == ('pending', None, None)",
        ]))
        self.assertEqual(self.source_db.read_bytes(), old_database)

    def test_specialty_migration_preserves_custom_names_and_reuses_an_existing_specialty(self):
        (self.root / "legacy").mkdir()
        self.command("legacy", "migrate", "auth", "--noinput", "--verbosity", "0")
        self.command("legacy", "migrate", "archive", "0009", "--noinput", "--verbosity", "0")
        self.command("legacy", "shell", "-c", "\n".join([
            "from django.contrib.auth.models import User",
            "from django.db import connection",
            "from django.db.migrations.executor import MigrationExecutor",
            "key = ('archive', '0009_study_area_descriptions')",
            "old = MigrationExecutor(connection).loader.project_state([key]).apps",
            "StudyArea = old.get_model('archive', 'StudyArea')",
            "Document = old.get_model('archive', 'Document')",
            "User.objects.create_user(pk=17, username='legacy')",
            "User.objects.create_user(pk=18, username='new')",
            "StudyArea.objects.create(pk=22, owner_id=17, slug='gastroenterology', name='Мой раздел', name_key='мой раздел')",
            "StudyArea.objects.create(pk=23, owner_id=17, slug='custom-lungs', "
            "name='ПУЛЬМОНОЛОГИЯ', name_key='пульмонология', description='Лёгкие')",
            "StudyArea.objects.create(pk=24, owner_id=17, slug='my-ortho', name='Ортопедия', "
            "name_key='ортопедия', description='Личные записи')",
            "StudyArea.objects.create(pk=25, owner_id=17, slug='custom-ent', name='ЛОР', name_key='лор')",
            "StudyArea.objects.create(pk=26, owner_id=17, slug='gyn', name='Гинекология', name_key='гинекология')",
            "StudyArea.objects.create(pk=27, owner_id=17, slug='immunology', name='Мой иммунитет', "
            "name_key='мой иммунитет', description='Моя заметка')",
            "User.objects.create_user(pk=19, username='untouched')",
            "StudyArea.objects.create(pk=28, owner_id=19, slug='immunology', name='Иммунология', "
            "name_key='иммунология', description='изучение и лечение нарушений иммунной системы')",
            "StudyArea.objects.create(pk=29, owner_id=19, slug='alias-ent', name='ЛОР', name_key='лор')",
            "StudyArea.objects.create(pk=30, owner_id=19, slug='canonical-ent', "
            "name='Оториноларингология (ЛОР)', name_key='оториноларингология (лор)')",
            "doc = Document.objects.create(owner_id=17, title='Документ', original='fixture.pdf', "
            "original_name='fixture.pdf', study_date='2025-01-02')",
            "doc.areas.add(24)",
        ]))
        self.command("legacy", "migrate", "--noinput", "--verbosity", "0")
        self.command("legacy", "shell", "-c", "\n".join([
            "from django.contrib.auth.models import User",
            "from archive.models import Document, StudyArea",
            "from archive.study_areas import areas_for",
            "legacy = StudyArea.objects.filter(owner_id=17)",
            "assert legacy.get(slug='gastroenterology').name == 'Мой раздел'",
            "assert legacy.get(pk=22).preset_id == 'gastroenterology'",
            "assert legacy.get(pk=22).description == ''",
            "assert legacy.get(preset_id='pulmonology').pk == 23",
            "assert legacy.get(pk=23).description == 'Лёгкие'",
            "assert legacy.get(preset_id='orthopedics').pk == 24",
            "assert legacy.get(pk=24).slug == 'my-ortho' and legacy.get(pk=24).description == 'Личные записи'",
            "assert Document.objects.get(owner_id=17).areas.get().pk == 24",
            "assert legacy.get(preset_id='otolaryngology').pk == 25",
            "assert legacy.get(preset_id='obstetrics_gynecology').pk == 26",
            "assert legacy.get(preset_id='immunology').name == 'Мой иммунитет'",
            "assert legacy.get(preset_id='immunology').description == 'Моя заметка'",
            "assert StudyArea.objects.get(pk=28).name == 'Аллергология и иммунология'",
            "assert StudyArea.objects.get(pk=29).preset_id is None",
            "assert StudyArea.objects.get(pk=30).preset_id == 'otolaryngology'",
            "assert legacy.count() == 19",
            "assert not StudyArea.objects.filter(owner_id=18).exists()",
            "assert areas_for(User.objects.get(pk=18)).count() == 19",
        ]))

    def test_rejects_missing_and_outside_files(self):
        self.original.unlink()
        self.transfer("--apply", error="Missing original")
        self.assert_empty_target()

        with sqlite3.connect(self.source_db) as source:
            source.execute("UPDATE archive_document SET original = '../outside.pdf'")
        self.transfer(error="Unsafe original path")

    def test_recovers_previously_published_identical_files(self):
        self.target_original.parent.mkdir(parents=True)
        self.target_original.write_bytes(b"different")
        self.transfer("--apply", error="Target originals differ")
        self.assertEqual(self.target_original.read_bytes(), b"different")

        self.target_original.write_bytes(self.original.read_bytes())
        self.transfer("--apply")
        self.command("target", "shell", "-c", "from archive.models import Document; assert Document.objects.count() == 1")
