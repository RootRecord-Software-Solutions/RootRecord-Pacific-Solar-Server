# Council relay contract

Component: `Communications/telegram/scripts/council-relay.py`, started by `ensure-relay.sh`.

## Promises

- Exactly one long-poll, Ava's token, chats listed in `config/relay.conf`.
- Sandbox replies when `SANDBOX_REPLIES=1`, even if `RR_RELAY_REPLIES` is 0.
- Live council and private DMs are held, not answered, while `RR_RELAY_REPLIES` is 0.
- Before a reply, refresh the desk file and the state snapshot.
- Post only the reply text. Drop a reply that echoes `DESK_LIVE:` or the instruction block.
- Eyes reaction, then inference, then typing, then the message.

## Consumes

- Relay config, voice config, persona JSON, measured desk file, state brief.
- Tokens from the environment. They are not written to logs or to the state file.

## Produces

- Telegram messages in the sandbox, from the voice that was routed.
- Inbox lines for held chats.
- A refresh of Database `Intake/desk-live.txt` and `System/status/rootrecord-state.json`.

## What can change it

- `relay.conf` for chat ids and the sandbox switch.
- `ensure-relay.sh` for the NPU flags. The poller starts the relay. Do not start a second one.
- Alexander, by setting `RR_RELAY_REPLIES=1` when the live room should speak.

## Must never happen

- A second getUpdates loop.
- Printing a bot token.
- Enabling quake or stats sends from this process.
- Raising FLM context above 4096, or leaving a 3B model resident.
- Treating a social "how are you" as a license to dump watts, or answering "No data" when the desk lines are present and the person asked what you see.
