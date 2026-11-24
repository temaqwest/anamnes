import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile
from typing import Self


OCR_LANGUAGES = "rus+eng"
MAX_IMAGE_SIDE = 3600
MAX_TEXT_BYTES = 2 * 1024 * 1024
RENDER_TIMEOUT = 20
RECOGNITION_TIMEOUT = 40


class OCRFailed(Exception):
    pass


def _run_page_tool(args, directory, timeout, *, stdout=subprocess.DEVNULL, env=None):
    subprocess.run(
        args, cwd=directory, timeout=timeout, check=True, env=env,
        stdin=subprocess.DEVNULL, stdout=stdout, stderr=subprocess.DEVNULL,
    )


@dataclass(frozen=True)
class PageOCR:
    renderer: str
    recognizer: str

    @classmethod
    def available(cls) -> Self | None:
        renderer = shutil.which("pdftoppm")
        recognizer = shutil.which("tesseract")
        if not renderer or not recognizer:
            return None
        try:
            languages = subprocess.check_output(
                [recognizer, "--list-langs"], text=True, timeout=5,
                stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.SubprocessError, UnicodeError):
            return None
        if not set(OCR_LANGUAGES.split("+")).issubset(languages.splitlines()):
            return None
        return cls(os.path.abspath(renderer), os.path.abspath(recognizer))

    def read_page(self, pdf: Path, number: int) -> str:
        page = str(number)
        try:
            with TemporaryDirectory(dir=pdf.parent) as directory:
                prefix = Path(directory) / "page"
                _run_page_tool(
                    [self.renderer, "-f", page, "-l", page, "-singlefile", "-cropbox", "-gray",
                     "-scale-to", str(MAX_IMAGE_SIDE), str(pdf), str(prefix)],
                    directory, RENDER_TIMEOUT,
                )
                with TemporaryFile(dir=directory) as output:
                    _run_page_tool(
                        [self.recognizer, str(prefix.with_suffix(".pgm")), "stdout",
                         "-l", OCR_LANGUAGES, "--dpi", "300"],
                        directory, RECOGNITION_TIMEOUT, stdout=output,
                        env={**os.environ, "OMP_THREAD_LIMIT": "1"},
                    )
                    output.seek(0)
                    result = output.read(MAX_TEXT_BYTES + 1)
                    if len(result) > MAX_TEXT_BYTES:
                        raise OCRFailed("OCR text exceeds the page size limit.")
                    return result.decode("utf-8")
        except (OSError, subprocess.SubprocessError, UnicodeError) as error:
            raise OCRFailed("Could not recognize the page.") from error
