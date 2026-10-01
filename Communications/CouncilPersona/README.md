# CouncilPersona

Communication adapter. It does not own agent identity.

`scripts/personas.py` reads, in place:

```text
5 - RootRecord-Library/Agent Context/{Ava,Bruce,Carly}-Agent-Context/
    IDENTITY.md
    ROLE-AND-BOUNDS.md
    PRINCIPLES.md
    WORKFLOW.md
```

`council-relay.py` passes that text as `RR_PERSONA_SYSTEM`. Discord `scripts/review.py` uses the same loader when `RR_DISCORD_REVIEW_PIPELINE=1`. There is no prompt copy in this folder.

`CONTEXT/`, `README.md`, `CHANGELOG.md`, and `HANDOFF-TEMPLATE.md` stay in the Library. They are not pasted into each Telegram turn. Council chat context is 4096 tokens (`0002`).

`SPEAK_LOCK` in `Media/Voice/scripts/speech_scrub.py` is a speech rule, not identity.

Sampling settings stay in `2 - RootRecord-Database/AI/FLM/Personas/{ava,bruce,carly}.json`. The `system` field in those files is an old Modelfile copy. It is not the identity. The relay uses it only when `RR_PERSONA_SYSTEM` is empty. Do not edit it to change who an agent is.
