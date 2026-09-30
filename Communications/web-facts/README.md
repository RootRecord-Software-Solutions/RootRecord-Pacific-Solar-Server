# Communications/web-facts — allowlisted HTTPS GET (G3 port)

| Field | Value |
| --- | --- |
| **Ported from** | G1 `Solar-Pacific-RootRecord-Server-Old/websites/web-facts/scripts/web_facts.py` (KEPT, unchanged) |
| **Date** | 2026-09-29 13:58 HST (old-repo migration, breadth pass) |
| **State** | LANDED · smoke test PASS · **on demand only** (no job, nothing periodic) |
| **Secrets** | none |

`python3 scripts/web_facts.py <https-url>` → JSON `{ok, url, text, truncated}`. HTTPS only; hosts limited to `api.weather.gov`, `earthquake.usgs.gov`, `en.wikipedia.org`, `lite.wikipedia.org`, `docs.litecoin.org`, `download.litecoin.org`; 8 s timeout; 8 000-byte cap; no cookies / JS.

Not wired to the council relay: council chat replies are BLOCKED (models missing), and adding it to the relay's prompt path is a sign-off decision.

**Check later (Alexander):** whether the allowlist is still right for G3 (e.g. add `volcanoes.usgs.gov`); whether the council relay should call it.
