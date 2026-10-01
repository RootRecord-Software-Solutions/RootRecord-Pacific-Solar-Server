# Root Record

Public presentation layer for the Root Record ecosystem.

This repository is the site. It explains the architecture and opens controlled paths into the systems underneath. It is not a copy of the runtime, the library, or the database, and it does not hold measurements or private infrastructure detail.

Production is [https://www.rootrecord.cloud/](https://www.rootrecord.cloud/).

## Pages

| Path | Purpose |
| --- | --- |
| `/` | Cinematic entrance, products, and what Root Record builds |
| `/products` | Business Manager by RootRecord, Weather Manager, and Kilauea Alerts |
| `/services` | Web, app, AI workflow, personalized agents, and custom software |
| `/solutions` | Customer problems those products and services address |
| `/about` | Root Record as a software company |
| `/security` | Security, privacy, operations, and the public boundary |
| `/terms` | Terms of Service |
| `/privacy` | Privacy Policy |
| `/data-deletion` | Request deletion of server-stored data without closing the account |
| `/status` | Public system status |
| `/radio` | Continuous stream. Music shuffles. Reports play in full over music at a quarter volume |
| `/reports` | Index of the latest field, energy, and operations readings |
| `/reports/<slug>` | One measured report. Spoken transcripts and persona names stay off the page |
| `/operations` | Public operations readings, including River and Delta charge, solar, and AC charts when the feed has them |
| `/infrastructure` | Hawaiʻi, the Root Record Network, and the Mainland Server |

Navigation is Home, Products, Services, Solutions, About, Security, and Status. Deeper pages stay available from status, reports, and the technology notes. Page footers link to Terms, Privacy, and Data deletion.

## Reports

`Website/scripts/publish_report_pages.py` writes `reports/` from `test-reports/Voice/<key>_current.md` and `Communications/Discord/config/report-channels.json`. Groups are Field, Energy, and Operations. A page is left as it is when the new bytes match. The Discord report relay runs that script before it posts. The post is the title, the measured lines, and `https://www.rootrecord.cloud/reports/<slug>`.

## Service windows

`service-notice.json` in this folder is the public list of planned down times. An empty `windows` array means there is no window. The homepage banner (`assets/service-banner.js`) shows a window that is active, or one that starts inside 24 hours. Dismiss hides that window for the browser session. During an active window, `assets/live.js` shows the stored network counts and labels the panel planned-down. Root Monitor's Telemetry page is what writes the file. The contract is Library `Documentation/02-Runtime-Jobs-and-Control/Desk-Automations-and-Service-Windows.md`.

## Live readings

`assets/telemetry.js` reads `/api/state`, `/api/operations`, and `/service-notice.json`. Missing readings stay missing. `assets/charts.js` draws the operations-page bars (state of charge, solar input, AC output) from those readings. `assets/shell.js` is the small-screen menu. `assets/home.js` draws the homepage globe from the state feed.

## Vocabulary

Hawaiʻi. Mainland Server. Root Record Network. Pacific Solar Server. RootRecord Library. RootRecord Database. The public relationship is Hawaiʻi and the Mainland Server. The site does not name a cloud provider, a finer server location, or private infrastructure.

Products on the public site are software Root Record ships: Business Manager by RootRecord, Weather Manager, and Kilauea Alerts. They are not presented as client case studies.

## Status feed

The homepage, systems page, and status page request `https://api.rootrecord.cloud` for public readings. A missing reading stays missing. Counts and field values are shown only when that feed reports them.
