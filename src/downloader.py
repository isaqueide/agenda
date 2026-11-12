"""Download e validação de documentos PDF."""

import hashlib
import logging
import time

from pathlib import Path

import fitz
import requests


LOG = logging.getLogger(__name__)


def download_pdf(
    url: str,
    destination: Path,
    timeout: int = 45,
    max_pdf_mb: int = 80,
    attempts: int = 3,
):
    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    last_error = None

    for attempt in range(1, attempts + 1):

        try:
            with requests.get(
                url,
                timeout=timeout,
                stream=True,
                headers={
                    "User-Agent": "MonitorDiarioOficial/1.0"
                },
            ) as response:

                response.raise_for_status()

                content_type = response.headers.get(
                    "Content-Type", ""
                ).lower()

                total = 0
                digest = hashlib.sha256()

                with destination.open("wb") as output:

                    for chunk in response.iter_content(
                        chunk_size=1024 * 256
                    ):

                        if not chunk:
                            continue

                        total += len(chunk)

                        if total > max_pdf_mb * 1024 * 1024:
                            raise ValueError(
                                "PDF excede o limite de tamanho."
                            )

                        digest.update(chunk)
                        output.write(chunk)

            if (
                total < 100
                or destination.read_bytes()[:5] != b"%PDF-"
            ):
                raise ValueError(
                    "A resposta não corresponde a um PDF válido. "
                    f"Content-Type: {content_type}"
                )

            try:
                with fitz.open(destination) as document:

                    if document.page_count < 1:
                        raise ValueError(
                            "PDF não contém páginas."
                        )

            except Exception as exc:
                raise ValueError(
                    f"PDF corrompido ou ilegível: {exc}"
                ) from exc

            sha256 = digest.hexdigest()

            LOG.info(
                "PDF validado: %s bytes; SHA-256=%s",
                total,
                sha256,
            )

            return sha256, total

        except (
            requests.RequestException,
            OSError,
            ValueError,
        ) as exc:

            last_error = exc

            LOG.warning(
                "Falha no download (%s/%s): %s",
                attempt,
                attempts,
                exc,
            )

            if attempt < attempts:
                time.sleep(
                    min(2 ** (attempt - 1), 8)
                )

    raise RuntimeError(
        f"Não foi possível baixar o PDF: {last_error}"
    ) from last_error