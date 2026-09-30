# CodeReview

Package name: `CodeReview`.

`scripts/code_review.py` writes an evidence pack (`CURRENT.md` and one dated file) under `2 - RootRecord-Database/CodeReview/`. Logs go under `2 - RootRecord-Database/Logs/CodeReview/`. The script does not patch source.

The coder section stays off unless `RR_CODE_REVIEW_CODER=1`. That flag stays unset. The job `code_review_pack` stays off unless `RR_CODE_REVIEW=1` at poller start. Neither flag is set by this folder.

```text
python3 scripts/code_review.py
python3 scripts/code_review.py --root /tmp/rr-mig-34
```
