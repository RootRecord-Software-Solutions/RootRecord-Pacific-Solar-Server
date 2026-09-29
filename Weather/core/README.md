# core/

**Owns:** the shared engine every fetcher in `fetch/` (and `alerts/`,
`hurricanes/`) calls into. One concern per file, strictly:

| File | Job | Never does |
|---|---|---|
| `http_client.py` | rate-floor-enforced GET/HEAD, UA header, conditional GET | know what a "resource" is beyond a URL + floor |
| `change_detection.py` | 3-layer check: headers → HEAD/Content-Length → SHA-256 | make its own HTTP calls (takes a response in) |
| `path_resolver.py` | URL → local path translation | touch the network or the filesystem |
| `archiver.py` | age `_current` out to `archive/MM-DD-YYYY/` under real fetch timestamp | make an HTTP call |
| `daily_zip.py` | HST-midnight consolidation: discover → zip → verify → delete | run itself on a schedule (that's `scheduler/`) |
| `text_cleaner.py` | strip `$`/`$$`/`&`/`&&` per config, collapse blank lines | decide *which* resources get cleaned (that's `fetch/`) |
| `validators.py` | magic-byte + text-sanity checks | touch disk or network |
| `manifest.py` | read/write per-resource state (etag, hash, timestamps, failures) | know what "changed" means (that's `change_detection.py`) |
| `hst_time.py` | single source of truth for HST (UTC-10, no DST) conversion | anything unrelated to time |

**Owns:** the above. **Does NOT own:** anything resource-specific — no URLs,
no knowledge of what SFP or AFD are. That belongs in `fetch/`.

**Depends on:** `config/` (for rate floors, UA strings, cleaning rules).

This is what makes isolating a bug survivable: if an archive folder is
malformed, the search space is `archiver.py` and nothing else.
