# Ava desktop file map (for agents)

All paths relative to `ava-desktop/` in this repo.

## Entry

| File | Role |
|---|---|
| `bin/start-ava-desktop.sh` | Sets `AVA_HOME`/`AVA_HANDOFF` to repo root of the live tree, Pulse/DISPLAY, launches Electron `--no-sandbox`. |
| `main.mjs` | Electron main: window, IPC (`ava:*`), ops spawn, `startAvaSession`, brain fetch to `:8787`. |
| `preload.cjs` | Isolated bridge `window.avaDesktop`. |
| `package.json` | Electron app `rootmc-ava-desktop`. |

## Libraries

| File | Role |
|---|---|
| `lib/avaLifecycle.mjs` | Start/stop uvicorn + voice director. Adopt existing `/health`. Watchdog every 8s. `detached: true` + `unref()` so origin outlives GUI. `stopAvaSession` is explicit power-off only. |
| `lib/avaBridge.mjs` | Tokens from env, rewrite URL, Discord/Slack, public chat helpers. Default API `https://api.rootmc.net`. |
| `lib/avaLinks.mjs` | Canonical operator link groups (status, wiki, products, APIs, community). |
| `lib/avaMedia.mjs` | List/import media under `AVA_HOME/media`. |
| `lib/connectionConfig.mjs` | Local vs remote brain; probe `/health`. |
| `lib/opsCommands.mjs` | Allowlisted Terminal commands. Cron IDs must match `ava-origin-python` scheduler job ids (`time-chime`, `rr-noaa`, `vercel-builds`, …). |

## Renderer (operator UI)

| File | Role |
|---|---|
| `renderer/index.html` | Shell: Ollama badges, activity log, command grid, Core chat, Links, Stream, Finance, Minecraft, shutdown timer, footer Join/Claims/Data. |
| `renderer/app.js` | All UI logic (~4k+ lines): core chat, finance KPIs, stream, links, shutdown, ops filter. |
| `renderer/styles.css` | Dark theme, teal/green accents. |

## Python bundled beside desktop (if present)

Live origin is `ava-origin-python/` at repo root of all-connections (copied from `apps/core`). Desktop historically also had `apps/desktop/core/` as a duplicate — prefer `ava-origin-python/` here.

Scheduler jobs (Honolulu): heartbeat 60s, NOAA 60m, Kīlauea 60m, time chime :00/:30, solar+weather hourly, system perf hourly, player economy 30m, morning 10:00, merged morning 10:05 → `#updates`, Cursor fallback 10:12 & 16:12, economy brief 15:00, overnight 22–05, D1 sync 5m, Vercel builds 5m.

## Voice

Origin tries `apps.voice.director` (not fully copied here). Clips live under `media/audio/`. GUI POSTs `/api/voice/play`.
