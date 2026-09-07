# UniBot

A Telegram bot for browsing university course resources stored in SQLite and forwarding the selected files or Telegram messages to users.

## Repository layout

- `bot2.py`: current bot entry point
- `manager.py`: Tkinter interface for managing the local SQLite database
- `id_finder.py`: optional helper for obtaining Telegram chat and message IDs
- `bot.py`: legacy local-file implementation retained for reference

## Setup

```bash
git clone https://github.com/Alborzsfe/UniBot.git
cd UniBot
python -m venv .venv
pip install -r requirements.txt
```

Set the following environment variables:

- `TELEGRAM_BOT_TOKEN`: a newly generated BotFather token
- `TELEGRAM_CHAT_ID`: ID of the source channel/group used by `bot2.py`

Then run:

```bash
python bot2.py
```

Run `python manager.py` to manage a local database. The bot creates `bot.db` when necessary.

## Privacy and security

- Never commit bot tokens or `.env` files.
- SQLite databases are ignored because the logs can contain Telegram usernames and user IDs.
- Restrict access to the machine and channel used by the bot.
- A token previously committed to Git must be revoked even if it was later deleted.

## Quality check

GitHub Actions verifies that every Python file can be compiled. End-to-end Telegram tests require a separate test bot and are not performed in CI.

## License

MIT
