"""Leitura e validação das configurações."""

import os
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_chat_id: str
    names: tuple[str, ...]
    pdf_url: str
    history_file: str
    request_timeout: int = 45
    max_pdf_mb: int = 80
    ocr_enabled: bool = True
    ocr_language: str = "por"

    @classmethod
    def from_env(cls):
        required = (
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
            "NOMES_PESQUISADOS",
            "PDF_URL",
        )

        missing = [
            key for key in required
            if not os.getenv(key, "").strip()
        ]

        if missing:
            raise ValueError(
                "Configurações obrigatórias ausentes: "
                + ", ".join(missing)
            )

        names = tuple(dict.fromkeys(
            item.strip()
            for item in os.environ[
                "NOMES_PESQUISADOS"
            ].split(";")
            if item.strip()
        ))

        if not names:
            raise ValueError(
                "Nenhum nome válido foi configurado."
            )

        pdf_url = os.environ["PDF_URL"].strip()
        parsed = urlparse(pdf_url)

        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError(
                "PDF_URL deve ser uma URL HTTPS válida."
            )

        return cls(
            telegram_bot_token=os.environ[
                "TELEGRAM_BOT_TOKEN"
            ].strip(),

            telegram_chat_id=os.environ[
                "TELEGRAM_CHAT_ID"
            ].strip(),

            names=names,
            pdf_url=pdf_url,

            history_file=os.getenv(
                "HISTORY_FILE",
                "state/history.json"
            ),

            request_timeout=int(
                os.getenv("REQUEST_TIMEOUT", "45")
            ),

            max_pdf_mb=int(
                os.getenv("MAX_PDF_MB", "80")
            ),

            ocr_enabled=os.getenv(
                "OCR_ENABLED", "true"
            ).lower() in {"1", "true", "yes"},

            ocr_language=os.getenv(
                "OCR_LANGUAGE", "por"
            ),
        )