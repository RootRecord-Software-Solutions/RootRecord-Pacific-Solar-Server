# Root Record

Public presentation layer for the Root Record ecosystem.

This repository is the site. It explains the architecture and opens controlled paths into the systems underneath. It is not a copy of the runtime, the library, or the database, and it does not hold measurements or private infrastructure detail.

Production is [https://www.rootrecord.cloud/](https://www.rootrecord.cloud/).

## Pages

| Path | Purpose |
| --- | --- |
| `/` | Live public overview |
| `/ecosystem` | How knowledge, runtime, and data fit together |
| `/infrastructure` | Hawaiʻi, the Root Record Network, and the VPS Node |
| `/operations` | Field systems and operations |
| `/intelligence` | Agents, context, execution, and verification |
| `/data` | Telemetry and persistent state |
| `/knowledge` | RootRecord Library |
| `/security` | Public security posture |
| `/status` | Public system status |
| `/reports` | Public reports from Ava, Bruce, and Carly |
| `/about` | Why Root Record exists |

Navigation stays short: Home, Ecosystem, Systems, Intelligence, Knowledge, Security, Reports, Status, and Login. Deeper pages cross-link.

## Vocabulary

Hawaiʻi. VPS Node. Root Record Network. Pacific Solar Server. RootRecord Library. RootRecord Database. Field systems. Intelligent systems. Runtime. Knowledge layer. Data layer. Verification. Continuity.

The public relationship is Hawaiʻi and the VPS Node. The site does not name a cloud provider, a finer server location, or private infrastructure.

## Status feed

The homepage, systems page, and status page request `https://api.rootrecord.cloud` for public readings. A missing reading stays missing. Counts and field values are shown only when that feed reports them.
