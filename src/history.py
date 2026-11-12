"""Histórico persistente de notificações."""

import hashlib
import json
import logging

from pathlib import Path


LOG = logging.getLogger(__name__)


class History:

    def __init__(self, path: str):

        self.path = Path(path)

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.path.exists():

            try:

                data = json.loads(
                    self.path.read_text(
                        encoding="utf-8"
                    )
                )

                self.sent = set(
                    data.get("sent", [])
                )

            except (
                OSError,
                json.JSONDecodeError,
                AttributeError,
            ) as exc:

                raise RuntimeError(
                    f"Histórico existente inválido: {exc}"
                ) from exc

        else:
            self.sent = set()

    @staticmethod
    def occurrence_id(
        document_sha256: str,
        normalized_name: str,
        page: int,
        ordinal_on_page: int,
    ):

        raw = (
            f"{document_sha256}|"
            f"{normalized_name.casefold()}|"
            f"{page}|"
            f"{ordinal_on_page}"
        )

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def no_results_id(document_sha256: str):

        raw = (
            f"{document_sha256}|no-results"
        )

        return hashlib.sha256(
            raw.encode()
        ).hexdigest()

    def contains(self, item_id: str):

        return item_id in self.sent

    def mark_many(self, item_ids: list[str]):

        self.sent.update(item_ids)

    def save(self):

        payload = {
            "version": 1,
            "sent": sorted(self.sent),
        }

        temporary = self.path.with_suffix(".tmp")

        temporary.write_text(
            json.dumps(
                payload,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary.replace(self.path)

        LOG.info(
            "Histórico salvo: %s identificadores.",
            len(self.sent),
        )