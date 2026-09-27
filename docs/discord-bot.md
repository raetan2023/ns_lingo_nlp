# Discord bot

`bot/discord_bot.py` answers NS lingo questions in Discord, grounded in the glossary.

```
question ──► bot/rag.py (keyword + local embeddings, free) ──► glossary excerpts
                                                                    │
                                          llm.py (OpenRouter / Gemini, 1 call) ◄┘
                                                                    │
                                                              Discord reply
```

## Ways to ask

| How | Example |
|-----|---------|
| Slash command | `/ns question: what does rabak mean?` |
| Mention the bot in a channel | `@NS Lingo kena extra after SBA then cannot book out` |
| Direct message the bot | `what do you call someone who pretends to be sick?` |

Replies end with a small `Glossary: ...` line listing the entries used, so answers can be checked.

## One-time setup

### 1. Create the bot in Discord

1. Go to https://discord.com/developers/applications → **New Application** → name it (e.g. `NS Lingo`).
2. **Bot** tab → **Reset Token** → copy the token. It is shown once.
3. **Installation** (or **OAuth2 → URL Generator**) tab:
   - Scopes: `bot`, `applications.commands`
   - Bot permissions: `Send Messages`, `Send Messages in Threads`, `Read Message History`
4. Open the generated invite URL and add the bot to your server.

No privileged intents are needed. Discord sends message text to bots for DMs and for
messages that mention them, which is all this bot reads.

### 2. Add to `.env` (repo root, never committed)

```
DISCORD_BOT_TOKEN=...
OPENROUTER_API_KEY=sk-or-v1-...      # or GEMINI_API_KEY=...
DISCORD_GUILD_ID=123456789012345678  # optional, see below
```

`DISCORD_GUILD_ID` is your server's ID (Discord settings → Advanced → Developer Mode, then
right-click the server → **Copy Server ID**). With it set, `/ns` appears in that server
immediately. Without it, `/ns` is registered globally, which can take up to an hour to show up.
Mentions and DMs work straight away either way.

### 3. Install and run

```powershell
conda activate ns_lingo_nlp
python -m pip install -r requirements.txt
python bot/discord_bot.py
```

Startup takes ~20s while the embedding model loads. The bot is online only while this
process runs. To keep it up 24/7 it needs to run on an always-on machine or host.

## Cost and limits

| Setting | Value | Where |
|---------|-------|-------|
| LLM cost | ~$0.0001 per question (Gemini 3.1 Flash Lite via OpenRouter) | billed to the API key owner |
| Rate limit | 20 questions per user per rolling hour | `RATE_LIMIT_CALLS` in `discord_bot.py` |
| Max question length | 300 characters | `MAX_QUESTION_CHARS` |

Set a credit limit on the OpenRouter key as a backstop. Replies never ping anyone
(`AllowedMentions.none()`), whatever the LLM writes.

## Hosting (keeping it online 24/7)

The bot keeps a live connection to Discord and loads a ~90MB embedding model (`torch`, ~1GB RAM),
so it needs an always-on machine. Not decided yet (27/09/26).

| Option | Cost | Notes |
|--------|------|-------|
| Oracle Cloud Always Free (Singapore region) | Free | Card needed at signup. ARM shapes often out of capacity; AMD 1GB micro just fits. Idle free VMs can be reclaimed unless the account is upgraded to Pay As You Go (still $0 within limits). |
| Google Cloud e2-micro | Free | Card needed. US regions only. 1GB RAM is tight; may need swap. |
| Paid VPS (Hetzner, DigitalOcean) | ~$4–6/month | Least hassle. |
| Own laptop / PC / Raspberry Pi | Free | Offline whenever the machine sleeps or restarts. |

On a server, run it as a `systemd` service so it starts on boot and restarts after crashes.

### Why not Vercel

Vercel runs code per request and can't hold the gateway connection, and `torch` exceeds its
function size limit. A Vercel version would have to be a rewrite using Discord's HTTP
**Interactions Endpoint** (slash/message commands only):

| Feature | Current bot (server) | Vercel version |
|---------|----------------------|----------------|
| `@mention`, plain DMs | ✅ | ❌ |
| `/ns` in servers and DMs | ✅ | ✅ |
| Paraphrases (local embeddings) | ✅ 37/40 retrieval | ❌ 33/40 keyword-only, unless a paid embeddings API is added |
| Rate limit | In memory | Needs external store (e.g. Upstash Redis) |
| Code changes | None | Signature verification, deferred reply within 3s, follow-up message |
| Hosting cost | Free (Oracle/GCP) or ~$5/month | Free (Hobby) |

## Improving answers

Questions are logged to the console (`user=... q='...'`). When the bot gets one wrong, add it to
`bot/retrieval_cases.json` with the expected term and rerun `python bot/retrieval_eval.py`.
