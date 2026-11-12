"""Integração com Telegram Bot API."""

import logging
import time

import requests


LOG = logging.getLogger(__name__)

TELEGRAM_MAX_LENGTH = 4000


class TelegramError(RuntimeError):
    pass


class TelegramBot:

    def __init__(
        self,
        token: str,
        chat_id: str,
        timeout: int = 30,
    ):

        self.token = token
        self.chat_id = chat_id
        self.timeout = timeout

        self.base_url = (
            f"https://api.telegram.org/bot{token}"
        )

    @staticmethod
    def split_message(
        text: str,
        limit: int = TELEGRAM_MAX_LENGTH,
    ):

        chunks = []

        remaining = text.strip()

        while len(remaining) > limit:

            cut = remaining.rfind(
                "\n",
                0,
                limit,
            )

            if cut < limit // 2:

                cut = remaining.rfind(
                    " ",
                    0,
                    limit,
                )

            if cut < limit // 2:
                cut = limit

            chunks.append(
                remaining[:cut].strip()
            )

            remaining = remaining[cut:].strip()

        if remaining:
            chunks.append(remaining)

        return chunks

    def send_text(self, text: str):

        for part_number, chunk in enumerate(
            self.split_message(text),
            start=1,
        ):

            self._send_chunk(
                chunk,
                part_number,
            )

    def _send_chunk(
        self,
        text: str,
        part_number: int,
    ):

        url = f"{self.base_url}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }

        for attempt in range(1, 5):

            try:

                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                )

                if response.status_code == 429:

                    body = response.json()

                    wait = int(
                        body.get(
                            "parameters", {}
                        ).get(
                            "retry_after",
                            5,
                        )
                    )

                    LOG.warning(
                        "Limite Telegram. Aguardando %s segundos.",
                        wait,
                    )

                    time.sleep(wait)
                    continue

                response.raise_for_status()

                body = response.json()

                if not body.get("ok"):
                    raise TelegramError(
                        "Telegram não confirmou o envio."
                    )

                LOG.info(
                    "Mensagem enviada (parte %s).",
                    part_number,
                )

                return

            except (
                requests.RequestException,
                ValueError,
                TelegramError,
            ) as exc:

                LOG.warning(
                    "Falha no envio (%s/4): %s",
                    attempt,
                    exc,
                )

                if attempt == 4:
                    raise TelegramError(
                        "Falha definitiva no envio."
                    ) from exc

                time.sleep(
                    min(2 ** (attempt - 1), 8)
                )