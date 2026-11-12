from pathlib import Path

import fitz

from src.downloader import download_pdf
from src.pdf_processor import extract_pages


def test_pdf_extraction(tmp_path: Path):

    path = tmp_path / "sample.pdf"

    doc = fitz.open()

    page = doc.new_page()

    page.insert_text(
        (72, 72),
        "Documento de teste - Maria de Souza",
    )

    doc.save(path)
    doc.close()

    pages = extract_pages(
        path,
        ocr_enabled=False,
    )

    assert "Maria de Souza" in pages[0]


def test_download_rejects_non_pdf(
    tmp_path: Path,
    monkeypatch,
):

    class FakeResponse:

        headers = {
            "Content-Type": "text/html"
        }

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size):

            yield b"<html>" + b"x" * 200

    import requests

    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **k: FakeResponse(),
    )

    try:

        download_pdf(
            "https://example.invalid/file",
            tmp_path / "bad.pdf",
            attempts=1,
        )

        assert False, "Deveria rejeitar HTML"

    except RuntimeError:

        assert True