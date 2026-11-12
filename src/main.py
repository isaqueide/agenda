"""Ponto de entrada da aplicação."""

import logging
import re
import sys
import unicodedata

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.config import Settings
from src.downloader import download_pdf
from src.history import History
from src.name_search import search_names, Occurrence
from src.pdf_processor import extract_pages
from src.telegram_bot import TelegramBot


LOG = logging.getLogger("monitor_diario")


def configure_logging():

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s %(levelname)s "
            "%(name)s - %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def publication_date(pages: list[str]):

    sample = "\n".join(pages[:3])

    patterns = [
        r"\b(\d{1,2}\s+de\s+[A-Za-zÀ-ÿ]+\s+de\s+\d{4})\b",
        r"\b(\d{2}/\d{2}/\d{4})\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            sample,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return "Não identificada automaticamente"


def normalize_for_id(value: str):

    value = unicodedata.normalize(
        "NFKD",
        value.casefold(),
    )

    return "".join(
        char
        for char in value
        if unicodedata.category(char) != "Mn"
    ).strip()


def format_name_message(
    name: str,
    occurrences: list[Occurrence],
    pdf_url: str,
    pub_date: str,
    total: int,
):

    lines = [
        "🔔 MONITORAMENTO DO DIÁRIO OFICIAL DO ACRE",

        (
            "📅 Data da consulta: "
            f"{datetime.now(ZoneInfo('America/Rio_Branco')):%d/%m/%Y %H:%M}"
        ),

        f"📄 Publicação: {pub_date}",
        "",
        "🔎 RESULTADO DA PESQUISA",
        f"Nome pesquisado: {name}",
        f"Quantidade de ocorrências: {total}",
        "",
    ]

    for item in occurrences:

        lines.extend([
            (
                f"📌 Página {item.page} "
                f"— ocorrência {item.ordinal_on_page}:"
            ),
            f'"{item.context}"',
            "",
        ])

    lines.extend([
        f"🔗 Documento original: {pdf_url}"
    ])

    return "\n".join(lines)


def run():

    settings = Settings.from_env()

    history = History(
        settings.history_file
    )

    pdf_path = Path(
        "tmp/diario_oficial.pdf"
    )

    document_hash, _ = download_pdf(
        settings.pdf_url,
        pdf_path,
        settings.request_timeout,
        settings.max_pdf_mb,
    )

    pages = extract_pages(
        pdf_path,
        settings.ocr_enabled,
        settings.ocr_language,
    )

    LOG.info(
        "Documento processado: %s páginas.",
        len(pages),
    )

    pub_date = publication_date(pages)

    found = search_names(
        pages,
        settings.names,
    )

    bot = TelegramBot(
        settings.telegram_bot_token,
        settings.telegram_chat_id,
    )

    total_found = sum(
        len(items)
        for items in found.values()
    )

    if total_found == 0:

        no_result_id = history.no_results_id(
            document_hash
        )

        if not history.contains(no_result_id):

            message = (
                "🔔 MONITORAMENTO DO DIÁRIO_OF\n"
                f"📅 Data da consulta: "
                f"{datetime.now(ZoneInfo('America/Rio_Branco')):%d/%m/%Y %H:%M}\n"
                f"📄 Publicação: {pub_date}\n\n"
                "🔎 Nenhuma ocorrência dos nomes monitorados "
                "foi encontrada no documento consultado.\n\n"
                f"🔗 Documento original: {settings.pdf_url}"
            )

            bot.send_text(message)

            history.mark_many([
                no_result_id
            ])

        else:

            LOG.info(
                "Aviso de ausência já enviado para este documento."
            )

    else:

        sent_count = 0

        for name, occurrences in found.items():

            new_items = []
            new_ids = []

            for item in occurrences:

                item_id = history.occurrence_id(
                    document_hash,
                    normalize_for_id(name),
                    item.page,
                    item.ordinal_on_page,
                )

                if not history.contains(item_id):

                    new_items.append(item)
                    new_ids.append(item_id)

            if not new_items:

                LOG.info(
                    "Nenhuma ocorrência inédita para o nome configurado."
                )

                continue

            message = format_name_message(
                name,
                new_items,
                settings.pdf_url,
                pub_date,
                len(new_items),
            )

            bot.send_text(message)

            history.mark_many(new_ids)

            sent_count += len(new_items)

        LOG.info(
            "Ocorrências inéditas notificadas: %s.",
            sent_count,
        )

    history.save()

    return 0


if __name__ == "__main__":

    configure_logging()

    try:

        sys.exit(run())

    except Exception:

        LOG = logging.getLogger("monitor_diario")

        LOG.exception(
            "Execução encerrada com falha."
        )

        sys.exit(1)
