"""Extração de texto e OCR de documentos PDF."""

import logging
import shutil

from pathlib import Path

import fitz


LOG = logging.getLogger(__name__)


def extract_pages(
    pdf_path: Path,
    ocr_enabled: bool = True,
    ocr_language: str = "por",
) -> list[str]:

    pages = []

    with fitz.open(pdf_path) as document:

        for page_number, page in enumerate(
            document,
            start=1
        ):

            text = page.get_text(
                "text",
                sort=True
            ).strip()

            if len(text) >= 20 or not ocr_enabled:
                pages.append(text)
                continue

            if not shutil.which("tesseract"):

                LOG.warning(
                    "Página %s sem texto e Tesseract indisponível.",
                    page_number,
                )

                pages.append(text)
                continue

            try:
                import pytesseract
                from PIL import Image

                pix = page.get_pixmap(
                    matrix=fitz.Matrix(2, 2),
                    alpha=False,
                )

                image = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples,
                )

                ocr_text = pytesseract.image_to_string(
                    image,
                    lang=ocr_language,
                ).strip()

                pages.append(ocr_text or text)

                LOG.info(
                    "OCR executado na página %s.",
                    page_number,
                )

            except Exception as exc:

                LOG.exception(
                    "Falha de OCR na página %s: %s",
                    page_number,
                    exc,
                )

                pages.append(text)

    if not any(page.strip() for page in pages):

        raise RuntimeError(
            "Não foi possível extrair texto do PDF. "
            "O documento pode estar protegido, vazio "
            "ou exigir configuração adicional de OCR."
        )

    return pages