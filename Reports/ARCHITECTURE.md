# Reports and YouTube

One report is the source of truth. Text, audio, and YouTube are outputs of that report.

## Flow

A profile in `pipeline/profiles.json` names the topic, scope, cadence, and which assets to make. The Pacific poller still runs the existing desk jobs. `voice_reports.py` and `system_perf.py` write the same markdown and WAV they already write, then save `pipeline` JSON for that window. The id is `profile + topic + scope + window_start + timezone`. Running it again updates that file.

`pipeline/run.py tick` is the single extra poller job (`RR_REPORT_PIPELINE`). It does not render audio. It records a deterministic news window when a `news_select` profile is enabled and due, refreshes `Reports/canonical/stream-queue.json`, and can answer which report contains the current clock (`recover`).

## Lifecycle

`scheduled`, `collecting`, `assembling`, `generating`, `generated`, `assets_pending`, `assets_ready`, `published`, `archived`, `failed`, `cancelled`.

Text, audio, image, video, and publication each have their own status. A busy Kokoro lock (rc 75) or a YouTube failure leaves the text in place. YouTube stays `not_configured` until `RR_YOUTUBE_STREAM_KEY` is set outside git. This tree does not open an RTMP stream.

## Windows

`pipeline/windows.py` quantizes an explicit clock. Five-minute profiles use bounds such as 14:25–14:30 in `Pacific/Honolulu`. Hourly desks use the clock hour. A filename stamp is not a window. Legacy markdown indexed by `run.py index` keeps `window_start` empty and keeps the file where it is.

## News

The hourly script is still `Media/RadioRss`. A spoken headline is not repeated by the summary. Stories that were spoken are marked `archived` and the next hour reads only `status='new'`. Death and violence terms in `policy.yaml` apply to every feed. Measured weather, quake, and energy desks are not filtered by that list. Earthquake, volcano, and marine-weather wording in news items is dropped on every feed because those desks already own the facts. Hurricane speech drops lines already present on the latest NWS report.

## Read API

The poller serves `GET /api/reports`, `GET /api/reports/{id}`, and `GET /api/reports/{id}/assets`, with `topic`, `scope`, `status`, and `date`. Public HTML still comes from `publish_report_pages.py`, which prefers the sidecar text when that file exists.

## Stream

Mainland `stream.js` plays a report file once per file identity. The same opus is not queued again at the next half-hour. `current_report` and `energy_report` are not queued. A `state/report-queue.json` file, when present, replaces the directory snapshot.

## Not removed

`voice_current_report` is already disabled. There is no `energy_report` job. Historical markdown, WAV, HTML, and old-repo scripts stay on disk.
