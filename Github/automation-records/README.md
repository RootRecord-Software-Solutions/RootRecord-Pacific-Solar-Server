# automation-records

Sync behavior is implemented in `../scripts/sync-all.sh` and `../scripts/push-repo-once.sh`, and scheduled as `github_sync_all` in Pacific `Automations/scripts/jobs.py`.

The public umbrella does not auto-commit the paths in `../scripts/ecosystem-skip-autocommit.txt`. A pull of the umbrella reloads the poller only when Pacific runtime code changes.
