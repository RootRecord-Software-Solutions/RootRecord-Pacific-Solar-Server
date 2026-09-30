---
name: clients
description: >-
  Web-development gig customers (not RootMC/RootRecord memberships). Use when
  asked about clients, nibble.love, paid site work, or customer websites.
---

# clients

These are **web-dev gig customers**. They are not memberships, Gold,
subscribers, or RootMC accounts. Do not mix them with the `membership` skill.

Ops desk is this folder. Live gig files: `gigs/<domain>/`.

## Status (2026-09-16)

Pulled from `/mnt/Projects/Clients`. One gig on disk:

| Gig | Domain | What it is | Files |
| --- | --- | --- | --- |
| Nibble.love | nibble.love | Static HTML for the Big Island community food exchange | `gigs/nibble.love/` |

README in that folder: Cloudflare Pages upload, no build step. Contact form is
mailto. Do not invent extra locations or a live deploy URL unless you checked.

## Rules

1. Client sites stay here (or a path this desk names). Do not dump them into
   RootRecord product sites (`avaivy-cloud`, `holding`, RootMC).
2. Do not treat a client as a member. Billing is the gig, not Gold.
3. Do not open `.env` or dump emails from contact pages into chat.
4. New gig: add a folder under `gigs/` and a row in `references/gigs.md`.

Topic index: `public-edge`. Memberships: `membership`.
