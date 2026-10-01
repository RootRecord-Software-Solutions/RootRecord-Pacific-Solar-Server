# mirrors

Mirror mode in `repos.conf` copies a local tree into `Github-worktrees/<id>` at the ecosystem root and syncs that worktree. The public umbrella is `inplace`, not a mirror. Enabled mirrors are `pacific`, `database`, `library`, `website`, and `website-personal`. Both website rows publish `Website/Home/` only, to the org and to the personal account. Worktrees stay outside `2 - RootRecord-Database` so the database publish copy cannot loop into itself.
