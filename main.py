from bot.config import get_settings
from bot.db.session import init_db


def main() -> None:
    settings = get_settings()
    init_db(settings.database_url)
    print(
        "Bot and web are not started yet. "
        "Use bot/main.py or web/app.py entrypoints."
    )


if __name__ == "__main__":
    main()
