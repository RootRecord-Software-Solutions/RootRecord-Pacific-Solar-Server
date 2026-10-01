# CouncilPersona

Telegram chat prompts for the council voices `ava`, `bruce`, and `carly`.

This folder is the runtime loader. It is not a second identity pack.

| Layer | Path |
| --- | --- |
| Canonical identity | `5 - RootRecord-Library/Agent Context/{Ava,Bruce,Carly}-Agent-Context/` |
| Operational wiring | Old skills packets `agents/{ava-ivy,bruce-monitor,carly-mal}/SKILL.md` (not on the live Pacific tree) |
| Chat prompts | `prompts/{ava,bruce,carly}.md` |
| Loader | `scripts/personas.py` → `system_for(voice)` |

`council-relay.py` passes `system_for` as `RR_PERSONA_SYSTEM`. `run-infer.sh` uses that text on the NPU path only when `RR_SPEC_SYS` is empty. Sampling settings still come from `2 - RootRecord-Database/AI/FLM/Personas/{ava,bruce,carly}.json` when `RR_NPU_PERSONA=1`. Those JSON files are not this loader. The `*-telegram` Ollama Modelfiles are unchanged and apply only on the Ollama fallback.

`system_for` prefixes `SPEAK_LOCK` from `Media/Voice/scripts/speech_scrub.py`.
