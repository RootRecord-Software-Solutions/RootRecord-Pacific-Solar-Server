# Root Record

Public home page for Root Record Software Solutions. Vercel builds this repository.

The globe is the page background. Services and operations are glass panels on top of it. Close a panel to use the globe. **+ Services** and **+ Operations** bring a closed panel back.

| File | Role |
| --- | --- |
| [index.html](index.html) | The page |
| [vercel.json](vercel.json) | Static hosting headers |

This repository does not hold measurements. The page reads two feeds from the AWS relay:

| Feed | URL |
| --- | --- |
| Globe arcs | `https://www.rootrecord.cloud/api/state` |
| Last-known operations | `https://www.rootrecord.cloud/api/operations` |

On the desk, edit `1 - Servers/1 - RootRecord-Pacific-Solar-Server/Website/Home/`. The `website` row in `Github/scripts/repos.conf` mirror-publishes that folder here. Do not put a `.git` directory in the umbrella tree. Do not bind port 3001.

Desk scripts, Stripe, and Cloudflare worker source stay in `Website/` outside this folder. They publish with the Pacific repository, not with this one.
