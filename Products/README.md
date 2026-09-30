# Products

Desk product apps that were not imported as their own domains. One capitalized folder. Python package name `Products`. No server `Logs/` directory. No `jobs.py` entry.

| Subfolder | Role |
| --- | --- |
| `scripts/Pantry/` | Shelf-count CLI. Store path is `2 - RootRecord-Database/Products/Pantry/stock.json`. The store starts empty. |
| `scripts/ProductPrices/` | Shelf-price CLI. Store path is `2 - RootRecord-Database/Products/ProductPrices/`. The store starts empty. |
| `scripts/FernForest/` | Public lot facts (TMK, lot, acreage, qPublic link). No owner names, mailing addresses, or watts. |
| `scripts/Clients/` | Gig index (domain and page names). nibble.love is not rehosted. |
| `scripts/Companions/` | Source copy only. Not a running path. Do not start these scripts. |
| `scripts/FinanceDesk/` | Source copy only. Not a running path. Do not call Stripe. `--db` stays outside this folder. |
| `scripts/Look/` | Source copy of `look.py` only. Not a running path. The DVR grabber was not copied. |

Public glass-card routes are remote Vercel only. Desk folder `3 - RootRecord-Website/` was removed 2026-09-30. There is no desk checkout. Do not start it again. Do not add a second site. `https://rootserver.rootrecord.cloud/` is the poller on `127.0.0.1:8799`, not a site.

Old themes live in `5 - RootRecord-Library/Archive/Website-Themes/` and stay out of the Vercel build.
