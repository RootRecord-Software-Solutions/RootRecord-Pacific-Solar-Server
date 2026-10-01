# mirrors

Mirror mode in `repos.conf` copies a local tree into `Github-worktrees/<id>` at the ecosystem root and syncs that worktree. The public umbrella is `inplace`, not a mirror. `website` is the disabled mirror row. Worktrees stay outside `2 - RootRecord-Database` so the database publish copy cannot loop into itself.
