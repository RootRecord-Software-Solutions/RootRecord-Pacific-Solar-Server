# config/

**Owns:** static, data-only definitions — the resource list, tier cadences,
county/UGC maps, per-host rate-limit floors, and text-cleaning rules.

**Does NOT own:** any fetch logic, any HTTP calls, any parsing. Nothing in
this folder imports `core/` or `fetch/`. If you're writing a `def`, it
probably belongs in `core/` or `fetch/` instead — this folder is YAML only.

**Depends on:** nothing. Everything else depends on this.

## Files

- `resources.yaml` — every URL from `NWS_Hawaii_Resource_Map.md`, tagged with
  tier + local path template.
- `tiers.yaml` — cadence per tier (0–6) and per-host rate-limit floors.
- `counties.yaml` — SAME/UGC → county map, plus area-text regex fallback
  patterns for when an alert has no geocode.
- `hosts.yaml` — per-host rate-limit floor, User-Agent string, timeout
  defaults. **Never put credentials or API keys in `resources.yaml` or any
  file the plan says should mirror into a public database — if a key is ever
  needed, it goes here, in the code tree, not the data tree.**
- `text_cleaning.yaml` — the `$` / `$$` / `&` / `&&` segment-marker stripping
  rules as data, not hardcoded regex.

Adding a newly-discovered resource should be a one-line YAML edit here, never
a code change.
