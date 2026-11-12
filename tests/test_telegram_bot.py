from src.telegram_bot import TelegramBot


def test_message_split_respects_limit():

    parts = TelegramBot.split_message(
        "linha\n" * 2000,
        limit=500,
    )

    assert len(parts) > 1

    assert all(
        len(part) <= 500
        for part in parts
    )


def test_history_duplicate_detection(tmp_path):

    from src.history import History

    history = History(
        str(tmp_path / "history.json")
    )

    key = history.occurrence_id(
        "abc",
        "maria",
        3,
        1,
    )

    assert not history.contains(key)

    history.mark_many([key])

    history.save()

    reloaded = History(
        str(tmp_path / "history.json")
    )

    assert reloaded.contains(key)