# Telegram bot

`bot/telegram_bot.py` is the Telegram version of the [Discord bot](discord-bot.md): same glossary,
same LLM, same answers. Shared logic is in `bot/answering.py`.

## Ways to ask

| How | Where | Example |
|-----|-------|---------|
| Just send a message | Private chat with the bot | `what does rabak mean?` |
| Tag the bot: `@botname <question>` | Group (needs privacy mode off, below) | `@nslingo_bot what is ERAC` |
| Reply to one of the bot's messages | Group | (reply) `what about SM?` |
| `/ns <question>` | Private chat or group (still works, not advertised) | `/ns kena extra after SBA then cannot book out` |

`/start` and `/help` show examples. Replies end with an italic `Glossary: ...` line listing the
entries used. Each question is answered on its own; the bot doesn't remember earlier messages.

## One-time setup

### 1. Create the bot with BotFather

1. In Telegram, open **@BotFather** → `/newbot`.
2. Give it a display name (e.g. `NS Lingo`) and a username ending in `bot` (e.g. `nslingo_bot`).
3. Copy the token it gives you. Anyone with it can control the bot, so keep it out of git.
4. Optional, so `/ns` shows in the command menu: `/setcommands` → pick the bot → send
   ```
   ns - Ask what some NS lingo means
   help - Examples of what to ask
   ```
5. Optional: `/setdescription` and `/setuserpic`.

**Turn off group privacy mode** (needed for tagging). It's on by default, and then in groups
Telegram only sends the bot `/ns` commands and replies to its own messages, not messages that tag
it. In BotFather: `/setprivacy` → pick the bot → **Disable**. Then remove and re-add the bot to any
group it's already in, since the setting only applies when it joins. With it off, Telegram sends
the bot every group message, but it ignores the ones that don't tag it or reply to it.

### 2. Add to `.env` (repo root, never committed)

```
TELEGRAM_BOT_TOKEN=123456789:AA...
```

The LLM key (`OPENROUTER_API_KEY` or `GEMINI_API_KEY`) is shared with the Discord bot.

### 3. Run

```powershell
python -m pip install -r requirements.txt
python bot/telegram_bot.py     # Telegram only, for testing
```

Telegram allows only one copy of a bot to poll for messages at a time. If the server is already
running it, a local copy will get `Conflict: terminated by other getUpdates request` errors, so
stop one of them.

## Limits

Same as Discord ([discord-bot.md](discord-bot.md#cost-and-limits)): 300 characters per question,
and 200 questions an hour across everyone, shared by both platforms. There's no per-user limit.
Replies are capped at Telegram's 4096 characters.

## Server (Google Cloud VM)

The server runs both bots from one process, `bot/run_bots.py`. It starts whichever bots have a
token in `.env`. One-time switch on the VM:

```bash
cd ~/ns_lingo_nlp && git pull
source venv/bin/activate && pip install "python-telegram-bot>=21.0"
nano .env                                   # add TELEGRAM_BOT_TOKEN=...
sudo systemctl edit --full ns-lingo         # ExecStart: bot/discord_bot.py -> bot/run_bots.py
sudo systemctl restart ns-lingo
journalctl -u ns-lingo -f                   # expect "Telegram bot polling as @..."
```

After that, updates deploy the same way as before (`git pull` + `sudo systemctl restart ns-lingo`).
