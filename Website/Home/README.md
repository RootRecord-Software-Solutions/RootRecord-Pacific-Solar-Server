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
| `/status` | Public system status |
| `/reports` | Latest field and operations readings |
| `/infrastructure` | Hawaiʻi, the Root Record Network, and the Mainland Server |

Navigation is Home, Products, Services, Solutions, About, Security, and Status. Deeper pages stay available from status, reports, and the technology notes.

## Vocabulary

Hawaiʻi. Mainland Server. Root Record Network. Pacific Solar Server. RootRecord Library. RootRecord Database. The public relationship is Hawaiʻi and the Mainland Server. The site does not name a cloud provider, a finer server location, or private infrastructure.

Products on the public site are software Root Record ships: Business Manager by RootRecord, Weather Manager, and Kilauea Alerts. They are not presented as client case studies.

## Status feed

The homepage, systems page, and status page request `https://api.rootrecord.cloud` for public readings. A missing reading stays missing. Counts and field values are shown only when that feed reports them.
